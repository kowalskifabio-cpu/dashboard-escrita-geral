import streamlit as st
import gspread
import pandas as pd
import plotly.graph_objects as go
from google.oauth2.service_account import Credentials

# 1. Configurações Iniciais da Página
st.set_page_config(page_title="Dashboard de Performance - Escrita", layout="wide")

# 2. Função para Conectar ao Google Sheets
def get_data():
    try:
        # Define o escopo de acesso
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        
        # Puxa as credenciais das 'Secrets' do Streamlit
        creds_dict = st.secrets["gcp_service_account"].to_dict()
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(credentials)
        
        # Abre a planilha pelo ID e acessa a aba 'respostas'
        sh = client.open_by_key(st.secrets["SHEET_ID"])
        wks = sh.worksheet("respostas")
        
        # Converte os dados em um DataFrame (tabela) do Pandas
        df = pd.DataFrame(wks.get_all_records())
        
        # Limpa possíveis espaços em branco nos nomes das colunas
        df.columns = [c.strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Erro na conexão com a planilha: {e}")
        return pd.DataFrame()

# 3. Função para criar os Gráficos de Círculo (Donut)
def criar_donut(valor, titulo, chave, cor="#0E3A5D"):
    # Garante que o valor seja numérico e não nulo
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
        margin=dict(t=30, b=10, l=10, r=10),
        height=180,
        annotations=[dict(text=f'{valor_num:.1f}', x=0.5, y=0.5, font_size=20, showarrow=False, font_color="#31333F")]
    )
    
    st.markdown(f"<p style='text-align: center; font-weight: bold; margin-bottom: -10px;'>{titulo}</p>", unsafe_allow_html=True)
    # O parâmetro 'key=chave' evita o erro de DuplicateElementId
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}, key=chave)

# 4. Execução do Dashboard
df = get_data()

if not df.empty:
    # --- BARRA LATERAL ---
    st.sidebar.image("Logo Escrita.png", width=150)
    st.sidebar.title("Filtros")
    # Filtro simples (ajustar conforme as colunas da sua planilha)
    lista_setores = ["Todos"]
    if 'setor' in df.columns:
        lista_setores = ["Todos"] + sorted(df['setor'].unique().tolist())
    
    setor_selecionado = st.sidebar.selectbox("Filtrar por Setor", lista_setores)
    
    # Filtragem dos dados
    if setor_selecionado != "Todos":
        df_filtrado = df[df['setor'] == setor_selecionado]
    else:
        df_filtrado = df

    # --- TÍTULO PRINCIPAL ---
    st.title("📊 Dashboard de Performance")
    
    # --- BLOCO 1: CARTÕES DE RESUMO (Top Cards) ---
    c1, c2, c3 = st.columns(3)
    
    total_resp = len(df_filtrado)
    nps_medio = pd.to_numeric(df_filtrado['nota_geral'], errors='coerce').mean()
    
    # Média operacional das 5 métricas principais
    cols_op = ['clareza', 'prazos', 'comunicacao', 'atendimento', 'custo']
    existentes = [c for c in cols_op if c in df_filtrado.columns]
    if existentes:
        media_op = df_filtrado[existentes].apply(pd.to_numeric, errors='coerce').mean().mean()
    else:
        media_op = 0.0

    with c1:
        st.markdown(f"<div style='background-color: white; padding: 20px; border-radius: 10px; border: 1px solid #ddd; text-align: center;'> <p style='color: #666; margin-bottom: 5px;'>Total de Respostas</p> <h2 style='margin: 0;'>{total_resp}</h2> </div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div style='background-color: white; padding: 20px; border-radius: 10px; border: 1px solid #ddd; text-align: center;'> <p style='color: #666; margin-bottom: 5px;'>NPS Médio</p> <h2 style='margin: 0;'>{nps_medio:.1f}</h2> </div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div style='background-color: white; padding: 20px; border-radius: 10px; border: 1px solid #ddd; text-align: center;'> <p style='color: #666; margin-bottom: 5px;'>Média Operacional</p> <h2 style='margin: 0;'>{media_op:.1f}</h2> </div>", unsafe_allow_html=True)

    st.markdown("##") # Espaçamento

    # --- BLOCO 2: INDICADORES POR DESEMPENHO (Donuts) ---
    st.markdown("### 🎯 Desempenho por Indicador")
    ind1, ind2, ind3, ind4, ind5 = st.columns(5)
    
    # Mapeamento seguro das notas
    with ind1: criar_donut(df_filtrado['clareza'].mean() if 'clareza' in df_filtrado.columns else 0, "Clareza", "d_clareza")
    with ind2: criar_donut(df_filtrado['prazos'].mean() if 'prazos' in df_filtrado.columns else 0, "Prazos", "d_prazos")
    with ind3: criar_donut(df_filtrado['comunicacao'].mean() if 'comunicacao' in df_filtrado.columns else 0, "Comunicação", "d_comunic")
    with ind4: criar_donut(df_filtrado['atendimento'].mean() if 'atendimento' in df_filtrado.columns else 0, "Atendimento", "d_atendim")
    with ind5: criar_donut(df_filtrado['custo'].mean() if 'custo' in df_filtrado.columns else 0, "Custo", "d_custo")

    st.divider()

    # --- BLOCO 3: TABELA DE FEEDBACKS ---
    st.markdown("### 💬 Últimos Feedbacks dos Clientes")
    # Seleciona apenas algumas colunas para não poluir a tela
    colunas_visiveis = ['timestamp', 'cliente', 'nota_geral']
    if 'obs_financeiro' in df_filtrado.columns:
        colunas_visiveis.append('obs_financeiro')
        
    st.dataframe(df_filtrado[colunas_visiveis].tail(10), use_container_width=True)

else:
    st.info("Aguardando o recebimento de dados da planilha para exibir o Dashboard.")
