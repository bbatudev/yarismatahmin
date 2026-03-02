"""
TÜM KORELASYON ANALİZLERİ - SIFIRDAN MANUEL HESAPLAMA
Her değişken çiftini sıfırdan analiz eder, doğruluğunu kontrol eder

Analiz Edilecekler:
1. RestDays (Season + DayNum → RestDays)
2. RestDaysDiff → Target
3. WScore → LScore
4. WLoc
5. NumOT
6. SeedDiff
7. MasseyRankDiff
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
import io
from scipy.stats import pearsonr, spearmanr

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def load_data():
    """Tüm veri dosyalarını yükle"""

    data_path = Path("march-machine-leraning-mania-2026")

    print("Veri dosyaları yükleniyor...")

    regular = pd.read_csv(data_path / "MRegularSeasonCompactResults.csv")
    tournament = pd.read_csv(data_path / "MNCAATourneyCompactResults.csv")
    seeds = pd.read_csv(data_path / "MNCAATourneySeeds.csv")
    massey = pd.read_csv(data_path / "MMasseyOrdinals.csv")
    regular_detailed = pd.read_csv(data_path / "MRegularSeasonDetailedResults.csv")
    tournament_detailed = pd.read_csv(data_path / "MNCAATourneyDetailedResults.csv")

    print(f"  Regular Season: {len(regular):,} maç")
    print(f"  Turnuva: {len(tournament):,} maç")
    print(f"  Seeds: {len(seeds):,} kayıt")
    print(f"  Massey: {len(massey):,} kayıt")
    print(f"  Regular Detailed: {len(regular_detailed):,} maç")
    print(f"  Tournament Detailed: {len(tournament_detailed):,} maç")

    return {
        "regular": regular,
        "tournament": tournament,
        "seeds": seeds,
        "massey": massey,
        "regular_detailed": regular_detailed,
        "tournament_detailed": tournament_detailed
    }


# ============================================
# ANALIZ 1: RESTDAYS (REGULAR SEASON)
# ============================================

def analyze_restdays_regular(regular_df):
    """Regular Season RestDays analizi - Sıfırdan"""

    print("\n" + "="*80)
    print("ANALİZ 1: RESTDAYS (REGULAR SEASON)")
    print("="*80)

    # Her takımın maçlarını topla
    all_games = []

    for _, row in regular_df.iterrows():
        season, daynum, wteam, lteam = row["Season"], row["DayNum"], row["WTeamID"], row["LTeamID"]
        all_games.append({"Season": season, "DayNum": daynum, "TeamID": wteam})
        all_games.append({"Season": season, "DayNum": daynum, "TeamID": lteam})

    team_df = pd.DataFrame(all_games)
    team_df = team_df.sort_values(["Season", "TeamID", "DayNum"]).reset_index(drop=True)

    # RestDays hesapla
    team_df["PrevDayNum"] = team_df.groupby(["Season", "TeamID"])["DayNum"].shift(1).fillna(0)
    team_df["RestDays"] = team_df["DayNum"] - team_df["PrevDayNum"]

    # İlk maçları hariç tut (ilk maçta RestDays = DayNum olur, bu ortalamayı çarpıtır)
    non_first = team_df[team_df["PrevDayNum"] > 0]

    mean_restdays = non_first["RestDays"].mean()
    median_restdays = non_first["RestDays"].median()

    print(f"\nRegular Season RestDays (İlk maçlar hariç):")
    print(f"  Ortalama: {mean_restdays:.2f} gün")
    print(f"  Medyan: {median_restdays:.2f} gün")

    # Dağılım
    print(f"\nRestDays Dağılımı:")
    for days in [1, 2, 3, 4, 5, 6, 7]:
        count = (non_first["RestDays"] == days).sum()
        pct = count / len(non_first) * 100
        print(f"  {days} gün: {count:,} (%{pct:.1f})")

    return {
        "mean": mean_restdays,
        "median": median_restdays
    }


# ============================================
# ANALIZ 2: RESTDAYSDIFF → TARGET (TURNUVA)
# ============================================

def analyze_restdays_diff_target(regular_df, tournament_df):
    """Turnuva maçları için RestDaysDiff analizi - Sıfırdan"""

    print("\n" + "="*80)
    print("ANALİZ 2: RESTDAYSDIFF → TARGET (TURNUVA)")
    print("="*80)

    # Her takımın son regular season maçını bul
    def get_last_daynum(season, team_id):
        team_games = regular_df[
            (regular_df["Season"] == season) &
            ((regular_df["WTeamID"] == team_id) | (regular_df["LTeamID"] == team_id))
        ]["DayNum"].max()
        return team_games if pd.notna(team_games) else 0

    results = []
    for _, row in tournament_df.iterrows():
        season, daynum, wteam, lteam = row["Season"], row["DayNum"], row["WTeamID"], row["LTeamID"]

        w_last = get_last_daynum(season, wteam)
        l_last = get_last_daynum(season, lteam)

        w_rest = daynum - w_last if w_last > 0 else daynum
        l_rest = daynum - l_last if l_last > 0 else daynum

        results.append({
            "W_RestDays": w_rest,
            "L_RestDays": l_rest,
            "RestDaysDiff": w_rest - l_rest
        })

    df = pd.DataFrame(results)

    # Kategorize et
    df["Category"] = df["RestDaysDiff"].apply(
        lambda x: "Winner More Rest" if x > 0 else ("Winner Less Rest" if x < 0 else "Equal")
    )

    counts = df["Category"].value_counts()
    total = len(df)

    print(f"\nToplam Turnuva Maçı: {total}")

    print(f"\nRestDaysDiff Kategorileri:")
    print(f"  {'Kategori':<25} {'Sayı':<12} {'Yüzde'}")
    print("-" * 55)

    for cat in ["Winner More Rest", "Equal", "Winner Less Rest"]:
        count = counts.get(cat, 0)
        pct = count / total * 100
        print(f"  {cat:<25} {count:<12,} %{pct:.1f}")

    avg_diff = df["RestDaysDiff"].mean()
    avg_w = df["W_RestDays"].mean()
    avg_l = df["L_RestDays"].mean()

    print(f"\nOrtalama RestDaysDiff: {avg_diff:.2f}")
    print(f"Ortalama Kazanan RestDays: {avg_w:.2f}")
    print(f"Ortalama Kaybeden RestDays: {avg_l:.2f}")

    return {
        "total": total,
        "winner_more": counts.get("Winner More Rest", 0),
        "equal": counts.get("Equal", 0),
        "winner_less": counts.get("Winner Less Rest", 0),
        "avg_diff": avg_diff
    }


# ============================================
# ANALIZ 3: WSCORE → LSCORE
# ============================================

def analyze_score_correlation(regular_detailed, tournament_detailed):
    """Skor korelasyonu analizi - Sıfırdan"""

    print("\n" + "="*80)
    print("ANALİZ 3: WSCORE → LSCORE (SKOR KORELASYONU)")
    print("="*80)

    # Regular season
    wscore_reg = regular_detailed["WScore"]
    lscore_reg = regular_detailed["LScore"]
    corr_reg, p_reg = pearsonr(wscore_reg, lscore_reg)

    # Turnuva
    wscore_tour = tournament_detailed["WScore"]
    lscore_tour = tournament_detailed["LScore"]
    corr_tour, p_tour = pearsonr(wscore_tour, lscore_tour)

    # PointDiff
    regular_detailed["PointDiff"] = regular_detailed["WScore"] - regular_detailed["LScore"]
    tournament_detailed["PointDiff"] = tournament_detailed["WScore"] - tournament_detailed["LScore"]

    avg_pointdiff_reg = regular_detailed["PointDiff"].mean()
    avg_pointdiff_tour = tournament_detailed["PointDiff"].mean()

    print(f"\nPearson Korelasyonu:")
    print(f"  Regular Season: {corr_reg:.3f} (p={p_reg:.2e})")
    print(f"  Turnuva: {corr_tour:.3f} (p={p_tour:.2e})")

    print(f"\nOrtalama PointDiff:")
    print(f"  Regular Season: +{avg_pointdiff_reg:.2f}")
    print(f"  Turnuva: +{avg_pointdiff_tour:.2f}")

    return {
        "reg_corr": corr_reg,
        "tour_corr": corr_tour,
        "reg_pointdiff": avg_pointdiff_reg,
        "tour_pointdiff": avg_pointdiff_tour
    }


# ============================================
# ANALIZ 4: WLOC
# ============================================

def analyze_wloc(regular_df, tournament_df, regular_detailed):
    """WLoc analizi - Sıfırdan"""

    print("\n" + "="*80)
    print("ANALİZ 4: WLOC (MAÇ YERİ)")
    print("="*80)

    # Turnuva
    tourney_wloc = tournament_df["WLoc"].value_counts()
    print(f"\nTurnuva WLoc:")
    print(f"  N: {tourney_wloc.get('N', 0):,} (%{tourney_wloc.get('N', 0)/len(tournament_df)*100:.1f})")

    # Regular Season
    reg_wloc = regular_df["WLoc"].value_counts()
    total_reg = len(regular_df)

    print(f"\nRegular Season WLoc:")
    print(f"  Toplam: {total_reg:,} maç")
    print(f"  H (Home): {reg_wloc.get('H', 0):,} (%{reg_wloc.get('H', 0)/total_reg*100:.1f})")
    print(f"  A (Away): {reg_wloc.get('A', 0):,} (%{reg_wloc.get('A', 0)/total_reg*100:.1f})")
    print(f"  N (Neutral): {reg_wloc.get('N', 0):,} (%{reg_wloc.get('N', 0)/total_reg*100:.1f})")

    # Ev sahibi avantajı
    h_count = (regular_df["WLoc"] == "H").sum()
    a_count = (regular_df["WLoc"] == "A").sum()
    home_win_pct = h_count / (h_count + a_count) * 100

    print(f"\nEv Sahibi Kazanma Oranı: %{home_win_pct:.1f}")

    # Skor avantajı (detailed results'tan)
    home_winner = regular_detailed[regular_detailed["WLoc"] == "H"]
    home_loser = regular_detailed[regular_detailed["WLoc"] == "A"]

    home_winner_margin = (home_winner["WScore"] - home_winner["LScore"]).mean()
    home_loser_margin = (home_loser["LScore"] - home_loser["WScore"]).mean()

    # Net skor avantajı
    total_home_games = (regular_df["WLoc"] == "H").sum() + (regular_df["WLoc"] == "A").sum()
    net_margin = ((home_winner["WScore"] - home_winner["LScore"]).sum() +
                  (home_loser["LScore"] - home_loser["WScore"]).sum()) / total_home_games

    print(f"\nEv Sahibi Skor Avantajı: +{net_margin:.2f}")

    return {
        "home_win_pct": home_win_pct,
        "score_advantage": net_margin
    }


# ============================================
# ANALIZ 5: NUMOT (UZATMA SAYISI)
# ============================================

def analyze_numot(regular_df, tournament_df):
    """NumOT analizi - Sıfırdan"""

    print("\n" + "="*80)
    print("ANALİZ 5: NUMOT (UZATMA SAYISI)")
    print("="*80)

    # Regular Season
    reg_ot = regular_df["NumOT"].value_counts().sort_index()
    total_reg = len(regular_df)

    print(f"\nRegular Season NumOT Dağılımı:")
    print(f"  {'Uzatma':<10} {'Maç':<15} {'Yüzde'}")
    print("-" * 40)

    for ot in range(0, 6):
        count = reg_ot.get(ot, 0)
        pct = count / total_reg * 100
        if count > 0:
            print(f"  {ot:<10} {count:<15,} %{pct:.2f}")

    # 6+ uzatma
    ot_6_plus = (regular_df["NumOT"] >= 6).sum()
    if ot_6_plus > 0:
        print(f"  6+        {ot_6_plus:<15,} %{ot_6_plus/total_reg*100:.2f}")

    # Turnuva
    tour_ot = tournament_df["NumOT"].value_counts().sort_index()
    total_tour = len(tournament_df)

    print(f"\nTurnuva NumOT Dağılımı:")
    print(f"  {'Uzatma':<10} {'Maç':<15} {'Yüzde'}")
    print("-" * 40)

    for ot in range(0, 6):
        count = tour_ot.get(ot, 0)
        pct = count / total_tour * 100
        if count > 0:
            print(f"  {ot:<10} {count:<15,} %{pct:.2f}")

    # 6+ uzatma
    ot_6_plus_tour = (tournament_df["NumOT"] >= 6).sum()
    if ot_6_plus_tour > 0:
        print(f"  6+        {ot_6_plus_tour:<15,} %{ot_6_plus_tour/total_tour*100:.2f}")

    return {
        "reg_zero_ot_pct": reg_ot.get(0, 0) / total_reg * 100,
        "tour_zero_ot_pct": tour_ot.get(0, 0) / total_tour * 100
    }


# ============================================
# ANALIZ 6: SEEDDIFF
# ============================================

def extract_seed_value(seed_str):
    """Seed'den sayısal değeri çıkar (örn: "W01" -> 1, "X16" -> 16)"""
    if pd.isna(seed_str):
        return None
    # Seed formatı: "W01", "X16", etc. - son 2 karakter rakam
    try:
        return int(str(seed_str)[-2:])
    except:
        return None


def analyze_seed_diff(tournament_df, seeds_df):
    """SeedDiff analizi - Sıfırdan"""

    print("\n" + "="*80)
    print("ANALİZ 6: SEEDDIFF")
    print("="*80)

    # Seed map oluştur
    seed_map = {}
    for _, row in seeds_df.iterrows():
        seed_map[(row["Season"], row["TeamID"])] = extract_seed_value(row["Seed"])

    results = []
    for _, row in tournament_df.iterrows():
        season, wteam, lteam = row["Season"], row["WTeamID"], row["LTeamID"]

        w_seed = seed_map.get((season, wteam))
        l_seed = seed_map.get((season, lteam))

        if w_seed and l_seed:
            # SeedDiff = Winner_Seed - Loser_Seed
            # Negatif = Kazanan daha iyi seed (düşük sayı)
            seed_diff = w_seed - l_seed
            results.append({"SeedDiff": seed_diff, "W_Seed": w_seed, "L_Seed": l_seed})

    df = pd.DataFrame(results)

    if len(df) == 0:
        print("Seed verisi bulunamadı!")
        return None

    avg_seed_diff = df["SeedDiff"].mean()
    avg_w_seed = df["W_Seed"].mean()
    avg_l_seed = df["L_Seed"].mean()

    print(f"\nToplam maç (seed verisi olan): {len(df):,}")

    print(f"\nSeedDiff İstatistikleri:")
    print(f"  Ortalama: {avg_seed_diff:.2f}")
    print(f"  (Negatif = Kazanan daha iyi seed)")

    print(f"\nOrtalama Seed:")
    print(f"  Kazanan: {avg_w_seed:.2f}")
    print(f"  Kaybeden: {avg_l_seed:.2f}")
    print(f"  Fark: Kazanan ortalama {avg_w_seed - avg_l_seed:.2f} seed daha iyi")

    # Kazanan daha iyi seed olan maç oranı
    winner_better_seed = (df["SeedDiff"] < 0).sum()
    winner_better_seed_pct = winner_better_seed / len(df) * 100

    print(f"\nKazanan Daha İyi Seed:")
    print(f"  Sayı: {winner_better_seed:,}")
    print(f"  Yüzde: %{winner_better_seed_pct:.1f}")

    # SeedDiff → Target korelasyonu
    # SeedDiff negatif olduğunda kazanan daha iyi, bu yüzden ters korelasyon bekleriz
    corr, p_val = spearmanr(abs(df["SeedDiff"]), df["SeedDiff"] < 0)  # Basit kontrol

    print(f"\nSeedDiff → Target ilişkisi:")
    print(f"  SeedDiff ne kadar negatifse, kazanma ihtimali o kadar yüksek")

    return {
        "avg_seed_diff": avg_seed_diff,
        "avg_w_seed": avg_w_seed,
        "avg_l_seed": avg_l_seed,
        "winner_better_pct": winner_better_seed_pct
    }


# ============================================
# ANALIZ 7: MASSEYRANKDIFF
# ============================================

def analyze_massey_rank_diff(tournament_df, massey_df):
    """MasseyRankDiff analizi - Sıfırdan"""

    print("\n" + "="*80)
    print("ANALİZ 7: MASSEYRANKDIFF")
    print("="*80)

    # Her sezon için son Massey sıralamasını al
    # Massey'de düşük rank = iyi takım!

    # Son RankingDayNum'u bul (her sezon)
    last_days = massey_df.groupby("Season")["RankingDayNum"].max().to_dict()

    # Seed map oluştur (son sıralama)
    rank_map = {}
    for _, row in massey_df.iterrows():
        season = row["Season"]
        team_id = row["TeamID"]
        day_num = row["RankingDayNum"]
        rank = row["OrdinalRank"]

        # Sadece son sıralamayı al
        if day_num == last_days[season]:
            rank_map[(season, team_id)] = rank

    results = []
    for _, row in tournament_df.iterrows():
        season, wteam, lteam = row["Season"], row["WTeamID"], row["LTeamID"]

        w_rank = rank_map.get((season, wteam))
        l_rank = rank_map.get((season, lteam))

        if w_rank and l_rank:
            # MasseyRankDiff = Winner_Rank - Loser_Rank
            # Düşük rank = iyi, bu yüzden negatif = kazanan daha iyi
            rank_diff = w_rank - l_rank
            results.append({"MasseyRankDiff": rank_diff, "W_Rank": w_rank, "L_Rank": l_rank})

    df = pd.DataFrame(results)

    if len(df) == 0:
        print("Massey rank verisi bulunamadı!")
        return None

    avg_rank_diff = df["MasseyRankDiff"].mean()
    avg_w_rank = df["W_Rank"].mean()
    avg_l_rank = df["L_Rank"].mean()

    print(f"\nToplam maç (rank verisi olan): {len(df):,}")

    print(f"\nMasseyRankDiff İstatistikleri:")
    print(f"  Ortalama: {avg_rank_diff:.2f}")
    print(f"  (Negatif = Kazanan daha iyi rank)")

    print(f"\nOrtalama Massey Rank:")
    print(f"  Kazanan: {avg_w_rank:.2f}")
    print(f"  Kaybeden: {avg_l_rank:.2f}")
    print(f"  Fark: Kazanan ortalama {avg_w_rank - avg_l_rank:.2f} rank daha iyi")

    # Kazanan daha iyi rank olan maç oranı
    winner_better_rank = (df["MasseyRankDiff"] < 0).sum()
    winner_better_rank_pct = winner_better_rank / len(df) * 100

    print(f"\nKazanan Daha İyi Rank:")
    print(f"  Sayı: {winner_better_rank:,}")
    print(f"  Yüzde: %{winner_better_rank_pct:.1f}")

    return {
        "avg_rank_diff": avg_rank_diff,
        "avg_w_rank": avg_w_rank,
        "avg_l_rank": avg_l_rank,
        "winner_better_pct": winner_better_rank_pct
    }


# ============================================
# ANA FONKSİYON
# ============================================

def main():
    """Tüm analizleri çalıştır"""

    print("="*80)
    print("TÜM KORELASYON ANALİZLERİ - SIFIRDAN MANUEL HESAPLAMA")
    print("="*80)

    # Veriyi yükle
    data = load_data()

    # Sonuçları topla
    all_results = {}

    # 1. RestDays (Regular Season)
    all_results["restdays"] = analyze_restdays_regular(data["regular"])

    # 2. RestDaysDiff → Target (Turnuva)
    all_results["restdaysdiff"] = analyze_restdays_diff_target(data["regular"], data["tournament"])

    # 3. WScore → LScore
    all_results["score"] = analyze_score_correlation(data["regular_detailed"], data["tournament_detailed"])

    # 4. WLoc
    all_results["wloc"] = analyze_wloc(data["regular"], data["tournament"], data["regular_detailed"])

    # 5. NumOT
    all_results["numot"] = analyze_numot(data["regular"], data["tournament"])

    # 6. SeedDiff
    all_results["seeddiff"] = analyze_seed_diff(data["tournament"], data["seeds"])

    # 7. MasseyRankDiff
    all_results["massey"] = analyze_massey_rank_diff(data["tournament"], data["massey"])

    # ÖZET
    print("\n" + "="*80)
    print("TÜM ANALİZLER ÖZETİ")
    print("="*80)

    print(f"\n{'Analiz':<25} {'Sonuç':<40}")
    print("-" * 70)

    print(f"{'RestDays (Reg. Ort)':<25} {all_results['restdays']['mean']:.2f} gün")
    print(f"{'RestDays (Kazanan az)':<25} %{all_results['restdaysdiff']['winner_less']/all_results['restdaysdiff']['total']*100:.1f}")
    print(f"{'RestDaysDiff Ort.':<25} {all_results['restdaysdiff']['avg_diff']:.2f}")
    print(f"{'WScore-LScore Korel.':<25} {all_results['score']['reg_corr']:.3f}")
    print(f"{'Ev Sahibi %':<25} %{all_results['wloc']['home_win_pct']:.1f}")
    print(f"{'Ev Sahibi Skor Adv.':<25} +{all_results['wloc']['score_advantage']:.2f}")
    print(f"{'Reg. 0 Uzatma %':<25} %{all_results['numot']['reg_zero_ot_pct']:.1f}")
    print(f"{'SeedDiff Ort.':<25} {all_results['seeddiff']['avg_seed_diff']:.2f}")
    print(f"{'Kazanan iyi Seed %':<25} %{all_results['seeddiff']['winner_better_pct']:.1f}")
    print(f"{'MasseyRankDiff Ort.':<25} {all_results['massey']['avg_rank_diff']:.2f}")
    print(f"{'Kazanan iyi Rank %':<25} %{all_results['massey']['winner_better_pct']:.1f}")

    print("\n" + "="*80)
    print("ANALİZ TAMAMLANDI")
    print("="*80)


if __name__ == "__main__":
    main()
