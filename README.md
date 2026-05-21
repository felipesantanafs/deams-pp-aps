<div align="center">

# 🔬 DEAM-PP — Avaliação de Impacto das Delegacias Especializadas de Atendimento à Mulher

**Violência contra Mulheres no Município de São Paulo:**
*Diagnóstico Espaço-Temporal e Avaliação de Impacto das DDMs*

[![Status](https://img.shields.io/badge/Status-Em%20Desenvolvimento-yellow?style=for-the-badge)]()
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)]()
[![Basedosdados](https://img.shields.io/badge/Base_dos_Dados-BigQuery-150458?style=for-the-badge)]()

---

*Projeto de pesquisa focado na gestão de políticas públicas no município de São Paulo.*

</div>

---

## 📋 Sumário

- [Sobre o Projeto](#-sobre-o-projeto)
- [Problema de Pesquisa](#-problema-de-pesquisa)
- [Cadeia Causal](#-cadeia-causal)
- [Metodologia](#-metodologia)
- [Estrutura do Repositório](#-estrutura-do-repositório)
- [Dados](#-dados)
- [Como Extrair os Dados](#-como-extrair-os-dados)
- [Roadmap](#-roadmap)

---

## 🎯 Sobre o Projeto

Este repositório contém o código-fonte, dados e relatórios do projeto de pesquisa que investiga a **eficácia das Delegacias de Defesa da Mulher (DDMs) com funcionamento 24 horas no município de São Paulo**.

O estudo combina **ciência de dados descritiva** (mapas de calor territoriais e funil da violência) com **avaliação de impacto causal** (Diferenças-em-Diferenças intra-municipal), produzindo evidências acionáveis para subsidiar a gestão de políticas públicas e otimizar a rede de proteção à mulher na capital paulista.

---

## 🔍 Problema de Pesquisa

A violência contra mulheres exige respostas capilarizadas e com disponibilidade ininterrupta, visto que grande parte das agressões em contexto doméstico ocorre durante madrugadas e finais de semana — períodos nos quais DDMs de horário comercial encontram-se fechadas.

O projeto busca responder à seguinte questão principal:
> **As DDMs que funcionam 24 hrs na cidade de São Paulo possuem maior impacto na ampliação de registros (redução da subnotificação) e na prevenção de feminicídios em seus distritos de abrangência, em comparação àquelas que funcionam apenas em horário comercial?**

---

## 🔗 Cadeia Causal

O projeto resolve o paradoxo econométrico da **causalidade reversa de registro**. Avaliar o sucesso de uma delegacia apenas pelo volume de denúncias é falho, pois a delegacia estimula o relato de crimes que já existiam (cifra oculta). 

Para contornar isso, o modelo possui duas variáveis dependentes:

```mermaid
flowchart LR
    A["🏛️ Inauguração/Conversão\nDDM 24h"] --> B["📈 Aumento de Acesso\n(Denúncias/SINAN)"]
    B --> C["🛡️ Proteção Ativa"]
    C --> D["📉 Redução de Letalidade\n(Feminicídios/SIM)"]

    style A fill:#4a90d9,color:#fff,stroke:#2c5f8a
    style B fill:#f5a623,color:#fff,stroke:#c48418
    style C fill:#7b68ee,color:#fff,stroke:#5b48ce
    style D fill:#50c878,color:#fff,stroke:#3a9a5a
```

> [!NOTE]
> Um coeficiente positivo na variável de denúncias (Ameaça/Lesão) indica **sucesso no acesso institucional**, e um coeficiente negativo na variável de óbitos indica **sucesso na eficácia protetiva da vida**.

---

## 📐 Metodologia

### Etapa 1 — Diagnóstico e Ciência de Dados
- **Análise Descritiva Espacial:** Mapas de densidade (Heatmaps) por Distrito Policial e Subprefeitura.
- **Funil da Violência:** Evolução e correlação temporal entre denúncias de Ameaça, Lesão Corporal e Feminicídios na capital.
- **Sazonalidade:** Gráficos temporais cruzando horários e dias da semana.

### Etapa 2 — Avaliação de Impacto Causal
- **Método:** Diferenças-em-Diferenças (DiD) em nível intra-municipal.
- **Controle:** Distritos paulistanos atendidos por DDMs em horário comercial (ou sem especializada) vs. DDMs 24h.
- **Pareamento:** Propensity Score Matching via indicadores socioeconômicos da Fundação SEADE.

### Produto Final
- 📊 Relatório técnico para tomada de decisão (Word).
- 🖥️ Dashboard interativo (Streamlit) com o mapa da capital e simulador de impactos.

---

## 📁 Estrutura do Repositório

```text
deams-pp-aps/
│
├── 📄 README.md                    # Este arquivo
├── 📄 pyproject.toml               # Dependências e metadados do projeto
│
├── 📂 codes/                       # Scripts de extração e pré-processamento
│   ├── extract_sim_bd.py            # Query para dados de Feminicídio — SIM (Base dos Dados)
│   ├── extract_sinan_bd.py          # Query para dados de Violência Não Letal — SINAN (Base dos Dados)
│   ├── extract_cnes_bd.py           # Dicionário geolocalizado do CNES para mapear delegacias
│   ├── merge_sinan_cnes.py          # Unifica o SINAN com as informações espaciais do CNES
│   ├── data_filter_sicpv.py         # Filtragem e limpeza da base SIPCV (Boletins de Ocorrência SSP-SP)
│   ├── pipeline_feminicidio.py      # Pipeline de pré-processamento da base de Feminicídio (2015-2022)
│   └── bd_config.py                 # ⚠️ LOCAL APENAS — contém o Billing ID do Google Cloud. Não versionado.
│
├── 📂 dados/                       # Dados brutos e processados (não versionados por tamanho)
│   ├── sim_feminicidios_sp.csv      # Extraído via BigQuery (SIM) — 7.554 registros
│   ├── sinan_violencia_sp.csv       # Extraído via BigQuery (SINAN) — 108.427 registros
│   ├── cnes_sp_geolocalizado.csv    # Dicionário do CNES extraído via BigQuery — 54.883 registros
│   ├── sinan_cnes_merged.csv        # Base unificada com as coordenadas dos hospitais
│   ├── Feminicidio_2015_2022.xlsx   # Base da SSP-SP
│   ├── SIPCV_2026.xlsx              # Base de Boletins de Ocorrência SSP-SP
│   └── data_sipcv.csv               # SIPCV filtrado e processado
│
└── 📂 relatorios/                  # Relatórios e documentação do projeto
    ├── PROJETO DE PESQUISA-VIOLENCIA SP.docx
    └── PROJETO DE PESQUISA-VIOLENCIA SP.txt
```

---

## 📊 Dados

Os microdados são obtidos diretamente via integração com o data lake público da **Base dos Dados (BigQuery)**, evitando downloads massivos de repositórios legados do DataSUS.

| Base | Fonte Original | Papel no Modelo | Filtros Aplicados |
|------|----------------|-----------------|-------------------|
| **SIM** | DataSUS | Eficácia (Feminicídios) | SP (3550308), Mulheres, CIDs Agressão (X85-Y09) |
| **SINAN** | DataSUS | Acesso (Ameaça/Lesão) | SP (3550308), Mulheres, com **Código CNES (Proxy Geográfico)** |
| **SEADE** | Gov. SP | Covariáveis (Controles) | Dados agregados por distrito (vulnerabilidade, renda) |

---

## 🚀 Como Extrair os Dados

Os scripts em Python dentro da pasta `codes/` já possuem as *queries* SQL otimizadas para processar os dados em nuvem antes de baixar, trazendo apenas o escopo do nosso estudo.

### Pré-requisitos

1. Ter Python 3.10+ instalado com Pandas e `basedosdados`:
   ```bash
   pip install pandas basedosdados
   ```
2. Ter um projeto no **Google Cloud Platform (GCP)**.
3. Estar autenticado no GCP no seu terminal local:
   ```bash
   gcloud auth application-default login
   ```

### Extração

1. Abra o arquivo `codes/extract_sim_bd.py` ou `codes/extract_sinan_bd.py`.
2. Crie o arquivo `codes/bd_config.py` localmente com o seguinte conteúdo:
   ```python
   BILLING_ID = "seu-projeto-id-aqui"
   ```
   > **Atenção:** este arquivo está no `.gitignore` e não deve ser versionado.
3. Execute no terminal:
   ```bash
   python codes/extract_sim_bd.py
   python codes/extract_sinan_bd.py
   ```
4. Os arquivos `.csv` prontos para análise aparecerão automaticamente na pasta `dados/`.

---

## 🗺️ Roadmap

- [x] Reestruturação do escopo do projeto (Foco em São Paulo e DiD Intra-municipal)
- [x] Criação das *queries* otimizadas para extração SIM/SINAN via Base dos Dados
- [x] Extração dos microdados SIM (7.554 registros) e SINAN (108.427 registros)
- [x] Pré-processamento das bases SSP-SP (SIPCV e Feminicídio 2015-2022)
- [ ] Construção do Funil da Violência e EDA Espaço-Temporal
- [ ] Estimação do modelo DiD
- [ ] Construção do Dashboard Interativo (Streamlit)