"""
causal_model.py
Executa a modelagem de inferência causal combinando:
1. Propensity Score Matching (PSM) para parear distritos com e sem DDM.
2. Diferenças-em-Diferenças (DiD) de painel (efeitos fixos) para estimar o efeito das DDMs 24h.
Salva os resultados em dados/consolidado/causal_results.json.
"""
import pandas as pd
import numpy as np
import json
import os
import unicodedata
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import statsmodels.api as sm
import statsmodels.formula.api as smf

# Garantir diretórios
os.makedirs("dados/consolidado", exist_ok=True)

# --- 1. CARREGAR OS DADOS ---
print("Carregando bases de dados...")
df_socio = pd.read_csv("dados/consolidado/distritos_socioeconomico.csv")
df_sinan = pd.read_csv("dados/sinan/sinan_cnes_merged.csv", low_memory=False)
df_fem = pd.read_excel("dados/ssp/dados_feminicidio.xlsx")

# Normalizar nomes de distritos para casamento perfeito
def normalize_name(name):
    if pd.isna(name):
        return ""
    name = str(name).strip().lower()
    name = ''.join(c for c in unicodedata.normalize('NFD', name) if unicodedata.category(c) != 'Mn')
    return name

df_socio['distrito_norm'] = df_socio['distrito'].apply(normalize_name)

# Dicionário de mapeamento manual para os bairros mais comuns nas bases SSP e SINAN
manual_mapping = {
    "jardim somara": "itaim paulista",
    "ermelino matarazo": "ermelino matarazzo",
    "parque america": "grajau",
    "jardim iva": "sapopemba",
    "jardim copacabana": "sao mateus",
    "cidade lider": "cidade lider",
    "jardim angela": "jardim angela",
    "sao miguel paulista": "sao miguel",
    "jardim helena": "jardim helena",
    "jardim sao luis": "jardim sao luis",
    "jd. marilia": "sao mateus",
    "jardim marilia": "sao mateus",
    "bras": "bras",
    "se": "se",
    "bosque da saude (s.p.)": "saude",
    "saude": "saude",
    "freguesia do o": "freguesia do o",
    "capao redondo": "capao redondo",
    "tatuape": "tatuape",
    "itaquera": "itaquera",
    "pirituba": "pirituba",
    "jaguare": "jaguare",
    "campo grande": "campo grande",
    "santo amaro": "santo amaro",
    "cambuci": "cambuci",
}

# Lista oficial de distritos normalizados para busca de correspondência mais próxima
official_districts = df_socio['distrito_norm'].tolist()

def map_to_district(bairro_name):
    norm = normalize_name(bairro_name)
    if not norm:
        return None
    # Verificar mapeamento manual primeiro
    if norm in manual_mapping:
        return manual_mapping[norm]
    # Verificar se já é um distrito oficial
    if norm in official_districts:
        return norm
    # Busca por correspondência aproximada (se contém o nome do distrito)
    for dist in official_districts:
        if dist in norm or norm in dist:
            return dist
    return None

# --- 2. GERAR O PAINEL DE DISTRITOS × ANOS ---
print("Processando painel de Distritos...")

# Mapear e agregar SINAN (Notificações)
df_sinan['distrito_mapped'] = df_sinan['bairro'].apply(map_to_district)
df_sinan_filt = df_sinan[df_sinan['distrito_mapped'].notna() & (df_sinan['ano'].between(2015, 2019))]
panel_sinan = df_sinan_filt.groupby(['distrito_mapped', 'ano']).size().reset_index(name='notificacoes')

# Mapear e agregar SSP (Feminicídios) usando a circunscrição da delegacia (ou elaboração como fallback)
df_fem['distrito_mapped'] = df_fem['DP_CIRCUNSCRICAO'].apply(map_to_district)
df_fem.loc[df_fem['distrito_mapped'].isna(), 'distrito_mapped'] = df_fem.loc[df_fem['distrito_mapped'].isna(), 'DP_ELABORACAO'].apply(map_to_district)

df_fem_filt = df_fem[df_fem['distrito_mapped'].notna() & (df_fem['ANO ESTATISTICA'].between(2015, 2019))]
panel_fem = df_fem_filt.groupby(['distrito_mapped', 'ANO ESTATISTICA']).size().reset_index(name='feminicicios')
panel_fem.rename(columns={'ANO ESTATISTICA': 'ano'}, inplace=True)

# Criar a matriz base do Painel Balanceado (96 distritos × 5 anos = 480 observações)
years = list(range(2015, 2020))
panel_base = []
for dist in official_districts:
    for y in years:
        panel_base.append({"distrito_norm": dist, "ano": y})
df_panel = pd.DataFrame(panel_base)

# Mesclar com os dados agregados de ocorrências
df_panel = df_panel.merge(panel_sinan, left_on=['distrito_norm', 'ano'], right_on=['distrito_mapped', 'ano'], how='left')
df_panel = df_panel.merge(panel_fem, left_on=['distrito_norm', 'ano'], right_on=['distrito_mapped', 'ano'], how='left')

# Preencher Nulos com 0 (distrito/ano sem registro = 0 ocorrências)
df_panel['notificacoes'] = df_panel['notificacoes'].fillna(0).astype(int)
df_panel['feminicicios'] = df_panel['feminicicios'].fillna(0).astype(int)
df_panel.drop(columns=['distrito_mapped_x', 'distrito_mapped_y'], errors='ignore', inplace=True)

# Mesclar com covariáveis socioeconômicas (estáticas)
df_panel = df_panel.merge(df_socio, on='distrito_norm', how='inner')

# --- 3. PROPENSITY SCORE MATCHING (PSM) ---
print("Executando Propensity Score Matching (PSM)...")

# Definir os distritos tratados (que possuem DDM)
# 9 distritos com DDM
ddm_districts = ["cambuci", "saude", "jaguare", "freguesia do o", "tatuape", "campo grande", "itaquera", "sao mateus", "pirituba"]

# Construir base de cross-section por distrito para o Matching
df_matching = df_socio.copy()
df_matching['has_ddm'] = df_matching['distrito_norm'].isin(ddm_districts).astype(int)

# Variáveis para pareamento
X_cols = ['populacao', 'renda_per_capita', 'ipvs', 'idh']
X = df_matching[X_cols]
y = df_matching['has_ddm']

# Escalonar variáveis
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Rodar Regressão Logística para estimar o Propensity Score
lr = LogisticRegression(random_state=42)
lr.fit(X_scaled, y)
df_matching['propensity_score'] = lr.predict_proba(X_scaled)[:, 1]

# Algoritmo de Pareamento (Nearest Neighbor 1-para-1 sem reposição)
treated = df_matching[df_matching['has_ddm'] == 1].sort_values('propensity_score', ascending=False)
control_pool = df_matching[df_matching['has_ddm'] == 0].copy()

matched_pairs = []
used_controls = set()

for idx, tr_row in treated.iterrows():
    # Encontrar o controle mais próximo que ainda não foi usado
    avail_controls = control_pool[~control_pool['distrito_norm'].isin(used_controls)]
    if len(avail_controls) == 0:
        break
    
    # Diferença absoluta no propensity score
    diff = (avail_controls['propensity_score'] - tr_row['propensity_score']).abs()
    best_match_idx = diff.idxmin()
    best_control = avail_controls.loc[best_match_idx]
    
    matched_pairs.append({
        "treated_district": tr_row['distrito'],
        "treated_score": round(tr_row['propensity_score'], 4),
        "control_district": best_control['distrito'],
        "control_score": round(best_control['propensity_score'], 4),
        "score_diff": round(abs(tr_row['propensity_score'] - best_control['propensity_score']), 4)
    })
    used_controls.add(best_control['distrito_norm'])

print(f"Pareamento concluído. {len(matched_pairs)} pares criados.")

# Lista dos distritos selecionados para a amostra pareada
matched_districts_norm = ddm_districts + list(used_controls)
df_panel_matched = df_panel[df_panel['distrito_norm'].isin(matched_districts_norm)].copy()

# Definir tratamento na amostra pareada
df_panel_matched['has_ddm'] = df_panel_matched['distrito_norm'].isin(ddm_districts).astype(int)

# --- 4. DIFERENÇAS-EM-DIFERENÇAS (DiD) ---
print("Estimando o modelo de Diferenças-em-Diferenças...")

# Definir a variável post24h de tratamento escalonado:
# Apenas bairros com DDM 24h em operação recebem 1 nos anos em que funcionam 24h.
# 1ª DDM Centro (Cambuci): torna-se 24h em Agosto de 2016 -> 1 em 2016, 2017, 2018, 2019
# 7ª DDM Leste (Itaquera) e 8ª DDM Leste (São Mateus): tornam-se 24h em Agosto de 2018 -> 1 em 2018, 2019
# Todos os outros distritos (com DDM comercial ou controle) são 0 sempre.
def check_post24h(row):
    dist = row['distrito_norm']
    ano = row['ano']
    if dist == 'cambuci' and ano >= 2016:
        return 1
    elif dist in ['itaquera', 'sao mateus'] and ano >= 2018:
        return 1
    return 0

df_panel_matched['post24h'] = df_panel_matched.apply(check_post24h, axis=1)
df_panel['post24h'] = df_panel.apply(check_post24h, axis=1)

# Regressão DiD de Efeitos Fixos (Bairro e Ano) usando OLS na amostra pareada
model_sinan = smf.ols("notificacoes ~ post24h + C(distrito) + C(ano)", data=df_panel_matched).fit(
    cov_type='cluster', cov_kwds={'groups': df_panel_matched['distrito']}
)
model_fem = smf.ols("feminicicios ~ post24h + C(distrito) + C(ano)", data=df_panel_matched).fit(
    cov_type='cluster', cov_kwds={'groups': df_panel_matched['distrito']}
)

# Regressão DiD de Efeitos Fixos na amostra completa (96 distritos - maior poder estatístico)
model_sinan_full = smf.ols("notificacoes ~ post24h + C(distrito) + C(ano)", data=df_panel).fit(
    cov_type='cluster', cov_kwds={'groups': df_panel['distrito']}
)
model_fem_full = smf.ols("feminicicios ~ post24h + C(distrito) + C(ano)", data=df_panel).fit(
    cov_type='cluster', cov_kwds={'groups': df_panel['distrito']}
)

# --- 5. AVALIAR O BALANCEAMENTO DAS COVARIÁVEIS (TESTE DE QUALIDADE) ---
balance_stats = {}
for col in X_cols:
    tr_mean = df_matching[df_matching['has_ddm'] == 1][col].mean()
    ctrl_mean_all = df_matching[df_matching['has_ddm'] == 0][col].mean()
    ctrl_mean_matched = df_matching[df_matching['distrito_norm'].isin(used_controls)][col].mean()
    
    balance_stats[col] = {
        "treated_mean": round(tr_mean, 2),
        "control_mean_all": round(ctrl_mean_all, 2),
        "control_mean_matched": round(ctrl_mean_matched, 2),
        "bias_reduction_pct": round(abs((tr_mean - ctrl_mean_all) - (tr_mean - ctrl_mean_matched)) / abs(tr_mean - ctrl_mean_all) * 100, 1) if abs(tr_mean - ctrl_mean_all) > 0 else 100
    }

# --- 6. SALVAR RESULTADOS PARA O STREAMLIT ---
causal_results = {
    "matched_pairs": matched_pairs,
    "balance_stats": balance_stats,
    "did_results_sinan": {
        "coef": round(model_sinan.params['post24h'], 4),
        "std_err": round(model_sinan.bse['post24h'], 4),
        "t_stat": round(model_sinan.tvalues['post24h'], 4),
        "p_value": round(model_sinan.pvalues['post24h'], 4),
        "ci_lower": round(model_sinan.conf_int().loc['post24h', 0], 4),
        "ci_upper": round(model_sinan.conf_int().loc['post24h', 1], 4),
        "r2_adj": round(model_sinan.rsquared_adj, 4),
        "n_obs": int(model_sinan.nobs)
    },
    "did_results_fem": {
        "coef": round(model_fem.params['post24h'], 4),
        "std_err": round(model_fem.bse['post24h'], 4),
        "t_stat": round(model_fem.tvalues['post24h'], 4),
        "p_value": round(model_fem.pvalues['post24h'], 4),
        "ci_lower": round(model_fem.conf_int().loc['post24h', 0], 4),
        "ci_upper": round(model_fem.conf_int().loc['post24h', 1], 4),
        "r2_adj": round(model_fem.rsquared_adj, 4),
        "n_obs": int(model_fem.nobs)
    },
    "did_results_sinan_full": {
        "coef": round(model_sinan_full.params['post24h'], 4),
        "std_err": round(model_sinan_full.bse['post24h'], 4),
        "t_stat": round(model_sinan_full.tvalues['post24h'], 4),
        "p_value": round(model_sinan_full.pvalues['post24h'], 4),
        "ci_lower": round(model_sinan_full.conf_int().loc['post24h', 0], 4),
        "ci_upper": round(model_sinan_full.conf_int().loc['post24h', 1], 4),
        "r2_adj": round(model_sinan_full.rsquared_adj, 4),
        "n_obs": int(model_sinan_full.nobs)
    },
    "did_results_fem_full": {
        "coef": round(model_fem_full.params['post24h'], 4),
        "std_err": round(model_fem_full.bse['post24h'], 4),
        "t_stat": round(model_fem_full.tvalues['post24h'], 4),
        "p_value": round(model_fem_full.pvalues['post24h'], 4),
        "ci_lower": round(model_fem_full.conf_int().loc['post24h', 0], 4),
        "ci_upper": round(model_fem_full.conf_int().loc['post24h', 1], 4),
        "r2_adj": round(model_fem_full.rsquared_adj, 4),
        "n_obs": int(model_fem_full.nobs)
    }
}

output_results_path = "dados/consolidado/causal_results.json"
with open(output_results_path, 'w', encoding='utf-8') as f:
    json.dump(causal_results, f, ensure_ascii=False, indent=4)

print(f"Resultados da modelagem causal gravados com sucesso em: {output_results_path}")
print("\n=== RESUMO DAS ESTIMATIVAS DiD (AMOSTRA PAREADA) ===")
print(f"1. Acesso (Notificações SINAN): Coef: {causal_results['did_results_sinan']['coef']}, P-valor: {causal_results['did_results_sinan']['p_value']}")
print(f"2. Letalidade (Feminicídios SSP): Coef: {causal_results['did_results_fem']['coef']}, P-valor: {causal_results['did_results_fem']['p_value']}")
print("\n=== RESUMO DAS ESTIMATIVAS DiD (AMOSTRA COMPLETA - 96 DISTRITOS) ===")
print(f"1. Acesso (Notificações SINAN): Coef: {causal_results['did_results_sinan_full']['coef']}, P-valor: {causal_results['did_results_sinan_full']['p_value']}")
print(f"2. Letalidade (Feminicídios SSP): Coef: {causal_results['did_results_fem_full']['coef']}, P-valor: {causal_results['did_results_fem_full']['p_value']}")
print("====================================================")
