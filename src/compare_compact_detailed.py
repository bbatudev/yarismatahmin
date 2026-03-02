"""
Hem Compact hem Detailed Results Karşılaştırma
Hangi dosyanın hangi değerlere sahip olduğunu tam olarak tespit et
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
    print("COMPACT vs DETAILED RESULTS KARŞILAŞTIRMA")
    print("="*80)

    # Detailed Results
    print("\nDetailed Results (MNCAATourneyDetailedResults.csv):")
    detailed = pd.read_csv(data_path / "MNCAATourneyDetailedResults.csv")
    print(f"  Toplam maç: {len(detailed):,}")
    print(f"  Season aralığı: {detailed['Season'].min()} - {detailed['Season'].max()}")

    # Compact Results
    print("\nCompact Results (MNCAATourneyCompactResults.csv):")
    compact = pd.read_csv(data_path / "MNCAATourneyCompactResults.csv")
    print(f"  Toplam maç: {len(compact):,}")
    print(f"  Season aralığı: {compact['Season'].min()} - {compact['Season'].max()}")

    # Karşılaştır
    print(f"\nFark: {len(compact) - len(detailed)} maç")

    # İstatistikleri hesapla
    print("\n" + "="*80)
    print("DETAILED RESULTS İSTATİSTİKLERİ")
    print("="*80)

    print(f"\nWScore:")
    print(f"  Ortalama: {detailed['WScore'].mean():.2f}")
    print(f"  Medyan: {detailed['WScore'].median():.0f}")
    print(f"  Min: {detailed['WScore'].min()}")
    print(f"  Max: {detailed['WScore'].max()}")

    print(f"\nLScore:")
    print(f"  Ortalama: {detailed['LScore'].mean():.2f}")
    print(f"  Medyan: {detailed['LScore'].median():.0f}")
    print(f"  Min: {detailed['LScore'].min()}")
    print(f"  Max: {detailed['LScore'].max()}")

    pointdiff_det = detailed["WScore"] - detailed["LScore"]
    print(f"\nPointDiff:")
    print(f"  Ortalama: {pointdiff_det.mean():.2f}")
    print(f"  Min: {pointdiff_det.min()}")
    print(f"  Max: {pointdiff_det.max()}")

    totalscore_det = detailed["WScore"] + detailed["LScore"]
    print(f"\nTotalScore:")
    print(f"  Ortalama: {totalscore_det.mean():.2f}")
    print(f"  Min: {totalscore_det.min()}")
    print(f"  Max: {totalscore_det.max()}")

    # Korelasyon
    from scipy.stats import pearsonr
    corr, _ = pearsonr(detailed["WScore"], detailed["LScore"])
    print(f"\nKorelasyon (WScore-LScore): {corr:.3f}")

    # Percentile'ler
    print(f"\nPercentile'ler:")
    for p in [10, 25, 50, 75, 90]:
        ws_p = np.percentile(detailed["WScore"], p)
        ls_p = np.percentile(detailed["LScore"], p)
        print(f"  %{p}: WScore={ws_p:.0f}, LScore={ls_p:.0f}")

    # ========================================
    # COMPACT RESULTS (Skor yok, sadece W-L var)
    # ========================================
    print("\n" + "="*80)
    print("COMPACT RESULTS - DETAYLI KARŞILAŞTIRMA")
    print("="*80)

    # Compact results'ta WScore ve LScore VARMI?
    if "WScore" in compact.columns and "LScore" in compact.columns:
        print("\n✅ Compact'ta WScore ve LScore sütunları VAR!")
        print(f"\nWScore:")
        print(f"  Ortalama: {compact['WScore'].mean():.2f}")
        print(f"  Medyan: {compact['WScore'].median():.0f}")
        print(f"  Min: {compact['WScore'].min()}")
        print(f"  Max: {compact['WScore'].max()}")

        print(f"\nLScore:")
        print(f"  Ortalama: {compact['LScore'].mean():.2f}")
        print(f"  Medyan: {compact['LScore'].median():.0f}")
        print(f"  Min: {compact['LScore'].min()}")
        print(f"  Max: {compact['LScore'].max()}")
    else:
        print("\n❌ Compact'ta WScore/LScore YOK - Sadece WTeamID/LTeamID var")

    # Season kontrolü
    print(f"\nDetailed season aralığı: {detailed['Season'].min()}-{detailed['Season'].max()}")
    print(f"Compact season aralığı: {compact['Season'].min()}-{compact['Season'].max()}")

    # Aynı sezonları filtreleyip karşılaştır
    seasons_detail = set(detailed["Season"].unique())
    seasons_compact = set(compact["Season"].unique())

    print(f"\nDetailed'de sezon sayısı: {len(seasons_detail)}")
    print(f"Compact'te sezon sayısı: {len(seasons_compact)}")

    # Fark
    only_compact = seasons_compact - seasons_detail
    only_detail = seasons_detail - seasons_compact

    if only_compact:
        print(f"\nSadece Compact'te olan sezonlar: {sorted(only_compact)}")
    if only_detail:
        print(f"Sadece Detailed'de olan sezonlar: {sorted(only_detail)}")

    # Son yılları kontrol et
    print(f"\nSon sezonlar:")
    recent_seasons = sorted(list(seasons_compact), reverse=True)[:5]
    for s in recent_seasons:
        det_count = len(detailed[detailed["Season"] == s])
        comp_count = len(compact[compact["Season"] == s])
        print(f"  {s}: Detailed={det_count}, Compact={comp_count}")


if __name__ == "__main__":
    main()
