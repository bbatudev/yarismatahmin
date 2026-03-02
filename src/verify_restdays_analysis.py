"""
RestDaysDiff analizini doğrula
Turnuva maçları için RestDaysDiff hesapla ve sonuçları kontrol et
"""

import pandas as pd
from pathlib import Path
import sys
import io

# Windows UTF-8 encoding sorunu için
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def get_last_regular_season_daynum(results_df, season, team_id):
    """
    Bir takımın regular season'daki son maçının DayNum'unu bulur.

    Parametres:
    ---------
    results_df : pd.DataFrame
        Regular Season sonuçları
    season : int
        Sezon
    team_id : int
        Takım ID

    Returns:
    --------
    int
        Son regular season maçının DayNum'u, bulunamazsa 0
    """

    team_games = results_df[
        (results_df["Season"] == season) &
        ((results_df["WTeamID"] == team_id) | (results_df["LTeamID"] == team_id))
    ]["DayNum"].max()

    return team_games if pd.notna(team_games) else 0


def calculate_tournament_restdays_diff(regular_df, tournament_df):
    """
    Turnuva maçları için RestDaysDiff hesaplar.
    RestDays = Turnuva maçının DayNum'u - Son regular season maçının DayNum'u

    Parametres:
    ---------
    regular_df : pd.DataFrame
        Regular Season sonuçları
    tournament_df : pd.DataFrame
        Turnuva sonuçları

    Returns:
    --------
    pd.DataFrame
        Turnuva maçları ve RestDaysDiff
    """

    results = []

    for _, row in tournament_df.iterrows():
        season = row["Season"]
        daynum = row["DayNum"]
        wteam = row["WTeamID"]
        lteam = row["LTeamID"]

        # Kazanan takımın son regular season maçını bul
        w_last_daynum = get_last_regular_season_daynum(regular_df, season, wteam)
        w_restdays = daynum - w_last_daynum if w_last_daynum > 0 else daynum

        # Kaybeden takımın son regular season maçını bul
        l_last_daynum = get_last_regular_season_daynum(regular_df, season, lteam)
        l_restdays = daynum - l_last_daynum if l_last_daynum > 0 else daynum

        # RestDaysDiff hesapla (W - L)
        restdays_diff = w_restdays - l_restdays

        results.append({
            "Season": season,
            "DayNum": daynum,
            "WTeamID": wteam,
            "LTeamID": lteam,
            "W_Last_DayNum": w_last_daynum,
            "L_Last_DayNum": l_last_daynum,
            "W_RestDays": w_restdays,
            "L_RestDays": l_restdays,
            "RestDaysDiff": restdays_diff
        })

    return pd.DataFrame(results)


def analyze_restdays_diff(tournament_restdays_df):
    """
    RestDaysDiff analizini yapar.

    Parametres:
    ---------
    tournament_restdays_df : pd.DataFrame
        Turnuva RestDays verileri

    Returns:
    --------
    dict
        Analiz sonuçları
    """

    # RestDaysDiff'e göre kategorize et
    # RestDaysDiff = W_RestDays - L_RestDays
    # Pozitif = Kazanan daha fazla dinlenmiş
    # Negatif = Kazanan daha az dinlenmiş
    # Sıfır = Eşit dinlenme

    categories = tournament_restdays_df["RestDaysDiff"].apply(
        lambda x: "Kazanan daha fazla dinlenmiş" if x > 0 else
                  ("Kazanan daha az dinlenmiş" if x < 0 else "Eşit dinlenme")
    )

    counts = categories.value_counts()
    total = len(tournament_restdays_df)

    avg_restdays_diff = tournament_restdays_df["RestDaysDiff"].mean()
    avg_w_restdays = tournament_restdays_df["W_RestDays"].mean()
    avg_l_restdays = tournament_restdays_df["L_RestDays"].mean()

    return {
        "total_games": total,
        "winner_more_rest": counts.get("Kazanan daha fazla dinlenmiş", 0),
        "winner_less_rest": counts.get("Kazanan daha az dinlenmiş", 0),
        "equal_rest": counts.get("Eşit dinlenme", 0),
        "avg_restdays_diff": avg_restdays_diff,
        "avg_w_restdays": avg_w_restdays,
        "avg_l_restdays": avg_l_restdays
    }


def verify_with_examples(tournament_restdays_df, n=10):
    """
    Örnek maçları göstererek doğrulama yapar.

    Parametres:
    ---------
    tournament_restdays_df : pd.DataFrame
        Turnuva RestDays verileri
    n : int
        Gösterilecek örnek sayısı
    """

    print(f"\n{'='*100}")
    print(f"ÖRNEK TURNUVA MAÇLARI - RestDaysDiff Doğrulama")
    print(f"{'='*100}")

    sample = tournament_restdays_df.sample(min(n, len(tournament_restdays_df))).sort_values("Season")

    print(f"\n{'Sezon':<8} {'DayNum':<8} {'WTşm':<8} {'LTşm':<8} {'W-Son':<8} {'L-Son':<8} {'W-REST':<8} {'L-REST':<8} {'Diff':<8} {'Kontrol'}")
    print("-" * 100)

    for _, row in sample.iterrows():
        season = row["Season"]
        daynum = row["DayNum"]
        wteam = row["WTeamID"]
        lteam = row["LTeamID"]
        w_last = row["W_Last_DayNum"]
        l_last = row["L_Last_DayNum"]
        w_rest = row["W_RestDays"]
        l_rest = row["L_RestDays"]
        diff = row["RestDaysDiff"]

        # Manuel kontrol
        expected_w_rest = daynum - w_last if w_last > 0 else daynum
        expected_l_rest = daynum - l_last if l_last > 0 else daynum
        expected_diff = expected_w_rest - expected_l_rest

        status = "✅" if (w_rest == expected_w_rest and l_rest == expected_l_rest and diff == expected_diff) else "❌"

        print(f"{season:<8} {daynum:<8} {wteam:<8} {lteam:<8} {w_last:<8} {l_last:<8} {w_rest:<8} {l_rest:<8} {diff:<8} {status}")


def main():
    """Ana fonksiyon"""

    data_path = Path("march-machine-leraning-mania-2026")

    # Regular Season verisini oku
    print("Regular Season verisi okunuyor...")
    regular_df = pd.read_csv(data_path / "MRegularSeasonCompactResults.csv")

    # Turnuva verisini oku
    print("Turnuva verisi okunuyor...")
    tournament_df = pd.read_csv(data_path / "MNCAATourneyCompactResults.csv")

    # TÜM sezonları filtrele (1985-2025) - analiz_sonuclari.txt ile karşılaştırma için
    # regular_df = regular_df[regular_df["Season"] >= 2016]
    # tournament_df = tournament_df[tournament_df["Season"] >= 2016]

    print(f"Regular Season maç sayısı: {len(regular_df)}")
    print(f"Turnuva maç sayısı: {len(tournament_df)}")

    # RestDaysDiff hesapla
    print("\nRestDaysDiff hesaplanıyor...")
    tournament_restdays_df = calculate_tournament_restdays_diff(regular_df, tournament_df)

    # Analiz yap
    print("\nAnaliz yapılıyor...")
    results = analyze_restdays_diff(tournament_restdays_df)

    # Sonuçları yazdır
    print(f"\n{'='*100}")
    print(f"RESTDAYSDIFF ANALİZ SONUÇLARI")
    print(f"{'='*100}")

    print(f"\nToplam Turnuva Maçı: {results['total_games']}")

    print(f"\n{'Kategoriler':<35} {'Sayı':<15} {'Yüzde'}")
    print("-" * 70)
    print(f"{'Kazanan daha fazla dinlenmiş':<35} {results['winner_more_rest']:<15} %{results['winner_more_rest']/results['total_games']*100:.1f}")
    print(f"{'Kazanan daha az dinlenmiş':<35} {results['winner_less_rest']:<15} %{results['winner_less_rest']/results['total_games']*100:.1f}")
    print(f"{'Eşit dinlenme':<35} {results['equal_rest']:<15} %{results['equal_rest']/results['total_games']*100:.1f}")

    print(f"\nOrtalama RestDaysDiff: {results['avg_restdays_diff']:.2f}")
    print(f"Ortalama Kazanan RestDays: {results['avg_w_restdays']:.2f}")
    print(f"Ortalama Kaybeden RestDays: {results['avg_l_restdays']:.2f}")

    print(f"\nYorum: ", end="")
    if results['avg_restdays_diff'] < 0:
        print(f"Kazanan ortalama {abs(results['avg_restdays_diff']):.2f} gün AZ dinlenmiş")
    else:
        print(f"Kazanan ortalama {results['avg_restdays_diff']:.2f} gün FAZLA dinlenmiş")

    # Örneklerle doğrula
    verify_with_examples(tournament_restdays_df, n=20)

    print(f"\n{'='*100}")
    print(f"DOĞRULAMA TAMAMLANDI")
    print(f"{'='*100}")


if __name__ == "__main__":
    main()
