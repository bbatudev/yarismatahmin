"""
Ayni Sezonlar Icin Compact vs Detailed Karsilastirma
Dosyada yazan degerlerin hangi filtre ile hesaplandigini bul
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def main():
    data_path = Path("march-machine-leraning-mania-2026")

    print("="*80)
    print("AYNI SEZONLAR KARŞILAŞTIRMA")
    print("="*80)

    # Tum veriyi oku
    compact = pd.read_csv(data_path / "MNCAATourneyCompactResults.csv")
    detailed = pd.read_csv(data_path / "MNCAATourneyDetailedResults.csv")

    print(f"Compact: {len(compact)} mac ({compact['Season'].min()}-{compact['Season'].max()})")
    print(f"Detailed: {len(detailed)} mac ({detailed['Season'].min()}-{detailed['Season'].max()})")

    # Ayni sezonlari filtrele
    common_seasons = sorted(list(set(compact["Season"].unique()) & set(detailed["Season"].unique())))
    print(f"\nOrtak sezonlar: {len(common_seasons)}")
    print(f"Ortak sezonlar: {common_seasons}")

    # Ortak sezonlar icin filtrele
    compact_common = compact[compact["Season"].isin(common_seasons)]
    detailed_common = detailed[detailed["Season"].isin(common_seasons)]

    print(f"\nCompact (ortak sezonlar): {len(compact_common)} mac")
    print(f"Detailed (ortak sezonlar): {len(detailed_common)} mac")

    # Detayli karsilastirma
    print("\n" + "="*80)
    print("DETAILED (Ortak Sezonlar)")
    print("="*80)

    wscore_det = detailed_common['WScore'].mean()
    lscore_det = detailed_common['LScore'].mean()
    pointdiff_det = (detailed_common['WScore'] - detailed_common['LScore']).mean()
    totalscore_det = (detailed_common['WScore'] + detailed_common['LScore']).mean()

    print(f"WScore Ortalama: {wscore_det:.2f}")
    print(f"LScore Ortalama: {lscore_det:.2f}")
    print(f"PointDiff Ortalama: {pointdiff_det:.2f}")
    print(f"TotalScore Ortalama: {totalscore_det:.2f}")

    from scipy.stats import pearsonr
    corr, _ = pearsonr(detailed_common["WScore"], detailed_common["LScore"])
    print(f"Korelasyon: {corr:.3f}")

    print("\n" + "="*80)
    print("COMPACT (Ortak Sezonlar)")
    print("="*80)

    wscore_comp = compact_common['WScore'].mean()
    lscore_comp = compact_common['LScore'].mean()
    pointdiff_comp = (compact_common['WScore'] - compact_common['LScore']).mean()
    totalscore_comp = (compact_common['WScore'] + compact_common['LScore']).mean()

    print(f"WScore Ortalama: {wscore_comp:.2f}")
    print(f"LScore Ortalama: {lscore_comp:.2f}")
    print(f"PointDiff Ortalama: {pointdiff_comp:.2f}")
    print(f"TotalScore Ortalama: {totalscore_comp:.2f}")

    corr_c, _ = pearsonr(compact_common["WScore"], compact_common["LScore"])
    print(f"Korelasyon: {corr_c:.3f}")

    # Son yillari filtrele (2016-2025 gibi)
    print("\n" + "="*80)
    print("SON YILLAR FILTRELEME (2016-2025)")
    print("="*80)

    compact_recent = compact_common[compact_common["Season"] >= 2016]
    detailed_recent = detailed_common[detailed_common["Season"] >= 2016]

    print(f"\nCompact (2016-2025): {len(compact_recent)} mac")
    print(f"Detailed (2016-2025): {len(detailed_recent)} mac")

    print(f"\nDetailed (2016-2025):")
    wscore_rec = detailed_recent['WScore'].mean()
    lscore_rec = detailed_recent['LScore'].mean()

    print(f"  WScore Ortalama: {wscore_rec:.2f}")
    print(f"  LScore Ortalama: {lscore_rec:.2f}")
    print(f"  PointDiff Ortalama: {(detailed_recent['WScore'] - detailed_recent['LScore']).mean():.2f}")
    print(f"  TotalScore Ortalama: {(detailed_recent['WScore'] + detailed_recent['LScore']).mean():.2f}")

    # Dosyada yazan degerler
    print(f"\nDosyada yazan degerler:")
    print(f"  WScore Ortalama: 79.0")
    print(f"  LScore Ortalama: 67.3")
    print(f"  PointDiff Ortalama: 11.74")
    print(f"  TotalScore Ortalama: 146.3")

    print(f"\nKarsilastirma:")
    print(f"  Detailed WScore: {wscore_rec:.2f} -> 79.0 = +{(79.0 - wscore_rec):.2f}")
    print(f"  Detailed LScore: {lscore_rec:.2f} -> 67.3 = +{(67.3 - lscore_rec):.2f}")

    # Tutaran mac kontrolu
    print("\n" + "="*80)
    print("TUTAR MAC KARSILASTIRMA")
    print("="*80)

    compact_key = compact_recent[["Season", "DayNum", "WTeamID", "LTeamID"]].copy()
    detailed_key = detailed_recent[["Season", "DayNum", "WTeamID", "LTeamID"]].copy()

    # Merge et
    merged = pd.merge(compact_key, detailed_key, on=["Season", "DayNum", "WTeamID", "LTeamID"], suffixes=["_C", "_D"])

    # Skorlari karsilastir
    merged["ScoreMatch"] = (merged["WScore_C"] == merged["WScore_D"]) & (merged["LScore_C"] == merged["LScore_D"])

    print(f"\nToplam ortak mac: {len(merged)}")
    print(f"Skorlar uysan: {merged['ScoreMatch'].sum()}")
    print(f"Farkli skorlar: {len(merged) - merged['ScoreMatch'].sum()}")

    if len(merged) > 0 and merged['ScoreMatch'].sum() == len(merged):
        print("\nTUM SKORLAR UYUSUYOR!")
    else:
        uyuşmayan = merged[~merged["ScoreMatch"]]
        print(f"\nUYUSMAYAN: {len(uyuşmayan)} mac")
        if len(uyuşmayan) > 0:
            print(uyuşmayan[["Season", "WScore_C", "WScore_D"]].head())


if __name__ == "__main__":
    main()
