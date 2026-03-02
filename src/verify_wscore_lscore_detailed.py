"""
WScore-LScore Analizi Detaylı Doğrulama
Her yüzdelik dağılım, percentile ve korelasyon değerlerini manuel olarak hesaplar
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
import io
from scipy.stats import pearsonr

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def main():
    data_path = Path("march-machine-leraning-mania-2026")

    print("="*80)
    print("WSCORE-LSCORE ANALİZİ DETAYLI DOĞRULAMA")
    print("="*80)

    # Turnuva detaylı sonuçlarını oku
    print("\nTurnuva verisi okunuyor...")
    tourney = pd.read_csv(data_path / "MNCAATourneyDetailedResults.csv")
    print(f"Turnuva maç sayısı: {len(tourney):,}")

    # Regular season detaylı sonuçlarını oku
    print("Regular Season verisi okunuyor...")
    regular = pd.read_csv(data_path / "MRegularSeasonDetailedResults.csv")
    print(f"Regular Season maç sayısı: {len(regular):,}")

    # ========================================
    # 1. TEMEL İSTATİSTİKLER
    # ========================================
    print("\n" + "="*80)
    print("1. TEMEL İSTATİSTİKLER DOĞRULAMA")
    print("="*80)

    # Turnuva
    wscore_mean = tourney["WScore"].mean()
    lscore_mean = tourney["LScore"].mean()
    pointdiff_mean = (tourney["WScore"] - tourney["LScore"]).mean()
    totalscore_mean = (tourney["WScore"] + tourney["LScore"]).mean()

    print(f"\nTurnuva:")
    print(f"  WScore Ortalama: {wscore_mean:.2f}  (Dosyada: 79.0)")
    print(f"  LScore Ortalama: {lscore_mean:.2f}  (Dosyada: 67.3)")
    print(f"  PointDiff Ortalama: {pointdiff_mean:.2f}  (Dosyada: 11.74)")
    print(f"  TotalScore Ortalama: {totalscore_mean:.2f}  (Dosyada: 146.3)")

    # Regular Season
    wscore_mean_reg = regular["WScore"].mean()
    lscore_mean_reg = regular["LScore"].mean()
    pointdiff_mean_reg = (regular["WScore"] - regular["LScore"]).mean()
    totalscore_mean_reg = (regular["WScore"] + regular["LScore"]).mean()

    print(f"\nRegular Season:")
    print(f"  WScore Ortalama: {wscore_mean_reg:.2f}  (Dosyada: 78.5)")
    print(f"  LScore Ortalama: {lscore_mean_reg:.2f}  (Dosyada: 66.5)")
    print(f"  PointDiff Ortalama: {pointdiff_mean_reg:.2f}  (Dosyada: 12.02)")
    print(f"  TotalScore Ortalama: {totalscore_mean_reg:.2f}  (Dosyada: 145.0)")

    # Doğrulama
    print(f"\nDoğrulama:")
    print(f"  WScore (Turnuva): {'✅' if abs(wscore_mean - 79.0) < 0.1 else '❌'}")
    print(f"  LScore (Turnuva): {'✅' if abs(lscore_mean - 67.3) < 0.1 else '❌'}")
    print(f"  PointDiff (Turnuva): {'✅' if abs(pointdiff_mean - 11.74) < 0.1 else '❌'}")
    print(f"  TotalScore (Turnuva): {'✅' if abs(totalscore_mean - 146.3) < 0.1 else '❌'}")

    # ========================================
    # 2. KORELASYONLAR
    # ========================================
    print("\n" + "="*80)
    print("2. KORELASYONLAR DOĞRULAMA")
    print("="*80)

    # Turnuva korelasyonları
    corr_wscore_lscore_tour, p_tour = pearsonr(tourney["WScore"], tourney["LScore"])
    corr_wscore_pointdiff_tour, _ = pearsonr(tourney["WScore"], tourney["WScore"] - tourney["LScore"])
    corr_lscore_pointdiff_tour, _ = pearsonr(tourney["LScore"], tourney["WScore"] - tourney["LScore"])

    print(f"\nTurnuva Korelasyonları:")
    print(f"  WScore - LScore: {corr_wscore_lscore_tour:.3f}  (Dosyada: 0.660)")
    print(f"  WScore - PointDiff: {corr_wscore_pointdiff_tour:.3f}  (Dosyada: 0.885)")
    print(f"  LScore - PointDiff: {corr_lscore_pointdiff_tour:.3f}  (Dosyada: -0.172)")

    # Regular Season korelasyonları
    corr_wscore_lscore_reg, p_reg = pearsonr(regular["WScore"], regular["LScore"])

    print(f"\nRegular Season Korelasyonları:")
    print(f"  WScore - LScore: {corr_wscore_lscore_reg:.3f}  (Dosyada: 0.642)")

    # Doğrulama
    print(f"\nDoğrulama:")
    print(f"  Reg. WScore-LScore: {'✅' if abs(corr_wscore_lscore_reg - 0.642) < 0.01 else '❌'}")
    print(f"  Tour. WScore-LScore: {'✅' if abs(corr_wscore_lscore_tour - 0.660) < 0.01 else '❌'}")

    # ========================================
    # 3. YÜZDELİK DAĞILIMLAR (TURNUVA)
    # ========================================
    print("\n" + "="*80)
    print("3. YÜZDELİK DAĞILIMLAR DOĞRULAMA (TURNUVA)")
    print("="*80)

    # WScore dağılımı
    print(f"\nWScore Dağılımı:")
    wscore_bins = [0, 70, 80, 90, 100, 200]
    wscore_labels = ["<70", "70-79", "80-89", "90-99", "100+"]
    tourney["WScore_Bin"] = pd.cut(tourney["WScore"], bins=wscore_bins, labels=wscore_labels)
    wscore_dist = tourney["WScore_Bin"].value_counts().sort_index()

    for label, count in wscore_dist.items():
        pct = count / len(tourney) * 100
        cum_pct = wscore_dist[:list(wscore_labels).index(label)].sum() / len(tourney) * 100
        print(f"  {label:<10} {count:>5}  (%{pct:.1f})  Kümülatif: %{cum_pct:.1f}")

    # Dosyada yazan değerler
    expected_wscore = {
        "<70": 26.3,
        "70-79": 35.2,
        "80-89": 25.1,
        "90-99": 9.7,
        "100+": 3.7
    }

    print(f"\nDoğrulama (Dosyada yazan):")
    for label, count in wscore_dist.items():
        expected = expected_wscore[label]
        actual = count / len(tourney) * 100
        status = "✅" if abs(actual - expected) < 0.5 else "❌"
        print(f"  {label}: {actual:.1f}% vs {expected}% {status}")

    # LScore dağılımı
    print(f"\nLScore Dağılımı:")
    lscore_bins = [0, 60, 70, 80, 90, 200]
    lscore_labels = ["<60", "60-69", "70-79", "80-89", "90+"]
    tourney["LScore_Bin"] = pd.cut(tourney["LScore"], bins=lscore_bins, labels=lscore_labels)
    lscore_dist = tourney["LScore_Bin"].value_counts().sort_index()

    for label, count in lscore_dist.items():
        pct = count / len(tourney) * 100
        print(f"  {label:<10} {count:>5}  (%{pct:.1f})")

    # Dosyada yazan değerler
    expected_lscore = {
        "<60": 31.8,
        "60-69": 35.3,
        "70-79": 23.4,
        "80-89": 7.4,
        "90+": 2.2
    }

    print(f"\nDoğrulama (Dosyada yazan):")
    for label, count in lscore_dist.items():
        expected = expected_lscore[label]
        actual = count / len(tourney) * 100
        status = "✅" if abs(actual - expected) < 0.5 else "❌"
        print(f"  {label}: {actual:.1f}% vs {expected}% {status}")

    # PointDiff dağılımı
    print(f"\nPointDiff Dağılımı:")
    pointdiff = tourney["WScore"] - tourney["LScore"]
    pd_bins = [0, 6, 11, 16, 21, 100]
    pd_labels = ["1-5", "6-10", "11-15", "16-20", "21+"]
    pointdiff_bins = pd.cut(pointdiff, bins=pd_bins, labels=pd_labels)
    pointdiff_dist = pointdiff_bins.value_counts().sort_index()

    for label, count in pointdiff_dist.items():
        pct = count / len(tourney) * 100
        cum_pct = pointdiff_dist[:list(pd_labels).index(label)].sum() / len(tourney) * 100
        print(f"  {label:<10} {count:>5}  (%{pct:.1f})  Kümülatif: %{cum_pct:.1f}")

    # Dosyada yazan değerler
    expected_pointdiff = {
        "1-5": 28.5,
        "6-10": 23.8,
        "11-15": 19.9,
        "16-20": 12.8,
        "21+": 14.9
    }

    print(f"\nDoğrulama (Dosyada yazan):")
    for label, count in pointdiff_dist.items():
        expected = expected_pointdiff[label]
        actual = count / len(tourney) * 100
        status = "✅" if abs(actual - expected) < 0.5 else "❌"
        print(f"  {label}: {actual:.1f}% vs {expected}% {status}")

    # TotalScore dağılımı
    print(f"\nTotalScore Dağılımı:")
    totalscore = tourney["WScore"] + tourney["LScore"]
    ts_bins = [0, 120, 140, 160, 180, 500]
    ts_labels = ["<120", "120-139", "140-159", "160-179", "180+"]
    totalscore_bins = pd.cut(totalscore, bins=ts_bins, labels=ts_labels)
    totalscore_dist = totalscore_bins.value_counts().sort_index()

    for label, count in totalscore_dist.items():
        pct = count / len(tourney) * 100
        cum_pct = totalscore_dist[:list(ts_labels).index(label)].sum() / len(tourney) * 100
        print(f"  {label:<10} {count:>5}  (%{pct:.1f})  Kümülatif: %{cum_pct:.1f}")

    # Dosyada yazan değerler
    expected_totalscore = {
        "<120": 13.4,
        "120-139": 33.1,
        "140-159": 35.2,
        "160-179": 13.7,
        "180+": 4.6
    }

    print(f"\nDoğrulama (Dosyada yazan):")
    for label, count in totalscore_dist.items():
        expected = expected_totalscore[label]
        actual = count / len(tourney) * 100
        status = "✅" if abs(actual - expected) < 0.5 else "❌"
        print(f"  {label}: {actual:.1f}% vs {expected}% {status}")

    # ========================================
    # 4. PERCENTILE DOĞRULAMA
    # ========================================
    print("\n" + "="*80)
    print("4. PERCENTILE DOĞRULAMA")
    print("="*80)

    # WScore percentiles
    print(f"\nWScore Percentiles (Turnuva):")
    percentiles = [10, 25, 50, 75, 90]
    expected_wscore_pct = {10: 65, 25: 71, 50: 78, 75: 86, 90: 93}

    for p in percentiles:
        val = np.percentile(tourney["WScore"], p)
        expected = expected_wscore_pct[p]
        status = "✅" if abs(val - expected) <= 1 else "❌"
        print(f"  %{p:<3}: {val:.0f}  (Beklenen: {expected})  {status}")

    # LScore percentiles
    print(f"\nLScore Percentiles (Turnuva):")
    expected_lscore_pct = {10: 53, 25: 60, 50: 67, 75: 75, 90: 81}

    for p in percentiles:
        val = np.percentile(tourney["LScore"], p)
        expected = expected_lscore_pct[p]
        status = "✅" if abs(val - expected) <= 1 else "❌"
        print(f"  %{p:<3}: {val:.0f}  (Beklenen: {expected})  {status}")

    # ========================================
    # 5. EXTREME DEĞERLER
    # ========================================
    print("\n" + "="*80)
    print("5. EXTREME DEĞERLER DOĞRULAMA")
    print("="*80)

    print(f"\nTurnuva:")
    print(f"  WScore Min: {tourney['WScore'].min()}  (Beklenen: 43)")
    print(f"  WScore Max: {tourney['WScore'].max()}  (Beklenen: 149)")
    print(f"  LScore Min: {tourney['LScore'].min()}  (Beklenen: 29)")
    print(f"  LScore Max: {tourney['LScore'].max()}  (Beklenen: 115)")

    pointdiff = tourney["WScore"] - tourney["LScore"]
    totalscore = tourney["WScore"] + tourney["LScore"]

    max_diff_row = tourney.loc[pointdiff.idxmax()]
    min_diff_row = tourney.loc[pointdiff.idxmin()]
    max_total_row = tourney.loc[totalscore.idxmax()]
    min_total_row = tourney.loc[totalscore.idxmin()]

    print(f"\nEn Farklı Maç: {max_diff_row['WScore']} - {max_diff_row['LScore']} = {pointdiff.max():.0f}")
    print(f"En Çakislı Maç: {min_diff_row['WScore']} - {min_diff_row['LScore']} = {pointdiff.min():.0f}")
    print(f"En Skorlu Maç: {max_total_row['WScore']} + {max_total_row['LScore']} = {totalscore.max():.0f}")
    print(f"En Düşük Skorlu: {min_total_row['WScore']} + {min_total_row['LScore']} = {totalscore.min():.0f}")

    print(f"\nDoğrulama:")
    print(f"  PointDiff Max: {pointdiff.max():.0f}  (Beklenen: 58)  {'✅' if pointdiff.max() == 58 else '❌'}")
    print(f"  PointDiff Min: {pointdiff.min():.0f}  (Beklenen: 1)  {'✅' if pointdiff.min() == 1 else '❌'}")
    print(f"  TotalScore Max: {totalscore.max():.0f}  (Beklenen: 264)  {'✅' if totalscore.max() == 264 else '❌'}")
    print(f"  TotalScore Min: {totalscore.min():.0f}  (Beklenen: 75)  {'✅' if totalscore.min() == 75 else '❌'}")

    # ========================================
    # SONUÇ ÖZETİ
    # ========================================
    print("\n" + "="*80)
    print("DOĞRULAMA SONUCU ÖZETİ")
    print("="*80)

    checks = {
        "WScore Ortalama": abs(wscore_mean - 79.0) < 0.1,
        "LScore Ortalama": abs(lscore_mean - 67.3) < 0.1,
        "PointDiff Ortalama": abs(pointdiff_mean - 11.74) < 0.1,
        "TotalScore Ortalama": abs(totalscore_mean - 146.3) < 0.1,
        "Korelasyon (Tour)": abs(corr_wscore_lscore_tour - 0.660) < 0.01,
        "Korelasyon (Reg)": abs(corr_wscore_lscore_reg - 0.642) < 0.01,
    }

    all_pass = all(checks.values())

    for check, passed in checks.items():
        status = "✅ DOĞRU" if passed else "❌ HATALI"
        print(f"  {check}: {status}")

    print(f"\n{'='*80}")
    if all_pass:
        print("✅ TÜM DEĞERLER DOĞRULANDI!")
    else:
        print("❌ BAZI DEĞERLER HATALI!")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
