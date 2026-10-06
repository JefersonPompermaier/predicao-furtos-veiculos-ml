import unittest
import pandas as pd
import numpy as np

from app.main import get_periodo_do_dia
from src.model_service import (
    load_model,
    load_hourly_profile_df,
    build_metadata,
    predict_all_hexagons,
    query_location,
    date_to_week_number,
)
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "baseline.joblib")
PANEL_PATH = os.path.join(BASE_DIR, "data", "SP", "processed", "painel_h3_semanal.csv")
HOURLY_PATH = os.path.join(BASE_DIR, "data", "SP", "processed", "perfil_horario.csv")


class TestAppLogic(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.model = load_model(MODEL_PATH)
        cls.panel = pd.read_csv(PANEL_PATH, dtype={"H3_INDEX": str, "ANO_SEMANA": str})
        cls.hourly_df = load_hourly_profile_df(HOURLY_PATH)
        cls.metadata = build_metadata(cls.panel, cls.hourly_df)

    def test_get_periodo_do_dia(self):
        self.assertEqual(get_periodo_do_dia(0), "Madrugada")
        self.assertEqual(get_periodo_do_dia(5), "Madrugada")
        self.assertEqual(get_periodo_do_dia(6), "Manha")
        self.assertEqual(get_periodo_do_dia(11), "Manha")
        self.assertEqual(get_periodo_do_dia(12), "Tarde")
        self.assertEqual(get_periodo_do_dia(17), "Tarde")
        self.assertEqual(get_periodo_do_dia(18), "Noite")
        self.assertEqual(get_periodo_do_dia(23), "Noite")

    def test_extreme_weeks(self):
        # Week 0
        df_w0 = predict_all_hexagons(self.model, self.metadata, week_num=0, hour=12)
        self.assertEqual(len(df_w0), 30977)
        self.assertTrue((df_w0["ESCORE_BASE"] >= 0.0).all())

        # Week 53
        df_w53 = predict_all_hexagons(self.model, self.metadata, week_num=53, hour=12)
        self.assertEqual(len(df_w53), 30977)
        self.assertTrue((df_w53["ESCORE_BASE"] >= 0.0).all())

    def test_csv_export_format(self):
        df_preds = predict_all_hexagons(self.model, self.metadata, week_num=30, hour=19)
        cols_export = [
            "H3_INDEX", "LATITUDE", "LONGITUDE",
            "ESCORE_BASE", "ESCORE_HORARIO", "PERCENTIL",
            "CRIMES_2023", "CLASSE_PREVISTA"
        ]
        subset = df_preds[cols_export].head(100)
        csv_bytes = subset.to_csv(index=False).encode("utf-8")
        self.assertGreater(len(csv_bytes), 1000)
        self.assertTrue(csv_bytes.startswith(b"H3_INDEX,LATITUDE,LONGITUDE"))

    def test_unknown_hexagon_query(self):
        # Coordinates in the middle of Atlantic ocean or Amazon
        # Lat -3.0, Lon -60.0 (Manaus area)
        res = query_location(self.model, self.metadata, -3.0, -60.0, week_num=10, hour=15)
        self.assertFalse(res["in_sp_bbox"])
        self.assertFalse(res["in_domain_2023"])
        self.assertIsNone(res["h3_code"])
        self.assertEqual(res["crimes_2023"], 0)
        self.assertGreaterEqual(res["score_base"], 0.0)


if __name__ == "__main__":
    unittest.main()
