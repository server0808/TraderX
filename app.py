import yfinance as yf
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from fpdf import FPDF
import os

# Função para calcular a regressão linear
def linear_regression(prices, period, index):
    x = np.arange(period)
    y = prices[index - period + 1 : index + 1]
    slope, intercept = np.polyfit(x, y, 1)
    return intercept + slope * (period - 1)

# Função para calcular o desvio padrão
def standard_deviation(prices, period, index):
    data = prices[index - period + 1 : index + 1]
    return np.std(data)

# Função para calcular as métricas
def calculate_metrics(pairA_prices, pairB_prices, period, ma_period):
    rates_total = len(pairA_prices)
    deviation_diff = []
    moving_average = []

    for i in range(period, rates_total):
        lr_A = linear_regression(pairA_prices, period, i)
        dev_A = (pairA_prices[i] - lr_A) / standard_deviation(pairA_prices, period, i)

        lr_B = linear_regression(pairB_prices, period, i)
        dev_B = (pairB_prices[i] - lr_B) / standard_deviation(pairB_prices, period, i)

        deviation_diff.append(dev_A - dev_B)

        if i >= ma_period:
            moving_average.append(np.mean(deviation_diff[-ma_period:]))
        else:
            moving_average.append(None)

    return deviation_diff, moving_average

# Função para gerar relatório em PDF
def generate_pdf(results, pair_selection, output_path="indicator_report.pdf"):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Relatório de Indicadores - {pair_selection}", ln=True, align="C")

    pdf.set_font("Courier", size=10)
    pdf.cell(200, 10, txt="Data       | Deviation Diff | Moving Average", ln=True)
    for _, row in results.iterrows():
        row_data = f"{row['Data'].strftime('%Y-%m-%d')} | {row['Deviation Diff']:.4f} | {row['Moving Average']:.4f}"
        pdf.cell(200, 10, txt=row_data, ln=True)

    pdf.output(output_path)
    return output_path

# Streamlit Interface
st.title("TradeX")

pair_options = {
    "XAUUSD / BTCUSD": ("GC=F", "BTC-USD"),
    "CHFUSD / EURUSD": ("CHF=X", "EURUSD=X"),
    "S&P500 / VIX": ("^GSPC", "^VIX"),
    "JPYUSD / GBPUSD": ("JPY=X", "GBPUSD=X"),
    "BTCUSD / ETHUSD": ("BTC-USD", "ETH-USD"),
    }
pair_selection = st.selectbox("Escolha os pares:", options=list(pair_options.keys()))
pairA, pairB = pair_options[pair_selection]

timeframes = {"Diário": "1d", "Semanal": "1wk", "Mensal": "1mo"}
timeframe = st.selectbox("Escolha o tempo gráfico:", options=list(timeframes.keys()))

regression_period = st.slider("Período de Regressão Linear:", 2, 50, 20)
ma_period = st.slider("Período da Média Móvel:", 2, 50, 20)

end_date = pd.Timestamp.today()
start_date = end_date - pd.Timedelta(days=365 * 2)
dataA = yf.download(pairA, start=start_date, end=end_date, interval=timeframes[timeframe])
dataB = yf.download(pairB, start=start_date, end=end_date, interval=timeframes[timeframe])

if not dataA.empty and not dataB.empty:
    pricesA = dataA["Close"].dropna().values
    pricesB = dataB["Close"].dropna().values
    deviation_diff, moving_average = calculate_metrics(pricesA, pricesB, regression_period, ma_period)

    dates = dataA.index[-len(deviation_diff) :]
    results = pd.DataFrame(
        {"Data": dates, "Deviation Diff": deviation_diff, "Moving Average": moving_average}
    ).dropna()
    results = results.sort_values(by="Data", ascending=False)

    st.subheader("Indicadores Calculados")
    st.line_chart(results.set_index("Data"))

    st.subheader("Últimos Valores do Indicador")
    st.write(results.head(20))

    if st.button("Gerar PDF"):
        pdf_path = generate_pdf(results, pair_selection)
        
        # Abrir o arquivo PDF para enviar ao download
        with open(pdf_path, "rb") as pdf_file:
            st.download_button(
                label="Baixar Relatório PDF",
                data=pdf_file,
                file_name="indicator_report.pdf",
                mime="application/pdf",
            )

else:
    st.error("Erro ao baixar os dados. Tente novamente.")

#streamlit run tradex4.py
