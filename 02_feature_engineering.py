import pandas as pd
import numpy as np
import os
import glob

print("Feature Engineering basliyor...")

data_dir = 'march-machine-leraning-mania-2026'

# 1. Hedef (Tourney Results) Verisi
tourney_results = pd.read_csv(os.path.join(data_dir, 'MNCAATourneyCompactResults.csv'))

# 2. Regular Season Stats (WinPct, PointDiff)
reg_season = pd.read_csv(os.path.join(data_dir, 'MRegularSeasonCompactResults.csv'))

# Kazanan takim istatistikleri
win_stats = reg_season.groupby(['Season', 'WTeamID']).agg(
    Wins=('WTeamID', 'count'),
    PointsScored=('WScore', 'sum'),
    PointsAllowed=('LScore', 'sum')
).reset_index().rename(columns={'WTeamID': 'TeamID'})

# Kaybeden takim istatistikleri
loss_stats = reg_season.groupby(['Season', 'LTeamID']).agg(
    Losses=('LTeamID', 'count'),
    PointsScored=('LScore', 'sum'),
    PointsAllowed=('WScore', 'sum')
).reset_index().rename(columns={'LTeamID': 'TeamID'})

# Birlestir
season_stats = pd.merge(win_stats, loss_stats, on=['Season', 'TeamID'], how='outer').fillna(0)
season_stats['Games'] = season_stats['Wins'] + season_stats['Losses']
season_stats['WinPct'] = season_stats['Wins'] / season_stats['Games']
season_stats['TotalPointsScored'] = season_stats['PointsScored_x'] + season_stats['PointsScored_y']
season_stats['TotalPointsAllowed'] = season_stats['PointsAllowed_x'] + season_stats['PointsAllowed_y']
season_stats['PointDiff'] = (season_stats['TotalPointsScored'] - season_stats['TotalPointsAllowed']) / season_stats['Games']

season_stats = season_stats[['Season', 'TeamID', 'WinPct', 'PointDiff']]

# 3. Massey Ordinals (Sadece DayNum=133, yani turnuva oncesi son siralamalar)
massey = pd.read_csv(os.path.join(data_dir, 'MMasseyOrdinals.csv'))
massey_133 = massey[massey['RankingDayNum'] == 133].copy()
avg_ranks = massey_133.groupby(['Season', 'TeamID'])['OrdinalRank'].mean().reset_index()
avg_ranks.rename(columns={'OrdinalRank': 'MasseyRank'}, inplace=True)

# 4. Seeds
seeds = pd.read_csv(os.path.join(data_dir, 'MNCAATourneySeeds.csv'))
# Seed'deki harfleri temizleme (Orn: 'W01' -> 1, 'X16a' -> 16)
seeds['SeedNum'] = seeds['Seed'].apply(lambda x: int(x[1:3]))
seeds = seeds[['Season', 'TeamID', 'SeedNum']]

print("Ara tablolar hazirlandi. Birlestirme islemi basliyor...")

# 5. Tourney Verisine Join
df = tourney_results[['Season', 'DayNum', 'WTeamID', 'LTeamID']].copy()

# Kazanan Takim Bilgileri (WTeam)
df = df.merge(season_stats, left_on=['Season', 'WTeamID'], right_on=['Season', 'TeamID'], how='left')
df.rename(columns={'WinPct': 'W_WinPct', 'PointDiff': 'W_PointDiff'}, inplace=True)
df.drop('TeamID', axis=1, inplace=True)

df = df.merge(avg_ranks, left_on=['Season', 'WTeamID'], right_on=['Season', 'TeamID'], how='left')
df.rename(columns={'MasseyRank': 'W_MasseyRank'}, inplace=True)
df.drop('TeamID', axis=1, inplace=True)

df = df.merge(seeds, left_on=['Season', 'WTeamID'], right_on=['Season', 'TeamID'], how='left')
df.rename(columns={'SeedNum': 'W_SeedNum'}, inplace=True)
df.drop('TeamID', axis=1, inplace=True)

# Kaybeden Takim Bilgileri (LTeam)
df = df.merge(season_stats, left_on=['Season', 'LTeamID'], right_on=['Season', 'TeamID'], how='left')
df.rename(columns={'WinPct': 'L_WinPct', 'PointDiff': 'L_PointDiff'}, inplace=True)
df.drop('TeamID', axis=1, inplace=True)

df = df.merge(avg_ranks, left_on=['Season', 'LTeamID'], right_on=['Season', 'TeamID'], how='left')
df.rename(columns={'MasseyRank': 'L_MasseyRank'}, inplace=True)
df.drop('TeamID', axis=1, inplace=True)

df = df.merge(seeds, left_on=['Season', 'LTeamID'], right_on=['Season', 'TeamID'], how='left')
df.rename(columns={'SeedNum': 'L_SeedNum'}, inplace=True)
df.drop('TeamID', axis=1, inplace=True)

# Sadece Massey rank'leri 2003'te basliyor. 2003 oncesine 50 (ortalama siralama) gibi bir deger atanabilir 
# veya drop edilebilir. Kaggle projelerinde yaygin olarak max rank veya median rank ile doldurulur.
median_rank = df['W_MasseyRank'].median()
df['W_MasseyRank'] = df['W_MasseyRank'].fillna(median_rank)
df['L_MasseyRank'] = df['L_MasseyRank'].fillna(median_rank)

# Diff Feature'larinin Hesaplanmasi
df['SeedDiff'] = df['W_SeedNum'] - df['L_SeedNum']
df['MasseyRankDiff'] = df['W_MasseyRank'] - df['L_MasseyRank']
df['WinPctDiff'] = df['W_WinPct'] - df['L_WinPct']
df['PointDiffDiff'] = df['W_PointDiff'] - df['L_PointDiff']

# DataFrame'in ilk yarisini Winner odakli, ikinci yarisini Loser odakli yapalim ki hedef degisken hep 1 olmasin
df_win = df.copy()
df_win['Target'] = 1
df_win['TeamA'] = df_win['WTeamID']
df_win['TeamB'] = df_win['LTeamID']
# Kazanan takim TeamA oldugu icin Diff'ler (W - L) ayni kaliyor.

df_loss = df.copy()
df_loss['Target'] = 0
df_loss['TeamA'] = df_loss['LTeamID']
df_loss['TeamB'] = df_loss['WTeamID']
# Kaybeden takim TeamA oldugu icin Diff'ler isaret degistirmeli (L - W)
df_loss['SeedDiff'] = -df_loss['SeedDiff']
df_loss['MasseyRankDiff'] = -df_loss['MasseyRankDiff']
df_loss['WinPctDiff'] = -df_loss['WinPctDiff']
df_loss['PointDiffDiff'] = -df_loss['PointDiffDiff']

# Birlestir
final_df = pd.concat([df_win, df_loss], ignore_index=True)

# Model egitimine girecek ana sutunlari secelim
features = ['Season', 'TeamA', 'TeamB', 'SeedDiff', 'MasseyRankDiff', 'WinPctDiff', 'PointDiffDiff', 'Target']
final_df = final_df[features]

# Karistirma (Shuffle)
final_df = final_df.sample(frac=1.0, random_state=42).reset_index(drop=True)

# Split sutunu (Train, Val, Test) ayarlama
def set_split(season):
    if season in [2016, 2017, 2018, 2019, 2021, 2022]:
        return 'Train'
    elif season == 2023:
        return 'Val'
    elif season in [2024, 2025]:
        return 'Test'
    else:
        return 'History' # Egitimde kullanilabilir veya dislanabilir, model performansina gore bakilir

final_df['Split'] = final_df['Season'].apply(set_split)

# Diske kaydet
os.makedirs('data', exist_ok=True)
final_df.to_csv('data/processed_features.csv', index=False)

print("Tamamlandi! processed_features.csv kaydedildi.")

# Sanity Check & Leakage Controllari
print("\n--- SANITY CHECKS ---")
print(f"Toplam Veri Sayisi: {len(final_df)} (Turnuva Mac Sayisinin 2 Kati: {len(tourney_results)*2})")
print("\nHedef Dagilimi:")
print(final_df['Target'].value_counts(normalize=True))

print("\nEksik Veri Durumu:")
print(final_df.isnull().sum())

print("\nSplit Dagilimi:")
print(final_df['Split'].value_counts())

print("\nKorelasyonlar:")
print(final_df[['Target', 'SeedDiff', 'MasseyRankDiff', 'WinPctDiff', 'PointDiffDiff']].corr()['Target'])

