"""
RestDays hesaplama modülü
Her takım için önceki maçtan geçen gün sayısını hesaplar
"""

import pandas as pd
from pathlib import Path
import sys
import io

# Windows UTF-8 encoding sorunu için
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def calculate_restdays(results_df: pd.DataFrame) -> pd.DataFrame:
    """
    Her takım için RestDays hesaplar.

    Parametres:
    ---------
    results_df : pd.DataFrame
        Regular Season veya Tournament sonuçları
        Columns: Season, DayNum, WTeamID, LTeamID

    Returns:
    --------
    pd.DataFrame
        Her takım için her maçın RestDays değeri
        Columns: Season, DayNum, TeamID, Result, PrevDayNum, RestDays
    """

    # Her takım için tüm maçları bir araya getir (kazanılan + kaybedilen)
    team_games = []

    for _, row in results_df.iterrows():
        season = row["Season"]
        daynum = row["DayNum"]
        wteam = row["WTeamID"]
        lteam = row["LTeamID"]

        # Kazanan takım için kayıt
        team_games.append({
            "Season": season,
            "DayNum": daynum,
            "TeamID": wteam,
            "Result": "W"
        })

        # Kaybeden takım için kayıt
        team_games.append({
            "Season": season,
            "DayNum": daynum,
            "TeamID": lteam,
            "Result": "L"
        })

    # DataFrame'e çevir
    team_df = pd.DataFrame(team_games)

    # Season ve TeamID göre sırala (önemli!)
    team_df = team_df.sort_values(["Season", "TeamID", "DayNum"]).reset_index(drop=True)

    # Her takım için bir önceki maçın DayNum'unu al (shift(1))
    team_df["PrevDayNum"] = team_df.groupby(["Season", "TeamID"])["DayNum"].shift(1)

    # İlk maçta PrevDayNum NaN olacak, bunu 0 yap
    team_df["PrevDayNum"] = team_df["PrevDayNum"].fillna(0)

    # RestDays hesapla
    team_df["RestDays"] = team_df["DayNum"] - team_df["PrevDayNum"]

    # İlk maçta RestDays = DayNum olmalı (sezon başı)
    team_df.loc[team_df["PrevDayNum"] == 0, "RestDays"] = team_df["DayNum"]

    return team_df


def add_restdays_to_results(results_df: pd.DataFrame) -> pd.DataFrame:
    """
    Orijinal results dataframe'ine RestDays ekler.

    Parametres:
    ---------
    results_df : pd.DataFrame
        Columns: Season, DayNum, WTeamID, LTeamID, ...

    Returns:
    --------
    pd.DataFrame
        Orijinal dataframe'e WRestDays ve LRestDays eklenmiş hali
    """

    # RestDays hesapla
    restdays_df = calculate_restdays(results_df)

    # Dictionary'e çevir (hızlı erişim için)
    restdays_dict = {}
    for _, row in restdays_df.iterrows():
        key = (row["Season"], row["DayNum"], row["TeamID"])
        restdays_dict[key] = row["RestDays"]

    # Orijinal dataframe'e kopyala
    results_df = results_df.copy()
    results_df["WRestDays"] = results_df.apply(
        lambda row: restdays_dict.get((row["Season"], row["DayNum"], row["WTeamID"]), 0),
        axis=1
    )
    results_df["LRestDays"] = results_df.apply(
        lambda row: restdays_dict.get((row["Season"], row["DayNum"], row["LTeamID"]), 0),
        axis=1
    )

    return results_df


def verify_restdays(results_df: pd.DataFrame, team_id: int, season: int) -> pd.DataFrame:
    """
    Belirli bir takım için RestDays değerlerini doğrular.

    Parametres:
    ---------
    results_df : pd.DataFrame
        RestDays eklenmiş results dataframe
    team_id : int
        Doğrulanacak takım ID
    season : int
        Sezon

    Returns:
    --------
    pd.DataFrame
        Takımın maçları ve RestDays değerleri
    """

    # Takımın tüm maçlarını bul
    team_games_w = results_df[
        (results_df["Season"] == season) &
        (results_df["WTeamID"] == team_id)
    ][["Season", "DayNum", "WTeamID", "LTeamID", "WRestDays"]].copy()

    team_games_l = results_df[
        (results_df["Season"] == season) &
        (results_df["LTeamID"] == team_id)
    ][["Season", "DayNum", "WTeamID", "LTeamID", "LRestDays"]].copy()

    team_games_w["Result"] = "W"
    team_games_w["RestDays"] = team_games_w["WRestDays"]
    team_games_w = team_games_w.rename(columns={"WTeamID": "TeamID", "LTeamID": "OpponentID"})

    team_games_l["Result"] = "L"
    team_games_l["RestDays"] = team_games_l["LRestDays"]
    team_games_l = team_games_l.rename(columns={"LTeamID": "TeamID", "WTeamID": "OpponentID"})

    # Birleştir ve sırala
    team_games = pd.concat([
        team_games_w[["Season", "DayNum", "TeamID", "OpponentID", "Result", "RestDays"]],
        team_games_l[["Season", "DayNum", "TeamID", "OpponentID", "Result", "RestDays"]]
    ])

    team_games = team_games.sort_values("DayNum").reset_index(drop=True)

    return team_games


def main():
    """Test fonksiyonu"""

    # Veri yolunu belirle
    data_path = Path("march-machine-leraning-mania-2026")
    results_file = data_path / "MRegularSeasonCompactResults.csv"

    # Veriyi oku
    print("Veri okunuyor...")
    df = pd.read_csv(results_file)
    print(f"Toplam maç sayısı: {len(df)}")

    # 2025 sezonunu filtrele
    df_2025 = df[df["Season"] == 2025].copy()
    print(f"2025 sezonu maç sayısı: {len(df_2025)}")

    # RestDays hesapla
    print("\nRestDays hesaplanıyor...")
    df_2025_with_restdays = add_restdays_to_results(df_2025)

    # Test takımları
    test_teams = {
        1101: "Abilene Chr",
        1102: "Air Force",
        1103: "Akron"
    }

    print("\n" + "="*70)
    print("RESTDOGS DOĞRULAMA TESTİ")
    print("="*70)

    for team_id, team_name in test_teams.items():
        print(f"\n{'='*70}")
        print(f"TAKIM: {team_name} (ID: {team_id}) - 2025 Sezonu")
        print(f"{'='*70}")

        team_games = verify_restdays(df_2025_with_restdays, team_id, 2025)

        print(f"\n{'DayNum':<8} {'Result':<8} {'Opponent':<12} {'RestDays':<10} {'Kontrol'}")
        print("-" * 70)

        prev_daynum = 0
        for _, row in team_games.iterrows():
            daynum = row["DayNum"]
            result = row["Result"]
            opponent = row["OpponentID"]
            restdays = row["RestDays"]

            # Manuel kontrol
            expected = daynum - prev_daynum if prev_daynum > 0 else daynum
            status = "✅" if restdays == expected else "❌"

            print(f"{daynum:<8} {result:<8} {opponent:<12} {restdays:<10} {status}")

            prev_daynum = daynum

    print(f"\n{'='*70}")
    print("TEST TAMAMLANDI")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
