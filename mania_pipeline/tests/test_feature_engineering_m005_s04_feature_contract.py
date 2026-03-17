import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "02_feature_engineering.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("feature_engineering_m005_s04_under_test", SCRIPT_PATH)
    assert spec and spec.loader, f"Could not load module spec from {SCRIPT_PATH}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_season_aggregates_emits_pythwr_and_luck():
    module = _load_module()

    games_long = pd.DataFrame(
        [
            {"Season": 2024, "TeamID": 1, "Win": 1, "Score": 80, "OppScore": 70, "TrueMargin": 10.0},
            {"Season": 2024, "TeamID": 1, "Win": 0, "Score": 68, "OppScore": 72, "TrueMargin": -4.0},
            {"Season": 2024, "TeamID": 2, "Win": 0, "Score": 70, "OppScore": 80, "TrueMargin": -10.0},
            {"Season": 2024, "TeamID": 2, "Win": 1, "Score": 72, "OppScore": 68, "TrueMargin": 4.0},
        ]
    )

    season_agg = module.build_season_aggregates(games_long, has_ff=False)

    team_one = season_agg.loc[season_agg["TeamID"] == 1].iloc[0]
    expected_pyth = module.compute_pythagorean_win_pct(
        pd.Series([team_one["AvgScore"]]),
        pd.Series([team_one["AvgOppScore"]]),
    ).iloc[0]

    assert "PythWR" in season_agg.columns
    assert "Luck" in season_agg.columns
    assert team_one["PythWR"] == expected_pyth
    assert team_one["Luck"] == team_one["WinPct"] - team_one["PythWR"]


def test_build_massey_features_uses_only_elite_systems_and_emits_dispersion_columns():
    module = _load_module()

    massey = pd.DataFrame(
        [
            {"Season": 2024, "TeamID": 1, "SystemName": "POM", "RankingDayNum": 133, "OrdinalRank": 10},
            {"Season": 2024, "TeamID": 1, "SystemName": "SAG", "RankingDayNum": 133, "OrdinalRank": 14},
            {"Season": 2024, "TeamID": 1, "SystemName": "FAKE", "RankingDayNum": 133, "OrdinalRank": 200},
            {"Season": 2024, "TeamID": 2, "SystemName": "POM", "RankingDayNum": 133, "OrdinalRank": 25},
            {"Season": 2024, "TeamID": 2, "SystemName": "SAG", "RankingDayNum": 133, "OrdinalRank": 21},
            {"Season": 2024, "TeamID": 2, "SystemName": "FAKE", "RankingDayNum": 133, "OrdinalRank": 1},
        ]
    )

    features = module.build_massey_features(massey)
    team_one = features.loc[features["TeamID"] == 1].iloc[0]

    assert {"MasseyRankStd", "MasseyPctSpread", "MasseyOrdinalRange"}.issubset(features.columns)
    assert team_one["MasseyAvgRank"] == 12.0
    assert team_one["MasseyOrdinalRange"] == 4.0
    assert team_one["MasseyRankStd"] == np.std([10.0, 14.0], ddof=1)
    assert team_one["MasseyPctSpread"] == 0.0


def test_build_matchup_matrix_emits_new_diff_columns():
    module = _load_module()

    tourney = pd.DataFrame(
        [
            {"Season": 2024, "DayNum": 136, "WTeamID": 1, "LTeamID": 2},
        ]
    )
    team_features = pd.DataFrame(
        [
            {
                "Season": 2024,
                "TeamID": 1,
                "SeedNum": 1,
                "PythWR": 0.88,
                "Luck": 0.04,
                "eFG": 0.58,
                "BlkPct": 0.07,
                "MasseyRankStd": 1.5,
                "MasseyPctSpread": 0.10,
                "MasseyOrdinalRange": 4.0,
            },
            {
                "Season": 2024,
                "TeamID": 2,
                "SeedNum": 8,
                "PythWR": 0.60,
                "Luck": -0.03,
                "eFG": 0.49,
                "BlkPct": 0.12,
                "MasseyRankStd": 4.5,
                "MasseyPctSpread": 0.35,
                "MasseyOrdinalRange": 12.0,
            },
        ]
    )

    matchup = module.build_matchup_matrix(tourney, team_features, gender="M")

    assert {
        "PythWR_diff",
        "Luck_diff",
        "MasseyRankStd_diff",
        "MasseyPctSpread_diff",
        "MasseyOrdinalRange_diff",
        "StyleClash_eFG_BlkPct_diff",
    }.issubset(matchup.columns)


def test_build_seed_mispricing_features_emits_expected_columns_by_gender():
    module = _load_module()

    team_feats = pd.DataFrame(
        [
            {
                "Season": 2024,
                "TeamID": 1,
                "SeedNum": 1,
                "PythWR": 0.92,
                "NetRtg": 28.0,
                "MasseyPct": 0.98,
            },
            {
                "Season": 2024,
                "TeamID": 2,
                "SeedNum": 8,
                "PythWR": 0.62,
                "NetRtg": 10.0,
                "MasseyPct": 0.72,
            },
        ]
    )

    men = module.build_seed_mispricing_features(team_feats, gender="M")
    women = module.build_seed_mispricing_features(team_feats.drop(columns=["MasseyPct"]), gender="W")

    assert {"SeedStrengthScore", "SeedPythMispricing", "SeedNetRtgMispricing", "SeedMasseyMispricing"}.issubset(men.columns)
    assert {"SeedStrengthScore", "SeedPythMispricing", "SeedNetRtgMispricing"}.issubset(women.columns)
    assert "SeedMasseyMispricing" not in women.columns
