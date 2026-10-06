import datetime
import os
import unittest
import numpy as np
import pandas as pd

from src.model_service import (
    DEFAULT_HOURLY_PROFILE,
    SP_LAT_MAX,
    SP_LAT_MIN,
    SP_LON_MAX,
    SP_LON_MIN,
    build_metadata,
    date_to_week_number,
    get_heat_color,
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


class TestModelService(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.model = load_model(MODEL_PATH)
        cls.panel = pd.read_csv(PANEL_PATH, dtype={"H3_INDEX": str, "ANO_SEMANA": str})
        cls.hourly_df = load_hourly_profile_df(HOURLY_PATH)
        cls.metadata = build_metadata(cls.panel, cls.hourly_df)

    def test_model_loading_and_features(self):
        self.assertIsNotNone(self.model)
        self.assertEqual(self.model.n_features_in_, 2)
        feature_names = list(getattr(self.model, "feature_names_in_", []))
        self.assertEqual(feature_names, ["H3_CODE", "SEMANA_NUM"])

    def test_panel_and_metadata_integrity(self):
        self.assertEqual(self.metadata["n_hexagons"], 30977)
        self.assertEqual(len(self.metadata["unique_hexagons"]), 30977)
        self.assertEqual(len(self.metadata["h3_to_code"]), 30977)

        # Confirm categorical ordering matches numpy sort
        panel_cat_codes = self.panel["H3_INDEX"].astype("category").cat.categories
        self.assertTrue(np.array_equal(self.metadata["unique_hexagons"], panel_cat_codes.values))

        # Check first and last code
        first_hex = self.metadata["unique_hexagons"][0]
        last_hex = self.metadata["unique_hexagons"][-1]
        self.assertEqual(self.metadata["h3_to_code"][first_hex], 0)
        self.assertEqual(self.metadata["h3_to_code"][last_hex], 30976)

    def test_coordinates_precomputation(self):
        self.assertEqual(len(self.metadata["latitudes"]), 30977)
        self.assertEqual(len(self.metadata["longitudes"]), 30977)
        # Check all are in or around SP bounding box
        min_lat = np.min(self.metadata["latitudes"])
        max_lat = np.max(self.metadata["latitudes"])
        self.assertTrue(min_lat > -26.0)
        self.assertTrue(max_lat < -19.0)

    def test_known_2023_set(self):
        self.assertGreater(len(self.metadata["known_2023_set"]), 30000)
        # Check that top crime count is positive
        self.assertGreater(max(self.metadata["crimes_2023_map"].values()), 100)

    def test_date_to_week_number(self):
        # 2023-01-01 was a Sunday -> week 01 with %U
        dt_sun = datetime.date(2023, 1, 1)
        self.assertEqual(date_to_week_number(dt_sun), int(dt_sun.strftime("%U")))

        # Test string parsing
        self.assertEqual(date_to_week_number("2023-10-15"), 42)

        # Test datetime object
        dt_obj = datetime.datetime(2023, 10, 15, 14, 30)
        self.assertEqual(date_to_week_number(dt_obj), 42)

        # Invalid type should raise ValueError
        with self.assertRaises(ValueError):
            date_to_week_number(12345)

    def test_predict_all_hexagons(self):
        df_pred = predict_all_hexagons(self.model, self.metadata, week_num=42, hour=20)
        self.assertEqual(len(df_pred), 30977)

        # Check column presence
        expected_cols = [
            "H3_INDEX", "H3_CODE", "LATITUDE", "LONGITUDE",
            "ESCORE_BASE", "PERCENTIL", "CLASSE_PREVISTA", "CRIMES_2023",
            "HORA_SELECIONADA", "FATOR_HORARIO", "ESCORE_HORARIO",
            "COR_R", "COR_G", "COR_B", "COR_A", "ELEVACAO"
        ]
        for col in expected_cols:
            self.assertIn(col, df_pred.columns)

        # Scores should be in valid probability ranges
        self.assertTrue((df_pred["ESCORE_BASE"] >= 0.0).all())
        self.assertTrue((df_pred["ESCORE_BASE"] <= 1.0).all())
        self.assertTrue((df_pred["ESCORE_HORARIO"] >= 0.0).all())
        self.assertTrue((df_pred["ESCORE_HORARIO"] <= 1.0).all())

        # Check color channels are within 0-255
        self.assertTrue((df_pred["COR_R"] >= 0).all() and (df_pred["COR_R"] <= 255).all())
        self.assertTrue((df_pred["COR_G"] >= 0).all() and (df_pred["COR_G"] <= 255).all())
        self.assertTrue((df_pred["COR_B"] >= 0).all() and (df_pred["COR_B"] <= 255).all())

    def test_query_location_inside_sp(self):
        # Praça da Sé coordinates
        res = query_location(self.model, self.metadata, -23.550520, -46.633308, week_num=42, hour=20)
        self.assertTrue(res["in_sp_bbox"])
        self.assertTrue(res["in_domain_2023"])
        self.assertGreater(res["crimes_2023"], 0)
        self.assertGreaterEqual(res["score_base"], 0.0)
        self.assertLessEqual(res["score_base"], 1.0)
        self.assertGreaterEqual(res["percentile"], 0.0)
        self.assertLessEqual(res["percentile"], 100.0)
        self.assertEqual(len(res["hourly_curve"]), 24)

    def test_query_location_outside_sp(self):
        # Rio de Janeiro coordinates
        res = query_location(self.model, self.metadata, -22.9068, -43.1729, week_num=42, hour=20)
        self.assertFalse(res["in_sp_bbox"])
        self.assertFalse(res["in_domain_2023"])
        self.assertEqual(res["crimes_2023"], 0)

    def test_get_heat_color_boundaries(self):
        c_min = get_heat_color(0.0)
        c_low = get_heat_color(0.25)
        c_mid = get_heat_color(0.50)
        c_high = get_heat_color(0.75)
        c_max = get_heat_color(1.0)

        self.assertEqual(len(c_min), 4)
        self.assertEqual(len(c_max), 4)

        # Min should be blueish
        self.assertGreater(c_min[2], c_min[0])
        # Max should be reddish
        self.assertGreater(c_max[0], c_max[2])

        # Test clamp below 0 and above 1
        self.assertEqual(get_heat_color(-0.5), c_min)
        self.assertEqual(get_heat_color(1.5), c_max)

    def test_hourly_profile_integrity(self):
        df_h = self.hourly_df
        self.assertEqual(len(df_h), 24)
        self.assertTrue((df_h["HORA"] == np.arange(24)).all())
        self.assertTrue((df_h["FATOR_HORARIO"] > 0).all())
        # Night peak around 20h should have factor > 1.5
        factor_20h = df_h.loc[df_h["HORA"] == 20, "FATOR_HORARIO"].values[0]
        self.assertGreater(factor_20h, 1.5)
        # Dawn valley around 4h should have factor < 0.7
        factor_4h = df_h.loc[df_h["HORA"] == 4, "FATOR_HORARIO"].values[0]
        self.assertLess(factor_4h, 0.7)

    def test_sp_bbox_check(self):
        self.assertTrue(is_in_sp_bbox(-23.55, -46.63))
        self.assertTrue(is_in_sp_bbox(-22.90, -47.06))
        self.assertFalse(is_in_sp_bbox(0.0, 0.0))
        self.assertFalse(is_in_sp_bbox(-30.0, -50.0))
        self.assertFalse(is_in_sp_bbox(-22.0, -40.0))

    def test_hourly_color_modulation_changes_with_hour(self):
        # 4h (dawn, low risk) vs 20h (peak night, high risk)
        df_4h = predict_all_hexagons(self.model, self.metadata, week_num=42, hour=4)
        df_20h = predict_all_hexagons(self.model, self.metadata, week_num=42, hour=20)

        # Elevation and color channels must dynamically respond to the hourly factor
        self.assertFalse((df_4h["ELEVACAO"] == df_20h["ELEVACAO"]).all())
        self.assertFalse((df_4h["COR_R"] == df_20h["COR_R"]).all())
        # Average red intensity should be higher at 20h than at 4h
        self.assertGreater(df_20h["COR_R"].mean(), df_4h["COR_R"].mean())
        # Average blue intensity should be higher at 4h than at 20h
        self.assertGreater(df_4h["COR_B"].mean(), df_20h["COR_B"].mean())

    def test_out_of_domain_does_not_borrow_code_zero(self):
        # Query location outside domain (e.g. Rio de Janeiro or an unrecorded location)
        res_out = query_location(self.model, self.metadata, -22.9068, -43.1729, week_num=42, hour=20)
        self.assertFalse(res_out["in_domain_2023"])
        self.assertEqual(res_out["score_base"], 0.0)
        self.assertEqual(res_out["score_hourly"], 0.0)
        self.assertEqual(res_out["percentile"], 0.0)
        self.assertEqual(res_out["classe_prevista"], 0)
        self.assertEqual(res_out["color"], [128, 128, 128, 160])

    def test_predict_all_hexagons_with_cached_base_scores(self):
        X = pd.DataFrame({
            "H3_CODE": np.arange(self.metadata["n_hexagons"], dtype=int),
            "SEMANA_NUM": np.full(self.metadata["n_hexagons"], 30, dtype=int),
        })
        raw_base_scores = self.model.predict_proba(X)[:, 1]

        df_direct = predict_all_hexagons(self.model, self.metadata, week_num=30, hour=18)
        df_cached = predict_all_hexagons(
            self.model, self.metadata, week_num=30, hour=18, base_scores=raw_base_scores
        )
        self.assertTrue(np.allclose(df_direct["ESCORE_BASE"], df_cached["ESCORE_BASE"]))
        self.assertTrue(np.allclose(df_direct["ESCORE_HORARIO"], df_cached["ESCORE_HORARIO"]))


if __name__ == "__main__":
    unittest.main()
