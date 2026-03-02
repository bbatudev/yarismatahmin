"""
Season Features Analizi
Bu script MSeasons.csv dosyasından feature'lar çıkarır ve korelasyon analizi yapar.
"""

import pandas as pd
import numpy as np
import os

print("="*80)
print("SEASON FEATURES ANALİZİ BAŞLIYOR")
print("="*80)

data_dir = 'march-machine-leraning-mania-2026'

# =============================================================================
# ADIM 1: MSeasons.csv Dosyasını Yükle ve İncele
# =============================================================================
print("\n[ADIM 1] MSeasons.csv dosyası yükleniyor...")

seasons = pd.read_csv(os.path.join(data_dir, 'MSeasons.csv'))

print("\n--- Dosya Boyutu ---")
print(f"Toplam sezon sayısı: {len(seasons)}")
print(f"Sütunlar: {list(seasons.columns)}")

print("\n--- İlk 5 Satır ---")
print(seasons.head())

print("\n--- Son 5 Satır ---")
print(seasons.tail())

print("\n--- Veri Tipleri ---")
print(seasons.dtypes)

print("\n--- Eksik Veri Kontrolü ---")
print(seasons.isnull().sum())

# =============================================================================
# ADIM 2: Sezon Uzunluğu Hesaplama
# =============================================================================
print("\n" + "="*80)
print("[ADIM 2] Sezon Uzunluğu Hesaplanıyor...")
print("="*80)

# DayZero'yu datetime formatına çevir
seasons['DayZero'] = pd.to_datetime(seasons['DayZero'])

print("\n--- DayZero Datetime'a Çevrildi ---")
print(seasons[['Season', 'DayZero']].head())

# Bir sonraki sezonun başlangıcına kadar olan gün sayısını hesapla
seasons['NextSeasonStart'] = seasons['DayZero'].shift(-1)
seasons['SeasonLength'] = (seasons['NextSeasonStart'] - seasons['DayZero']).dt.days

print("\n--- Sezon Uzunluğu Hesaplandı ---")
print(seasons[['Season', 'DayZero', 'NextSeasonStart', 'SeasonLength']].head(10))

print("\n--- Sezon Uzunluğu İstatistikleri ---")
print(f"Ortalama sezon uzunluğu: {seasons['SeasonLength'].mean():.1f} gün")
print(f"En kısa sezon: {seasons['SeasonLength'].min():.0f} gün")
print(f"En uzun sezon: {seasons['SeasonLength'].max():.0f} gün")
print(f"Standart sapma: {seasons['SeasonLength'].std():.1f} gün")

# Son sezon için uzunluk yok (çünkü bir sonraki sezon henüz başlamadı)
print(f"\nNot: {seasons[seasons['SeasonLength'].isnull()]['Season'].values} sezonu için uzunluk hesaplanamadı (henüz bitmedi)")

# =============================================================================
# ADIM 3: Bölge Bilgilerini İncele
# =============================================================================
print("\n" + "="*80)
print("[ADIM 3] Bölge Bilgileri İnceleniyor...")
print("="*80)

print("\n--- Bölge Sütunları ---")
print(seasons[['Season', 'RegionW', 'RegionX', 'RegionY', 'RegionZ']].head(10))

# Hangi bölgeler var?
all_regions = pd.concat([
    seasons['RegionW'],
    seasons['RegionX'],
    seasons['RegionY'],
    seasons['RegionZ']
])

print("\n--- Tüm Bölgeler (Benzersiz) ---")
print(all_regions.unique())

print("\n--- Bölge Dağılımı ---")
print(all_regions.value_counts())

# =============================================================================
# ADIM 4: Turnuva Seeds Dosyasını Yükle (Bölge Bilgisi İçin)
# =============================================================================
print("\n" + "="*80)
print("[ADIM 4] Turnuva Seeds Dosyası Yükleniyor...")
print("="*80)

seeds = pd.read_csv(os.path.join(data_dir, 'MNCAATourneySeeds.csv'))

print("\n--- Seeds Dosyası Boyutu ---")
print(f"Toplam kayıt: {len(seeds)}")
print(f"Sütunlar: {list(seeds.columns)}")

print("\n--- İlk 10 Satır ---")
print(seeds.head(10))

# Seed formatı: W01, X16, Y08 gibi
# İlk harf = Bölge (W/X/Y/Z veya East/West/Midwest/South kısaltması)
# Sonraki sayılar = Seed numarası

print("\n--- Seed Formatı Analizi ---")
seeds['Region'] = seeds['Seed'].str[0]  # İlk harfi al
seeds['SeedNum'] = seeds['Seed'].str[1:3].astype(int)  # 2. ve 3. karakteri al

print(seeds[['Season', 'TeamID', 'Seed', 'Region', 'SeedNum']].head(10))

print("\n--- Bölge Dağılımı (Seeds'den) ---")
print(seeds['Region'].value_counts())

print("\n--- Seed Numarası Dağılımı ---")
print(seeds['SeedNum'].value_counts().sort_index())

# =============================================================================
# ADIM 5: Turnuva Sonuçlarını Yükle
# =============================================================================
print("\n" + "="*80)
print("[ADIM 5] Turnuva Sonuçları Yükleniyor...")
print("="*80)

tourney = pd.read_csv(os.path.join(data_dir, 'MNCAATourneyCompactResults.csv'))

print("\n--- Turnuva Sonuçları Boyutu ---")
print(f"Toplam maç: {len(tourney)}")
print(f"Sütunlar: {list(tourney.columns)}")

print("\n--- İlk 10 Maç ---")
print(tourney.head(10))

print("\n--- Sezon Bazında Maç Sayıları ---")
print(tourney['Season'].value_counts().sort_index().tail(10))

# =============================================================================
# ADIM 6: Bölge Gücü Hesaplama
# =============================================================================
print("\n" + "="*80)
print("[ADIM 6] Bölge Gücü Hesaplanıyor...")
print("="*80)

# Kazanan takımların bölgelerini bul
tourney_with_regions = tourney.merge(
    seeds[['Season', 'TeamID', 'Region', 'SeedNum']],
    left_on=['Season', 'WTeamID'],
    right_on=['Season', 'TeamID'],
    how='left'
)
tourney_with_regions.rename(columns={'Region': 'W_Region', 'SeedNum': 'W_SeedNum'}, inplace=True)
tourney_with_regions.drop('TeamID', axis=1, inplace=True)

# Kaybeden takımların bölgelerini bul
tourney_with_regions = tourney_with_regions.merge(
    seeds[['Season', 'TeamID', 'Region', 'SeedNum']],
    left_on=['Season', 'LTeamID'],
    right_on=['Season', 'TeamID'],
    how='left'
)
tourney_with_regions.rename(columns={'Region': 'L_Region', 'SeedNum': 'L_SeedNum'}, inplace=True)
tourney_with_regions.drop('TeamID', axis=1, inplace=True)

print("\n--- Bölge Bilgileri Eklendi ---")
print(tourney_with_regions[['Season', 'WTeamID', 'W_Region', 'W_SeedNum', 'LTeamID', 'L_Region', 'L_SeedNum']].head(10))

# Her bölgenin kazanma oranını hesapla
print("\n--- Bölge Bazında Kazanma İstatistikleri ---")

# Toplam maç sayısı (her bölgeden)
region_stats = pd.DataFrame()

# Kazanan bölge sayıları
wins_by_region = tourney_with_regions['W_Region'].value_counts()
# Kaybeden bölge sayıları
losses_by_region = tourney_with_regions['L_Region'].value_counts()

region_stats['Wins'] = wins_by_region
region_stats['Losses'] = losses_by_region
region_stats['TotalGames'] = region_stats['Wins'] + region_stats['Losses']
region_stats['WinRate'] = region_stats['Wins'] / region_stats['TotalGames']

print(region_stats.sort_values('WinRate', ascending=False))

# =============================================================================
# ADIM 7: Sezon Bazında Bölge Gücü
# =============================================================================
print("\n" + "="*80)
print("[ADIM 7] Sezon Bazında Bölge Gücü Hesaplanıyor...")
print("="*80)

# Her sezon için her bölgenin kazanma oranı
season_region_stats = tourney_with_regions.groupby(['Season', 'W_Region']).size().reset_index(name='Wins')
season_region_losses = tourney_with_regions.groupby(['Season', 'L_Region']).size().reset_index(name='Losses')

season_region_stats = season_region_stats.merge(
    season_region_losses,
    left_on=['Season', 'W_Region'],
    right_on=['Season', 'L_Region'],
    how='outer'
).fillna(0)

# Sütun isimlerini düzelt
season_region_stats['Region'] = season_region_stats['W_Region'].fillna(season_region_stats['L_Region'])
season_region_stats['TotalGames'] = season_region_stats['Wins'] + season_region_stats['Losses']
season_region_stats['WinRate'] = season_region_stats['Wins'] / season_region_stats['TotalGames']

season_region_stats = season_region_stats[['Season', 'Region', 'Wins', 'Losses', 'TotalGames', 'WinRate']]

print("\n--- Son 3 Sezon İçin Bölge İstatistikleri ---")
print(season_region_stats[season_region_stats['Season'].isin([2023, 2024, 2025])].sort_values(['Season', 'WinRate'], ascending=[False, False]))

# =============================================================================
# ADIM 8: Özet ve Kaydetme
# =============================================================================
print("\n" + "="*80)
print("[ADIM 8] Sonuçlar Kaydediliyor...")
print("="*80)

# Sezon feature'larını kaydet
seasons_final = seasons[['Season', 'SeasonLength']].copy()
seasons_final.to_csv('data/season_features.csv', index=False)
print("\n✓ data/season_features.csv kaydedildi")

# Bölge istatistiklerini kaydet
season_region_stats.to_csv('data/region_strength.csv', index=False)
print("✓ data/region_strength.csv kaydedildi")

# Seeds + Region bilgisini kaydet
seeds_final = seeds[['Season', 'TeamID', 'Region', 'SeedNum']].copy()
seeds_final.to_csv('data/seeds_with_region.csv', index=False)
print("✓ data/seeds_with_region.csv kaydedildi")

print("\n" + "="*80)
print("ANALİZ TAMAMLANDI!")
print("="*80)
print("\nOluşturulan dosyalar:")
print("1. data/season_features.csv - Sezon uzunluğu bilgileri")
print("2. data/region_strength.csv - Bölge gücü istatistikleri")
print("3. data/seeds_with_region.csv - Takım seed ve bölge bilgileri")
