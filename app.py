import streamlit as st
import gspread
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from google.oauth2.service_account import Credentials

# 1. Configurações Iniciais da Página
st.set_page_config(page_title="Dashboard de Performance - Escrita", layout="wide")

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

# 3. Função para criar os Gráficos de Círculo (Donut) - CORRIGIDA PARA VISIBILIDADE TOTAL
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
        # Ajuste de margem para evitar sobreposição do título markdown
        margin=dict(t=30, b=0, l=10, r=10),
        height=180, 
        annotations=[dict(text=f'{valor_num:.1f}', x=0.5, y=0.5, font_size=22, showarrow=False, font_color="#31333F")]
    )
    
    # Título centralizado sem o margin-bottom negativo que causava o corte
    with st.container():
        st.markdown(f"<p style='text-align: center; font-weight: bold; font-size: 16px; color: #0E3A5D;'>{titulo}</p>", unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar
