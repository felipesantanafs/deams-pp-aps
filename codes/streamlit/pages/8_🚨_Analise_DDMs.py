"""
🚨 Página 8 — Análise de Encaminhamentos DDM
Painel focado na hipótese causal: o acesso à Delegacia da Mulher (DDM).
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.data_loader import load_sinan_cnes
from utils.charts import apply_theme, COLORS, PALETTE, metric_card_css, render_metric, section_header

st.set_page_config(page_title="Análise DDMs | DDM", page_icon="🚨", layout="wide")
st.markdown(metric_card_css(), unsafe_allow_html=True)

st.markdown("# 🚨 Acesso e Encaminhamento às DDMs")
st.markdown("*Análise focada na atuação das Delegacias de Defesa da Mulher (DDM) e evidências para a hipótese causal das DDMs 24h.*")
st.markdown("---")

df_sinan = load_sinan_cnes()

# Filtros
ano_range = st.slider("Período (Base 🏥 SINAN)", 2015, 2019, (2015, 2019), key="ddm_ano")
df_filt = df_sinan[
    (df_sinan['ano'] >= ano_range[0]) & 
    (df_sinan['ano'] <= ano_range[1])
].copy()

# ─── Cálculos Globais ──────────────────────────────────────────────────
total_casos = len(df_filt)
casos_ddm = df_filt['encaminhamento_delegacia_mulher'].sum()
taxa_ddm = (casos_ddm / total_casos) * 100 if total_casos > 0 else 0

casos_dp_comum = df_filt['encaminhamento_delegacia'].sum()
taxa_dp_comum = (casos_dp_comum / total_casos) * 100 if total_casos > 0 else 0

# ─── KPIs ─────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(render_metric("Total Ocorrências (SINAN)", f"{total_casos:,.0f}".replace(',','.')), unsafe_allow_html=True)
with c2:
    st.markdown(render_metric("Encaminhadas à DDM", f"{casos_ddm:,.0f}".replace(',','.'), f"{taxa_ddm:.1f}% (Base SINAN)"), unsafe_allow_html=True)
with c3:
    st.markdown(render_metric("Encaminhadas à DP Comum", f"{casos_dp_comum:,.0f}".replace(',','.'), f"{taxa_dp_comum:.1f}% (Base SINAN)", "down"), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── Evidências Causalidade e Contexto ───────────────────────────────
st.markdown("""
<div class="insight-box">
    🚨 <strong>O que é uma DDM?</strong><br>
    Diferente de uma Delegacia de Polícia (DP) comum, as <strong>Delegacias de Defesa da Mulher (DDMs)</strong> 
    são especializadas em registrar ocorrências, investigar e apurar crimes de violência contra a mulher. 
    Elas oferecem atendimento humanizado, encaminhamento jurídico e para exames de corpo de delito no IML.
    <br><br>
    🎯 <strong>O Desafio do Acesso (Hipótese Causal)</strong>: O município de São Paulo possui <strong>apenas 9 DDMs territoriais</strong> 
    para cobrir toda a cidade. Antes de funcionarem 24 horas, a restrição de horário destas poucas unidades somada 
    à distância representava uma barreira institucional. A taxa geral de encaminhamento para a DDM a partir do sistema de saúde é 
    abaixo de 20%, o que indica que a restrição de acesso pode desestimular a denúncia formal.
</div>
""", unsafe_allow_html=True)

with st.expander("📍 Ver endereços das 9 DDMs na capital"):
    st.markdown("""
    **• Centro**
    - **1ª DDM Centro**: Rua Bittencourt Rodrigues, 200 - Sé
    
    **• Zona Leste**
    - **5ª DDM Leste**: Rua Doutor Corinto Baldoino Costa, 400 - Tatuapé
    - **7ª DDM Leste**: Rua Sabado D'Angelo, 46 - Itaquera
    - **8ª DDM São Paulo**: Avenida Osvaldo Valle Cordeiro, 190 - Jardim Marília
    
    **• Zona Oeste**
    - **3ª DDM Oeste**: Av. Corifeu de Azevedo Marques, 4.300 (no 93° DP) - Jaguaré
    - **9ª DDM Oeste**: Av. Menotti Laudísio, 286 (ao lado do 87° DP) - Pirituba
    
    **• Zona Norte**
    - **4ª DDM Norte**: Avenida Itaberaba, 731 - Freguesia do Ó
    
    **• Zona Sul**
    - **2ª DDM Sul**: Avenida 11 de Junho, 89 - Saúde
    - **6ª DDM Campo Grande**: Rua Sargento Manoel Barbosa da Silva, 115 - Campo Grande
    """)

st.markdown("<br>", unsafe_allow_html=True)

col1, col2 = st.columns(2)

# ─── Gráfico 1: Evolução do Encaminhamento DDM ───────────────────────
with col1:
    st.markdown(section_header("📈 Evolução da Taxa de Encaminhamento DDM (Base 🏥 SINAN)"), unsafe_allow_html=True)
    
    evol_ddm = df_filt.groupby('ano').agg(
        total=('encaminhamento_delegacia_mulher', 'count'),
        ddm=('encaminhamento_delegacia_mulher', 'sum')
    ).reset_index()
    evol_ddm['taxa'] = (evol_ddm['ddm'] / evol_ddm['total']) * 100

    fig_evol = go.Figure()
    fig_evol.add_trace(go.Scatter(
        x=evol_ddm['ano'], y=evol_ddm['taxa'],
        mode='lines+markers+text',
        text=evol_ddm['taxa'].apply(lambda x: f"{x:.1f}%"),
        textposition='top center',
        line=dict(color=COLORS['primary'], width=3),
        marker=dict(size=10, color=COLORS['secondary']),
        name='% DDM'
    ))
    fig_evol.update_layout(title="Encaminhamentos para DDM (% do Total)", xaxis_title="Ano", yaxis_title="%")
    apply_theme(fig_evol, height=400, show_legend=False)
    st.plotly_chart(fig_evol, use_container_width=True)

# ─── Gráfico 2: DDM por Horário da Ocorrência ────────────────────────
with col2:
    st.markdown(section_header("⏰ Encaminhamento vs. Horário da Ocorrência (Base 🏥 SINAN)"), unsafe_allow_html=True)
    
    df_hora = df_filt[df_filt['hora'].notna()].copy()
    
    # Classificar horário
    def classifica_horario(h):
        if 8 <= h < 18: return 'Horário Comercial (08h-18h)'
        else: return 'Fora de Expediente (18h-08h)'
        
    df_hora['periodo'] = df_hora['hora'].apply(classifica_horario)
    
    hora_ddm = df_hora.groupby('periodo').agg(
        total=('encaminhamento_delegacia_mulher', 'count'),
        ddm=('encaminhamento_delegacia_mulher', 'sum')
    ).reset_index()
    hora_ddm['taxa'] = (hora_ddm['ddm'] / hora_ddm['total']) * 100
    
    fig_hora = go.Figure(data=[
        go.Bar(
            x=hora_ddm['periodo'], y=hora_ddm['taxa'],
            text=hora_ddm['taxa'].apply(lambda x: f"{x:.1f}%"),
            textposition='auto',
            marker_color=[COLORS['danger'], COLORS['success']]
        )
    ])
    fig_hora.update_layout(title="Taxa de Encaminhamento por Período", yaxis_title="% DDM")
    apply_theme(fig_hora, height=400, show_legend=False)
    st.plotly_chart(fig_hora, use_container_width=True)

# ─── Gráfico 3: Concentração de Casos (Hexagon Map) ────────────────────
st.markdown("---")
st.markdown(section_header("📍 Densidade Territorial e Zonas Críticas (Hexagon Binning)"), unsafe_allow_html=True)

df_geo = df_filt[df_filt['latitude'].notna() & df_filt['longitude'].notna()][['latitude', 'longitude']].copy()

# Cores baseadas no print de referência: do azul (baixa) para o vermelho (alta)
color_range = [
    [224, 224, 224], # Cinza (Baixa)
    [52, 152, 219],  # Azul (Relevante)
    [46, 204, 113],  # Verde (Média)
    [241, 196, 15],  # Amarelo (Alta)
    [230, 126, 34],  # Laranja (Centro)
    [231, 76, 60],   # Vermelho (Subcentro/Principal)
    [142, 68, 173]   # Roxo (Máxima)
]

import pydeck as pdk
import urllib.request
import json

# Mapeamento de macro-zonas de São Paulo
ZONAS_SP = {
    'Centro': (['SE'], [255, 255, 255, 200]), # Branco
    'Leste': (['ARICANDUVA-FORMOSA-CARRAO', 'CIDADE TIRADENTES', 'ERMELINO MATARAZZO', 'GUAIANASES', 'ITAIM PAULISTA', 'ITAQUERA', 'MOOCA', 'PENHA', 'SAO MATEUS', 'SAO MIGUEL', 'SAPOPEMBA', 'VILA PRUDENTE'], [231, 76, 60, 200]), # Vermelho
    'Norte': (['CASA VERDE-CACHOEIRINHA', 'FREGUESIA-BRASILANDIA', 'JACANA-TREMEMBE', 'PERUS', 'PIRITUBA-JARAGUA', 'SANTANA-TUCURUVI', 'VILA MARIA-VILA GUILHERME'], [52, 152, 219, 200]), # Azul
    'Oeste': (['BUTANTA', 'LAPA', 'PINHEIROS'], [46, 204, 113, 200]), # Verde
    'Sul': (['CAMPO LIMPO', 'CAPELA DO SOCORRO', 'CIDADE ADEMAR', 'IPIRANGA', 'JABAQUARA', "M'BOI MIRIM", 'PARELHEIROS', 'SANTO AMARO', 'VILA MARIANA'], [241, 196, 15, 200]) # Amarelo
}

# Criar dicionário reverso para busca rápida da cor
subpref_color_map = {}
for zona, (subprefs, color) in ZONAS_SP.items():
    for sp in subprefs:
        subpref_color_map[sp] = color

# Carregar GeoJSON na memória e injetar cores
@st.cache_data
def get_colored_geojson():
    url = 'https://raw.githubusercontent.com/codigourbano/distritos-sp/master/distritos-sp.geojson'
    req = urllib.request.urlopen(url)
    data = json.loads(req.read())
    for feature in data['features']:
        subpref = feature['properties'].get('ds_subpref', '')
        # Atribui a cor da macro-zona ou cinza se não encontrar
        feature['properties']['line_color'] = subpref_color_map.get(subpref, [200, 200, 200, 100])
    return data

geojson_data = get_colored_geojson()

# Camada de delimitação física dos bairros com cores por Zona
geojson_layer = pdk.Layer(
    "GeoJsonLayer",
    data=geojson_data,
    opacity=0.8,
    stroked=True,
    filled=False,
    get_line_color="properties.line_color",
    line_width_min_pixels=2,
)

# Camada hexagonal 2D para densidade
hexagon_layer = pdk.Layer(
    "HexagonLayer",
    data=df_geo,
    get_position=["longitude", "latitude"],
    radius=600, # Raio do hexágono em metros (ajuste de granularidade)
    pickable=True,
    extruded=False, # Gráfico 2D conforme referência do usuário
    color_range=color_range,
    coverage=0.9,
    auto_highlight=True,
)

view_state = pdk.ViewState(
    longitude=-46.6333,
    latitude=-23.5505,
    zoom=9.5,
    pitch=0, # Mapa reto (2D)
    bearing=0
)

r = pdk.Deck(
    layers=[geojson_layer, hexagon_layer],
    initial_view_state=view_state,
    map_style="mapbox://styles/mapbox/dark-v10",
    tooltip={"text": "Densidade de Ocorrências: {elevationValue}"}
)

# Legenda HTML Customizada
legend_html = """
<div style="display: flex; justify-content: space-between; flex-wrap: wrap; background-color: rgba(30,30,30,0.8); padding: 15px; border-radius: 8px; margin-bottom: 10px; border: 1px solid #444;">
    <div style="flex: 1; min-width: 250px;">
        <h4 style="margin-top: 0; margin-bottom: 10px; color: #fff; font-size: 14px;">Densidade (Hexágonos)</h4>
        <div style="display: flex; align-items: center; margin-bottom: 5px;"><div style="width: 15px; height: 15px; background-color: rgb(224,224,224); margin-right: 8px;"></div> <span style="font-size: 12px;">Baixa Concentração (< P20)</span></div>
        <div style="display: flex; align-items: center; margin-bottom: 5px;"><div style="width: 15px; height: 15px; background-color: rgb(52,152,219); margin-right: 8px;"></div> <span style="font-size: 12px;">Área Relevante (P20)</span></div>
        <div style="display: flex; align-items: center; margin-bottom: 5px;"><div style="width: 15px; height: 15px; background-color: rgb(46,204,113); margin-right: 8px;"></div> <span style="font-size: 12px;">Média Concentração (P50)</span></div>
        <div style="display: flex; align-items: center; margin-bottom: 5px;"><div style="width: 15px; height: 15px; background-color: rgb(241,196,15); margin-right: 8px;"></div> <span style="font-size: 12px;">Alta Concentração (P80)</span></div>
        <div style="display: flex; align-items: center; margin-bottom: 5px;"><div style="width: 15px; height: 15px; background-color: rgb(230,126,34); margin-right: 8px;"></div> <span style="font-size: 12px;">Centro (P90)</span></div>
        <div style="display: flex; align-items: center; margin-bottom: 5px;"><div style="width: 15px; height: 15px; background-color: rgb(231,76,60); margin-right: 8px;"></div> <span style="font-size: 12px;">Subcentro (P95)</span></div>
        <div style="display: flex; align-items: center;"><div style="width: 15px; height: 15px; background-color: rgb(142,68,173); margin-right: 8px;"></div> <span style="font-size: 12px;">CBD Principal (P99)</span></div>
    </div>
    <div style="flex: 1; min-width: 250px;">
        <h4 style="margin-top: 0; margin-bottom: 10px; color: #fff; font-size: 14px;">Zonas de SP (Linhas)</h4>
        <div style="display: flex; align-items: center; margin-bottom: 5px;"><div style="width: 20px; height: 3px; background-color: rgb(255,255,255); margin-right: 8px;"></div> <span style="font-size: 12px;">Centro</span></div>
        <div style="display: flex; align-items: center; margin-bottom: 5px;"><div style="width: 20px; height: 3px; background-color: rgb(52,152,219); margin-right: 8px;"></div> <span style="font-size: 12px;">Zona Norte</span></div>
        <div style="display: flex; align-items: center; margin-bottom: 5px;"><div style="width: 20px; height: 3px; background-color: rgb(241,196,15); margin-right: 8px;"></div> <span style="font-size: 12px;">Zona Sul</span></div>
        <div style="display: flex; align-items: center; margin-bottom: 5px;"><div style="width: 20px; height: 3px; background-color: rgb(231,76,60); margin-right: 8px;"></div> <span style="font-size: 12px;">Zona Leste</span></div>
        <div style="display: flex; align-items: center;"><div style="width: 20px; height: 3px; background-color: rgb(46,204,113); margin-right: 8px;"></div> <span style="font-size: 12px;">Zona Oeste</span></div>
    </div>
</div>
"""

st.markdown(legend_html, unsafe_allow_html=True)
st.pydeck_chart(r, use_container_width=True)

st.markdown("""
<div class="insight-box">
    <strong>Interpretação e Zonas de SP:</strong> 
    As linhas coloridas delineiam as cinco macro-zonas de São Paulo (Norte, Sul, Leste, Oeste e Centro). 
    Ao cruzar essa delimitação territorial com a densidade hexagonal (H3-style), fica evidente como a demanda 
    (casos de violência) se concentra ou se espalha. <br><br>
    
    Por exemplo, manchas vermelhas/roxas (CBD/Subcentros) nas áreas delimitadas em amarelo (Zona Sul) e vermelho (Zona Leste) 
    indicam núcleos críticos que exigem a presença imediata de uma DDM ou protocolos de encaminhamento mais robustos. 
    Diferente de pontos soltos, esta visão revela verdadeiros "polos" de incidência de forma clara e geográfica.
</div>
""", unsafe_allow_html=True)
