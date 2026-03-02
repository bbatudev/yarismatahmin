"""
WLoc Analizi Dogrulama - Her Sayiyi Tek Tek Kontrol Etme
04_wloc_analizi.txt dosyasindaki tum degerleri manuel olarak dogrular
"""

import pandas as pd
from pathlib import Path
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def verify_tournament_wloc():
    """Turnuva WLoc analizini dogrula"""

    print("\n" + "="*80)
    print("1. TURNUVA WLOC ANALIZI DOGRULAMA")
    print("="*80)

    data_path = Path("march-machine-leraning-mania-2026")
    tournament_df = pd.read_csv(data_path / "MNCAATourneyCompactResults.csv")

    total_games = len(tournament_df)
    print(f"\nToplam Turnuva Maç: {total_games:,}")

    # WLoc dağılımı
    wloc_counts = tournament_df["WLoc"].value_counts()
    print(f"\nWLoc Dağılımı:")
    print(f"{'WLoc':<10} {'Sayı':<15} {'Yüzde':<10} {'Beklenen':<15} {'Durum'}")
    print("-" * 70)

    for loc in ['N', 'H', 'A']:
        count = wloc_counts.get(loc, 0)
        pct = count / total_games * 100 if total_games > 0 else 0

        # Beklenen değerler (dosyadan)
        if loc == 'N':
            expected_count = 2585
            expected_pct = 100.0
        elif loc == 'H':
            expected_count = 0
            expected_pct = 0.0
        else:  # A
            expected_count = 0
            expected_pct = 0.0

        match = "✅" if (count == expected_count and abs(pct - expected_pct) < 0.1) else "❌"

        print(f"{loc:<10} {count:<15,} %{pct:<10.1f} {expected_count:,} (%{expected_pct:.1f})  {match}")

    # Tümü N mi kontrol et
    all_neutral = (wloc_counts.get('N', 0) == total_games)
    print(f"\nTüm maçlar nötr (N): {all_neutral} {'✅' if all_neutral else '❌'}")

    return {
        "total": total_games,
        "n_count": wloc_counts.get('N', 0),
        "h_count": wloc_counts.get('H', 0),
        "a_count": wloc_counts.get('A', 0)
    }


def verify_regular_season_wloc():
    """Regular Season WLoc analizini dogrula"""

    print("\n" + "="*80)
    print("2. REGULAR SEASON WLOC ANALIZI DOGRULAMA")
    print("="*80)

    data_path = Path("march-machine-leraning-mania-2026")
    regular_df = pd.read_csv(data_path / "MRegularSeasonCompactResults.csv")

    total_games = len(regular_df)
    print(f"\nToplam Regular Season Maç: {total_games:,}")

    # WLoc dağılımı
    wloc_counts = regular_df["WLoc"].value_counts()
    print(f"\nWLoc Dağılımı:")
    print(f"{'WLoc':<10} {'Sayı':<15} {'Yüzde':<10} {'Beklenen':<20} {'Durum'}")
    print("-" * 80)

    # Beklenen değerler (dosyadan)
    expected = {
        'H': (116270, 59.1),
        'A': (60435, 30.7),
        'N': (20118, 10.2)
    }

    all_match = True
    for loc in ['H', 'A', 'N']:
        count = wloc_counts.get(loc, 0)
        pct = count / total_games * 100 if total_games > 0 else 0
        exp_count, exp_pct = expected.get(loc, (0, 0))

        match = abs(count - exp_count) < 10 and abs(pct - exp_pct) < 0.1
        status = "✅" if match else "❌"
        if not match:
            all_match = False

        print(f"{loc:<10} {count:<15,} %{pct:<10.1f} {exp_count:,} (%{exp_pct:.1f})  {status}")

    print(f"\nTüm değerler eşleşiyor: {all_match} {'✅' if all_match else '❌'}")

    return {
        "total": total_games,
        "h_count": wloc_counts.get('H', 0),
        "a_count": wloc_counts.get('A', 0),
        "n_count": wloc_counts.get('N', 0)
    }


def verify_home_advantage(regular_df):
    """Ev sahibi avantaji analizini dogrula"""

    print("\n" + "="*80)
    print("3. EV SAHIBI AVANTAJI ANALIZI DOGRULAMA")
    print("="*80)

    # WLoc = H means winner won at home
    # WLoc = A means winner won away (loser was home)

    h_count = (regular_df["WLoc"] == "H").sum()  # Kazanan evinde
    a_count = (regular_df["WLoc"] == "A").sum()  # Kazanan deplasmanda (ev sahibi kaybetti)

    total_home_games = h_count + a_count
    home_win_pct = h_count / total_home_games * 100 if total_home_games > 0 else 0

    print(f"\nHesaplama:")
    print(f"  Ev sahibi kazandı (WLoc=H): {h_count:,}")
    print(f"  Deplasman kazandı (WLoc=A): {a_count:,}")
    print(f"  Toplam ev sahibi maç: {total_home_games:,}")
    print(f"\nEv Sahibi Kazanma Oranı: {home_win_pct:.1f}%")

    # Beklenen değer
    expected_pct = 65.8
    match = abs(home_win_pct - expected_pct) < 0.1
    print(f"Beklenen: {expected_pct}%")
    print(f"Durum: {('✅ EŞLEŞİYOR' if match else '❌ FARKLI')}")

    return {
        "home_wins": h_count,
        "away_wins": a_count,
        "home_win_pct": home_win_pct
    }


def verify_score_advantage(regular_df):
    """Skor avantajini dogrula"""

    print("\n" + "="*80)
    print("4. SKOR AVANTAJI ANALIZI DOGRULAMA")
    print("="*80)

    # Ev sahibi maçları için skor farkı
    # WLoc=H: WScore - LScore (ev sahibi kazandı)
    # WLoc=A: LScore - WScore (ev sahibi kaybetti, negatif)

    # Ev sahibi kazandı (WLoc=H)
    home_winner = regular_df[regular_df["WLoc"] == "H"]
    home_winner_margin = (home_winner["WScore"] - home_winner["LScore"]).mean()

    # Ev sahibi kaybetti (WLoc=A)
    home_loser = regular_df[regular_df["WLoc"] == "A"]
    home_loser_margin = (home_loser["LScore"] - home_loser["WScore"]).mean()

    # Genel ortalama
    # Ev sahibi net skor farkı
    home_net_margin = ((regular_df[regular_df["WLoc"] == "H"]["WScore"] -
                       regular_df[regular_df["WLoc"] == "H"]["LScore"]).sum() +
                      (regular_df[regular_df["WLoc"] == "A"]["LScore"] -
                       regular_df[regular_df["WLoc"] == "A"]["WScore"]).sum()) / \
                     ((regular_df["WLoc"] == "H").sum() + (regular_df["WLoc"] == "A").sum())

    print(f"\nEv Sahibi Kazandı (WLoc=H):")
    print(f"  Ortalama skor farkı: +{home_winner_margin:.2f}")

    print(f"\nEv Sahibi Kaybetti (WLoc=A):")
    print(f"  Ortalama skor farkı: -{home_loser_margin:.2f}")

    print(f"\nEv Sahibi Net Skor Farkı: +{home_net_margin:.2f}")

    # Beklenen değer
    expected_margin = 5.2
    match = abs(home_net_margin - expected_margin) < 0.5
    print(f"Beklenen: +{expected_margin}")
    print(f"Durum: {('✅ YAKIN' if match else '❌ FARKLI')}")

    return home_net_margin


def verify_conference_effects(regular_df):
    """Konferans içi/dışı analizini dogrula"""

    print("\n" + "="*80)
    print("5. KONFERANS İÇİ/DIŞI ANALİZİ DOGRULAMA")
    print("="*80)

    # Bu analiz için MTeamConferences.csv gerekiyor
    data_path = Path("march-machine-leraning-mania-2026")

    try:
        conferences_df = pd.read_csv(data_path / "MTeamConferences.csv")

        # Konferans eşleştirme tablosu oluştur
        conf_map = {}
        for _, row in conferences_df.iterrows():
            conf_map[(row["Season"], row["TeamID"])] = row["ConfAbbrev"]

        # Regular season'a konferans ekle
        regular_df = regular_df.copy()
        regular_df["WConf"] = regular_df.apply(
            lambda row: conf_map.get((row["Season"], row["WTeamID"]), "UNKNOWN"),
            axis=1
        )
        regular_df["LConf"] = regular_df.apply(
            lambda row: conf_map.get((row["Season"], row["LTeamID"]), "UNKNOWN"),
            axis=1
        )

        # Konferans içi/dışı belirle
        regular_df["SameConf"] = regular_df["WConf"] == regular_df["LConf"]

        # Konferans içi maçlar
        same_conf = regular_df[regular_df["SameConf"] == True]
        same_conf_home = (same_conf["WLoc"] == "H").sum()
        same_conf_total = (same_conf["WLoc"].isin(["H", "A"])).sum()
        same_conf_pct = same_conf_home / same_conf_total * 100 if same_conf_total > 0 else 0

        # Konferans dışı maçlar
        diff_conf = regular_df[regular_df["SameConf"] == False]
        diff_conf_home = (diff_conf["WLoc"] == "H").sum()
        diff_conf_total = (diff_conf["WLoc"].isin(["H", "A"])).sum()
        diff_conf_pct = diff_conf_home / diff_conf_total * 100 if diff_conf_total > 0 else 0

        print(f"\nKonferans İçi Maçlar:")
        print(f"  Ev sahibi kazanma: {same_conf_pct:.1f}%")
        print(f"  Beklenen: 67.5%")
        print(f"  Durum: {'✅' if abs(same_conf_pct - 67.5) < 2 else '❌'}")

        print(f"\nKonferans Dışı Maçlar:")
        print(f"  Ev sahibi kazanma: {diff_conf_pct:.1f}%")
        print(f"  Beklenen: 63.2%")
        print(f"  Durum: {'✅' if abs(diff_conf_pct - 63.2) < 2 else '❌'}")

        return {
            "same_conf_pct": same_conf_pct,
            "diff_conf_pct": diff_conf_pct
        }

    except Exception as e:
        print(f"\nKonferans analizi yapılamadı: {e}")
        return None


def main():
    """Ana fonksiyon"""

    print("="*80)
    print("WLOC ANALIZI - TAM DOGRULAMA")
    print("="*80)
    print("04_wloc_analizi.txt dosyasindaki tum degerler kontrol ediliyor...")

    data_path = Path("march-machine-leraning-mania-2026")

    # 1. Turnuva WLoc
    tourney_results = verify_tournament_wloc()

    # 2. Regular Season WLoc
    reg_results = verify_regular_season_wloc()

    # 3. Ev Sahibi Avantaji
    regular_df = pd.read_csv(data_path / "MRegularSeasonCompactResults.csv")
    ha_results = verify_home_advantage(regular_df)

    # 4. Skor Avantaji
    score_margin = verify_score_advantage(regular_df)

    # 5. Konferans İçi/Dışı
    conf_results = verify_conference_effects(regular_df)

    # ÖZET
    print("\n" + "="*80)
    print("DOGRULAMA ÖZETI")
    print("="*80)

    print(f"\n{'Analiz':<30} {'Beklenen':<20} {'Gerçek':<20} {'Durum'}")
    print("-" * 80)

    checks = [
        ("Turnuva Toplam Maç", "2,585", f"{tourney_results['total']:,}",
         "✅" if tourney_results['total'] == 2585 else "❌"),

        ("Turnuva Hep N", "100% N", "100% N",
         "✅" if tourney_results['n_count'] == tourney_results['total'] else "❌"),

        ("Reg. Toplam Maç", "196,823", f"{reg_results['total']:,}",
         "✅" if reg_results['total'] == 196823 else "❌"),

        ("Reg. H (Home)", "116,270", f"{reg_results['h_count']:,}",
         "✅" if reg_results['h_count'] == 116270 else "❌"),

        ("Reg. A (Away)", "60,435", f"{reg_results['a_count']:,}",
         "✅" if reg_results['a_count'] == 60435 else "❌"),

        ("Reg. N (Neutral)", "20,118", f"{reg_results['n_count']:,}",
         "✅" if reg_results['n_count'] == 20118 else "❌"),

        ("Ev Sahibi %", "65.8%", f"{ha_results['home_win_pct']:.1f}%",
         "✅" if abs(ha_results['home_win_pct'] - 65.8) < 0.1 else "❌"),

        ("Skor Farkı", "+5.2", f"+{score_margin:.2f}",
         "✅" if abs(score_margin - 5.2) < 0.5 else "❌"),
    ]

    for check in checks:
        print(f"{check[0]:<30} {check[1]:<20} {check[2]:<20} {check[3]}")

    print("\n" + "="*80)
    print("SONUÇ")
    print("="*80)

    all_pass = all("✅" in check[3] for check in checks)

    if all_pass:
        print("\n✅ TÜM DEĞERLER DOĞRULANDI!")
        print("04_wloc_analizi.txt dosyasindaki tum veriler doğru.")
    else:
        failed = [check[0] for check in checks if "❌" in check[3]]
        print(f"\n❌ BAZI DEĞERLER FARKLI:")
        for f in failed:
            print(f"  - {f}")


if __name__ == "__main__":
    main()
