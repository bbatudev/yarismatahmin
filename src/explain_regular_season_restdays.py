"""
Regular Season RestDays Analizi - Adım Adım Açıklama

Bu kod analiz_sonuclari.txt'deki değerlerin nasıl hesaplandığını gösterir:
- Regular Season Ortalama Rest Days: 3.96 gün
- Regular Season Medyan: 3.0 gün
- Turnuva öncesi ortalama dinlenme: ~5-7 gün
"""

import pandas as pd
from pathlib import Path
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def calculate_all_restdays(regular_df):
    """
    Regular Season'daki HER MAÇ için RestDays hesaplar.

    Yöntem:
    1. Her takımın tüm maçlarını (kazanılan + kaybedilen) topla
    2. DayNum'a göre sırala
    3. RestDays = mevcut DayNum - önceki DayNum
    4. İlk maçta RestDays = DayNum (sezon başı)

    Parametres:
    ---------
    regular_df : pd.DataFrame
        Regular Season sonuçları

    Returns:
    --------
    pd.DataFrame
        Season, DayNum, TeamID, RestDays sütunları
    """

    all_team_games = []

    print("ADIM 1: Her takımın maçlarını topla...")

    for _, row in regular_df.iterrows():
        season = row["Season"]
        daynum = row["DayNum"]
        wteam = row["WTeamID"]
        lteam = row["LTeamID"]

        # Kazanan takım için kayıt
        all_team_games.append({
            "Season": season,
            "DayNum": daynum,
            "TeamID": wteam
        })

        # Kaybeden takım için kayıt
        all_team_games.append({
            "Season": daynum,
            "DayNum": daynum,
            "TeamID": lteam
        })

    # DataFrame'e çevir
    team_df = pd.DataFrame(all_team_games)
    team_df.columns = ["Season", "DayNum", "TeamID"]  # Sütun isimlerini düzelt

    print("ADIM 2: Season ve TeamID göre sırala...")
    team_df = team_df.sort_values(["Season", "TeamID", "DayNum"]).reset_index(drop=True)

    print("ADIM 3: Bir önceki maçın DayNum'unu bul (shift)...")
    team_df["PrevDayNum"] = team_df.groupby(["Season", "TeamID"])["DayNum"].shift(1)

    print("ADIM 4: RestDays hesapla...")
    # İlk maçta PrevDayNum NaN olacak, bunu 0 yap
    team_df["PrevDayNum"] = team_df["PrevDayNum"].fillna(0)

    # RestDays = DayNum - PrevDayNum
    # İlk maçta RestDays = DayNum (sezon başından itibaren)
    team_df["RestDays"] = team_df["DayNum"] - team_df["PrevDayNum"]

    # İlk maçta (PrevDayNum == 0) RestDays = DayNum olmalı
    team_df.loc[team_df["PrevDayNum"] == 0, "RestDays"] = team_df["DayNum"]

    return team_df


def analyze_regular_season_restdays(all_restdays_df):
    """
    Regular Season RestDays istatistiklerini hesaplar.

    Parametres:
    ---------
    all_restdays_df : pd.DataFrame
        Tüm takımların RestDays verileri

    Returns:
    --------
    dict
        İstatistikler
    """

    print("\n" + "="*80)
    print("REGULAR SEASON RESTDAYS ANALİZİ")
    print("="*80)

    # Toplam maç sayısı (her takımın her maçı)
    total_games = len(all_restdays_df)
    print(f"\nToplam takım-maç kaydı: {total_games:,}")
    print(f"(Her maç için 2 kayıt: kazanan + kaybeden)")

    # RestDays istatistikleri
    mean_restdays = all_restdays_df["RestDays"].mean()
    median_restdays = all_restdays_df["RestDays"].median()
    min_restdays = all_restdays_df["RestDays"].min()
    max_restdays = all_restdays_df["RestDays"].max()

    print(f"\n{'İstatistik':<30} {'Değer'}")
    print("-" * 50)
    print(f"{'Ortalama RestDays':<30} {mean_restdays:.2f} gün")
    print(f"{'Medyan RestDays':<30} {median_restdays:.2f} gün")
    print(f"{'Minimum RestDays':<30} {min_restdays:.0f} gün")
    print(f"{'Maximum RestDays':<30} {max_restdays:.0f} gün")

    # RestDays dağılımı
    print(f"\n{'RestDays Aralığı':<20} {'Sayı':<15} {'Yüzde'}")
    print("-" * 55)

    # 0 gün (ilk maçlar)
    count_0 = (all_restdays_df["RestDays"] == 0).sum()
    print(f"{'0 gün (ilk maç)':<20} {count_0:<15} %{count_0/total_games*100:.1f}")

    # 1 gün (back-to-back)
    count_1 = (all_restdays_df["RestDays"] == 1).sum()
    print(f"{'1 gün (back-to-back)':<20} {count_1:<15} %{count_1/total_games*100:.1f}")

    # 2-3 gün
    count_2_3 = ((all_restdays_df["RestDays"] >= 2) & (all_restdays_df["RestDays"] <= 3)).sum()
    print(f"{'2-3 gün':<20} {count_2_3:<15} %{count_2_3/total_games*100:.1f}")

    # 4-5 gün
    count_4_5 = ((all_restdays_df["RestDays"] >= 4) & (all_restdays_df["RestDays"] <= 5)).sum()
    print(f"{'4-5 gün':<20} {count_4_5:<15} %{count_4_5/total_games*100:.1f}")

    # 6-7 gün
    count_6_7 = ((all_restdays_df["RestDays"] >= 6) & (all_restdays_df["RestDays"] <= 7)).sum()
    print(f"{'6-7 gün':<20} {count_6_7:<15} %{count_6_7/total_games*100:.1f}")

    # 8+ gün
    count_8_plus = (all_restdays_df["RestDays"] >= 8).sum()
    print(f"{'8+ gün':<20} {count_8_plus:<15} %{count_8_plus/total_games*100:.1f}")

    return {
        "mean": mean_restdays,
        "median": median_restdays,
        "min": min_restdays,
        "max": max_restdays,
        "total_games": total_games
    }


def show_examples(all_restdays_df, team_id, season, team_name):
    """
    Belirli bir takım için örnek RestDays hesaplaması göster.

    Parametres:
    ---------
    all_restdays_df : pd.DataFrame
        Tüm RestDays verileri
    team_id : int
        Takım ID
    season : int
        Sezon
    team_name : str
        Takım adı
    """

    team_games = all_restdays_df[
        (all_restdays_df["Season"] == season) &
        (all_restdays_df["TeamID"] == team_id)
    ].copy().sort_values("DayNum").reset_index(drop=True)

    print(f"\n{'='*80}")
    print(f"ÖRNEK: {team_name} (ID: {team_id}) - {season} Sezonu")
    print(f"{'='*80}")

    print(f"\n{'Maç #':<8} {'DayNum':<10} {'PrevDayNum':<12} {'RestDays':<10} {'Açıklama'}")
    print("-" * 80)

    prev_daynum = 0
    for i, row in team_games.iterrows():
        daynum = row["DayNum"]
        prev = row["PrevDayNum"]
        restdays = row["RestDays"]

        if i == 0 or prev == 0:
            explanation = "İlk maç (sezon başı)"
        elif restdays == 1:
            explanation = "Back-to-back!"
        elif restdays <= 3:
            explanation = "Kısa dinlenme"
        elif restdays <= 7:
            explanation = "Normal dinlenme"
        else:
            explanation = "Uzun dinlenme (sezonda ara?)"

        print(f"{i+1:<8} {daynum:<10} {prev:<12} {restdays:<10} {explanation}")

        prev_daynum = daynum


def main():
    """Ana fonksiyon"""

    data_path = Path("march-machine-leraning-mania-2026")

    # Regular Season verisini oku
    print("Regular Season verisi okunuyor...")
    regular_df = pd.read_csv(data_path / "MRegularSeasonCompactResults.csv")

    print(f"Toplam maç sayısı: {len(regular_df):,}")

    # RestDays hesapla
    all_restdays_df = calculate_all_restdays(regular_df)

    # Analiz yap
    stats = analyze_regular_season_restdays(all_restdays_df)

    # Örnekler
    show_examples(all_restdays_df, 1101, 2025, "Abilene Chr")
    show_examples(all_restdays_df, 1102, 2025, "Air Force")
    show_examples(all_restdays_df, 1103, 2025, "Akron")

    print(f"\n{'='*80}")
    print("ÖZET")
    print(f"{'='*80}")
    print(f"\nRegular Season'da her takım için:")
    print(f"1. Tüm maçlarını (kazanılan + kaybedilen) listele")
    print(f"2. DayNum'a göre sırala")
    print(f"3. Her maç için RestDays = mevcut DayNum - önceki DayNum")
    print(f"\nSonra tüm takımların tüm RestDays değerlerinin:")
    print(f"- Ortalaması: {stats['mean']:.2f} gün")
    print(f"- Medyanı: {stats['median']:.2f} gün")


if __name__ == "__main__":
    main()
