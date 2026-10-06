import os

import joblib
import pandas as pd
import streamlit as st

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "baseline.joblib")
PANEL_PATH = os.path.join(BASE_DIR, "data", "SP", "processed", "painel_h3_semanal.csv")

st.set_page_config(page_title="Risco de Furtos e Roubos de Veículos - SP", layout="wide")


@st.cache_resource
def load_model():
    return joblib.load(MODEL_PATH)


@st.cache_data
def load_panel():
    return pd.read_csv(PANEL_PATH, dtype={"H3_INDEX": str, "ANO_SEMANA": str})


def main():
    st.title("Predição de risco de furtos e roubos de veículos - São Paulo")

    for path in (MODEL_PATH, PANEL_PATH):
        if not os.path.exists(path):
            st.error(f"Arquivo não encontrado: {os.path.relpath(path, BASE_DIR)}")
            st.stop()

    model = load_model()
    panel = load_panel()

    aba_mapa, aba_consulta, aba_modelo = st.tabs(["Mapa de risco", "Consulta por local", "Sobre o modelo"])

    with aba_mapa:
        # TODO: escolher semana, prever para todos os hexágonos e exibir no mapa
        st.dataframe(panel.head(), hide_index=True)

    with aba_consulta:
        # TODO: receber latitude/longitude, converter para H3 e retornar o escore
        pass

    with aba_modelo:
        # TODO: descrever atributos, métricas e limitações do baseline
        st.write(type(model).__name__)


if __name__ == "__main__":
    main()

