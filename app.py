import streamlit as st
import gspread
import pandas as pd
import plotly.express as px
from google.oauth2.service_account import Credentials

# 1. Configurações da Página
st.set_page_config(page_title="Dashboard NPS - Escrita", layout="wide")

# 2. Conexão com Google Planilhas
def get_data():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"].to_dict()
    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    credentials = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(credentials)
    
    sh = client.open_by_key(st.secrets["SHEET_ID"])
    wks = sh.worksheet("respostas")
    data = wks.get_all_records()
    return pd.DataFrame(data)

# 3. Estilo e Cores
cores_escrita = ["#0E3A5D", "#1F5E8C", "#B79A5B", "#F4F6F8"]

st.markdown(f"""
    <style>
    .main {{ background-color: #F4F6F8; }}
    .metric-card {{
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #B79A5B;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }}
    </style>
""", unsafe_allow_html=True)

# 4. Interface
try:
    df = get_data()
    
    # Título e Logo
    col_l, col_t = st.columns([1, 4])
    with col_l:
        st.image("Logo Escrita.png", width=150)
    with col_t:
        st.title("Painel Estratégico de Satisfação")
        st.write(f"Analisando {len(df)} respostas de clientes.")

    st.divider()

    # --- BLOCO 1: MÉTRICAS GERAIS ---
    st.subheader("🎯 Indicadores de Desempenho")
    m1, m2, m3, m4, m5 = st.columns(5)
    
    with m1: st.metric("Nota Geral", f"{df['nota_geral'].mean():.1f}/10")
    with m2: st.metric("Clareza", f"{df['clareza'].mean():.1f}")
    with m3: st.metric("Prazos", f"{df['prazos'].mean():.1f}")
    with m4: st.metric("Comunicação", f"{df['comunicacao'].mean():.1f}")
    with m5: st.metric("Atendimento", f"{df['atendimento'].mean():.1f}")

    st.write("---")

    # --- BLOCO 2: GRÁFICOS POR SETOR ---
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.markdown("### Médias por Departamento")
        setores = {
            "Contábil": df['n_contabil'].mean(),
            "Fiscal": df['n_fiscal'].mean(),
            "RH": df['n_rh'].mean(),
            "Legal": df['n_legal'].mean(),
            "Financeiro": df['n_financeiro'].mean(),
            "BPO": df['n_bpo'].mean()
        }
        df_setores = pd.DataFrame(list(setores.items()), columns=['Setor', 'Média'])
        fig_setores = px.bar(df_setores, x='Setor', y='Média', color_discrete_sequence=[cores_escrita[0]])
        st.plotly_chart(fig_setores, use_container_width=True)

    with col_g2:
        st.markdown("### Evolução das Respostas")
        df['timestamp'] = pd.to_datetime(df['timestamp'], dayfirst=True)
        df_tempo = df.groupby(df['timestamp'].dt.date).size().reset_index(name='Volume')
        fig_evolucao = px.line(df_tempo, x='timestamp', y='Volume', color_discrete_sequence=[cores_escrita[2]])
        st.plotly_chart(fig_evolucao, use_container_width=True)

    st.write("---")

    # --- BLOCO 3: FEEDBACKS QUALITATIVOS ---
    st.subheader("💬 O que os clientes estão dizendo?")
    setor_filtro = st.selectbox("Filtrar comentários por setor:", 
                                ["Todos", "Contábil", "Fiscal", "RH", "Legal", "Financeiro", "BPO"])
    
    # Mapeamento de colunas de comentários
    mapa_obs = {
        "Contábil": "obs_contabil", "Fiscal": "obs_fiscal", "RH": "obs_rh", 
        "Legal": "obs_legal", "Financeiro": "obs_financeiro", "BPO": "obs_bpo"
    }

    if setor_filtro == "Todos":
        # Mostra os 10 últimos clientes e seus comentários gerais de BPO/Fin (onde concentramos as obs)
        st.table(df[['timestamp', 'cliente', 'nota_geral', 'obs_financeiro']].tail(10))
    else:
        col_obs = mapa_obs[setor_filtro]
        filtro_df = df[df[col_obs] != ""][['cliente', col_obs]].tail(10)
        if not filtro_df.empty:
            for i, row in filtro_df.iterrows():
                st.markdown(f"**{row['cliente']}**: {row[col_obs]}")
        else:
            st.info(f"Nenhum comentário registrado para o setor {setor_filtro} ainda.")

except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
    st.info("Dica: Verifique se a planilha tem dados e se os nomes das colunas estão corretos.")
