"""
RestDays ortalaması düzeltme - İlk maçlar hariç
"""

import pandas as pd
from pathlib import Path
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def main():
    data_path = Path("march-machine-leraning-mania-2026")

    print("Regular Season verisi okunuyor...")
    regular_df = pd.read_csv(data_path / "MRegularSeasonCompactResults.csv")

    # Tüm takım maçlarını topla
    all_team_games = []

    for _, row in regular_df.iterrows():
        season = row["Season"]
        daynum = row["DayNum"]
        wteam = row["WTeamID"]
        lteam = row["LTeamID"]

        all_team_games.append({"Season": season, "DayNum": daynum, "TeamID": wteam})
        all_team_games.append({"Season": season, "DayNum": daynum, "TeamID": lteam})

    team_df = pd.DataFrame(all_team_games)
    team_df = team_df.sort_values(["Season", "TeamID", "DayNum"]).reset_index(drop=True)

    # Bir önceki maçın DayNum'unu bul
    team_df["PrevDayNum"] = team_df.groupby(["Season", "TeamID"])["DayNum"].shift(1)
    team_df["PrevDayNum"] = team_df["PrevDayNum"].fillna(0)

    # RestDays hesapla
    team_df["RestDays"] = team_df["DayNum"] - team_df["PrevDayNum"]

    # İlk maç işaretle
    team_df["IsFirstGame"] = team_df["PrevDayNum"] == 0

    print("\n" + "="*80)
    print("RESTDAYS ANALİZİ - İLK MAÇLAR HARİÇ")
    print("="*80)

    # Tüm maçlar dahil
    all_mean = team_df["RestDays"].mean()
    all_median = team_df["RestDays"].median()

    print(f"\nTÜM MAÇLAR DAHİL:")
    print(f"  Ortalama RestDays: {all_mean:.2f} gün")
    print(f"  Medyan RestDays: {all_median:.2f} gün")

    # İlk maçlar hariç
    non_first = team_df[team_df["IsFirstGame"] == False]
    non_first_mean = non_first["RestDays"].mean()
    non_first_median = non_first["RestDays"].median()

    print(f"\nİLK MAÇLAR HARİÇ:")
    print(f"  Toplam maç: {len(non_first):,}")
    print(f"  Ortalama RestDays: {non_first_mean:.2f} gün")
    print(f"  Medyan RestDays: {non_first_median:.2f} gün")

    print(f"\n{'='*80}")
    print("KARŞILAŞTIRMA")
    print(f"{'='*80}")
    print(f"\n{'Metrik':<25} {'Tümü':<15} {'İlk Maç Hariç':<20} {'Hedef'}")
    print("-" * 80)
    print(f"{'Ortalama RestDays':<25} {all_mean:<15.2f} {non_first_mean:<20.2f} {3.96}")
    print(f"{'Medyan RestDays':<25} {all_median:<15.2f} {non_first_median:<20.2f} {3.0}")

    # Fark analizi
    diff = abs(non_first_mean - 3.96)
    if diff < 0.1:
        print(f"\n✅ Ortalama DOĞRU! (Fark: {diff:.3f})")
    else:
        print(f"\n❌ Ortalama FARKLI! (Fark: {diff:.3f})")

    # Dağılım
    print(f"\n{'='*80}")
    print("RESTDAYS DAĞILIMI (İlk Maçlar Hariç)")
    print(f"{'='*80}")

    print(f"\n{'RestDays':<15} {'Sayı':<15} {'Yüzde'}")
    print("-" * 50)

    for days in range(1, 15):
        count = (non_first["RestDays"] == days).sum()
        pct = count / len(non_first) * 100
        if count > 0:
            print(f"{days} gün{'':<10} {count:<15} %{pct:.1f}")

    # 15+ gün
    count_15_plus = (non_first["RestDays"] >= 15).sum()
    pct_15_plus = count_15_plus / len(non_first) * 100
    print(f"{"15+ gün":<15} {count_15_plus:<15} %{pct_15_plus:.1f}")


if __name__ == "__main__":
    main()
