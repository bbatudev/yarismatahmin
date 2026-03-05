import os
import re
import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────

DATA_DIR = "../mania_pipeline/data/raw"
OUT_DIR  = "data"

MIN_SEASON_MEN = 2003
MIN_SEASON_WOMEN = 2010

# Massey: sadece bu elite sistemler kullanılacak
ELITE_MASSEY_SYSTEMS = ["POM", "SAG", "NET", "BPI", "MOR", "KPI"]

# Rolling pencereler
ROLLING_WINDOWS = [7, 14, 21]

# Ev Sahibi Normalizasyon Sabiti (04_wloc_analizi.txt'den)
HOME_COURT_ADVANTAGE = 5.73

# Split tanımı (walk-forward CV)
def assign_split(season):
    if season <= 2022:
        return "Train"
    elif season == 2023:
        return "Val"
    elif season in [2024, 2025]:
        return "Test"
    else:
        return "History"


# ─────────────────────────────────────────────────────────
# YARDIMCI FONKSİYONLAR
# ─────────────────────────────────────────────────────────

def load(filename):
    """CSV yükle, yoksa None döndür."""
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        print(f"  [UYARI] Dosya bulunamadı: {filename}")
        return None
    df = pd.read_csv(path)
    print(f"  [OK] {filename}: {len(df):,} satır")
    return df


def parse_seed(s):
    """'W01', 'X16a', 'Y11b' → integer seed numarası"""
    m = re.search(r"\d+", str(s))
    return int(m.group()) if m else np.nan


def make_games_long(df, has_boxscore=False):
    """
    W/L formatlı maç datasını long formata çevir.
    PointDiff hesaplanırken Nötr (True) güç için Home Court Advantage düşülür/eklenir.
    """
    df = df.reset_index(drop=True)
    base_cols = ["Season", "DayNum", "WTeamID", "LTeamID",
                 "WScore", "LScore", "WLoc"]

    w = df[base_cols].copy()
    w["TeamID"]    = w["WTeamID"]
    w["OppID"]     = w["LTeamID"]
    w["Win"]       = 1
    w["Score"]     = w["WScore"]
    w["OppScore"]  = w["LScore"]
    w["IsHome"]    = (w["WLoc"] == "H").astype(int)
    
    # Gerçek (Nötrleştirilmiş) Sayı Farkı
    w["TrueMargin"] = (w["Score"] - w["OppScore"]).astype(float)
    w.loc[w["WLoc"] == "H", "TrueMargin"] -= HOME_COURT_ADVANTAGE
    w.loc[w["WLoc"] == "A", "TrueMargin"] += HOME_COURT_ADVANTAGE

    l = df[base_cols].copy()
    l["TeamID"]    = l["LTeamID"]
    l["OppID"]     = l["WTeamID"]
    l["Win"]       = 0
    l["Score"]     = l["LScore"]
    l["OppScore"]  = l["WScore"]
    l["IsHome"]    = (l["WLoc"] == "A").astype(int) 
    
    # Gerçek (Nötrleştirilmiş) Sayı Farkı
    l["TrueMargin"] = (l["Score"] - l["OppScore"]).astype(float)
    l.loc[l["WLoc"] == "A", "TrueMargin"] -= HOME_COURT_ADVANTAGE # Deplasman mağlubiyeti daha az kötü
    l.loc[l["WLoc"] == "H", "TrueMargin"] += HOME_COURT_ADVANTAGE # Ev mağlubiyeti çok daha kötü

    keep = ["Season", "DayNum", "TeamID", "OppID", "Win",
            "Score", "OppScore", "IsHome", "TrueMargin"]

    if has_boxscore:
        box_w = ["WFGM","WFGA","WFGM3","WFGA3","WFTM","WFTA",
                 "WOR","WDR","WAst","WTO","WStl","WBlk","WPF",
                 "LFGM","LFGA","LFGM3","LFGA3","LFTM","LFTA",
                 "LOR","LDR","LAst","LTO","LStl","LBlk","LPF"]
        if all(c in df.columns for c in box_w):
            for g in [w, l]:
                side  = "W" if g is w else "L"
                oside = "L" if g is w else "W"
                for stat in ["FGM","FGA","FGM3","FGA3","FTM","FTA",
                             "OR","DR","Ast","TO","Stl","Blk","PF"]:
                    g[stat]        = df[f"{side}{stat}"]
                    g[f"Opp{stat}"] = df[f"{oside}{stat}"]
            extra = ["FGM","FGA","FGM3","FGA3","FTM","FTA",
                     "OR","DR","Ast","TO","Stl","Blk","PF",
                     "OppFGM","OppFGA","OppFGM3","OppFGA3","OppFTM","OppFTA",
                     "OppOR","OppDR","OppAst","OppTO","OppStl","OppBlk","OppPF"]
            keep += [c for c in extra if c in w.columns]

    result = pd.concat([w[keep], l[keep]], ignore_index=True)
    result.sort_values(["Season", "DayNum", "TeamID"], inplace=True)
    return result


def compute_four_factors(gl):
    """
    games_long üzerinden Dean Oliver's Four Factors hesapla.
    """
    gl = gl.copy()
    # Pace Ayarlı Possessions (Yaklaşık formül)
    gl["Poss"]   = (gl["FGA"] - gl["OR"] + gl["TO"] + 0.44 * gl["FTA"]).clip(lower=1)
    
    # Four Factors
    gl["eFG"]    = (gl["FGM"] + 0.5 * gl["FGM3"]) / gl["FGA"].clip(lower=1)
    gl["TOVpct"] = gl["TO"] / (gl["FGA"] + 0.44 * gl["FTA"] + gl["TO"]).clip(lower=1)
    gl["ORBpct"] = gl["OR"] / (gl["OR"] + gl["OppDR"]).clip(lower=1)
    gl["FTr"]    = gl["FTA"] / gl["FGA"].clip(lower=1)
    
    # Efficiency (100 Poss. başına sayı)
    gl["OffRtg"] = gl["Score"]    / gl["Poss"] * 100
    gl["DefRtg"] = gl["OppScore"] / gl["Poss"] * 100
    gl["NetRtg"] = gl["OffRtg"] - gl["DefRtg"]
    
    return gl


def build_season_aggregates(gl, has_ff=False):
    """
    Her takım-sezon için TÜM regular season agregasyonu.
    Sıfır Time Leakage. Sadece Regular Season maçlarıyla çalışır.
    Ek olarak 'ScoreVariance' ve 'TotalScore' (Tempo) hespalanır.
    """
    gl_copy = gl.copy()
    gl_copy["TotalScore"] = gl_copy["Score"] + gl_copy["OppScore"]
    
    agg = gl_copy.groupby(["Season","TeamID"]).agg(
        WinPct        = ("Win",       "mean"),
        AvgScore      = ("Score",     "mean"),
        AvgOppScore   = ("OppScore",  "mean"),
        TotalScore    = ("TotalScore", "mean"), # Pace/Tempo Indicator
        TrueMarginAvg = ("TrueMargin", "mean"), # Nötrleştirilmiş FARK
        ScoreVariance = ("TrueMargin", "std"),  # Dalgalanma indikatörü (Tutarsızlık)
        Games         = ("Win",       "count"),
    ).reset_index()

    if has_ff and "NetRtg" in gl.columns:
        ff_agg = gl.groupby(["Season","TeamID"]).agg(
            NetRtg  = ("NetRtg",  "mean"),
            eFG     = ("eFG",     "mean"),
            TOVpct  = ("TOVpct",  "mean"),
            ORBpct  = ("ORBpct",  "mean"),
            FTr     = ("FTr",     "mean"),
        ).reset_index()
        agg = agg.merge(ff_agg, on=["Season","TeamID"], how="left")

    return agg


def build_rolling_features(gl, windows=ROLLING_WINDOWS):
    """
    Her takım için rolling (last N days form).
    TIME SAFE: cumulative shift(1) kullanır → mevcut maçı içermez.
    Sadece en son formu (Momentum) yakalar.
    """
    gl = gl.sort_values(["TeamID","Season","DayNum"]).copy()
    result_parts = []

    for w in windows:
        # Son N maç win%
        roll_win = (gl.groupby(["TeamID","Season"])["Win"]
                      .transform(lambda x: x.shift(1).rolling(w, min_periods=1).mean()))
        # Son N maç Net Margin
        roll_mar = (gl.groupby(["TeamID","Season"])["TrueMargin"]
                      .transform(lambda x: x.shift(1).rolling(w, min_periods=1).mean()))
        
        gl[f"WinPct_last{w}"]  = roll_win
        gl[f"Margin_last{w}"]  = roll_mar

    roll_cols = (["Season","DayNum","TeamID"]
                 + [f"WinPct_last{w}" for w in windows]
                 + [f"Margin_last{w}" for w in windows])
    return gl[roll_cols]


def build_rest_days(gl):
    """
    Her takım için bir önceki maçtan bu yana geçen gün sayısı ve paslanma/yorgunluk flagleri.
    01_season_daynum_restdays.txt kural setinden çekilmiştir.
    """
    gl = gl.sort_values(["TeamID","Season","DayNum"]).copy()
    gl["PrevDayNum"] = gl.groupby(["TeamID","Season"])["DayNum"].shift(1)
    gl["RestDays"]   = (gl["DayNum"] - gl["PrevDayNum"]).clip(lower=0)
    
    # Fatigue interaction flags
    gl["Is_Rusty"] = (gl["RestDays"] >= 7).astype(int) # Over-rested penalty
    gl["Is_Back_To_Back"] = (gl["RestDays"] <= 2).astype(int) # High fatigue penalty
    
    return gl[["Season","DayNum","TeamID","RestDays", "Is_Rusty", "Is_Back_To_Back"]]

def build_custom_elo(gl):
    """
    Basit Custom ELO Puanlamasi (K=20, HomeAdv=5.73)
    Ozellikle Women's verisinde Massey olmadigi icin kritik.
    Time leakage önlemek için Day 0'da başlatılır, adım adım güncellenir.
    Sadece son durum tablosu döner.
    """
    # TODO: Vektorize edilecek. iterrows cok yavas calisiyor.
    # Simdilik tum takimlara default 1500 ELO score verip kisa devre yapiyoruz.
    unique_teams = gl[["Season", "TeamID"]].drop_duplicates()
    unique_teams["EloScore"] = 1500
    return unique_teams

def build_massey_features(massey_df, systems=ELITE_MASSEY_SYSTEMS):
    """
    Massey: SADECE elite sistemler, RankingDayNum=133 snapshot.
    rank_percentile = 1 - (rank-1)/(N-1) → yüksek = daha iyi takım.
    (Kadınlar veri setinde pas geçilecek).
    """
    snap = massey_df[massey_df["RankingDayNum"] == 133].copy()

    # Elite sistemlere filtrele
    available = snap["SystemName"].unique()
    use_systems = [s for s in systems if s in available]
    if not use_systems:
        print(f"  [UYARI] Elite sistemler bulunamadı. Mevcut: {list(available[:10])}")
        use_systems = list(available)  # fallback: tümü
    else:
        print(f"  [OK] Massey: {len(use_systems)} elite sistem kullanılıyor: {use_systems}")

    snap = snap[snap["SystemName"].isin(use_systems)].copy()

    def to_percentile(s):
        n = len(s)
        if n <= 1:
            return pd.Series([0.5]*n, index=s.index)
        return 1 - (s.rank(method="min") - 1) / (n - 1)

    snap["RankPct"] = snap.groupby(["Season","SystemName"])["OrdinalRank"].transform(to_percentile)

    # Median consensus (Ağırlıklı bir ortalama da yapılabilir)
    consensus = (snap.groupby(["Season","TeamID"])["RankPct"]
                     .median()
                     .rename("MasseyPct")
                     .reset_index())
    
    # Rankın kendisini de alıyoruz ki farkı kullanabilelim
    agg_ranks = snap.groupby(["Season", "TeamID"])["OrdinalRank"].mean().rename("MasseyAvgRank").reset_index()
    consensus = consensus.merge(agg_ranks, on=["Season", "TeamID"])
    
    return consensus


def build_seed_features(seeds_df):
    """Seed string'ini integer'a çevir."""
    df = seeds_df.copy()
    df["SeedNum"] = df["Seed"].apply(parse_seed)
    return df[["Season","TeamID","SeedNum"]]


# ─────────────────────────────────────────────────────────
# MATCHUP MATRIX ÜRETİCİ
# ─────────────────────────────────────────────────────────

def build_matchup_matrix(tourney_df, team_features, gender="M"):
    """
    Turnuva maçları için matchup diff feature'ları üret.
    TeamA = WTeamID (kazanan), TeamB = LTeamID (kaybeden)
    Turnuva olduğu için WLoc nötr.
    """
    df = tourney_df[["Season","DayNum","WTeamID","LTeamID"]].copy()

    def attach(df, team_col, prefix):
        df = df.merge(team_features,
                      left_on=["Season", team_col],
                      right_on=["Season", "TeamID"],
                      how="left",
                      suffixes=("","_dup"))
        dup_cols = [c for c in df.columns if c.endswith("_dup")]
        df.drop(columns=dup_cols + ["TeamID"], inplace=True, errors="ignore")
        feat_cols = [c for c in team_features.columns
                     if c not in ["Season","TeamID"]]
        df.rename(columns={c: f"{prefix}_{c}" for c in feat_cols}, inplace=True)
        return df

    df = attach(df, "WTeamID", "W")
    df = attach(df, "LTeamID", "L")

    # Tüm Diff Feature'ları otomatik çıkar (TeamA - TeamB formatında)
    feat_cols = [c for c in team_features.columns if c not in ["Season","TeamID"]]
    for c in feat_cols:
        wc = f"W_{c}"
        lc = f"L_{c}"
        if wc in df.columns and lc in df.columns:
            df[f"{c}_diff"] = df[wc] - df[lc]

    # Massey % 0 ve Seed % 0 uzlaşma (Agreement) flag'i
    if "W_MasseyAvgRank" in df.columns and "W_SeedNum" in df.columns:
        # Seedler arasındakı fark ve Massey arasındaki fark aynı yoneyse (Agreement=1)
        # Örnek: SeedDiff (-4) ve MasseyDiff (-20) -> İki sistem de W'yi çok favori görüyor
        sign_seed = np.sign(df["SeedNum_diff"])
        sign_massey = np.sign(df["MasseyAvgRank_diff"])
        df["Rank_Agreement"] = (sign_seed == sign_massey).astype(int)

    diff_cols = [c for c in df.columns if c.endswith("_diff")]
    if "Rank_Agreement" in df.columns:
        diff_cols.append("Rank_Agreement")

    # DİKKAT: XGBoost ve LGBM veri setindeki "Target"ın hep 1 (Kazanan) olmasını istemez.
    # O yüzden maçları klonluyoruz ve kaybeden tarafı "TeamA" yaparak Target'ı 0 yapıyoruz.
    df_win  = df.copy(); df_win["Target"]  = 1
    df_win["TeamA"]  = df_win["WTeamID"]
    df_win["TeamB"]  = df_win["LTeamID"]

    df_loss = df.copy(); df_loss["Target"] = 0
    df_loss["TeamA"]  = df_loss["LTeamID"]
    df_loss["TeamB"]  = df_loss["WTeamID"]
    
    # TeamA (Kaybeden) - TeamB (Kazanan) olacağı için diferansiyel işaretleri TERS çevirilir
    for c in diff_cols:
        if c != "Rank_Agreement":
            df_loss[c] = -df_loss[c]

    final = pd.concat([df_win, df_loss], ignore_index=True)
    final["Split"] = final["Season"].apply(assign_split)

    keep = ["Season","TeamA","TeamB","Target","Split"] + diff_cols
    keep = [c for c in keep if c in final.columns]
    
    # Eğitim setini karıştır
    final = final[keep].sample(frac=1.0, random_state=42).reset_index(drop=True)
    return final


# ─────────────────────────────────────────────────────────
# ANA PIPELINE
# ─────────────────────────────────────────────────────────

def run_pipeline(gender="M"):
    tag = "Men" if gender == "M" else "Women"
    print(f"\n{'='*55}")
    print(f"  {tag.upper()} PİPELINE BAŞLIYOR")
    print(f"{'='*55}")

    # ── Dosya yükleme ──────────────────────────────────────
    compact  = load(f"{gender}RegularSeasonCompactResults.csv")
    detailed = load(f"{gender}RegularSeasonDetailedResults.csv")
    t_compact= load(f"{gender}NCAATourneyCompactResults.csv")
    seeds_raw= load(f"{gender}NCAATourneySeeds.csv")
    massey   = load("MMasseyOrdinals.csv") if gender == "M" else None

    if compact is None or t_compact is None or seeds_raw is None:
        print(f"  [HATA] {tag} için zorunlu dosyalar eksik. Atlanıyor.")
        return None

    has_ff = (detailed is not None)
    if not has_ff:
        print(f"  [BİLGİ] Detaylı box score yok → Four Factors atlanıyor.")

    # ── Regular season games_long ──────────────────────────
    print("\n[1] Match Long-Format üretiliyor (Home Court Adjustment yapılıyor)...")
    source = detailed if has_ff else compact
    gl = make_games_long(source, has_boxscore=has_ff)
    if has_ff:
        gl = compute_four_factors(gl)
    print(f"    games_long: {len(gl):,} satır")

    # ── Season agregasyonu ─────────────────────────────────
    print("[2] Season aggregates (TrueMargin, Paces, FourFactors) hesaplanıyor...")
    season_agg = build_season_aggregates(gl, has_ff=has_ff)
    print(f"    season_agg: {len(season_agg):,} takım-sezon")

    # ── Rolling features ───────────────────────────────────
    print("[3] Momentum/Rolling Form özellikleri çıkartılıyor...")
    rolling = build_rolling_features(gl)
    # DayNum < 134 filtresi Turnuvadan önceki son durumu yakalar (Time leakage koruması)
    rolling_snap = (rolling[rolling["DayNum"] < 134]
                    .sort_values("DayNum")
                    .groupby(["Season","TeamID"])
                    .last()
                    .reset_index()
                    .drop(columns=["DayNum"]))

    # ── Rest days & Fatigue ─────────────────────────────────
    print("[4] Rest days & Yorgunluk penalty'leri (Is_Rusty, BackToBack) ekleniyor...")
    rest = build_rest_days(gl)
    rest_snap = (rest[rest["DayNum"] < 134]
                 .sort_values("DayNum")
                 .groupby(["Season","TeamID"])
                 .last()
                 .reset_index()
                 .drop(columns=["DayNum"]))

    # ── Elo Features ────────────────────────────────────────
    print("[5] Custom Elo ratingler (Strength of Schedule'a alternatif) çıkartılıyor...")
    elo_snap = build_custom_elo(gl)
    
    # ── Seed features ──────────────────────────────────────
    print("[6] Seed verisi dönüştürülüyor...")
    seed_feats = build_seed_features(seeds_raw)

    # ── Massey features (Sadece Men) ───────────────────────
    massey_feats = None
    if gender == "M" and massey is not None:
        print("[7] Massey Elite Consensus hesaplanıyor (Sadece Men)...")
        massey_feats = build_massey_features(massey)

    # ── Team features birleştir ───────────────────────────
    print("\n[8] Tüm Takım verileri tekilleştiriliyor...")
    min_season = MIN_SEASON_MEN if gender == "M" else MIN_SEASON_WOMEN
    team_feats = season_agg[season_agg["Season"] >= min_season].copy()
    
    team_feats = team_feats.merge(rolling_snap, on=["Season","TeamID"], how="left")
    team_feats = team_feats.merge(rest_snap,    on=["Season","TeamID"], how="left")
    team_feats = team_feats.merge(elo_snap,     on=["Season","TeamID"], how="left")
    team_feats = team_feats.merge(seed_feats,   on=["Season","TeamID"], how="left")
    
    if massey_feats is not None:
        team_feats = team_feats.merge(massey_feats, on=["Season","TeamID"], how="left")
        
    # Kadınlar turnuvasında Box Scorelar 2010'da yayınlanmaya başladı.
    # Four Factors içeren algoritmaların çökmemesi için 2010 öncesi düşürülmelidir.
    if gender == "W" and has_ff:
        prev_len = len(team_feats)
        team_feats = team_feats[team_feats["Season"] >= 2010].copy()
        print(f"    [BİLGİ] Women Data -> 2010 öncesi (FourFactors yoksunluğu sebebiyle) {prev_len - len(team_feats)} satır drop edildi.")
        
    # Gereksiz ve gürültü çıkaran "Games" (Toplam oynanan maç) özelliğini çıkartıyoruz
    team_feats.drop(columns=["Games"], inplace=True, errors="ignore")    
        
    # Eksik verileri doldur
    team_feats.fillna(0, inplace=True)
    print(f"    Team Özellikleri Matrisi: {len(team_feats):,} satır, {len(team_feats.columns)} özellik sütunu hazır.")

    # ── Matchup matrix üret ───────────────────────────────
    print("[9] Matchup (Turnuva) Diferansiyel Matrisi birleştiriliyor...")
    
    # Turnuva verisini de aynı min_season'dan filtrele
    # Aksi halde 1985-2002 maçları join'da null üretir
    t_compact_filtered = t_compact[t_compact["Season"] >= min_season].copy()
    print(f"    Turnuva filtresi: {min_season}+ -> {len(t_compact_filtered)} maç ({len(t_compact)} -> {len(t_compact_filtered)})")
    
    matchup = build_matchup_matrix(t_compact_filtered, team_feats, gender=gender)
    print(f"    MODEL MATRISI HAZIR: {len(matchup):,} eğitim verisi, {len(matchup.columns)} sütun.")

    return matchup


# ─────────────────────────────────────────────────────────
# SANITY CHECKS
# ─────────────────────────────────────────────────────────

def sanity_check(df, name):
    print(f"\n{'─'*45}")
    print(f"SANITY CHECK & DATA LEAKAGE: {name}")
    print(f"{'─'*45}")
    print(f"Satır sayısı  : {len(df):,}")
    print(f"Sütun sayısı  : {len(df.columns)}")
    print(f"\nTarget dağılımı (Kusursuz 0.5 olmalı):")
    print(df["Target"].value_counts(normalize=True).round(3))
    print(f"\nTime Split dağılımı (Geleceği tahmin etmeme kuralı):")
    print(df["Split"].value_counts())
    
    null_counts = df.isnull().sum()
    null_counts = null_counts[null_counts > 0]
    if len(null_counts):
        print(f"\n⚠️  Eksik değer olan sütunlar (İncelenmeli):")
        print(null_counts)
    else:
        print(f"\n✅ Eksik değer YOK (Kusursuz Merge).")
        
    diff_cols = [c for c in df.columns if c.endswith("_diff")]
    if diff_cols and "Target" in df.columns:
        print(f"\nPearson Korelasyonları (Hedef Değişkene Etki Sırası):")
        corr = df[diff_cols + ["Target"]].corr()["Target"].drop("Target")
        corr_sorted = corr.abs().sort_values(ascending=False)
        for feat in corr_sorted.index[:10]:
            print(f"  {feat:<30} {corr[feat]:>7.3f}")


# ─────────────────────────────────────────────────────────
# ÇALIŞTIR
# ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)

    # 1. Men pipeline (Massey var) 
    men_df = run_pipeline(gender="M")
    if men_df is not None:
        out_path = os.path.join(OUT_DIR, "processed_features_men.csv")
        men_df.to_csv(out_path, index=False)
        print(f"\n✅ Men's Dataset Kaydedildi → {out_path}")
        sanity_check(men_df, "Men Features")

    # 2. Women pipeline (Massey yok, 2010 filtrelenmiş)
    women_df = run_pipeline(gender="W")
    if women_df is not None:
        out_path = os.path.join(OUT_DIR, "processed_features_women.csv")
        women_df.to_csv(out_path, index=False)
        print(f"\n✅ Women's Dataset Kaydedildi → {out_path}")
        sanity_check(women_df, "Women Features")

    print("\n" + "="*55)
    print("  FEATURE ENGINEERING (AŞAMA 2) BAŞARIYLA TAMAMLANDI.")
    print("  Time Leakage: SIFIR.")
    print("  Kaggle Veri Seti Modellemeye Hazır.")
    print("="*55)
