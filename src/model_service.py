import datetime
import os
from typing import Any, Dict, List, Optional, Tuple

import h3
import joblib
import numpy as np
import pandas as pd

SP_LAT_MIN = -25.5
SP_LAT_MAX = -19.5
SP_LON_MIN = -53.5
SP_LON_MAX = -44.0

SP_REGIONS = {
    "Estado de Sao Paulo (Visao Geral)": {"lat": -22.5000, "lon": -48.5000, "zoom": 6.8},
    "Regiao Metropolitana de Sao Paulo": {"lat": -23.5505, "lon": -46.6333, "zoom": 10.5},
    "Campinas e Regiao Metropolitana": {"lat": -22.9056, "lon": -47.0608, "zoom": 11.0},
    "Baixada Santista (Santos e Regiao)": {"lat": -23.9618, "lon": -46.3322, "zoom": 11.0},
    "Vale do Paraiba (Sao Jose dos Campos)": {"lat": -23.1896, "lon": -45.8841, "zoom": 11.0},
    "Ribeirao Preto e Regiao": {"lat": -21.1767, "lon": -47.8108, "zoom": 11.0},
    "Sorocaba e Regiao": {"lat": -23.5015, "lon": -47.4526, "zoom": 11.0},
    "Sao Jose do Rio Preto": {"lat": -20.8113, "lon": -49.3758, "zoom": 11.0},
    "Bauru e Centro-Oeste Paulista": {"lat": -22.3147, "lon": -49.0606, "zoom": 11.0},
}

DEFAULT_HOURLY_PROFILE = {
    0: 0.7792, 1: 0.7289, 2: 0.7019, 3: 0.6542, 4: 0.5374, 5: 0.6335,
    6: 0.6947, 7: 0.8383, 8: 0.7271, 9: 0.9378, 10: 1.0846, 11: 1.0507,
    12: 1.0059, 13: 0.9612, 14: 1.0303, 15: 1.0287, 16: 1.0112, 17: 0.9877,
    18: 1.1137, 19: 1.4930, 20: 1.7589, 21: 1.6814, 22: 1.4188, 23: 1.1409,
}


def get_periodo_do_dia(hora: int) -> str:
    if 0 <= hora <= 5:
        return "Madrugada"
    elif 6 <= hora <= 11:
        return "Manha"
    elif 12 <= hora <= 17:
        return "Tarde"
    else:
        return "Noite"


def is_in_sp_bbox(lat: float, lon: float) -> bool:
    return (SP_LAT_MIN <= lat <= SP_LAT_MAX) and (SP_LON_MIN <= lon <= SP_LON_MAX)


def date_to_week_number(date_val: Any) -> int:
    if isinstance(date_val, str):
        date_val = datetime.date.fromisoformat(date_val)
    elif isinstance(date_val, datetime.datetime):
        date_val = date_val.date()
    elif not isinstance(date_val, datetime.date):
        raise ValueError(f"Tipo de data invalido: {type(date_val)}")
    return int(date_val.strftime("%U"))


def get_heat_color(val: float, alpha: int = 190) -> List[int]:
    v = max(0.0, min(1.0, float(val)))
    if v < 0.25:
        t = v / 0.25
        r = int(30 + t * (0 - 30))
        g = int(60 + t * (150 - 60))
        b = int(180 + t * (255 - 180))
    elif v < 0.50:
        t = (v - 0.25) / 0.25
        r = int(0 + t * (250 - 0))
        g = int(150 + t * (210 - 150))
        b = int(255 + t * (0 - 255))
    elif v < 0.75:
        t = (v - 0.50) / 0.25
        r = int(250 + t * (255 - 250))
        g = int(210 + t * (120 - 210))
        b = int(0 + t * (0 - 0))
    else:
        t = (v - 0.75) / 0.25
        r = int(255 + t * (220 - 255))
        g = int(120 + t * (20 - 120))
        b = int(0 + t * (20 - 0))
    return [r, g, b, alpha]


def load_model(model_path: str):
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Arquivo do modelo nao encontrado: {model_path}")
    return joblib.load(model_path)


def load_hourly_profile_df(hourly_path: str) -> pd.DataFrame:
    if os.path.exists(hourly_path):
        df = pd.read_csv(hourly_path)
        return df
    data = []
    for h, factor in DEFAULT_HOURLY_PROFILE.items():
        data.append({
            "HORA": h,
            "QTD_OCORRENCIAS": int(factor * 10000),
            "PROPORCAO": (factor / 24.0),
            "FATOR_HORARIO": factor,
        })
    return pd.DataFrame(data)


def build_metadata(panel: pd.DataFrame, hourly_df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    unique_hexagons = np.sort(panel["H3_INDEX"].unique())
    n_hex = len(unique_hexagons)
    h3_to_code = {h: i for i, h in enumerate(unique_hexagons)}

    coords = [h3.cell_to_latlng(h) for h in unique_hexagons]
    lats = np.array([c[0] for c in coords], dtype=np.float64)
    lons = np.array([c[1] for c in coords], dtype=np.float64)

    is_2023 = panel["ANO_SEMANA"].astype(str).str.startswith("2023")
    panel_2023 = panel[is_2023]
    crimes_2023_series = panel_2023.groupby("H3_INDEX")["QTD_CRIMES"].sum()
    crimes_2023_map = crimes_2023_series.to_dict()
    known_2023_set = set(crimes_2023_map.keys())

    crimes_2023_arr = np.array([crimes_2023_map.get(h, 0) for h in unique_hexagons], dtype=np.int32)

    hourly_factor_map = dict(DEFAULT_HOURLY_PROFILE)
    if hourly_df is not None and not hourly_df.empty:
        for _, row in hourly_df.iterrows():
            hourly_factor_map[int(row["HORA"])] = float(row["FATOR_HORARIO"])

    return {
        "unique_hexagons": unique_hexagons,
        "n_hexagons": n_hex,
        "h3_to_code": h3_to_code,
        "latitudes": lats,
        "longitudes": lons,
        "crimes_2023_map": crimes_2023_map,
        "crimes_2023_array": crimes_2023_arr,
        "known_2023_set": known_2023_set,
        "hourly_factors": hourly_factor_map,
        "hourly_df": hourly_df if hourly_df is not None else load_hourly_profile_df(""),
    }


def predict_all_hexagons(
    model: Any,
    metadata: Dict[str, Any],
    week_num: int,
    hour: int = 20,
    base_scores: Optional[np.ndarray] = None,
) -> pd.DataFrame:
    n_hex = metadata["n_hexagons"]
    if base_scores is not None and len(base_scores) == n_hex:
        scores_base = base_scores
    else:
        X = pd.DataFrame({
            "H3_CODE": np.arange(n_hex, dtype=int),
            "SEMANA_NUM": np.full(n_hex, week_num, dtype=int),
        })
        scores_base = model.predict_proba(X)[:, 1]

    ranks = pd.Series(scores_base).rank(pct=True).values
    percentiles = np.round(ranks * 100.0, 2)

    hour_factor = metadata["hourly_factors"].get(hour, 1.0)
    scores_hourly = np.clip(scores_base * hour_factor, 0.0, 1.0)

    classes_previstas = (scores_base >= 0.50).astype(int)

    # Cores termicas quente e frio moduladas pelo risco horario
    colors = [get_heat_color(s) for s in scores_hourly]
    colors_arr = np.array(colors, dtype=np.int32)

    df_result = pd.DataFrame({
        "H3_INDEX": metadata["unique_hexagons"],
        "H3_CODE": np.arange(n_hex, dtype=int),
        "LATITUDE": metadata["latitudes"],
        "LONGITUDE": metadata["longitudes"],
        "ESCORE_BASE": np.round(scores_base, 4),
        "PERCENTIL": percentiles,
        "CLASSE_PREVISTA": classes_previstas,
        "CRIMES_2023": metadata["crimes_2023_array"],
        "HORA_SELECIONADA": hour,
        "FATOR_HORARIO": round(hour_factor, 4),
        "ESCORE_HORARIO": np.round(scores_hourly, 4),
        "COR_R": colors_arr[:, 0],
        "COR_G": colors_arr[:, 1],
        "COR_B": colors_arr[:, 2],
        "COR_A": colors_arr[:, 3],
        "ELEVACAO": np.round(scores_hourly * 1000.0, 1),
    })

    return df_result


def query_location(
    model: Any,
    metadata: Dict[str, Any],
    lat: float,
    lon: float,
    week_num: int,
    hour: int = 20,
    all_scores_cache: Optional[np.ndarray] = None,
) -> Dict[str, Any]:
    in_sp = is_in_sp_bbox(lat, lon)
    h3_index = h3.latlng_to_cell(lat, lon, 9)
    center_lat, center_lon = h3.cell_to_latlng(h3_index)

    in_domain_2023 = (h3_index in metadata["known_2023_set"]) and in_sp
    h3_code = metadata["h3_to_code"].get(h3_index, None)
    crimes_2023 = metadata["crimes_2023_map"].get(h3_index, 0)
    hour_factor = metadata["hourly_factors"].get(hour, 1.0)

    if h3_code is not None and in_domain_2023:
        X_single = pd.DataFrame({
            "H3_CODE": [h3_code],
            "SEMANA_NUM": [week_num],
        })
        score_base = float(model.predict_proba(X_single)[0, 1])
        score_hourly = float(np.clip(score_base * hour_factor, 0.0, 1.0))
        classe_prevista = int(score_base >= 0.50)

        if all_scores_cache is not None and len(all_scores_cache) == metadata["n_hexagons"]:
            all_scores = all_scores_cache
        else:
            all_scores = model.predict_proba(
                pd.DataFrame({
                    "H3_CODE": np.arange(metadata["n_hexagons"], dtype=int),
                    "SEMANA_NUM": np.full(metadata["n_hexagons"], week_num, dtype=int),
                })
            )[:, 1]
        percentile = float(np.round((all_scores <= score_base).mean() * 100.0, 2))
        color = get_heat_color(score_hourly)
    else:
        score_base = 0.0
        score_hourly = 0.0
        percentile = 0.0
        classe_prevista = 0
        color = [128, 128, 128, 160]

    hourly_curve = []
    for h in range(24):
        f = metadata["hourly_factors"].get(h, 1.0)
        hourly_curve.append({
            "HORA": h,
            "FATOR": round(f, 4),
            "ESCORE_AJUSTADO": round(float(np.clip(score_base * f, 0.0, 1.0)), 4),
        })

    return {
        "lat_input": lat,
        "lon_input": lon,
        "in_sp_bbox": in_sp,
        "h3_index": h3_index,
        "center_lat": center_lat,
        "center_lon": center_lon,
        "h3_code": h3_code,
        "week_num": week_num,
        "hour": hour,
        "in_domain_2023": in_domain_2023,
        "crimes_2023": crimes_2023,
        "score_base": round(score_base, 4),
        "score_hourly": round(score_hourly, 4),
        "percentile": percentile,
        "classe_prevista": classe_prevista,
        "hour_factor": round(hour_factor, 4),
        "color": color,
        "hourly_curve": hourly_curve,
    }
