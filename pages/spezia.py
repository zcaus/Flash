import streamlit as st
import pandas as pd
from datetime import datetime
import altair as alt

st.set_page_config(
    page_title="Sistema de Controle - Flash",
    page_icon="planilha/mascote_instagram-removebg-preview.png",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Esconde a sidebar
st.markdown(
    """
    <style>
        section[data-testid="stSidebar"] {display: none;}
    </style>
    """,
    unsafe_allow_html=True,
)

# Navegação
col_nav = st.columns(8)
with col_nav[0]:
    st.page_link("main.py", label="Flash Foxmix", icon="📊")
with col_nav[1]:
    st.page_link("pages/spezia.py", label="Flash Spezia", icon="📇")

@st.cache_data
def carregar_dados():
    df = pd.read_excel('planilha/SPEZIA.XLSX')
    return df

df = carregar_dados()

# Limpa nomes de colunas
df.columns = df.columns.str.strip()

# Lista de exclusões (vazia neste exemplo)
exclusoes = []
df = df[~df['Ped. Cliente'].isin(exclusoes)]

df['Dt.pedido'] = pd.to_datetime(
    df['Dt.pedido'], dayfirst=True, errors='coerce', infer_datetime_format=True
)
df = df.dropna(subset=['Dt.pedido'])
df['Mes/Ano'] = df['Dt.pedido'].dt.strftime('%Y-%m')

# Seleciona o mês
meses = sorted(df['Mes/Ano'].unique())
mes_atual = datetime.today().strftime('%Y-%m')
default_index = meses.index(mes_atual) if mes_atual in meses else 0
mes_selecionado = st.selectbox("Selecione o mês", meses, index=default_index)

df_mes = df[df['Mes/Ano'] == mes_selecionado]

# Preenche os valores vazios da coluna Vendedor com "PAULO"
if 'Vendedor' in df_mes.columns:
    df_mes['Vendedor'] = df_mes['Vendedor'].fillna("PAULO")
else:
    df_mes['Vendedor'] = "PAULO"

# Agrupa os pedidos incluindo a coluna Vendedor
pedidos_agrupados = df_mes.groupby(
    ['Fantasia', 'Ped. Cliente', 'Dt.pedido', 'Vendedor'], as_index=False
)['Vl.Total'].sum()

# Renomeia as colunas
pedidos_agrupados.rename(columns={
    'Fantasia': 'Fantasia',
    'Ped. Cliente': 'Ped. Cliente',
    'Dt.pedido': 'Data do Pedido',
    'Vendedor': 'Vendedor',
    'Vl.Total': 'Valor Total do Pedido'
}, inplace=True)

colunas_exibicao = ['Fantasia', 'Ped. Cliente', 'Data do Pedido', 'Valor Total do Pedido', 'Vendedor']

# KPIs
total_mes = pedidos_agrupados['Valor Total do Pedido'].sum()
meta_mes = 50000.00
percentual = (total_mes / meta_mes) * 100 if meta_mes > 0 else 0
falta_valor = meta_mes - total_mes if total_mes < meta_mes else 0

# Função para formatar os valores no padrão brasileiro
def format_currency_br(value):
    formatted = f"{value:,.2f}"  # Ex: 12,345.67
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"

# Exibição dos KPIs com formatação brasileira
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Valor Total dos Pedidos", format_currency_br(total_mes))
col2.metric("Meta do Mês", format_currency_br(meta_mes))
col3.metric("Falta para Meta (%)", f"{100 - percentual:.2f}%" if percentual < 100 else "0%")
col4.metric("Meta Batida (%)", f"{percentual:.2f}%")
col5.metric("Falta para Meta (R$)", format_currency_br(falta_valor))

# Formata os valores para exibição no DataFrame
formatted_df = pedidos_agrupados.copy()
formatted_df["Valor Total do Pedido"] = formatted_df["Valor Total do Pedido"].apply(format_currency_br)

# Título
st.header(f"Flash de Vendas do Mês {mes_selecionado}")

# Exibe o DataFrame formatado
st.dataframe(formatted_df[colunas_exibicao], use_container_width=True)

# Gráfico de barras: Total vendido por vendedor
vendas_por_vendedor = pedidos_agrupados.groupby('Vendedor')['Valor Total do Pedido'].sum().reset_index()

# Cria uma coluna com o valor formatado para usar no tooltip
vendas_por_vendedor['Valor Formatado'] = vendas_por_vendedor['Valor Total do Pedido'].apply(format_currency_br)

# Gráfico Altair
grafico = alt.Chart(vendas_por_vendedor).mark_bar(color='#4CAF50').encode(
    x=alt.X('Vendedor:N', sort='-y', title='Vendedor', axis=alt.Axis(labelAngle=0)),
    y=alt.Y('Valor Total do Pedido:Q', title='Total Vendido (R$)'),
    tooltip=[alt.Tooltip('Vendedor:N', title='Vendedor'),
             alt.Tooltip('Valor Formatado:N', title='Total Vendido')]
).properties(
    title='Total de Vendas por Vendedor',
    width=700,
    height=400
).configure_axis(
    labelFontSize=12,
    titleFontSize=14
).configure_title(
    fontSize=16
)

# Exibe o gráfico
st.altair_chart(grafico, use_container_width=True)
