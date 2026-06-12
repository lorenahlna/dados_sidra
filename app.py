import streamlit as st
import requests
import pandas as pd

# CONFIGURAÇÃO DE DESIGN DA PÁGINA
st.set_page_config(
    page_title="SIDRA v5.6",
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
            st.success("Configurado para: Brasil (all). Prontinho na Guia Principal!")
            
    elif tipo_busca == "Estado (UF)":
        with st.spinner("Buscando estados..."):
            res_uf = requests.get("https://servicodados.ibge.gov.br/api/v1/localidades/estados?ordenar=nome")
            if res_uf.status_code == 200:
                list_uf = res_uf.json()
                opcoes_uf = {f"{uf['nome']} ({uf['sigla']})": str(uf['id']) for uf in list_uf}
                uf_escolhida = st.selectbox("Selecione o Estado:", list(opcoes_uf.keys()))
                
                if st.button("Ativar Estado Selecionado", type="primary"):
                    st.session_state.localidade_selecionada = opcoes_uf[uf_escolhida]
                    st.session_state.nivel_territorial = "3"
                    st.success(f"Estado ativado com sucesso! Código: {opcoes_uf[uf_escolhida]}")
                    
    elif tipo_busca == "Município":
        termo_busca = st.text_input("Digite o nome da cidade (Ex: Belo Horizonte, Redenção...):", value="").strip()
        
        if termo_busca:
            with st.spinner("Consultando municípios na API do IBGE..."):
                res_mun = requests.get("https://servicodados.ibge.gov.br/api/v1/localidades/municipios?ordenar=nome")
                if res_mun.status_code == 200:
                    todos_mun = res_mun.json()
                    filtrados = [m for m in todos_mun if termo_busca.lower() in m['nome'].lower()]
                    
                    if filtrados:
                        opcoes_mun = {f"{m['nome']} - {m['microrregiao']['mesorregiao']['UF']['sigla']}": str(m['id']) for m in filtrados}
                        municipio_escolhido = st.selectbox(f"Encontramos {len(filtrados)} resultados. Selecione o correto:", list(opcoes_mun.keys()))
                        
                        id_final_mun = opcoes_mun[municipio_escolhido]
                        st.markdown(f"**Código de 7 dígitos encontrado:** `{id_final_mun}`")
                        
                        if st.button("🚀 Ativar Município e Direcionar para Pesquisa", type="primary"):
                            st.session_state.localidade_selecionada = id_final_mun
                            st.session_state.nivel_territorial = "6"
                            st.success(f"Cidade ativada! O código {id_final_mun} foi preenchido na Guia Principal.")
                    else:
                        st.error("Nenhum município encontrado com este nome. Tente digitar de outra forma.")

# =========================================================
# GUIA PRINCIPAL
# =========================================================
elif aba_ativa == "📋 Guia Principal":
    st.title("SIDRA v5.6")
    st.caption("Insira os dados à esquerda e veja a mágica acontecer à direita")
    st.markdown("---")
    
    col_inputs, col_outputs = st.columns([1, 2])
    
    with col_inputs:
        st.subheader("📥 Insira os Dados")
        
        tabela_id = st.text_input("ID da Tabela:", value=st.session_state.id_selecionado).strip()
        
        # BOTÃO 1: CONSULTAR TABELA
        if st.button("🔵 CONSULTAR TABELA (Metadados)", type="secondary", use_container_width=True):
            if not tabela_id:
                st.error("Erro: Digite o ID da Tabela.")
            else:
                with st.spinner("Buscando informações no IBGE..."):
                    url_meta = f"https://servicodados.ibge.gov.br/api/v3/agregados/{tabela_id}/metadados"
                    url_periodos = f"https://servicodados.ibge.gov.br/api/v3/agregados/{tabela_id}/periodos"
                    try:
                        res_meta = requests.get(url_meta)
                        res_anos = requests.get(url_periodos)
                        if res_meta.status_code == 200:
                            meta = res_meta.json()
                            anos_data = res_anos.json() if res_anos.status_code == 200 else []
                            
                            st.session_state.meta_nome = meta.get("nome", "Tabela Sem Nome")
                            st.session_state.anos_disp = ", ".join([str(a["id"]) for a in anos_data]) if anos_data else "Não especificado"
                            st.session_state.vars_disp = "\n".join([f"[{v['id']}] {v['nome']}" for v in meta.get("variaveis", [])])
                            
                            classifs_list = []
                            sugestoes = []
                            for c in meta.get("classificacoes", []):
                                cats = ", ".join([f"{cat['id']}:{cat['nome']}" for cat in c.get("categorias", [])])
                                classifs_list.append(f"Subvariável [{c['id']}] {c['nome']}:\n   Categorias: {cats}")
                                sugestoes.append(f"c{c['id']}/all")
                            
                            st.session_state.subvars_disp = "\n\n".join(classifs_list)
                            st.session_state.sugestao_filtro = "/".join(sugestoes)
                            st.toast("Metadados Atualizados!", icon="✅")
                        else:
                            st.error("ID inválido ou erro no IBGE.")
                    except Exception as e:
                        st.error(f"Erro de conexão: {str(e)}")
                        
        st.markdown("---")
        st.subheader("⚙️ Parâmetros do Filtro")
        
        # Recebe os dados dinâmicos salvos nas abas de Catálogo e Localidades
        cod_territorio = st.text_input("Nível Territorial (1=Brasil, 3=Estado, 6=Município):", value=st.session_state.nivel_territorial)
        cod_municipio = st.text_input("Cód. Localidade / Município (all ou id de 7 dígitos):", value=st.session_state.localidade_selecionada)
        
        ano_periodo = st.text_input("Ano (Período) (ex: last 1, all, 2022):", value="last 1")
        variavel = st.text_input("Variável ID (ex: all):", value="all")
        subvariaveis = st.text_input("Subvariáveis / Classificações:", value=st.session_state.sugestao_filtro)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # BOTÃO 2: BAIXAR DADOS
        btn_baixar = st.button("🚀 BAIXAR DADOS DA TABELA", type="primary", use_container_width=True)

    with col_outputs:
        if st.session_state.meta_nome:
            st.info(f"📍 **Tabela Selecionada:** {st.session_state.meta_nome}")
            with st.expander("📂 INFORMAÇÕES E DADOS DISPONÍVEIS", expanded=True):
                sub_tab1, sub_tab2, sub_tab3 = st.tabs(["📅 Anos Disponíveis", "🔢 Variáveis", "🧩 Subvariáveis"])
                with sub_tab1: st.write(st.session_state.anos_disp)
                with sub_tab2: st.text(st.session_state.vars_disp)
                with sub_tab3: st.text(st.session_state.subvars_disp)
        
        st.subheader("📥 Dados Extraídos")
        
        if btn_baixar:
            n_limpo = "".join(filter(str.isdigit, cod_territorio))
            m_limpo = cod_municipio.strip()
            
            url_dados = f"https://apisidra.ibge.gov.br/values/t/{tabela_id}/n{n_limpo}/{m_limpo}/v/{variavel}/p/{ano_periodo}"
            
            if subvariaveis.strip():
                filtro_limpo = subvariaveis.strip() if subvariaveis.strip().startswith("/") else "/" + subvariaveis.strip()
                url_dados += filtro_limpo
                
            with st.spinner("Processando download do IBGE..."):
                try:
                    res_dados = requests.get(url_dados)
                    if res_dados.status_code == 200:
                        json_dados = res_dados.json()
                        
                        if "excecao" in json_dados or (isinstance(json_dados, dict) and json_dados.get("D1C")):
                            st.error(f"Erro retornado pelo IBGE. Verifique os parâmetros informados.")
                        else:
                            df = pd.DataFrame(json_dados)
                            colunas_filtradas = [col for col in df.columns if col.endswith("N") or col in ["V", "MN"]]
                            df_final = df[colunas_filtradas]
                            
                            df_exibicao = df_final[1:].copy()
                            df_exibicao.columns = df_final.iloc[0]
                            
                            st.balloons()
                            st.success("✅ Download concluído com sucesso!")
                            
                            st.dataframe(df_exibicao, use_container_width=True)
                            
                            csv = df_exibicao.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                label="💾 Exportar Tabela para Planilha (CSV)",
                                data=csv,
                                file_name=f"sidra_tabela_{tabela_id}.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
                    else:
                        st.error("Erro na resposta do IBGE.")
                except Exception as e:
                    st.error(f"Erro técnico: {str(e)}")
        else:
            st.info("Aguardando comandos. Preencha os campos e clique em **BAIXAR DADOS DA TABELA**.")

# =========================================================
# ABA: TUTORIAL DE SUBVARIÁVEIS
# =========================================================
elif aba_ativa == "💡 Tutorial Interativo":
    st.title("💡 Tutorial de Subvariáveis (Sua Aba Tutorial)")
    st.markdown("Guia rápido de como preencher o campo de classificações sem travar o script.")
    st.markdown("---")
    
    st.markdown("""
    <div class="card-tutorial">
        <h3>📍 A Estrutura Básica</h3>
        <p>O formato que você deve digitar é sempre: <b>c[CÓDIGO]/[CATEGORIA]</b></p>
        <ul>
            <li><b>c</b>: Letra obrigatória que indica "Classificação".</li>
            <li><b>[CÓDIGO]</b>: O número do grupo (ex: 1 para Sexo, 2 para Cor).</li>
            <li><b>all</b>: Palavra mágica que baixa todos os itens daquele grupo.</li>
            <li><b>/ (Barra)</b>: Separador para adicionar mais filtros.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.subheader("🛠️ Exemplos Práticos de Preenchimento")
    exemplos = {
        "O que você quer": ["Tudo detalhado", "Apenas um item", "Vários itens específicos", "Total Geral"],
        "O que digitar no campo": ["c1/all/c2/all", "c1/1", "c1/1,2", "(Deixar Vazio)"],
        "Explicação Prática": [
            "Baixa todos os Sexos (c1) e todas as Cores (c2) abertos.",
            "Se 1 for o código para 'Homens', baixa apenas homens.",
            "Baixa os itens 1 e 2 (ex: Homens e Mulheres), ignorando o resto.",
            "Se deixar a caixinha vazia, o IBGE ignora divisões e traz apenas a soma total da cidade."
        ]
    }
    st.table(pd.DataFrame(exemplos))
