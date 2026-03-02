"""
Konferans verisi kontrolü - Hangi sezonlarda var?
"""

import pandas as pd
from pathlib import Path
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def main():
    data_path = Path("march-machine-leraning-mania-2026")

    print("MTeamConferences.csv analiz ediliyor...")

    conf_df = pd.read_csv(data_path / "MTeamConferences.csv")

    print(f"\nToplam kayıt: {len(conf_df):,}")

    # Sezonlara göre dağılım
    season_counts = conf_df["Season"].value_counts().sort_index()

    print(f"\nSezon dağılımı:")
    print(f"{'Sezon':<10} {'Takım Sayısı':<15}")
    print("-" * 30)

    for season in [1985, 1990, 2000, 2010, 2015, 2016, 2020, 2025]:
        count = season_counts.get(season, 0)
        print(f"{season:<10} {count:<15,}")

    # Min ve max sezon
    print(f"\nİlk sezon: {conf_df['Season'].min()}")
    print(f"Son sezon: {conf_df['Season'].max()}")

    # Regular season ile karşılaştır
    reg_df = pd.read_csv(data_path / "MRegularSeasonCompactResults.csv")

    print(f"\nRegular Season sezon aralığı: {reg_df['Season'].min()} - {reg_df['Season'].max()}")

    # Hangi sezonlarda eksik var?
    reg_seasons = set(reg_df["Season"].unique())
    conf_seasons = set(conf_df["Season"].unique())

    missing = reg_seasons - conf_seasons

    if missing:
        print(f"\n⚠️ Konferans verisi OLMAYAN sezonlar: {sorted(missing)}")
    else:
        print(f"\n✅ Tüm sezonların konferans verisi var!")


if __name__ == "__main__":
    main()
