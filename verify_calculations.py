"""
Hesaplamaların doğruluğunu kontrol et
"""
import pandas as pd
import os

print("="*80)
print("HESAPLAMA DOĞRULAMA")
print("="*80)

data_dir = 'march-machine-leraning-mania-2026'

# =============================================================================
# TEST 1: Sezon Uzunluğu Doğrulaması
# =============================================================================
print("\n[TEST 1] Sezon Uzunluğu Kontrolü")
print("-"*80)

seasons = pd.read_csv(os.path.join(data_dir, 'MSeasons.csv'))
seasons['DayZero'] = pd.to_datetime(seasons['DayZero'])

# Manuel hesaplama: 2023 ve 2024 arası
season_2023 = seasons[seasons['Season'] == 2023]['DayZero'].values[0]
season_2024 = seasons[seasons['Season'] == 2024]['DayZero'].values[0]

diff = pd.to_datetime(season_2024) - pd.to_datetime(season_2023)
print(f"2023 başlangıç: {season_2023}")
print(f"2024 başlangıç: {season_2024}")
print(f"Fark (manuel): {diff.days} gün")

# Dosyadan oku
season_features = pd.read_csv('data/season_features.csv')
calculated = season_features[season_features['Season'] == 2023]['SeasonLength'].values[0]
print(f"Fark (hesaplanan): {calculated} gün")

if diff.days == calculated:
    print("✓ Sezon uzunluğu hesaplaması DOĞRU")
else:
    print("✗ Sezon uzunluğu hesaplaması YANLIŞ")

# =============================================================================
# TEST 2: Bölge Gücü Doğrulaması
# =============================================================================
print("\n[TEST 2] Bölge Gücü Kontrolü (2025 Sezonu)")
print("-"*80)

# Turnuva sonuçlarını yükle
tourney = pd.read_csv(os.path.join(data_dir, 'MNCAATourneyCompactResults.csv'))
seeds = pd.read_csv(os.path.join(data_dir, 'MNCAATourneySeeds.csv'))
seeds['Region'] = seeds['Seed'].str[0]

# 2025 sezonu için manuel hesaplama
tourney_2025 = tourney[tourney['Season'] == 2025]
print(f"2025 sezonunda toplam maç: {len(tourney_2025)}")

# Kazanan takımların bölgelerini bul
winners_2025 = tourney_2025.merge(
    seeds[['Season', 'TeamID', 'Region']],
    left_on=['Season', 'WTeamID'],
    right_on=['Season', 'TeamID'],
    how='left'
)

# Kaybeden takımların bölgelerini bul
losers_2025 = tourney_2025.merge(
    seeds[['Season', 'TeamID', 'Region']],
    left_on=['Season', 'LTeamID'],
    right_on=['Season', 'TeamID'],
    how='left'
)

print("\nKazanan bölge dağılımı:")
print(winners_2025['Region'].value_counts().sort_index())

print("\nKaybeden bölge dağılımı:")
print(losers_2025['Region'].value_counts().sort_index())

# Dosyadan oku
region_strength = pd.read_csv('data/region_strength.csv')
region_2025 = region_strength[region_strength['Season'] == 2025]

print("\nHesaplanan bölge istatistikleri:")
print(region_2025[['Region', 'Wins', 'Losses', 'WinRate']].to_string(index=False))

# Manuel doğrulama: Z bölgesi
z_wins_manual = winners_2025['Region'].value_counts().get('Z', 0)
z_losses_manual = losers_2025['Region'].value_counts().get('Z', 0)
z_winrate_manual = z_wins_manual / (z_wins_manual + z_losses_manual)

z_wins_calc = region_2025[region_2025['Region'] == 'Z']['Wins'].values[0]
z_winrate_calc = region_2025[region_2025['Region'] == 'Z']['WinRate'].values[0]

print(f"\nZ Bölgesi Manuel: {z_wins_manual} kazanma, WinRate: {z_winrate_manual:.4f}")
print(f"Z Bölgesi Hesaplanan: {z_wins_calc} kazanma, WinRate: {z_winrate_calc:.4f}")

if abs(z_winrate_manual - z_winrate_calc) < 0.0001:
    print("✓ Bölge gücü hesaplaması DOĞRU")
else:
    print("✗ Bölge gücü hesaplaması YANLIŞ")

# =============================================================================
# TEST 3: Seeds Dosyası Doğrulaması
# =============================================================================
print("\n[TEST 3] Seeds Dosyası Kontrolü")
print("-"*80)

seeds_with_region = pd.read_csv('data/seeds_with_region.csv')

# Orijinal seeds dosyası ile karşılaştır
original_seeds = pd.read_csv(os.path.join(data_dir, 'MNCAATourneySeeds.csv'))

print(f"Orijinal seeds kayıt sayısı: {len(original_seeds)}")
print(f"İşlenmiş seeds kayıt sayısı: {len(seeds_with_region)}")

if len(original_seeds) == len(seeds_with_region):
    print("✓ Kayıt sayısı eşleşiyor")
else:
    print("✗ Kayıt sayısı eşleşmiyor")

# Rastgele bir takımı kontrol et
sample = seeds_with_region.sample(1)
season = sample['Season'].values[0]
team_id = sample['TeamID'].values[0]
region = sample['Region'].values[0]
seed_num = sample['SeedNum'].values[0]

original_seed = original_seeds[(original_seeds['Season'] == season) & 
                               (original_seeds['TeamID'] == team_id)]['Seed'].values[0]

print(f"\nRastgele örnek:")
print(f"Season: {season}, TeamID: {team_id}")
print(f"Orijinal Seed: {original_seed}")
print(f"Çıkarılan Region: {region}, SeedNum: {seed_num}")
print(f"Beklenen: Region={original_seed[0]}, SeedNum={int(original_seed[1:3])}")

if original_seed[0] == region and int(original_seed[1:3]) == seed_num:
    print("✓ Seed parsing DOĞRU")
else:
    print("✗ Seed parsing YANLIŞ")

# =============================================================================
# TEST 4: Genel İstatistikler
# =============================================================================
print("\n[TEST 4] Genel İstatistikler")
print("-"*80)

print("\nSezon uzunluğu dağılımı:")
print(season_features['SeasonLength'].value_counts().sort_index())

print("\nToplam bölge kazanma oranları (tüm sezonlar):")
total_by_region = region_strength.groupby('Region').agg({
    'Wins': 'sum',
    'Losses': 'sum'
})
total_by_region['TotalGames'] = total_by_region['Wins'] + total_by_region['Losses']
total_by_region['WinRate'] = total_by_region['Wins'] / total_by_region['TotalGames']
print(total_by_region.sort_values('WinRate', ascending=False))

print("\n" + "="*80)
print("TÜM TESTLER TAMAMLANDI")
print("="*80)
