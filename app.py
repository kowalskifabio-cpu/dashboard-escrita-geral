import streamlit as st
import gspread
import pandas as pd
import plotly.express as px
from google.oauth2.service_account import Credentials

# 1. Configurações da Página
st.set_page_config(page_title="Dashboard NPS - Escrita", layout="wide")

# 2. Conexão Blindada
def get_data():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"].to_dict()
    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    credentials = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(credentials)
    
    sh = client.open_by_key(st.secrets["SHEET_ID"])
    wks = sh.worksheet("respostas")
    data = wks.get_all_records()
    df = pd.DataFrame(data)
    
    # Limpeza: remove espaços em branco dos nomes das colunas
    df.columns = [c.strip() for c in df.columns]
    return df

# Cores
cores_escrita = ["#0E3A5D", "#1F5E8C", "#B79A5B", "#F4F6F8"]

# 3. Interface
try:
    df = get_data()
    
    # Título e Logo
    col_l, col_t = st.columns([1, 4])
    with col_l:
        st.image("Logo Escrita.png", width=150)
    with col_t:
        st.title("Painel Estratégico de Satisfação")
        st.write(f"Analisando {len(df)} respostas.")

    st.divider()

    # --- MÉTRICAS GERAIS ---
    st.subheader("🎯 Indicadores de Desempenho")
    m1, m2, m3, m4, m5 = st.columns(5)
    
    # Usamos .get para não dar erro se a coluna sumir
    m1.metric("Nota Geral", f"{df.get('nota_geral', pd.Series([0])).mean():.1f}/10")
    m2.metric("Clareza", f"{df.get('clareza', pd.Series([0])).mean():.1f}")
    m3.metric("Prazos", f"{df.get('prazos', pd.Series([0])).mean():.1f}")
    m4.metric("Comunicação", f"{df.get('comunicacao', pd.Series([0])).mean():.1f}")
    m5.metric("Atendimento", f"{df.get('atendimento', pd.Series([0])).mean():.1f}")

    st.write("---")

    # --- GRÁFICO DE DEPARTAMENTOS ---
    st.subheader("📊 Médias por Departamento")
    
    # Mapeamento seguro: Nome exibido -> Nome na Planilha
    mapeamento = {
        "Contábil": "n_contabil",
        "Fiscal": "n_fiscal",
        "RH": "n_rh",
        "Legal": "n_legal",
        "Financeiro": "n_financeiro",
        "BPO": "n_bpo"
    }
    
    valores_setores = []
    for nome_exibido, nome_planilha in mapeamento.items():
        if nome_planilha in df.columns:
            media = pd.to_numeric(df[nome_planilha], errors='coerce').mean()
            valores_setores.append({"Setor": nome_exibido, "Média": media})
    
    if valores_setores:
        df_plot = pd.DataFrame(valores_setores)
        fig = px.bar(df_plot, x='Setor', y='Média', color_discrete_sequence=[cores_escrita[0]])
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Nenhuma coluna de departamento (n_contabil, n_fiscal, etc) foi encontrada na planilha.")

except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
    st.info("Dica: Verifique se a planilha tem dados e se os nomes das colunas estão corretos.")
