"""
analiz_sonuclari.txt dosyasındaki hesaplamaları doğrula
"""
import pandas as pd
import numpy as np
import os

print("="*80)
print("ANALİZ SONUÇLARI DOĞRULAMA")
print("="*80)

data_dir = 'march-machine-leraning-mania-2026'

# =============================================================================
# TEST 1: RestDays Ortalama ve Medyan
# =============================================================================
print("\n[TEST 1] RestDays İstatistikleri")
print("-"*80)

# Regular Season verisi
reg_season = pd.read_csv(os.path.join(data_dir, 'MRegularSeasonCompactResults.csv'))

# RestDays hesapla (basit yöntem)
from src.calculate_restdays import calculate_restdays

restdays_df = calculate_restdays(reg_season)

# İlk maçları çıkar (sezon başı)
restdays_df_filtered = restdays_df[restdays_df['PrevDayNum'] > 0]

print(f"Ortalama RestDays: {restdays_df_filtered['RestDays'].mean():.2f} gün")
print(f"Medyan RestDays: {restdays_df_filtered['RestDays'].median():.1f} gün")

# Dosyada yazılan: 3.96 gün ortalama, 3.0 medyan
expected_mean = 3.96
expected_median = 3.0

if abs(restdays_df_filtered['RestDays'].mean() - expected_mean) < 0.1:
    print("✓ Ortalama DOĞRU")
else:
    print(f"✗ Ortalama YANLIŞ (Beklenen: {expected_mean})")

if restdays_df_filtered['RestDays'].median() == expected_median:
    print("✓ Medyan DOĞRU")
else:
    print(f"✗ Medyan YANLIŞ (Beklenen: {expected_median})")

# =============================================================================
# TEST 2: RestDaysDiff → Target
# =============================================================================
print("\n[TEST 2] RestDaysDiff Analizi")
print("-"*80)

# Turnuva verisi
tourney = pd.read_csv(os.path.join(data_dir, 'MNCAATourneyCompactResults.csv'))

# Her takım için son regular season maçını bul
last_reg_games = reg_season.groupby(['Season', 'WTeamID'])['DayNum'].max().reset_index()
last_reg_games.rename(columns={'WTeamID': 'TeamID', 'DayNum': 'LastRegDayNum'}, inplace=True)

last_reg_games_l = reg_season.groupby(['Season', 'LTeamID'])['DayNum'].max().reset_index()
last_reg_games_l.rename(columns={'LTeamID': 'TeamID', 'DayNum': 'LastRegDayNum'}, inplace=True)

# Birleştir
last_reg_games = pd.concat([last_reg_games, last_reg_games_l])
last_reg_games = last_reg_games.groupby(['Season', 'TeamID'])['LastRegDayNum'].max().reset_index()

# Turnuva maçlarına ekle
tourney_with_rest = tourney.merge(
    last_reg_games,
    left_on=['Season', 'WTeamID'],
    right_on=['Season', 'TeamID'],
    how='left'
)
tourney_with_rest.rename(columns={'LastRegDayNum': 'W_LastRegDayNum'}, inplace=True)
tourney_with_rest.drop('TeamID', axis=1, inplace=True)

tourney_with_rest = tourney_with_rest.merge(
    last_reg_games,
    left_on=['Season', 'LTeamID'],
    right_on=['Season', 'TeamID'],
    how='left'
)
tourney_with_rest.rename(columns={'LastRegDayNum': 'L_LastRegDayNum'}, inplace=True)
tourney_with_rest.drop('TeamID', axis=1, inplace=True)

# RestDays hesapla (turnuva DayNum - son regular season DayNum)
tourney_with_rest['W_RestDays'] = tourney_with_rest['DayNum'] - tourney_with_rest['W_LastRegDayNum']
tourney_with_rest['L_RestDays'] = tourney_with_rest['DayNum'] - tourney_with_rest['L_LastRegDayNum']
tourney_with_rest['RestDaysDiff'] = tourney_with_rest['W_RestDays'] - tourney_with_rest['L_RestDays']

# Analiz
total = len(tourney_with_rest)
winner_more_rest = len(tourney_with_rest[tourney_with_rest['RestDaysDiff'] > 0])
equal_rest = len(tourney_with_rest[tourney_with_rest['RestDaysDiff'] == 0])
winner_less_rest = len(tourney_with_rest[tourney_with_rest['RestDaysDiff'] < 0])

print(f"Toplam maç: {total}")
print(f"Kazanan daha fazla dinlenmiş: {winner_more_rest} ({winner_more_rest/total*100:.1f}%)")
print(f"Eşit dinlenme: {equal_rest} ({equal_rest/total*100:.1f}%)")
print(f"Kazanan daha az dinlenmiş: {winner_less_rest} ({winner_less_rest/total*100:.1f}%)")
print(f"Ortalama RestDaysDiff: {tourney_with_rest['RestDaysDiff'].mean():.2f}")

# Dosyada yazılan: 29.1%, 20.9%, 49.9%, -0.86
if abs(winner_more_rest/total*100 - 29.1) < 1:
    print("✓ Yüzdeler DOĞRU")
else:
    print("✗ Yüzdeler YANLIŞ")

if abs(tourney_with_rest['RestDaysDiff'].mean() - (-0.86)) < 0.5:
    print("✓ Ortalama DOĞRU")
else:
    print("✗ Ortalama YANLIŞ")

# =============================================================================
# TEST 3: WScore → LScore Korelasyon
# =============================================================================
print("\n[TEST 3] WScore - LScore Korelasyonu")
print("-"*80)

correlation = tourney['WScore'].corr(tourney['LScore'])
print(f"Korelasyon: {correlation:.2f}")

# Dosyada yazılan: 0.70
if abs(correlation - 0.70) < 0.05:
    print("✓ Korelasyon DOĞRU")
else:
    print("✗ Korelasyon YANLIŞ (Beklenen: 0.70)")

# =============================================================================
# TEST 4: PointDiff Ortalama
# =============================================================================
print("\n[TEST 4] PointDiff Ortalama")
print("-"*80)

tourney['PointDiff'] = tourney['WScore'] - tourney['LScore']
avg_pointdiff = tourney['PointDiff'].mean()
print(f"Ortalama PointDiff: {avg_pointdiff:.1f} sayı")

# Dosyada yazılan: 11.8
if abs(avg_pointdiff - 11.8) < 0.5:
    print("✓ PointDiff DOĞRU")
else:
    print("✗ PointDiff YANLIŞ (Beklenen: 11.8)")

# =============================================================================
# TEST 5: WLoc Dağılımı
# =============================================================================
print("\n[TEST 5] WLoc (Maç Yeri) Dağılımı")
print("-"*80)

print("Regular Season:")
print(reg_season['WLoc'].value_counts())

print("\nTurnuva:")
print(tourney['WLoc'].value_counts())

# Dosyada yazılan: Turnuva hep N
if (tourney['WLoc'] == 'N').all():
    print("✓ Turnuva WLoc DOĞRU (hepsi N)")
else:
    print("✗ Turnuva WLoc YANLIŞ")

# =============================================================================
# TEST 6: NumOT Dağılımı
# =============================================================================
print("\n[TEST 6] NumOT (Uzatma) Dağılımı")
print("-"*80)

print(tourney['NumOT'].value_counts().sort_index())

total_tourney = len(tourney)
no_ot = len(tourney[tourney['NumOT'] == 0])
print(f"\n0 uzatma: {no_ot} maç ({no_ot/total_tourney*100:.0f}%)")

# Dosyada yazılan: %94
if abs(no_ot/total_tourney*100 - 94) < 1:
    print("✓ NumOT DOĞRU")
else:
    print("✗ NumOT YANLIŞ")

# =============================================================================
# TEST 7: SeedDiff ve MasseyRankDiff
# =============================================================================
print("\n[TEST 7] SeedDiff ve MasseyRankDiff")
print("-"*80)

# processed_features.csv'yi oku (eğer varsa)
if os.path.exists('data/processed_features.csv'):
    processed = pd.read_csv('data/processed_features.csv')
    
    # Sadece kazanan takımların verisi (Target=1)
    winners = processed[processed['Target'] == 1]
    
    print(f"Ortalama SeedDiff: {winners['SeedDiff'].mean():.1f}")
    print(f"Ortalama MasseyRankDiff: {winners['MasseyRankDiff'].mean():.1f}")
    
    # Dosyada yazılan: -3.7, -29.9
    if abs(winners['SeedDiff'].mean() - (-3.7)) < 0.5:
        print("✓ SeedDiff DOĞRU")
    else:
        print("✗ SeedDiff YANLIŞ (Beklenen: -3.7)")
    
    if abs(winners['MasseyRankDiff'].mean() - (-29.9)) < 5:
        print("✓ MasseyRankDiff DOĞRU")
    else:
        print("✗ MasseyRankDiff YANLIŞ (Beklenen: -29.9)")
else:
    print("⚠ processed_features.csv bulunamadı, test atlandı")

print("\n" + "="*80)
print("TÜM TESTLER TAMAMLANDI")
print("="*80)
