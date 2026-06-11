import streamlit as st
import requests
import pandas as pd

# Configuração da página do Streamlit
st.set_page_config(
    page_title="ROBÔ SIDRA v5.6",
    page_icon="📊",
    layout="wide"
)

st.title("📊 ROBÔ SIDRA v5.6")
st.markdown("---")

# Criando duas colunas principais no Layout: Esquerda para Configurações, Direita para Resultados
col_config, col_resultado = st.columns([1, 2])

# Inicializando variáveis no estado da sessão (Session State) para guardar metadados
if "meta_nome" not in st.session_state:
    st.session_state.meta_nome = ""
if "anos_disp" not in st.session_state:
    st.session_state.anos_disp = ""
if "vars_disp" not in st.session_state:
    st.session_state.vars_disp = ""
if "subvars_disp" not in st.session_state:
    st.session_state.subvars_disp = ""
if "sugestao_filtro" not in st.session_state:
    st.session_state.sugestao_filtro = ""

# ==========================================
# COLUNA DA ESQUERDA: ENTRADAS E CONFIGURAÇÕES
# ==========================================
with col_config:
    st.header("⚙️ Parâmetros de Busca")
    
    # Campo equivalente à célula B2 da Guia
    tabela_id = st.text_input("ID da Tabela (ex: 1737, 1612):", value="1737").strip()
    
    # Botão para consultar metadados (Passo 1)
    if st.button("1. Consultar Metadados (Anos/Vars/Subs)", use_container_width=True):
        if not tabela_id:
            st.error("Erro: Digite o ID da Tabela.")
        else:
            with st.spinner("Buscando metadados no IBGE..."):
                url_meta = f"https://servicodados.ibge.gov.br/api/v3/agregados/{tabela_id}/metadados"
                url_periodos = f"https://servicodados.ibge.gov.br/api/v3/agregados/{tabela_id}/periodos"
                
                try:
                    res_meta = requests.get(url_meta)
                    res_anos = requests.get(url_periodos)
                    
                    if res_meta.status_code == 200 and res_anos.status_code == 200:
                        meta = res_meta.json()
                        anos_data = res_anos.json()
                        
                        # Processando dados igual ao seu script
                        st.session_state.meta_nome = meta.get("nome", "")
                        st.session_state.anos_disp = ", ".join([str(a["id"]) for a in anos_data])
                        st.session_state.vars_disp = "\n".join([f"[{v['id']}] {v['nome']}" for v in meta.get("variaveis", [])])
                        
                        classifs_list = []
                        sugestoes = []
                        for c in meta.get("classificacoes", []):
                            cats = ", ".join([f"{cat['id']}:{cat['nome']}" for cat in c.get("categorias", [])])
                            classifs_list.append(f"Subvariável [{c['id']}] {c['nome']}:\n   Categorias: {cats}")
                            sugestoes.append(f"c{c['id']}/all")
                        
                        st.session_state.subvars_disp = "\n\n".join(classifs_list)
                        st.session_state.sugestao_filtro = "/".join(sugestoes)
                        st.toast("Metadados carregados com sucesso!", icon="✅")
                    else:
                        st.error("Erro ao acessar API do IBGE. Verifique o ID da tabela.")
                except Exception as e:
                    st.error(f"Erro ao buscar metadados: {str(e)}")

    if st.session_state.meta_nome:
        st.info(f"📋 **Tabela selecionada:**\n{st.session_state.meta_nome}")

    st.markdown("---")
    st.subheader("Filtros para Download")
    
    # Campos equivalentes às células B3, B5, B6 e B8 da planilha Guia
    # Deixei valores padrão comuns do SIDRA para facilitar o teste inicial
    n_territorio = st.text_input("Nível Territorial (Apenas números - ex: 6 para Municípios):", value="6")
    periodos = st.text_input("Períodos / Anos (ex: last 1, 2023, all):", value="last 1")
    variavel = st.text_input("ID da Variável (ex: 226):", value="all")
    
    # Campo de classificação pré-preenchido com a sugestão que veio dos metadados
    classificacao = st.text_input(
        "Subvariáveis / Classificações (Opcional):", 
        value=st.session_state.sugestao_filtro,
        help="Exemplo: c1/all"
    )

    # Botão para Baixar Dados (Passo 2)
    botao_baixar = st.button("2. Baixar Dados com Filtros", type="primary", use_container_width=True)

# ==========================================
# COLUNA DA DIREITA: EXIBIÇÃO DOS RESULTADOS
# ==========================================
with col_resultado:
    # Se existirem metadados carregados, mostra em abas organizadas
    if st.session_state.meta_nome:
        st.header("📋 Informações da Tabela")
        aba_anos, aba_vars, aba_subs = st.tabs(["📅 Anos Disponíveis", "🔢 Variáveis", "🧩 Subvariáveis"])
        
        with aba_anos:
            st.write(st.session_state.anos_disp)
        with aba_vars:
            st.text(st.session_state.vars_disp)
        with aba_subs:
            st.text(st.session_state.subvars_disp)
        st.markdown("---")

    st.header("📥 Dados Baixados")
    
    if botao_baixar:
        # Limpando caracteres não numéricos do território como no seu script original
        n_limpo = "".join(filter(str.isdigit, n_territorio))
        
        # Montando a URL da API SIDRA
        url_dados = f"https://apisidra.ibge.gov.br/values/t/{tabela_id}/n6/{n_limpo}/v/{variavel}/p/{periodos}"
        
        if classificacao.strip():
            filtro_limpo = classificacao.strip() if classificacao.strip().startswith("/") else "/" + classificacao.strip()
            url_dados += filtro_limpo
            
        with st.spinner("Fazendo download dos dados..."):
            try:
                res_dados = requests.get(url_dados)
                
                if res_dados.status_code != 200:
                    st.error(f"Erro no IBGE: {res_dados.text}")
                else:
                    json_dados = res_dados.json()
                    
                    if "excecao" in json_dados or (isinstance(json_dados, dict) and json_dados.get("D1C")):
                         st.error(f"Erro retornado pelo SIDRA: {json_dados}")
                    else:
                        # Convertendo o JSON para DataFrame do Pandas (equivalente às linhas da Guia Dados)
                        df = pd.DataFrame(json_dados)
                        
                        # Filtro de colunas exatamente igual à sua lógica App Script:
                        # Pega chaves que terminam com "N" (Nomes), além de "V" (Valor) e "MN" (Unidade de Medida)
                        colunas_filtradas = [col for col in df.columns if col.endswith("N") or col in ["V", "MN"]]
                        df_final = df[colunas_filtradas]
                        
                        # Ajustando a primeira linha como cabeçalho para ficar bonito visualmente no Streamlit
                        # O IBGE traz os nomes das colunas na primeira linha de dados
                        novos_cabecalhos = df_final.iloc[0]
                        df_exibicao = df_final[1:]
                        df_exibicao.columns = novos_cabecalhos
                        
                        st.success("✅ Download concluído com sucesso!")
                        
                        # Exibe a tabela interativa na tela
                        st.dataframe(df_exibicao, use_container_width=True)
                        
                        # Recurso extra do Streamlit: Botão para o usuário baixar em Excel/CSV direto no PC se quiser!
                        csv = df_exibicao.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 Baixar esta tabela em CSV",
                            data=csv,
                            file_name=f"sidra_tabela_{tabela_id}.csv",
                            mime="text/csv",
                        )
                        
            except Exception as e:
                st.error(f"Erro ao processar dados: {str(e)}")
    else:
        st.info("Preencha os parâmetros à esquerda e clique em 'Baixar Dados' para visualizar a tabela aqui.")
