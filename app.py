import streamlit as st
import gspread
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from google.oauth2.service_account import Credentials
import io  # Necessário para a exportação de arquivos


# 1. Configurações Iniciais da Página
st.set_page_config(page_title="Dashboard de Performance - Escrita", layout="wide")

# --- BLOCO DE SEGURANÇA VISUAL DEFINITIVO ---
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            
            /* Esconde a Toolbar e botões de Status/Deploy para usuários externos */
            [data-testid="stToolbar"] {visibility: hidden !important; display: none !important;}
            [data-testid="stStatusWidget"] {visibility: hidden !important; display: none !important;}
            .stAppDeployButton {display: none !important;}
            
            /* Remove especificamente os botões que você circulou na imagem */
            button[title="View app status"], 
            button[title="Manage app"],
            div[class*="st-emotion-cache-1vq4p4l"],
            div[class*="stStatusWidget"] {
                display: none !important;
            }

            /* Ajuste para mobile: remove o cabeçalho flutuante */
            .stApp > header {display: none !important;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)
# ------------------------------------------------------------

# 2. Função para Conectar ao Google Sheets
def get_data():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds_dict = st.secrets["gcp_service_account"].to_dict()
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(credentials)
        sh = client.open_by_key(st.secrets["SHEET_ID"])
        wks = sh.worksheet("respostas")
        df = pd.DataFrame(wks.get_all_records())
        # Limpa espaços em branco nos nomes das colunas
        df.columns = [c.strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Erro na conexão com a planilha: {e}")
        return pd.DataFrame()

# 3. Função para criar os Gráficos de Círculo (Donut)
def criar_donut(valor, titulo, chave, cor="#0E3A5D"):
    valor_num = pd.to_numeric(valor, errors='coerce')
    if pd.isna(valor_num):
        valor_num = 0.0
        
    fig = go.Figure(go.Pie(
        values=[valor_num, 10 - valor_num] if valor_num <= 10 else [10, 0],
        labels=["Nota", ""],
        hole=.7,
        marker_colors=[cor, "#F0F2F6"],
        sort=False,
        textinfo='none'
    ))
    
    fig.update_layout(
        showlegend=False,
        margin=dict(t=30, b=0, l=10, r=10),
        height=180, 
        annotations=[dict(text=f'{valor_num:.1f}', x=0.5, y=0.5, font_size=22, showarrow=False, font_color="#31333F")]
    )
    
    with st.container():
        st.markdown(f"<p style='text-align: center; font-weight: bold; font-size: 16px; color: #0E3A5D;'>{titulo}</p>", unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}, key=chave)

# 4. Função para converter DataFrame para Excel (Download)
def to_excel(df):
    output = io.BytesIO()
    # Usando 'with' para garantir que o writer salve e feche corretamente
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Dados_Dashboard')
    processed_data = output.getvalue()
    return processed_data

# 5. Execução do Dashboard
df = get_data()

if not df.empty:
    # --- BARRA LATERAL ---
    try:
        st.sidebar.image("Logo Escrita.png", width=150)
    except:
        pass
    st.sidebar.title("Filtros")
    
    lista_setores = ["Todos"]
    if 'setor' in df.columns:
        setores_unicos = sorted([str(s) for s in df['setor'].unique() if s != ""])
        lista_setores = ["Todos"] + setores_unicos
    
    setor_selecionado = st.sidebar.selectbox("Filtrar por Setor", lista_setores)
    
    if setor_selecionado != "Todos":
        df_filtrado = df[df['setor'] == setor_selecionado]
    else:
        df_filtrado = df

    # --- BOTÃO DE EXPORTAÇÃO ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("Exportar Dados")
    try:
        excel_data = to_excel(df_filtrado)
        st.sidebar.download_button(
            label="📥 Baixar em Excel",
            data=excel_data,
            file_name=f'performance_escrita_{setor_selecionado.lower()}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        st.sidebar.error("Erro ao gerar Excel. Verifique se 'xlsxwriter' está instalado.")

    # --- TÍTULO PRINCIPAL ---
    st.title("📊 Dashboard de Performance")
    
    # --- BLOCO 1: CARTÕES DE RESUMO ---
    c1, c2, c3 = st.columns(3)
    
    total_resp = len(df_filtrado)
    nps_medio = pd.to_numeric(df_filtrado['nota_geral'], errors='coerce').mean()
    
    cols_op = ['clareza', 'prazos', 'comunicacao', 'atendimento', 'custo']
    existentes = [c for c in cols_op if c in df_filtrado.columns]
    media_op = df_filtrado[existentes].apply(pd.to_numeric, errors='coerce').mean().mean() if existentes else 0.0

    with c1:
        st.markdown(f"<div style='background-color: white; padding: 20px; border-radius: 10px; border: 1px solid #ddd; text-align: center;'> <p style='color: #666; margin-bottom: 5px;'>Total de Respostas</p> <h2 style='margin: 0; color: #0E3A5D;'>{total_resp}</h2> </div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div style='background-color: white; padding: 20px; border-radius: 10px; border: 1px solid #ddd; text-align: center;'> <p style='color: #666; margin-bottom: 5px;'>NPS Médio</p> <h2 style='margin: 0; color: #0E3A5D;'>{nps_medio:.1f}</h2> </div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div style='background-color: white; padding: 20px; border-radius: 10px; border: 1px solid #ddd; text-align: center;'> <p style='color: #666; margin-bottom: 5px;'>Média Operacional</p> <h2 style='margin: 0; color: #0E3A5D;'>{media_op:.1f}</h2> </div>", unsafe_allow_html=True)

    st.markdown("##") 

    # --- BLOCO 2: INDICADORES POR DESEMPENHO (Donuts) ---
    st.markdown("### 🎯 Desempenho por Indicador")
    ind1, ind2, ind3, ind4, ind5 = st.columns(5)
    
    with ind1: criar_donut(df_filtrado['clareza'].mean() if 'clareza' in df_filtrado.columns else 0, "Clareza", "d_clareza")
    with ind2: criar_donut(df_filtrado['prazos'].mean() if 'prazos' in df_filtrado.columns else 0, "Prazos", "d_prazos")
    with ind3: criar_donut(df_filtrado['comunicacao'].mean() if 'comunicacao' in df_filtrado.columns else 0, "Comunicação", "d_comunic")
    with ind4: criar_donut(df_filtrado['atendimento'].mean() if 'atendimento' in df_filtrado.columns else 0, "Atendimento", "d_atendim")
    with ind5: criar_donut(df_filtrado['custo'].mean() if 'custo' in df_filtrado.columns else 0, "Custo", "d_custo")

    st.divider()

    # --- BLOCO 3: MÉDIAS POR DEPARTAMENTO (Barras) ---
    st.markdown("### 🏢 Médias por Departamento")
    mapeamento_setores = {
        "Contábil": "n_contabil",
        "Fiscal": "n_fiscal",
        "RH": "n_rh",
        "Legal": "n_legal",
        "Financeiro": "n_financeiro",
        "BPO Fin.": "n_bpo"
    }
    
    dados_b = []
    for nome, col in mapeamento_setores.items():
        if col in df_filtrado.columns:
            media = pd.to_numeric(df_filtrado[col], errors='coerce').mean()
            if not pd.isna(media):
                dados_b.append({"Departamento": nome, "Média": round(media, 1)})
    
    if dados_b:
        df_b = pd.DataFrame(dados_b)
        fig_b = px.bar(df_b, x='Departamento', y='Média', text='Média', color_discrete_sequence=["#0E3A5D"])
        fig_b.update_layout(yaxis=dict(range=[0, 10.5]), margin=dict(t=20, b=20))
        st.plotly_chart(fig_b, use_container_width=True, key="bar_deptos")
    else:
        st.info("Sem dados de departamentos para exibir.")

    st.divider()

    # --- BLOCO 4: TABELA DE FEEDBACKS ---
    st.markdown("### 💬 Últimos Feedbacks dos Clientes")
    colunas_visiveis = ['timestamp', 'cliente', 'nota_geral']
    if 'obs_financeiro' in df_filtrado.columns: colunas_visiveis.append('obs_financeiro')
    if 'obs_bpo' in df_filtrado.columns: colunas_visiveis.append('obs_bpo')
        
    st.dataframe(df_filtrado[colunas_visiveis].tail(10), use_container_width=True)

else:
    st.info("Aguardando o recebimento de dados da planilha para exibir o Dashboard.")
else:
    st.info("Aguardando o recebimento de dados da planilha para exibir o Dashboard.")
