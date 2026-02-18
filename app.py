import streamlit as st
import gspread
import pandas as pd
import plotly.graph_objects as go
from google.oauth2.service_account import Credentials

# 1. Configurações da Página
st.set_page_config(page_title="Dashboard de Performance - Escrita", layout="wide")

# 2. Conexão com Dados
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
        df.columns = [c.strip() for c in df.columns] # Limpa espaços nos nomes das colunas
        return df
    except Exception as e:
        st.error(f"Erro na conexão: {e}")
        return pd.DataFrame()

# 3. Função para criar o Gráfico de Círculo (Donut)
def criar_donut(valor, titulo, cor="#0E3A5D"):
    fig = go.Figure(go.Pie(
        values=[valor, 10-valor] if valor <= 10 else [10, 0],
        labels=["Nota", ""],
        hole=.7,
        marker_colors=[cor, "#F0F2F6"],
        sort=False,
        textinfo='none'
    ))
    fig.update_layout(
        showlegend=False,
        margin=dict(t=30, b=10, l=10, r=10),
        height=180,
        annotations=[dict(text=f'{valor:.1f}', x=0.5, y=0.5, font_size=20, showarrow=False, font_color="#31333F")]
    )
    st.markdown(f"<p style='text-align: center; font-weight: bold; margin-bottom: -10px;'>{titulo}</p>", unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# 4. Interface Principal
df = get_data()

if not df.empty:
    # Cabeçalho Lateral
    st.sidebar.image("Logo Escrita.png", width=150)
    st.sidebar.title("Filtros")
    setor_f = st.sidebar.selectbox("Setor", ["Todos"] + list(df.columns[8::2])) # Pega os nomes dos setores da planilha
    
    st.title("📊 Dashboard de Performance")
    
    # --- BLOCO 1: CARTÕES DE RESUMO ---
    c1, c2, c3 = st.columns(3)
    
    total_resp = len(df)
    nps_medio = pd.to_numeric(df['nota_geral'], errors='coerce').mean()
    
    # Média operacional (média de clareza, prazos, comunicação, atendimento e custo)
    cols_op = ['clareza', 'prazos', 'comunicacao', 'atendimento', 'custo']
    existentes = [c for c in cols_op if c in df.columns]
    media_op = df[existentes].apply(pd.to_numeric, errors='coerce').mean().mean()

    with c1:
        st.markdown(f"<div style='background-color: white; padding: 20px; border-radius: 10px; border: 1px solid #ddd; text-align: center;'> <p style='color: #666;'>Total de Respostas</p> <h2>{total_resp}</h2> </div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div style='background-color: white; padding: 20px; border-radius: 10px; border: 1px solid #ddd; text-align: center;'> <p style='color: #666;'>NPS Médio</p> <h2>{nps_medio:.1f}</h2> </div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div style='background-color: white; padding: 20px; border-radius: 10px; border: 1px solid #ddd; text-align: center;'> <p style='color: #666;'>Média Operacional</p> <h2>{media_op:.1f}</h2> </div>", unsafe_allow_html=True)

    st.write("##")

    # --- BLOCO 2: INDICADORES CIRCULARES ---
    st.markdown("### 🎯 Desempenho por Indicador")
    ind1, ind2, ind3, ind4, ind5 = st.columns(5)
    
    with ind1: criar_donut(df['clareza'].astype(float).mean(), "Clareza")
    with ind2: criar_donut(df['prazos'].astype(float).mean(), "Prazos")
    with ind3: criar_donut(df['comunicacao'].astype(float).mean(), "Comunicação")
    with ind4: criar_donut(df['atendimento'].astype(float).mean(), "Atendimento")
    with ind5: criar_donut(df['custo'].astype(float).mean(), "Custo")

    st.divider()

    # --- BLOCO 3: FEEDBACKS ---
    st.markdown("### 💬 Feedbacks dos Clientes")
    # Mostra a tabela com as últimas respostas, focando no que é importante
    st.dataframe(df[['timestamp', 'cliente', 'nota_geral', 'obs_financeiro']].tail(10), use_container_width=True)

else:
    st.warning("Aguardando os primeiros dados na planilha para gerar os gráficos.")
