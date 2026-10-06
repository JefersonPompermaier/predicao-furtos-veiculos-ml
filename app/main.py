import datetime
import os
import sys

import h3
import joblib
import numpy as np
import pandas as pd
try:
    import pydeck as pdk
    import streamlit as st
except ImportError:
    pdk = None
    st = None

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.model_service import (
    DEFAULT_HOURLY_PROFILE,
    SP_REGIONS,
    build_metadata,
    date_to_week_number,
    get_heat_color,
    get_periodo_do_dia,
    is_in_sp_bbox,
    load_hourly_profile_df,
    load_model,
    predict_all_hexagons,
    query_location,
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "baseline.joblib")
PANEL_PATH = os.path.join(BASE_DIR, "data", "SP", "processed", "painel_h3_semanal.csv")
HOURLY_PATH = os.path.join(BASE_DIR, "data", "SP", "processed", "perfil_horario.csv")

if st is not None:
    st.set_page_config(
        page_title="Predicao de Risco de Furtos e Roubos de Veiculos - SP",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def cache_resource_decorator(fn):
    if st is not None:
        return st.cache_resource(fn)
    return fn


def cache_data_decorator(fn):
    if st is not None:
        return st.cache_data(fn)
    return fn


@cache_resource_decorator
def get_model():
    return load_model(MODEL_PATH)


@cache_data_decorator
def get_panel_data():
    return pd.read_csv(PANEL_PATH, dtype={"H3_INDEX": str, "ANO_SEMANA": str})


@cache_data_decorator
def get_hourly_data():
    return load_hourly_profile_df(HOURLY_PATH)


@cache_data_decorator
def get_metadata():
    panel = get_panel_data()
    hourly_df = get_hourly_data()
    return build_metadata(panel, hourly_df)


@cache_data_decorator
def get_base_predictions(week_num: int):
    model = get_model()
    metadata = get_metadata()
    n_hex = metadata["n_hexagons"]
    X = pd.DataFrame({
        "H3_CODE": np.arange(n_hex, dtype=int),
        "SEMANA_NUM": np.full(n_hex, week_num, dtype=int),
    })
    return model.predict_proba(X)[:, 1]


def build_pydeck_map(
    df_points: pd.DataFrame,
    center_lat: float,
    center_lon: float,
    zoom: float,
    tipo_camada: str,
    is_3d: bool,
    map_theme: str = "Claro",
):
    layers = []

    if tipo_camada in ("Malha Hexagonal H3 (Quente e Frio)", "Camadas Combinadas (Hexagonos + Calor)"):
        h3_layer = pdk.Layer(
            "H3HexagonLayer",
            data=df_points,
            get_hexagon="H3_INDEX",
            get_fill_color="[COR_R, COR_G, COR_B, COR_A]",
            extruded=is_3d,
            elevation_scale=1.5 if is_3d else 0,
            get_elevation="ELEVACAO" if is_3d else "0",
            pickable=True,
            auto_highlight=True,
        )
        layers.append(h3_layer)

    if tipo_camada in ("Mapa de Calor Continuo (Densidade Quente/Frio)", "Camadas Combinadas (Hexagonos + Calor)"):
        heatmap_colors = [
            [30, 60, 180, 150],
            [0, 150, 255, 180],
            [0, 220, 200, 200],
            [250, 210, 0, 220],
            [255, 120, 0, 230],
            [220, 20, 20, 240],
        ]
        heat_layer = pdk.Layer(
            "HeatmapLayer",
            data=df_points,
            get_position="[LONGITUDE, LATITUDE]",
            get_weight="ESCORE_HORARIO",
            radius_pixels=20,
            intensity=0.8,
            threshold=0.03,
            color_range=heatmap_colors,
            pickable=True,
        )
        layers.append(heat_layer)

    tooltip = {
        "html": (
            "<b>Hexagono H3:</b> {H3_INDEX}<br/>"
            "<b>Latitude:</b> {LATITUDE}<br/>"
            "<b>Longitude:</b> {LONGITUDE}<br/>"
            "<b>Escore Base Semanal:</b> {ESCORE_BASE}<br/>"
            "<b>Risco Horario ({HORA_SELECIONADA}h):</b> {ESCORE_HORARIO}<br/>"
            "<b>Percentil Estadual:</b> {PERCENTIL}%<br/>"
            "<b>Crimes em 2023:</b> {CRIMES_2023}<br/>"
            "<b>Classe Prevista:</b> {CLASSE_PREVISTA}"
        ),
        "style": {
            "backgroundColor": "#1e293b",
            "color": "#f8fafc",
            "fontSize": "12px",
            "padding": "10px",
            "borderRadius": "4px",
        },
    }

    view_state = pdk.ViewState(
        latitude=center_lat,
        longitude=center_lon,
        zoom=zoom,
        pitch=45 if is_3d else 0,
        bearing=0,
    )

    style_choice = pdk.map_styles.CARTO_DARK if map_theme == "Escuro" else pdk.map_styles.CARTO_LIGHT

    return pdk.Deck(
        layers=layers,
        initial_view_state=view_state,
        tooltip=tooltip,
        map_style=style_choice,
    )


def main():
    st.title("Predicao de Risco de Furtos e Roubos de Veiculos - Estado de Sao Paulo")
    st.caption("Sprint 3 - MVP do Produto | Modelo RandomForestClassifier com Malha Uber H3")

    for path in (MODEL_PATH, PANEL_PATH):
        if not os.path.exists(path):
            st.error(f"Arquivo obrigatorio nao encontrado: {os.path.relpath(path, BASE_DIR)}")
            st.stop()

    model = get_model()
    metadata = get_metadata()

    with st.sidebar:
        st.header("Parametros Espaco-Temporais")

        data_ref = st.date_input(
            "Data de referencia",
            value=datetime.date(2023, 10, 15),
            min_value=datetime.date(2020, 1, 1),
            max_value=datetime.date(2026, 12, 31),
            help="A data e convertida automaticamente para o numero da semana do ano (0 a 53).",
        )
        semana_num = date_to_week_number(data_ref)
        st.info(f"Semana correspondente no ano: {semana_num}")

        hora_ref = st.slider(
            "Horario de analise (0h a 23h)",
            min_value=0,
            max_value=23,
            value=20,
            step=1,
            help="Modula a probabilidade semanal pelo perfil empírico das 24 horas do dia na SSP-SP.",
        )
        periodo = get_periodo_do_dia(hora_ref)
        fator_hora = metadata["hourly_factors"].get(hora_ref, 1.0)
        st.caption(f"Periodo: {periodo} | Fator historico SSP-SP: {fator_hora:.2f}x da media")

        st.markdown("---")
        st.header("Configuracao do Mapa")

        regiao_sel = st.selectbox(
            "Regiao de foco no Estado de SP",
            options=list(SP_REGIONS.keys()),
            index=0,
            help="Centraliza o mapa diretamente no polo regional selecionado (padrao: visao geral do Estado de SP).",
        )
        regiao_params = SP_REGIONS[regiao_sel]

        filtro_densidade = st.selectbox(
            "Densidade de pontos exibidos",
            options=[
                "Todos os 30.977 hexagonos do Estado de SP (Malha Completa)",
                "Top 15.000 maiores escores",
                "Top 5.000 maiores escores",
                "Top 2.500 maiores escores",
                "Personalizado via Slider",
                "Filtrar por escore minimo",
            ],
            index=0,
            help="Permite visualizar desde a malha estadual completa ate recortes priorizados.",
        )

        n_top = metadata["n_hexagons"]
        score_min = 0.0
        if filtro_densidade == "Todos os 30.977 hexagonos do Estado de SP (Malha Completa)":
            n_top = metadata["n_hexagons"]
        elif filtro_densidade == "Top 15.000 maiores escores":
            n_top = 15000
        elif filtro_densidade == "Top 5.000 maiores escores":
            n_top = 5000
        elif filtro_densidade == "Top 2.500 maiores escores":
            n_top = 2500
        elif filtro_densidade == "Personalizado via Slider":
            n_top = st.slider(
                "Quantidade de pontos",
                min_value=500,
                max_value=metadata["n_hexagons"],
                value=metadata["n_hexagons"],
                step=500,
            )
        elif filtro_densidade == "Filtrar por escore minimo":
            score_min = st.slider("Escore minimo", 0.30, 0.90, 0.55, 0.05)
            n_top = metadata["n_hexagons"]

        tipo_camada = st.radio(
            "Estilo da visualizacao termica",
            options=[
                "Mapa de Calor Continuo (Densidade Quente/Frio)",
                "Camadas Combinadas (Hexagonos + Calor)",
                "Malha Hexagonal H3 (Quente e Frio)",
            ],
            index=0,
            help="Renderizacao em mapa de calor quente/frio continuo ou celulas hexagonais.",
        )

        mapa_3d = st.checkbox("Visualizacao 3D (Elevacao por risco)", value=False)

        tema_mapa = st.selectbox(
            "Tema do mapa base",
            options=["Claro (Carto Positron)", "Escuro (Carto Dark Matter)"],
            index=0,
            help="Estilo do mapa base sem dependencia de chaves externas de API.",
        )
        map_theme = "Escuro" if "Escuro" in tema_mapa else "Claro"

    aba_mapa, aba_consulta, aba_modelo = st.tabs([
        "Mapa de risco",
        "Consulta por local",
        "Sobre o modelo",
    ])

    base_scores = get_base_predictions(semana_num)

    with aba_mapa:
        st.subheader("Mapa Geoespacial de Risco Criminal - Estado de Sao Paulo")
        st.write(
            "Visualizacao da malha de risco criminal dividida em celulas Uber H3 (resolucao 9). "
            "A paleta termica quente e frio mapeia os indices estatisticos modulados pelo horario: "
            "tons azuis indicam menor criticidade relativa, tons amarelos representam risco intermediario "
            "e tons vermelhos destacam as zonas de concentracao de furtos e roubos de veiculos."
        )

        df_preds = predict_all_hexagons(
            model=model,
            metadata=metadata,
            week_num=semana_num,
            hour=hora_ref,
            base_scores=base_scores,
        )

        if filtro_densidade == "Filtrar por escore minimo":
            df_display = df_preds[df_preds["ESCORE_BASE"] >= score_min].copy()
            if df_display.empty:
                st.warning("Nenhum hexagono atende ao limiar de escore especificado. Exibindo os 500 maiores.")
                df_display = df_preds.sort_values("ESCORE_BASE", ascending=False).head(500).copy()
        elif n_top < metadata["n_hexagons"]:
            df_display = df_preds.sort_values("ESCORE_HORARIO", ascending=False).head(n_top).copy()
        else:
            df_display = df_preds

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Pontos Exibidos no Mapa", f"{len(df_display):,}".replace(",", "."))
        c2.metric("Total de Celulas Monitoradas", f"{metadata['n_hexagons']:,}".replace(",", "."))
        c3.metric("Semana e Hora Selecionadas", f"Semana {semana_num} | {hora_ref:02d}:00h")
        c4.metric("Fator Temporal Horario", f"{fator_hora:.2f}x")

        st.markdown(
            """
            <div style="display: flex; align-items: center; justify-content: space-between;
                        padding: 8px 16px; background-color: #f1f5f9; border-radius: 6px; margin-bottom: 12px;
                        border: 1px solid #cbd5e1;">
                <span style="font-weight: 600; color: #1e293b;">Escala Termica Quente e Frio:</span>
                <span style="color: #1e3a8a; font-weight: 500;">Azul Escuro (Risco Baixo)</span>
                <span style="color: #0284c7; font-weight: 500;">Ciano (Risco Moderado-Baixo)</span>
                <span style="color: #ca8a04; font-weight: 500;">Amarelo (Risco Medio)</span>
                <span style="color: #ea580c; font-weight: 500;">Laranja (Risco Moderado-Alto)</span>
                <span style="color: #b91c1c; font-weight: 500;">Vermelho (Risco Elevado)</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        deck = build_pydeck_map(
            df_points=df_display,
            center_lat=regiao_params["lat"],
            center_lon=regiao_params["lon"],
            zoom=regiao_params["zoom"],
            tipo_camada=tipo_camada,
            is_3d=mapa_3d,
            map_theme=map_theme,
        )
        st.pydeck_chart(deck, use_container_width=True)

        st.subheader("Perfil de Distribuicao Horaria no Estado de Sao Paulo")
        st.write(
            "Proporcao historica de ocorrencias de furto e roubo de veiculos ao longo das 24 horas "
            "do dia, obtida a partir da analise de 269.403 registros da SSP-SP em 2023. O horario "
            f"selecionado ({hora_ref:02d}:00h) representa {metadata['hourly_df'].iloc[hora_ref]['PROPORCAO']*100:.2f}% "
            "do total diario de delitos."
        )

        chart_df = metadata["hourly_df"][["HORA", "PROPORCAO"]].copy()
        chart_df["PERCENTUAL"] = np.round(chart_df["PROPORCAO"] * 100.0, 2)
        chart_df = chart_df.set_index("HORA")
        st.bar_chart(chart_df["PERCENTUAL"])

        st.subheader("Hexagonos Prioritarios para Alocacao Operacional")
        cols_export = [
            "H3_INDEX",
            "LATITUDE",
            "LONGITUDE",
            "ESCORE_BASE",
            "ESCORE_HORARIO",
            "PERCENTIL",
            "CRIMES_2023",
            "CLASSE_PREVISTA",
        ]
        tabela_export = df_display[cols_export].copy()
        tabela_export = tabela_export.rename(columns={
            "H3_INDEX": "Hexagono_H3",
            "LATITUDE": "Latitude",
            "LONGITUDE": "Longitude",
            "ESCORE_BASE": "Escore_Base_Semanal",
            "ESCORE_HORARIO": f"Risco_Horario_{hora_ref:02d}h",
            "PERCENTIL": "Percentil_Estadual",
            "CRIMES_2023": "Ocorrencias_2023",
            "CLASSE_PREVISTA": "Classe_Prevista",
        })

        st.dataframe(tabela_export.head(50), hide_index=True, use_container_width=True)

        csv_data = tabela_export.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Baixar Relatorio de Risco em CSV",
            data=csv_data,
            file_name=f"relatorio_risco_sp_semana_{semana_num}_hora_{hora_ref:02d}.csv",
            mime="text/csv",
        )

    with aba_consulta:
        st.subheader("Consulta Pontual por Coordenada Geografica")
        st.write(
            "Informe a latitude e a longitude para converter o ponto no identificador hexagonal "
            "correspondente (Uber H3 resolucao 9) e verificar o escore estatistico estimado."
        )

        locais_predefinidos = {
            "Personalizado": None,
            "Praca da Se (Centro - Sao Paulo)": (-23.550520, -46.633308),
            "Avenida Paulista (Bela Vista - Sao Paulo)": (-23.561414, -46.655881),
            "Terminal Rodoviario Tiete (Santana - Sao Paulo)": (-23.516248, -46.625345),
            "Centro de Campinas (Largo do Rosario)": (-22.905624, -47.060833),
            "Porto de Santos (Baixada Santista)": (-23.961840, -46.332210),
            "Centro de Ribeirao Preto (Praca XV de Novembro)": (-21.176720, -47.810840),
            "Centro de Sao Jose dos Campos": (-23.189610, -45.884120),
        }

        col_pre, _ = st.columns([2, 2])
        with col_pre:
            ponto_escolhido = st.selectbox("Pontos de Referencia em SP", list(locais_predefinidos.keys()))

        if locais_predefinidos[ponto_escolhido] is not None:
            default_lat, default_lon = locais_predefinidos[ponto_escolhido]
        else:
            default_lat, default_lon = -23.550520, -46.633308

        col_lat, col_lon = st.columns(2)
        with col_lat:
            input_lat = st.number_input(
                "Latitude (WGS84)",
                value=float(default_lat),
                format="%.6f",
                step=0.001,
                help="Valores validos para o Estado de SP: entre -25.5 e -19.5",
            )
        with col_lon:
            input_lon = st.number_input(
                "Longitude (WGS84)",
                value=float(default_lon),
                format="%.6f",
                step=0.001,
                help="Valores validos para o Estado de SP: entre -53.5 e -44.0",
            )

        if not is_in_sp_bbox(input_lat, input_lon):
            st.error(
                "As coordenadas informadas estao fora dos limites geograficos do Estado de Sao Paulo "
                "(Latitude entre -25.5 e -19.5, Longitude entre -53.5 e -44.0). "
                "O modelo baseline opera exclusivamente sobre celulas do Estado de Sao Paulo."
            )
        else:
            res_consulta = query_location(
                model=model,
                metadata=metadata,
                lat=input_lat,
                lon=input_lon,
                week_num=semana_num,
                hour=hora_ref,
                all_scores_cache=base_scores,
            )

            h3_cell = res_consulta["h3_index"]
            st.markdown(f"**Indice H3 Resolucao 9:** `{h3_cell}`")

            if not res_consulta["in_domain_2023"]:
                st.warning(
                    "Aviso de dominio estatistico: Este hexagono H3 nao possui registros de furtos ou "
                    "roubos de veiculos no ano de 2023. Celulas sem historico no periodo base encontram-se "
                    "fora do dominio amostral do modelo baseline treinado."
                )

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Escore Base Semanal", "0.0000 (Sem historico)")
                m2.metric(f"Risco Horario ({hora_ref:02d}h)", "0.0000 (Sem historico)")
                m3.metric("Percentil Estadual", "0.0% (Fora do dominio)")
                m4.metric("Ocorrencias em 2023", f"{res_consulta['crimes_2023']}")

                st.info(
                    "Classificacao Prevista: Sem ocorrencias registradas em 2023. "
                    "Esta celula territorial nao possui historico de criminalidade veicular na base de treino."
                )
            else:
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Escore Base Semanal", f"{res_consulta['score_base']:.4f}")
                m2.metric(f"Risco Horario ({hora_ref:02d}h)", f"{res_consulta['score_hourly']:.4f}")
                m3.metric("Percentil Estadual", f"{res_consulta['percentile']:.1f}%")
                m4.metric("Ocorrencias em 2023", f"{res_consulta['crimes_2023']}")

                st.write(
                    f"**Classificacao Prevista:** "
                    f"{'Risco Elevado (Classe 1)' if res_consulta['classe_prevista'] == 1 else 'Risco Reduzido (Classe 0)'} "
                    f"(limiar decisorio padrao 0.50)."
                )

            df_single_point = pd.DataFrame([{
                "H3_INDEX": h3_cell,
                "LATITUDE": res_consulta["center_lat"],
                "LONGITUDE": res_consulta["center_lon"],
                "ESCORE_BASE": res_consulta["score_base"],
                "ESCORE_HORARIO": res_consulta["score_hourly"],
                "PERCENTIL": res_consulta["percentile"],
                "CRIMES_2023": res_consulta["crimes_2023"],
                "CLASSE_PREVISTA": res_consulta["classe_prevista"],
                "HORA_SELECIONADA": hora_ref,
                "COR_R": res_consulta["color"][0],
                "COR_G": res_consulta["color"][1],
                "COR_B": res_consulta["color"][2],
                "COR_A": res_consulta["color"][3],
                "ELEVACAO": 500.0,
            }])

            single_deck = build_pydeck_map(
                df_points=df_single_point,
                center_lat=res_consulta["center_lat"],
                center_lon=res_consulta["center_lon"],
                zoom=14.0,
                tipo_camada="Malha Hexagonal H3 (Quente e Frio)",
                is_3d=False,
                map_theme=map_theme,
            )
            st.pydeck_chart(single_deck, use_container_width=True)

            if res_consulta["in_domain_2023"]:
                st.subheader("Curva de Risco Estimado ao Longo das 24 Horas para esta Celula")
                df_curve = pd.DataFrame(res_consulta["hourly_curve"]).set_index("HORA")
                st.line_chart(df_curve["ESCORE_AJUSTADO"])

    with aba_modelo:
        st.subheader("Documentacao Tecnica do Modelo Baseline")
        st.write(
            "O modelo em producao e o artefato preditivo desenvolvido e congelado na Sprint 2, "
            "projetado como baseline comparativo para estimativa de risco de furtos e roubos de veiculos."
        )

        st.markdown(
            """
            ### Especificacoes do Modelo
            - **Algoritmo:** RandomForestClassifier (scikit-learn 1.9.0)
            - **Hiperparametros:** n_estimators=50, max_depth=5, class_weight='balanced', random_state=42
            - **Artefato Serializado:** `models/baseline.joblib`
            - **Atributos Preditivos (Features):**
              1. `H3_CODE`: Codigo ordinal associado a posicao do identificador hexagonal na lista ordenada de celulas H3 unicas do Estado de Sao Paulo.
              2. `SEMANA_NUM`: Numero da semana do ano correspondente a data de analise (padrao strftime '%U', de 0 a 53, semana com inicio aos domingos).
            - **Variavel Alvo (Target):** Variavel binaria (`ALVO`), indicando a ocorrencia de pelo menos um furto ou roubo de veiculo no par hexagono-semana.
            - **Particionamento dos Dados:** Divisao temporal com 80% dos dados para treino e 20% para teste, preservando a cronologia historica e evitando vazamento de dados.

            ### Metricas de Desempenho no Conjunto de Teste
            - **Area sob a Curva ROC (ROC-AUC):** 0,617
            - **Classe 1 (Com Ocorrencia):**
              - Precisao: 0,08
              - Revocacao (Recall): 0,50
              - F1-Score: 0,14
            - **Acuracia Geral:** 0,67

            ### Modelagem Temporal e Analise Horaria
            O modelo central opera na granulometria temporal semanal, capturando a sazonalidade ampla e o comportamento base de cada quadrante espacial. A analise horaria integrada no painel combina a probabilidade predita semanal com a densidade de distribuicao temporal calculada a partir de 269.403 ocorrencias georreferenciadas da Secretaria de Seguranca Publica do Estado de Sao Paulo (SSP-SP) registradas em 2023. O fator multiplicativo resultante reflete os picos noturnos de ocorrencias (maximo entre 19h e 22h) e as janelas de menor incidencia na madrugada.

            ### Limitacoes Conhecidas do Baseline
            1. **Discretizacao Categorica:** O atributo H3_CODE trata o identificador hexagonal como variavel categorica enumerada, sem representacao explicita de distancias geograficas contiguas entre celulas vizinhas.
            2. **Forte Desbalanceamento Amostral:** Devido a dispersao geografica da criminalidade veicular, a maioria dos pares hexagono-semana nao registra crimes, impactando a precisao da classe minoritaria.
            3. **Delimitacao do Dominio Espacial:** Hexagonos sem registros historicos em 2023 estao fora do dominio estatistico do modelo baseline.
            4. **Variaveis Exogenas:** O baseline nao contempla informacoes de iluminacao publica, cameras de monitoramento, fluxo de trafego ou pontos de interesse comercial, sendo indicado como marco de comparacao para modelos complexos subsequentes.
            """
        )

    st.markdown("---")
    st.subheader("Descricao do Funcionamento do Sistema")
    st.write(
        "Esta aplicacao opera como um sistema de apoio a decisao policial estruturado em seis etapas "
        "interconectadas:\n\n"
        "1. **Captura dos Parametros Espaco-Temporais:** O usuario define a data e o horario desejados, "
        "alem de filtros de densidade e polos regionais no Estado de Sao Paulo.\n"
        "2. **Indexacao Espacial Hierarquica:** As coordenadas geograficas sao mapeadas para celulas "
        "hexagonais discretas no sistema Uber H3 na resolucao 9 (aresta aproximada de 174 metros e area de ~0,1 km²), "
        "permitindo granularidade tatica compativel com o raio de atuacao de patrulhas ostensivas.\n"
        "3. **Codificacao Deterministica de Atributos:** O identificador H3 e convertido no indice ordinal "
        "H3_CODE compativel com o treino original, e a data e decomposta no numero sequencial da semana "
        "(SEMANA_NUM).\n"
        "4. **Inferencia de Probabilidade pelo Modelo:** O classificador Random Forest processa os "
        "atributos e infere a probabilidade de ocorrencia de furto ou roubo de veiculo para cada celula.\n"
        "5. **Modulacao Temporal Horaria:** O escore probabilistico semanal e ponderado pelo perfil "
        "horario empirico consolidado da SSP-SP (2023), modulando a criticidade de acordo com a hora do dia.\n"
        "6. **Sintese Geoespacial em Gradiente Termico:** Os resultados sao renderizados em mapa interativo "
        "Pydeck utilizando a paleta termica quente e frio (azul para risco reduzido e vermelho para risco critico), "
        "viabilizando a priorizacao imediata de recursos operacionais e a exportacao de relatorios tabulares em CSV."
    )


if __name__ == "__main__":
    main()
