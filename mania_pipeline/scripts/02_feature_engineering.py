import os
import re
import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────

DATA_DIR = "march-machine-leraning-mania-2026"
OUT_DIR  = "mania_pipeline/artifacts/data"

MIN_SEASON_MEN = 2003
MIN_SEASON_WOMEN = 2010

# Massey: sadece bu elite sistemler kullanılacak
ELITE_MASSEY_SYSTEMS = ["POM", "SAG", "NET", "BPI", "MOR", "KPI"]

# Rolling pencereler
ROLLING_WINDOWS = [7, 10, 14, 21]

# Close-game tanimi ve Bayesian smoothing parametreleri
CLOSE_GAME_MARGIN = 5
CLOSE_PRIOR_ALPHA = 2.0
CLOSE_PRIOR_BETA = 2.0
PYTHAGOREAN_EXPECTATION_EXPONENT = 11.5

# Four Factors icin gerekli boxscore kolonlari (raw detailed dosyasi)
REQUIRED_BOXSCORE_COLUMNS = [
    "WFGM","WFGA","WFGM3","WFGA3","WFTM","WFTA",
    "WOR","WDR","WAst","WTO","WStl","WBlk","WPF",
    "LFGM","LFGA","LFGM3","LFGA3","LFTM","LFTA",
    "LOR","LDR","LAst","LTO","LStl","LBlk","LPF"
]

# compute_four_factors calismasi icin games_long uzerinde gereken kolonlar
REQUIRED_FOUR_FACTOR_COLUMNS = ["FGA", "OR", "TO", "FTA", "FGM", "FGM3", "OppDR", "Stl", "Blk"]

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


def get_missing_columns(df, required_cols):
    """DataFrame icinde eksik zorunlu kolonlari listele."""
    if df is None:
        return list(required_cols)
    return [c for c in required_cols if c not in df.columns]


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
                 "WScore", "LScore", "WLoc", "NumOT"]

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

    if "NumOT" in df.columns:
        w["NumOT"] = df["NumOT"]
        l["NumOT"] = df["NumOT"]
        w["WentOT"] = (w["NumOT"] > 0).astype(int)
        l["WentOT"] = (l["NumOT"] > 0).astype(int)
        w["IsMultiOT"] = (w["NumOT"] >= 2).astype(int)
        l["IsMultiOT"] = (l["NumOT"] >= 2).astype(int)
        keep += ["NumOT", "WentOT", "IsMultiOT"]

    if has_boxscore:
        if all(c in df.columns for c in REQUIRED_BOXSCORE_COLUMNS):
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
    
    # Contextual FTr: Kendi atma oranın - Rakibin savunmada izin verdiği FTr
    # Oyundaki rakibi (Opp) ele alıyoruz
    gl["OppFTr"] = gl["OppFTA"] / gl["OppFGA"].clip(lower=1)
    gl["FTr_vs_OppAllowed"] = gl["FTr"] - gl["OppFTr"]
    
    # Efficiency (100 Poss. başına sayı)
    gl["OffRtg"] = gl["Score"]    / gl["Poss"] * 100
    gl["DefRtg"] = gl["OppScore"] / gl["Poss"] * 100
    gl["NetRtg"] = gl["OffRtg"] - gl["DefRtg"]
    
    # Defensive Stats as % of Possessions
    gl["StlPct"] = gl["Stl"] / gl["Poss"].clip(lower=1)
    gl["BlkPct"] = gl["Blk"] / gl["Poss"].clip(lower=1)
    
    return gl


def compute_pythagorean_win_pct(avg_score, avg_opp_score, exponent=PYTHAGOREAN_EXPECTATION_EXPONENT):
    """
    Basketbol için klasik Pythagorean expectation.
    Season aggregate seviyesinde kullanılır; yalnızca regular season özetlerinden türetilir.
    """
    score = pd.to_numeric(avg_score, errors="coerce").fillna(0.0).clip(lower=0.0)
    opp_score = pd.to_numeric(avg_opp_score, errors="coerce").fillna(0.0).clip(lower=0.0)

    score_pow = np.power(score.clip(lower=1e-6), exponent)
    opp_pow = np.power(opp_score.clip(lower=1e-6), exponent)
    denom = (score_pow + opp_pow).clip(lower=1e-12)
    return score_pow / denom


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

    agg["PythWR"] = compute_pythagorean_win_pct(agg["AvgScore"], agg["AvgOppScore"])
    agg["Luck"] = agg["WinPct"] - agg["PythWR"]

    # Overtime profili (tempo/volatilite sinyali)
    if {"NumOT", "WentOT", "IsMultiOT"}.issubset(gl_copy.columns):
        ot_agg = gl_copy.groupby(["Season", "TeamID"]).agg(
            OTRate = ("WentOT", "mean"),
            AvgOT = ("NumOT", "mean"),
            MultiOTRate = ("IsMultiOT", "mean"),
        ).reset_index()
        agg = agg.merge(ot_agg, on=["Season", "TeamID"], how="left")

    # Close-game kazanma orani: az ornekli takimlar icin Bayesian smoothing uygula
    gl_copy["IsClose"] = (gl_copy["TrueMargin"].abs() <= CLOSE_GAME_MARGIN).astype(int)
    gl_copy["CloseWin"] = ((gl_copy["IsClose"] == 1) & (gl_copy["Win"] == 1)).astype(int)
    
    close_agg = gl_copy.groupby(["Season","TeamID"]).agg(
        CloseWins = ("CloseWin", "sum"),
        CloseGamesCount = ("IsClose", "sum"),
    ).reset_index()
    close_agg["CloseWinPct"] = (
        close_agg["CloseWins"] + CLOSE_PRIOR_ALPHA
    ) / (
        close_agg["CloseGamesCount"] + CLOSE_PRIOR_ALPHA + CLOSE_PRIOR_BETA
    )
    close_agg = close_agg[["Season", "TeamID", "CloseWinPct", "CloseGamesCount"]]
    agg = agg.merge(close_agg, on=["Season","TeamID"], how="left")

    if has_ff and "NetRtg" in gl.columns:
        ff_agg = gl.groupby(["Season","TeamID"]).agg(
            NetRtg  = ("NetRtg",  "mean"),
            eFG     = ("eFG",     "mean"),
            TOVpct  = ("TOVpct",  "mean"),
            ORBpct  = ("ORBpct",  "mean"),
            FTr     = ("FTr",     "mean"),
            FTr_vs_OppAllowed = ("FTr_vs_OppAllowed", "mean"),
            StlPct  = ("StlPct",  "mean"),
            BlkPct  = ("BlkPct",  "mean"),
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
    Bağlamsal özelliklerle: DaysSinceLastGame, GamesLast7Days, GamesLast14Days, vb.
    """
    gl = gl.sort_values(["TeamID","Season","DayNum"]).copy()
    
    # DaysSinceLastGame (önceki maç ile gün farkı)
    gl["PrevDayNum"] = gl.groupby(["TeamID","Season"])["DayNum"].shift(1)
    gl["DaysSinceLastGame"] = (gl["DayNum"] - gl["PrevDayNum"]).clip(lower=0)
    
    # Kendi kendine B2B_flag hesapla (eğer 2 veya daha az gün ise)
    gl["Is_B2B_Game"] = (gl["DaysSinceLastGame"] <= 2).astype(int)
    
    # GamesLast7Days ve GamesLast14Days için kendi takımı bazında geriye dönük rolling count
    # Veriler TeamID ve Season'a sıralı. Rolling hesaplarken her maçın oynandığı 'DayNum'
    # değerine göre geçmiş 7 veya 14 güne bakarız.
    
    # Daha iyi bir yaklaşım: Geriye dönük sorgu
    def count_recent_games(df_team, days=14):
        # DayNum array'ini al
        day_nums = df_team["DayNum"].values
        counts = np.zeros(len(day_nums))
        b2b_counts = np.zeros(len(day_nums))
        
        is_b2b = df_team["Is_B2B_Game"].values
        
        for i, d in enumerate(day_nums):
            # i'nci maça kadar olan geçmiş maçlardan (kendisinden öncekiler)
            # son `days` gün içindekileri say
            valid_idx = np.where((day_nums[:i] > d - days) & (day_nums[:i] <= d))[0]
            counts[i] = len(valid_idx)
            # Bu filtrede B2B olanları da ayrı say (yorgunluk birikimi = B2B_LastXDays)
            b2b_counts[i] = is_b2b[valid_idx].sum()
            
        return pd.DataFrame({"GamesLastX": counts, "B2B_LastX": b2b_counts}, index=df_team.index)

    # df'yi apply etmesi pahali olabilir, list comprehension ile daha hizli:
    t_groups = []
    for (team_id, season), df_team in gl.groupby(["TeamID", "Season"]):
        day_nums = df_team["DayNum"].values
        is_b2b = df_team["Is_B2B_Game"].values
        
        counts_7, counts_14, b2b_14 = [], [], []
        for i, d in enumerate(day_nums):
            valid_14 = (day_nums[:i] > d - 14) & (day_nums[:i] <= d)
            valid_7 = (day_nums[:i] > d - 7) & (day_nums[:i] <= d)
            counts_14.append(valid_14.sum())
            counts_7.append(valid_7.sum())
            b2b_14.append(is_b2b[:i][valid_14].sum() if len(valid_14)>0 else 0)
            
        df_team = df_team.copy()
        df_team["GamesLast7Days"] = counts_7
        df_team["GamesLast14Days"] = counts_14
        df_team["B2B_Last14Days"] = b2b_14
        t_groups.append(df_team)
        
    gl = pd.concat(t_groups)
    
    return gl[["Season","DayNum","TeamID","DaysSinceLastGame", "GamesLast7Days", "GamesLast14Days", "B2B_Last14Days"]]

def build_massey_features(massey_df, systems=ELITE_MASSEY_SYSTEMS):
    """
    Massey: SADECE elite sistemler, RankingDayNum=133 snapshot.
    (Kadınlar veri setinde pas geçilecek).
    """
    snap = massey_df[massey_df["RankingDayNum"] == 133].copy()

    # Elite sistemlere filtrele
    available = snap["SystemName"].unique()
    use_systems = [s for s in systems if s in available]
    if not use_systems:
        print(f"  [UYARI] Elite sistemler bulunamadı. Mevcut: {list(available[:10])}")
        return pd.DataFrame(
            columns=[
                "Season",
                "TeamID",
                "MasseyPct",
                "MasseyAvgRank",
                "MasseyRankStd",
                "MasseyPctSpread",
                "MasseyOrdinalRange",
            ]
        )
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
    rank_dispersion = (
        snap.groupby(["Season", "TeamID"])["OrdinalRank"]
        .agg(MasseyRankStd="std", MasseyOrdinalMin="min", MasseyOrdinalMax="max")
        .reset_index()
    )
    rank_dispersion["MasseyOrdinalRange"] = (
        rank_dispersion["MasseyOrdinalMax"] - rank_dispersion["MasseyOrdinalMin"]
    )
    rank_dispersion = rank_dispersion.drop(columns=["MasseyOrdinalMin", "MasseyOrdinalMax"])

    pct_dispersion = (
        snap.groupby(["Season", "TeamID"])["RankPct"]
        .agg(MasseyPctMin="min", MasseyPctMax="max")
        .reset_index()
    )
    pct_dispersion["MasseyPctSpread"] = pct_dispersion["MasseyPctMax"] - pct_dispersion["MasseyPctMin"]
    pct_dispersion = pct_dispersion.drop(columns=["MasseyPctMin", "MasseyPctMax"])

    consensus = consensus.merge(agg_ranks, on=["Season", "TeamID"])
    consensus = consensus.merge(rank_dispersion, on=["Season", "TeamID"], how="left")
    consensus = consensus.merge(pct_dispersion, on=["Season", "TeamID"], how="left")

    return consensus


def build_seed_features(seeds_df):
    """Seed string'ini integer'a çevir."""
    df = seeds_df.copy()
    df["SeedNum"] = df["Seed"].apply(parse_seed)
    return df[["Season","TeamID","SeedNum"]]

def build_conference_features(team_base, conf_df, seed_feats):
    """
    Konferans bazli strength/depth feature'lari.
    Leave-one-out ortalama kullanilir: takimin kendi degeri konferans ortalamasindan cikarilir.
    """
    required = {"Season", "TeamID", "ConfAbbrev"}
    if conf_df is None or not required.issubset(conf_df.columns):
        return pd.DataFrame(columns=["Season", "TeamID", "ConfStrength", "ConfWinPct", "ConfTeamCount", "ConfBidCount"])

    conf = conf_df[["Season", "TeamID", "ConfAbbrev"]].drop_duplicates()

    metric_candidates = ["TrueMarginAvg", "WinPct", "NetRtg"]
    metric_cols = [c for c in metric_candidates if c in team_base.columns]
    if not metric_cols:
        return pd.DataFrame(columns=["Season", "TeamID", "ConfStrength", "ConfWinPct", "ConfTeamCount", "ConfBidCount"])

    conf_team = team_base[["Season", "TeamID"] + metric_cols].merge(
        conf, on=["Season", "TeamID"], how="left"
    )
    conf_team = conf_team.dropna(subset=["ConfAbbrev"]).copy()

    grp_keys = ["Season", "ConfAbbrev"]
    conf_team["ConfTeamCount"] = conf_team.groupby(grp_keys)["TeamID"].transform("count")

    if "NetRtg" in conf_team.columns:
        source_strength = "NetRtg"
    else:
        source_strength = "TrueMarginAvg"

    for metric in [source_strength, "WinPct"]:
        if metric not in conf_team.columns:
            continue
        gsum = conf_team.groupby(grp_keys)[metric].transform("sum")
        gcnt = conf_team["ConfTeamCount"]
        season_mean = conf_team.groupby("Season")[metric].transform("mean")
        loo_mean = np.where(gcnt > 1, (gsum - conf_team[metric]) / (gcnt - 1), season_mean)
        conf_team[f"Conf_{metric}_LOO"] = loo_mean

    # Konferansin o sezon turnuvaya kac takim soktugu
    seed_conf = seed_feats.merge(conf, on=["Season", "TeamID"], how="left")
    bid_counts = (
        seed_conf.dropna(subset=["ConfAbbrev"])
        .groupby(grp_keys)["TeamID"]
        .nunique()
        .rename("ConfBidCount")
        .reset_index()
    )
    conf_team = conf_team.merge(bid_counts, on=grp_keys, how="left")
    conf_team["ConfBidCount"] = conf_team["ConfBidCount"].fillna(0)

    if "Conf_NetRtg_LOO" in conf_team.columns:
        conf_team["ConfStrength"] = conf_team["Conf_NetRtg_LOO"]
    else:
        conf_team["ConfStrength"] = conf_team["Conf_TrueMarginAvg_LOO"]
    conf_team["ConfWinPct"] = conf_team.get("Conf_WinPct_LOO", 0.5)

    return conf_team[["Season", "TeamID", "ConfStrength", "ConfWinPct", "ConfTeamCount", "ConfBidCount"]]

def build_coach_features(coaches_df):
    """
    Coach tenure feature'i.
    Yalnizca turnuva oncesi snapshot (FirstDayNum < 134) dikkate alinir.
    """
    required = {"Season", "TeamID", "FirstDayNum", "LastDayNum", "CoachName"}
    if coaches_df is None or not required.issubset(coaches_df.columns):
        return pd.DataFrame(columns=["Season", "TeamID", "CoachTenureYears"])

    df = coaches_df[list(required)].dropna(subset=["CoachName"]).copy()
    df = df[df["FirstDayNum"] < 134].copy()
    if df.empty:
        return pd.DataFrame(columns=["Season", "TeamID", "CoachTenureYears"])

    latest = (
        df.sort_values(["Season", "TeamID", "LastDayNum", "FirstDayNum"])
        .drop_duplicates(subset=["Season", "TeamID"], keep="last")
        .loc[:, ["Season", "TeamID", "CoachName"]]
        .rename(columns={"CoachName": "CurrentCoach"})
    )

    latest = latest.sort_values(["TeamID", "Season"]).reset_index(drop=True)
    latest["CoachTenureYears"] = 1
    for team_id, idx in latest.groupby("TeamID").groups.items():
        idx_list = list(idx)
        tenure = []
        prev_coach = None
        prev_tenure = 0
        for i in idx_list:
            coach = latest.at[i, "CurrentCoach"]
            if coach == prev_coach:
                prev_tenure += 1
            else:
                prev_tenure = 1
            tenure.append(prev_tenure)
            prev_coach = coach
        latest.loc[idx_list, "CoachTenureYears"] = tenure

    return latest[["Season", "TeamID", "CoachTenureYears"]]

def build_program_features(team_base, teams_df):
    """
    Program age: takimin D1 tecrubesi.
    """
    required = {"TeamID", "FirstD1Season"}
    if teams_df is None or not required.issubset(teams_df.columns):
        return pd.DataFrame(columns=["Season", "TeamID", "ProgramAge"])

    base = team_base[["Season", "TeamID"]].drop_duplicates().merge(
        teams_df[["TeamID", "FirstD1Season"]], on="TeamID", how="left"
    )
    base["ProgramAge"] = (base["Season"] - base["FirstD1Season"]).clip(lower=0)
    base["ProgramAge"] = base["ProgramAge"].fillna(0)
    return base[["Season", "TeamID", "ProgramAge"]]


def build_seed_mispricing_features(team_feats, gender="M"):
    """
    Committee seed ile takımın underlying season strength'i arasındaki sapma.
    Sadece turnuva takımları için tanımlıdır; seed snapshot + season aggregate kullanır.
    """
    if "SeedNum" not in team_feats.columns:
        return pd.DataFrame(columns=["Season", "TeamID"])

    out = team_feats[["Season", "TeamID", "SeedNum"]].copy()
    out = out[out["SeedNum"].notna()].copy()
    if out.empty:
        return pd.DataFrame(columns=["Season", "TeamID"])

    out["SeedStrengthScore"] = ((17.0 - out["SeedNum"].astype(float)) / 16.0).clip(lower=0.0, upper=1.0)

    if "PythWR" in team_feats.columns:
        out = out.merge(team_feats[["Season", "TeamID", "PythWR"]], on=["Season", "TeamID"], how="left")
        out["SeedPythMispricing"] = out["PythWR"] - out["SeedStrengthScore"]

    if "NetRtg" in team_feats.columns:
        net_pct = team_feats[["Season", "TeamID", "NetRtg"]].copy()
        net_pct["NetRtgSeasonPct"] = (
            net_pct.groupby("Season")["NetRtg"]
            .rank(method="average", pct=True)
            .clip(lower=0.0, upper=1.0)
        )
        out = out.merge(net_pct[["Season", "TeamID", "NetRtgSeasonPct"]], on=["Season", "TeamID"], how="left")
        out["SeedNetRtgMispricing"] = out["NetRtgSeasonPct"] - out["SeedStrengthScore"]

    if gender == "M" and "MasseyPct" in team_feats.columns:
        out = out.merge(team_feats[["Season", "TeamID", "MasseyPct"]], on=["Season", "TeamID"], how="left")
        out["SeedMasseyMispricing"] = out["MasseyPct"] - out["SeedStrengthScore"]

    keep_cols = [column for column in out.columns if column not in {"SeedNum", "PythWR", "NetRtgSeasonPct", "MasseyPct"}]
    return out[keep_cols]

def build_conf_tourney_features(conf_tourney_df, ncaa_tourney_df, min_season=None):
    """
    Konferans turnuvasi baglami:
    - kac mac oynadi (yorgunluk)
    - kazanma orani (guncel form)
    - konferans sampiyonu mu
    - konferans finalinden NCAA baslangicina kac gun var
    """
    required = {"Season", "ConfAbbrev", "DayNum", "WTeamID", "LTeamID"}
    if conf_tourney_df is None or not required.issubset(conf_tourney_df.columns):
        return pd.DataFrame(
            columns=[
                "Season",
                "TeamID",
                "ConfTourneyGamesPlayed",
                "ConfTourneyWinPct",
                "ConfTourneyChampion",
                "DaysSinceConfFinal",
            ]
        )

    ct = conf_tourney_df[list(required)].copy()
    if min_season is not None:
        ct = ct[ct["Season"] >= min_season].copy()
    if ct.empty:
        return pd.DataFrame(
            columns=[
                "Season",
                "TeamID",
                "ConfTourneyGamesPlayed",
                "ConfTourneyWinPct",
                "ConfTourneyChampion",
                "DaysSinceConfFinal",
            ]
        )

    w = ct[["Season", "ConfAbbrev", "DayNum", "WTeamID"]].rename(columns={"WTeamID": "TeamID"})
    w["Win"] = 1
    l = ct[["Season", "ConfAbbrev", "DayNum", "LTeamID"]].rename(columns={"LTeamID": "TeamID"})
    l["Win"] = 0
    long_ct = pd.concat([w, l], ignore_index=True)

    agg = long_ct.groupby(["Season", "TeamID"]).agg(
        ConfTourneyGamesPlayed=("Win", "count"),
        ConfTourneyWinPct=("Win", "mean"),
        LastConfTourneyDay=("DayNum", "max"),
    ).reset_index()

    finals = ct[ct["DayNum"] == ct.groupby(["Season", "ConfAbbrev"])["DayNum"].transform("max")].copy()
    champions = finals[["Season", "WTeamID"]].drop_duplicates().rename(columns={"WTeamID": "TeamID"})
    champions["ConfTourneyChampion"] = 1
    agg = agg.merge(champions, on=["Season", "TeamID"], how="left")
    agg["ConfTourneyChampion"] = agg["ConfTourneyChampion"].fillna(0).astype(int)

    ncaa_start = ncaa_tourney_df.groupby("Season")["DayNum"].min().rename("NCAAStartDay").reset_index()
    agg = agg.merge(ncaa_start, on="Season", how="left")
    agg["DaysSinceConfFinal"] = (agg["NCAAStartDay"] - agg["LastConfTourneyDay"]).clip(lower=0)

    return agg[
        [
            "Season",
            "TeamID",
            "ConfTourneyGamesPlayed",
            "ConfTourneyWinPct",
            "ConfTourneyChampion",
            "DaysSinceConfFinal",
        ]
    ]

def build_round_context_features(df, gender="M", seed_round_slots_df=None):
    """
    Match bazli tur baglami.
    M verisi icin NCAATourneySeedRoundSlots'tan gun->tur eslemesi denenir.
    Eksik kalanlarda fallback: sezon icindeki DayNum sirasini 1..6 banda mapler.
    """
    out = df[["Season", "DayNum"]].copy()
    out["Round_Num"] = np.nan

    has_seed_round_slots = (
        seed_round_slots_df is not None
        and {"GameRound", "EarlyDayNum", "LateDayNum"}.issubset(seed_round_slots_df.columns)
    )
    if has_seed_round_slots:
        srs = seed_round_slots_df[["GameRound", "EarlyDayNum", "LateDayNum"]].copy()
        early = srs[["GameRound", "EarlyDayNum"]].rename(columns={"EarlyDayNum": "DayNum"})
        late = srs[["GameRound", "LateDayNum"]].rename(columns={"LateDayNum": "DayNum"})
        day_round = pd.concat([early, late], ignore_index=True).dropna(subset=["DayNum"])
        day_round["DayNum"] = day_round["DayNum"].astype(int)
        # Kaggle dosyasında GameRound=0 (First Four/play-in) bulunabiliyor.
        # Model tarafında Round_Num'u 1..6 bandında tutmak için 0 değerini 1'e mapliyoruz.
        day_to_round = day_round.groupby("DayNum")["GameRound"].min().to_dict()
        day_to_round = {k: max(1, int(v)) for k, v in day_to_round.items()}
        known_days = sorted(day_to_round.keys())

        if known_days:
            def map_round(day_num):
                d = int(day_num)
                if d in day_to_round:
                    return int(day_to_round[d])
                lower = [x for x in known_days if x <= d]
                if lower:
                    return int(day_to_round[lower[-1]])
                return int(day_to_round[known_days[0]])

            out["Round_Num"] = out["DayNum"].map(map_round)

    missing = out["Round_Num"].isna()
    if missing.any():
        rank = out.groupby("Season")["DayNum"].rank(method="dense").astype(int)
        max_rank = out.groupby("Season")["DayNum"].transform("nunique").clip(lower=1)
        fallback_round = np.ceil((rank / max_rank) * 6).astype(int).clip(1, 6)
        out.loc[missing, "Round_Num"] = fallback_round[missing]

    out["Round_Num"] = out["Round_Num"].astype(int).clip(1, 6)
    out["Is_FirstWeekend"] = (out["Round_Num"] <= 2).astype(int)
    out["Is_SecondWeekend"] = out["Round_Num"].between(3, 4).astype(int)
    out["Is_FinalWeekend"] = (out["Round_Num"] >= 5).astype(int)
    return out[["Round_Num", "Is_FirstWeekend", "Is_SecondWeekend", "Is_FinalWeekend"]]


# ─────────────────────────────────────────────────────────
# MATCHUP MATRIX ÜRETİCİ
# ─────────────────────────────────────────────────────────

def build_matchup_matrix(tourney_df, team_features, gender="M", seed_round_slots_df=None):
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

    if {"W_eFG", "L_eFG", "W_BlkPct", "L_BlkPct"}.issubset(df.columns):
        # Hücum verimliliğini rakibin pota koruma profiliyle çarpıştıran tek, yönlü style-clash sinyali.
        df["StyleClash_eFG_BlkPct_diff"] = (
            df["W_eFG"] * (1.0 - df["L_BlkPct"].clip(lower=0.0, upper=1.0))
            - df["L_eFG"] * (1.0 - df["W_BlkPct"].clip(lower=0.0, upper=1.0))
        )

    diff_cols = [c for c in df.columns if c.endswith("_diff")]
    
    # Women tarafinda klasik FTr_diff zayif; baglamsal versiyonu tutup bunu cikariyoruz.
    if gender == "W" and "FTr_diff" in diff_cols and "FTr_vs_OppAllowed_diff" in diff_cols:
        diff_cols.remove("FTr_diff")

    # DİKKAT: XGBoost ve LGBM veri setindeki "Target"ın hep 1 (Kazanan) olmasını istemez.
    # O yüzden maçları klonluyoruz ve kaybeden tarafı "TeamA" yaparak Target'ı 0 yapıyoruz.
    df_win  = df.copy(); df_win["Target"]  = 1
    df_win["TeamA"]  = df_win["WTeamID"]
    df_win["TeamB"]  = df_win["LTeamID"]
    if "W_SeedNum" in df_win.columns and "L_SeedNum" in df_win.columns:
        df_win["TeamA_SeedNum"] = df_win["W_SeedNum"]
        df_win["TeamB_SeedNum"] = df_win["L_SeedNum"]

    df_loss = df.copy(); df_loss["Target"] = 0
    df_loss["TeamA"]  = df_loss["LTeamID"]
    df_loss["TeamB"]  = df_loss["WTeamID"]
    if "W_SeedNum" in df_loss.columns and "L_SeedNum" in df_loss.columns:
        df_loss["TeamA_SeedNum"] = df_loss["L_SeedNum"]
        df_loss["TeamB_SeedNum"] = df_loss["W_SeedNum"]
    
    # TeamA (Kaybeden) - TeamB (Kazanan) olacağı için diferansiyel işaretleri TERS çevirilir
    for c in diff_cols:
        df_loss[c] = -df_loss[c]

    final = pd.concat([df_win, df_loss], ignore_index=True)
    
    # Recalculate Logic Flags on the combined dataframe to handle directions correctly
    # Heavy_Favorite: Current TeamA is much better than TeamB
    final["Heavy_Favorite"] = (final["SeedNum_diff"] <= -8).astype(int)
    final["TeamA_Is_Favorite"] = (final["SeedNum_diff"] < 0).astype(int)
    final["TeamA_Is_Underdog"] = (final["SeedNum_diff"] > 0).astype(int)
    
    # Toss_Up: Seeds are very close
    final["Toss_Up"] = (final["SeedNum_diff"].abs() <= 3).astype(int)
    
    # TeamA yonlu seed bayraklari (simetrik veri setinde 0'a kilitlenmemesi icin)
    if "TeamA_SeedNum" in final.columns and "TeamB_SeedNum" in final.columns:
        final["TeamA_Seed_Top4"] = final["TeamA_SeedNum"].between(1, 4).astype(int)
        final["TeamA_Seed_Mid"] = final["TeamA_SeedNum"].between(5, 10).astype(int)
        final["TeamA_Seed_Low"] = (final["TeamA_SeedNum"] >= 11).astype(int)
        final["TeamA_Is_11_12_vs_5_6"] = (
            final["TeamA_SeedNum"].isin([11, 12]) & final["TeamB_SeedNum"].isin([5, 6])
        ).astype(int)
        final["TeamA_Is_5_6_vs_11_12"] = (
            final["TeamA_SeedNum"].isin([5, 6]) & final["TeamB_SeedNum"].isin([11, 12])
        ).astype(int)

    round_ctx = build_round_context_features(
        final[["Season", "DayNum"]],
        gender=gender,
        seed_round_slots_df=seed_round_slots_df,
    )
    for c in round_ctx.columns:
        final[c] = round_ctx[c].values

    final["Split"] = final["Season"].apply(assign_split)

    extra_logic_cols = [
        "Heavy_Favorite",
        "Toss_Up",
        "TeamA_Is_Favorite",
        "TeamA_Is_Underdog",
        "TeamA_Seed_Top4",
        "TeamA_Seed_Mid",
        "TeamA_Seed_Low",
        "TeamA_Is_11_12_vs_5_6",
        "TeamA_Is_5_6_vs_11_12",
        "Round_Num",
        "Is_FirstWeekend",
        "Is_SecondWeekend",
        "Is_FinalWeekend",
    ]
    keep = ["Season","TeamA","TeamB","Target","Split"] + diff_cols + extra_logic_cols
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
    conf_tourney_raw = load(f"{gender}ConferenceTourneyGames.csv")
    seed_round_slots_raw = load(f"{gender}NCAATourneySeedRoundSlots.csv")
    seeds_raw= load(f"{gender}NCAATourneySeeds.csv")
    conf_raw = load(f"{gender}TeamConferences.csv")
    coaches_raw = load(f"{gender}TeamCoaches.csv")
    teams_raw = load(f"{gender}Teams.csv")
    massey   = load("MMasseyOrdinals.csv") if gender == "M" else None

    if compact is None or t_compact is None or seeds_raw is None:
        print(f"  [HATA] {tag} için zorunlu dosyalar eksik. Atlanıyor.")
        return None

    missing_box_cols = get_missing_columns(detailed, REQUIRED_BOXSCORE_COLUMNS)
    has_ff = detailed is not None and not missing_box_cols
    if detailed is None:
        print(f"  [BILGI] Detayli box score yok -> Four Factors atlaniyor.")
    elif not has_ff:
        preview = ", ".join(missing_box_cols[:6])
        suffix = " ..." if len(missing_box_cols) > 6 else ""
        print(f"  [UYARI] Detaylı box score dosyası eksik kolon içeriyor ({preview}{suffix}).")
        print(f"  [BİLGİ] Güvenli fallback: CompactResults kullanılacak, Four Factors atlanacak.")

    # ── Regular season games_long ──────────────────────────
    print("\n[1] Match Long-Format üretiliyor (Home Court Adjustment yapılıyor)...")
    source = detailed if has_ff else compact
    gl = make_games_long(source, has_boxscore=has_ff)
    if has_ff:
        missing_ff_cols = get_missing_columns(gl, REQUIRED_FOUR_FACTOR_COLUMNS)
        if missing_ff_cols:
            preview = ", ".join(missing_ff_cols[:6])
            suffix = " ..." if len(missing_ff_cols) > 6 else ""
            print(f"  [UYARI] Four Factors için games_long kolonları eksik ({preview}{suffix}).")
            print(f"  [BİLGİ] Güvenli fallback: Four Factors kapatıldı, compact-style akışla devam.")
            has_ff = False
        else:
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
    print("[4] Rest days & yorgunluk baglami (DaysSinceLastGame, GamesLast7/14Days, B2B_Last14Days) ekleniyor...")
    rest = build_rest_days(gl)
    rest_snap = (rest[rest["DayNum"] < 134]
                 .sort_values("DayNum")
                 .groupby(["Season","TeamID"])
                 .last()
                 .reset_index()
                 .drop(columns=["DayNum"]))

    # ── Seed features ──────────────────────────────────────
    print("[5] Seed verisi dönüştürülüyor...")
    seed_feats = build_seed_features(seeds_raw)
    
    # ── Conference features ────────────────────────────────
    conf_feats = None
    conf_tourney_feats = None
    if conf_raw is not None:
        print("[6] Konferans strength feature'ları hazırlanıyor...")
    else:
        print("[6] [UYARI] Conference dosyası bulunamadı, konferans feature'ları atlanıyor.")
    if conf_tourney_raw is not None:
        print("[6.1] Konferans turnuvası context feature'ları hazırlanıyor...")
    else:
        print("[6.1] [UYARI] ConferenceTourney dosyası bulunamadı, conference-tourney feature'ları atlanıyor.")
    
    # ── Coach & Program features ───────────────────────────
    coach_feats = None
    program_feats = None
    if coaches_raw is not None:
        print("[7] Coach tenure feature'ları hazırlanıyor...")
    else:
        print("[7] [UYARI] Coach dosyası bulunamadı, coach feature'ları atlanıyor.")
    if teams_raw is not None:
        print("[8] Program age feature'ları hazırlanıyor...")
    else:
        print("[8] [UYARI] Teams dosyası bulunamadı, program-age atlanıyor.")

    # ── Massey features (Sadece Men) ───────────────────────
    massey_feats = None
    if gender == "M" and massey is not None:
        print("[9] Massey Elite Consensus hesaplanıyor (Sadece Men)...")
        massey_feats = build_massey_features(massey)

    # ── Team features birleştir ───────────────────────────
    print("\n[10] Tüm Takım verileri tekilleştiriliyor...")
    min_season = MIN_SEASON_MEN if gender == "M" else MIN_SEASON_WOMEN
    team_feats = season_agg[season_agg["Season"] >= min_season].copy()

    if conf_raw is not None:
        conf_feats = build_conference_features(team_feats, conf_raw, seed_feats)
    if conf_tourney_raw is not None:
        conf_tourney_feats = build_conf_tourney_features(conf_tourney_raw, t_compact, min_season=min_season)
    if coaches_raw is not None:
        coach_feats = build_coach_features(coaches_raw)
    if teams_raw is not None:
        program_feats = build_program_features(team_feats, teams_raw)
    
    team_feats = team_feats.merge(rolling_snap, on=["Season","TeamID"], how="left")
    team_feats = team_feats.merge(rest_snap,    on=["Season","TeamID"], how="left")
    team_feats = team_feats.merge(seed_feats,   on=["Season","TeamID"], how="left")
    if conf_feats is not None and len(conf_feats):
        team_feats = team_feats.merge(conf_feats, on=["Season","TeamID"], how="left")
    if conf_tourney_feats is not None and len(conf_tourney_feats):
        team_feats = team_feats.merge(conf_tourney_feats, on=["Season","TeamID"], how="left")
    if coach_feats is not None and len(coach_feats):
        team_feats = team_feats.merge(coach_feats, on=["Season","TeamID"], how="left")
    if program_feats is not None and len(program_feats):
        team_feats = team_feats.merge(program_feats, on=["Season","TeamID"], how="left")
    
    if massey_feats is not None:
        team_feats = team_feats.merge(massey_feats, on=["Season","TeamID"], how="left")

    seed_mispricing_feats = build_seed_mispricing_features(team_feats, gender=gender)
    if len(seed_mispricing_feats):
        team_feats = team_feats.merge(seed_mispricing_feats, on=["Season", "TeamID"], how="left")
        
    # Kadınlar turnuvasında Box Scorelar 2010'da yayınlanmaya başladı.
    # Four Factors içeren algoritmaların çökmemesi için 2010 öncesi düşürülmelidir.
    if gender == "W" and has_ff:
        prev_len = len(team_feats)
        team_feats = team_feats[team_feats["Season"] >= 2010].copy()
        print(f"    [BİLGİ] Women Data -> 2010 öncesi (FourFactors yoksunluğu sebebiyle) {prev_len - len(team_feats)} satır drop edildi.")
        
    # Gereksiz ve gürültü çıkaran "Games" (Toplam oynanan maç) özelliğini çıkartıyoruz
    team_feats.drop(columns=["Games"], inplace=True, errors="ignore")    

    # Nötr fallback'ler: conference-tourney verisi olmayan takımlar/model satırları için.
    if "ConfTourneyGamesPlayed" in team_feats.columns:
        team_feats["ConfTourneyGamesPlayed"] = team_feats["ConfTourneyGamesPlayed"].fillna(0)
    if "ConfTourneyWinPct" in team_feats.columns:
        team_feats["ConfTourneyWinPct"] = team_feats["ConfTourneyWinPct"].fillna(0.5)
    if "ConfTourneyChampion" in team_feats.columns:
        team_feats["ConfTourneyChampion"] = team_feats["ConfTourneyChampion"].fillna(0).astype(int)
    if "DaysSinceConfFinal" in team_feats.columns:
        median_days = team_feats["DaysSinceConfFinal"].dropna().median()
        if pd.isna(median_days):
            median_days = 7
        team_feats["DaysSinceConfFinal"] = team_feats["DaysSinceConfFinal"].fillna(median_days)
        
    # Eksik verileri doldur
    team_feats.fillna(0, inplace=True)
    print(f"    Team Özellikleri Matrisi: {len(team_feats):,} satır, {len(team_feats.columns)} özellik sütunu hazır.")

    # ── Matchup matrix üret ───────────────────────────────
    print("[11] Matchup (Turnuva) Diferansiyel Matrisi birleştiriliyor...")
    
    # Turnuva verisini de aynı min_season'dan filtrele
    # Aksi halde 1985-2002 maçları join'da null üretir
    t_compact_filtered = t_compact[t_compact["Season"] >= min_season].copy()
    print(f"    Turnuva filtresi: {min_season}+ -> {len(t_compact_filtered)} maç ({len(t_compact)} -> {len(t_compact_filtered)})")
    
    matchup = build_matchup_matrix(
        t_compact_filtered,
        team_feats,
        gender=gender,
        seed_round_slots_df=seed_round_slots_raw,
    )
    print(f"    MODEL MATRISI HAZIR: {len(matchup):,} eğitim verisi, {len(matchup.columns)} sütun.")

    return matchup


# ─────────────────────────────────────────────────────────
# SANITY CHECKS
# ─────────────────────────────────────────────────────────

def sanity_check(df, name):
    print(f"\n{'-'*45}")
    print(f"SANITY CHECK & DATA LEAKAGE: {name}")
    print(f"{'-'*45}")
    print(f"Satır sayısı  : {len(df):,}")
    print(f"Sütun sayısı  : {len(df.columns)}")
    print(f"\nTarget dağılımı (Kusursuz 0.5 olmalı):")
    print(df["Target"].value_counts(normalize=True).round(3))
    print(f"\nTime Split dağılımı (Geleceği tahmin etmeme kuralı):")
    print(df["Split"].value_counts())
    
    null_counts = df.isnull().sum()
    null_counts = null_counts[null_counts > 0]
    if len(null_counts):
        print(f"\n[UYARI] Eksik deger olan sutunlar (incelenmeli):")
        print(null_counts)
    else:
        print(f"\n[OK] Eksik deger yok (kusursuz merge).")
        
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
        print(f"\n[OK] Men's Dataset Kaydedildi -> {out_path}")
        sanity_check(men_df, "Men Features")

    # 2. Women pipeline (Massey yok, 2010 filtrelenmiş)
    women_df = run_pipeline(gender="W")
    if women_df is not None:
        out_path = os.path.join(OUT_DIR, "processed_features_women.csv")
        women_df.to_csv(out_path, index=False)
        print(f"\n[OK] Women's Dataset Kaydedildi -> {out_path}")
        sanity_check(women_df, "Women Features")

    print("\n" + "="*55)
    print("  FEATURE ENGINEERING (AŞAMA 2) BAŞARIYLA TAMAMLANDI.")
    print("  Time Leakage: SIFIR.")
    print("  Kaggle Veri Seti Modellemeye Hazır.")
    print("="*55)
