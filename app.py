import streamlit as st
import requests
import pandas as pd

# CONFIGURAÇÃO DE DESIGN DA PÁGINA
st.set_page_config(
    page_title="SidraX",
    page_icon="📊",
    layout="wide"
)

# Customização visual 
st.markdown("""
    <style>
    .main { background-color: #f4f6f9; }
    h1, h2, h3 { color: #003399 !important; font-family: 'Segoe UI', sans-serif; }
    .stButton>button { border-radius: 8px; font-weight: bold; background-color: #003399; color: white; }
    .stButton>button:hover { background-color: #002266; color: white; }
    div[data-testid="stExpander"] { background-color: #ffffff; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .card-tutorial { background-color: #e6f0ff; padding: 15px; border-left: 5px solid #003399; border-radius: 4px; }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# CARREGAMENTO ARQUIVO REPOSITÓRIO
# ---------------------------------------------------------
@st.cache_data
def carregar_dados_catalogo():
    try:
        # Lê o arquivo JSON estável que está no seu repositório
        df = pd.read_json('tabelas.json', dtype={'ID': str})
        return df
    except Exception as e:
        # Caso o arquivo dê erro ou não seja encontrado, cria um aviso para não travar o app
        return pd.DataFrame([{
            "Grupo": "Erro", 
            "Assunto": "Erro", 
            "ID": "9606", 
            "Nome": "Arquivo tabelas.json não encontrado ou inválido", 
            "Anos": "-", 
            "Descrição": str(e)
        }])

df_catalogo = carregar_dados_catalogo()

# Estado da sessão para não perder variáveis no clique e transferir entre as telas
if "id_selecionado" not in st.session_state: st.session_state.id_selecionado = "9606"
if "localidade_selecionada" not in st.session_state: st.session_state.localidade_selecionada = "all"
if "nivel_territorial" not in st.session_state: st.session_state.nivel_territorial = "6"
if "meta_nome" not in st.session_state: st.session_state.meta_nome = ""
if "anos_disp" not in st.session_state: st.session_state.anos_disp = ""
if "vars_disp" not in st.session_state: st.session_state.vars_disp = ""
if "subvars_disp" not in st.session_state: st.session_state.subvars_disp = ""
if "sugestao_filtro" not in st.session_state: st.session_state.sugestao_filtro = ""

# =========================================================
# NAVEGAÇÃO POR MENU LATERAL 
# =========================================================
st.sidebar.title("📊 DADOS SIDRA")
aba_ativa = st.sidebar.radio(
    "Navegar para:",
    ["📋 Guia Principal", "📖 Catálogo (Consultas)", "📍 Localidades (Cód. IBGE)", "💡 Tutorial Interativo"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🗺️ Parâmetros Ativos:")
st.sidebar.info(f"**Tabela ID:** {st.session_state.id_selecionado}\n\n**Cód. Local:** {st.session_state.localidade_selecionada}")

# =========================================================
# ABA: CATALOGO DE CONSULTAS (LENDO DO REPOSITÓRIO JSON)
# =========================================================
if aba_ativa == "📖 Catálogo (Consultas)":
    st.title("📖 Catálogo de Tabelas")
    st.markdown("Selecione uma tabela no catálogo abaixo para configurar os filtros automaticamente.")
    
    # Exibe a tabela lida do JSON
    st.dataframe(df_catalogo, use_container_width=True, hide_index=True)
    
    st.subheader("🎯 Ativação Rápida:")
    if "Grupo" in df_catalogo.columns:
        grupos = df_catalogo["Grupo"].unique()
        
        for g in grupos:
            with st.expander(f"📁 Tabelas de {g}"):
                sub_df = df_catalogo[df_catalogo["Grupo"] == g]
                for _, row in sub_df.iterrows():
                    id_limpo = str(row['ID']).strip()
                    if st.button(f"Ativar Tabela {id_limpo} - {row['Nome']}", key=f"btn_{id_limpo}"):
                        st.session_state.id_selecionado = id_limpo
                        st.success(f"Tabela {id_limpo} ativada! Vá para a '📋 Guia Principal' para rodar.")

# =========================================================
# ABA: CONSULTA DE LOCALIDADES (AUTOMÁTICA)
# =========================================================
elif aba_ativa == "📍 Localidades (Cód. IBGE)":
    st.title("📍 Localizador de Municípios e Estados")
    st.markdown("Pesquise o nome da cidade para capturar automaticamente o código de 7 dígitos exigido pelo SIDRA.")
    st.markdown("---")
    
    tipo_busca = st.selectbox("O que deseja buscar?", ["Município", "Estado (UF)", "Todo o Brasil"])
    
    if tipo_busca == "Todo o Brasil":
        st.info("Para pesquisar dados agregados de todo o país, o código padrão é **all**.")
        if st.button("Ativar código para o Brasil Inteiro", type="primary"):
            st.session_state.localidade_selecionada = "all"
            st.session_state.nivel_territorial = "1"
            st.success("Configurado para: Brasil (all).
