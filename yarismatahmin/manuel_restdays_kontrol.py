"""
RestDays hesaplamalarını MANUEL olarak kontrol et
Adım adım göster
"""
import pandas as pd
import os

print("="*80)
print("MANUEL RESTDAYS KONTROLÜ")
print("="*80)

data_dir = 'march-machine-leraning-mania-2026'

# =============================================================================
# KONTROL 1: SEASON + DAYNUM → RESTDAYS (Regular Season)
# =============================================================================
print("\n[KONTROL 1] Regular Season RestDays Hesaplama")
print("="*80)

reg_season = pd.read_csv(os.path.join(data_dir, 'MRegularSeasonCompactResults.csv'))

# Örnek takım seç: 1101 (Abilene Chr), 2025 sezonu
team_id = 1101
season = 2025

print(f"\nÖrnek Takım: {team_id}, Sezon: {season}")
print("-"*80)

# Bu takımın tüm maçlarını bul (kazandığı + kaybettiği)
team_wins = reg_season[(reg_season['Season'] == season) & 
                       (reg_season['WTeamID'] == team_id)][['DayNum', 'WTeamID', 'LTeamID']].copy()
team_wins['Result'] = 'W'
team_wins['Opponent'] = team_wins['LTeamID']

team_losses = reg_season[(reg_season['Season'] == season) & 
                         (reg_season['LTeamID'] == team_id)][['DayNum', 'WTeamID', 'LTeamID']].copy()
team_losses['Result'] = 'L'
team_losses['Opponent'] = team_losses['WTeamID']

# Birleştir ve sırala
team_games = pd.concat([
    team_wins[['DayNum', 'Result', 'Opponent']],
    team_losses[['DayNum', 'Result', 'Opponent']]
]).sort_values('DayNum').reset_index(drop=True)

print("\nTakımın Maçları:")
print(f"{'Maç #':<8} {'DayNum':<10} {'Result':<8} {'Opponent':<10} {'RestDays':<12} {'Manuel Hesap'}")
print("-"*80)

prev_daynum = None
for idx, row in team_games.head(10).iterrows():
    daynum = row['DayNum']
    result = row['Result']
    opponent = row['Opponent']
    
    if prev_daynum is None:
        # İlk maç
        restdays = daynum  # Sezon başından beri
        manual = f"{daynum} - 0 = {daynum}"
    else:
        # Sonraki maçlar
        restdays = daynum - prev_daynum
        manual = f"{daynum} - {prev_daynum} = {restdays}"
    
    print(f"{idx+1:<8} {daynum:<10} {result:<8} {opponent:<10} {restdays:<12} {manual}")
    
    prev_daynum = daynum

# Tüm takımlar için ortalama hesapla
print("\n" + "="*80)
print("TÜM TAKIMLAR İÇİN ORTALAMA RESTDAYS")
print("="*80)

all_restdays = []

# Her takım için RestDays hesapla
for team in reg_season['WTeamID'].unique():
    # Takımın tüm maçları
    team_w = reg_season[reg_season['WTeamID'] == team][['Season', 'DayNum']].copy()
    team_l = reg_season[reg_season['LTeamID'] == team][['Season', 'DayNum']].copy()
    
    team_all = pd.concat([team_w, team_l]).sort_values(['Season', 'DayNum'])
    
    # Her sezon için ayrı hesapla
    for s in team_all['Season'].unique():
        season_games = team_all[team_all['Season'] == s]['DayNum'].values
        
        for i in range(1, len(season_games)):
            restdays = season_games[i] - season_games[i-1]
            all_restdays.append(restdays)

all_restdays = pd.Series(all_restdays)

print(f"\nToplam RestDays hesaplama sayısı: {len(all_restdays):,}")
print(f"Ortalama RestDays: {all_restdays.mean():.2f} gün")
print(f"Medyan RestDays: {all_restdays.median():.1f} gün")
print(f"Min RestDays: {all_restdays.min():.0f} gün")
print(f"Max RestDays: {all_restdays.max():.0f} gün")

print("\nDosyada yazılan: Ortalama 3.96 gün, Medyan 3.0 gün")
if abs(all_restdays.mean() - 3.96) < 0.1:
    print("✓ ORTALAMA DOĞRU")
else:
    print(f"✗ ORTALAMA YANLIŞ (Hesaplanan: {all_restdays.mean():.2f})")

if all_restdays.median() == 3.0:
    print("✓ MEDYAN DOĞRU")
else:
    print(f"✗ MEDYAN YANLIŞ (Hesaplanan: {all_restdays.median():.1f})")

# =============================================================================
# KONTROL 2: RESTDAYSDIFF → TARGET (Turnuva)
# =============================================================================
print("\n\n[KONTROL 2] Turnuva RestDaysDiff Hesaplama")
print("="*80)

tourney = pd.read_csv(os.path.join(data_dir, 'MNCAATourneyCompactResults.csv'))

print("\nHesaplama Mantığı:")
print("1. Her takımın son regular season maçını bul")
print("2. Turnuva maçı DayNum - Son regular season DayNum = RestDays")
print("3. RestDaysDiff = Kazanan RestDays - Kaybeden RestDays")

# Her takım için son regular season maçını bul
print("\n" + "-"*80)
print("Adım 1: Son Regular Season Maçları")
print("-"*80)

# Kazanan takımlar için
last_reg_w = reg_season.groupby(['Season', 'WTeamID'])['DayNum'].max().reset_index()
last_reg_w.rename(columns={'WTeamID': 'TeamID', 'DayNum': 'LastRegDay'}, inplace=True)

# Kaybeden takımlar için
last_reg_l = reg_season.groupby(['Season', 'LTeamID'])['DayNum'].max().reset_index()
last_reg_l.rename(columns={'LTeamID': 'TeamID', 'DayNum': 'LastRegDay'}, inplace=True)

# Birleştir (her takım için en son maç)
last_reg = pd.concat([last_reg_w, last_reg_l])
last_reg = last_reg.groupby(['Season', 'TeamID'])['LastRegDay'].max().reset_index()

print(f"Toplam takım-sezon kombinasyonu: {len(last_reg)}")
print("\nÖrnek (ilk 5):")
print(last_reg.head())

# Turnuva maçlarına ekle
print("\n" + "-"*80)
print("Adım 2: Turnuva Maçlarına RestDays Ekle")
print("-"*80)

tourney_rest = tourney.copy()

# Kazanan takım için
tourney_rest = tourney_rest.merge(
    last_reg,
    left_on=['Season', 'WTeamID'],
    right_on=['Season', 'TeamID'],
    how='left'
)
tourney_rest.rename(columns={'LastRegDay': 'W_LastRegDay'}, inplace=True)
tourney_rest.drop('TeamID', axis=1, inplace=True)

# Kaybeden takım için
tourney_rest = tourney_rest.merge(
    last_reg,
    left_on=['Season', 'LTeamID'],
    right_on=['Season', 'TeamID'],
    how='left'
)
tourney_rest.rename(columns={'LastRegDay': 'L_LastRegDay'}, inplace=True)
tourney_rest.drop('TeamID', axis=1, inplace=True)

# RestDays hesapla
tourney_rest['W_RestDays'] = tourney_rest['DayNum'] - tourney_rest['W_LastRegDay']
tourney_rest['L_RestDays'] = tourney_rest['DayNum'] - tourney_rest['L_LastRegDay']
tourney_rest['RestDaysDiff'] = tourney_rest['W_RestDays'] - tourney_rest['L_RestDays']

print("\nÖrnek Maçlar (ilk 5):")
print(tourney_rest[['Season', 'DayNum', 'WTeamID', 'W_LastRegDay', 'W_RestDays', 
                    'LTeamID', 'L_LastRegDay', 'L_RestDays', 'RestDaysDiff']].head())

# Manuel hesaplama örneği
print("\n" + "-"*80)
print("Manuel Hesaplama Örneği (İlk Maç)")
print("-"*80)

first_game = tourney_rest.iloc[0]
print(f"Sezon: {first_game['Season']}")
print(f"Turnuva DayNum: {first_game['DayNum']}")
print(f"\nKazanan Takım: {first_game['WTeamID']}")
print(f"  Son Regular Season Maçı: DayNum {first_game['W_LastRegDay']}")
print(f"  RestDays = {first_game['DayNum']} - {first_game['W_LastRegDay']} = {first_game['W_RestDays']}")
print(f"\nKaybeden Takım: {first_game['LTeamID']}")
print(f"  Son Regular Season Maçı: DayNum {first_game['L_LastRegDay']}")
print(f"  RestDays = {first_game['DayNum']} - {first_game['L_LastRegDay']} = {first_game['L_RestDays']}")
print(f"\nRestDaysDiff = {first_game['W_RestDays']} - {first_game['L_RestDays']} = {first_game['RestDaysDiff']}")

# Analiz
print("\n" + "="*80)
print("RESTDAYSDIFF ANALİZİ")
print("="*80)

total = len(tourney_rest)
winner_more = len(tourney_rest[tourney_rest['RestDaysDiff'] > 0])
equal = len(tourney_rest[tourney_rest['RestDaysDiff'] == 0])
winner_less = len(tourney_rest[tourney_rest['RestDaysDiff'] < 0])

print(f"\nToplam maç: {total}")
print(f"\nKazanan daha fazla dinlenmiş (RestDaysDiff > 0): {winner_more} ({winner_more/total*100:.1f}%)")
print(f"Eşit dinlenme (RestDaysDiff = 0): {equal} ({equal/total*100:.1f}%)")
print(f"Kazanan daha az dinlenmiş (RestDaysDiff < 0): {winner_less} ({winner_less/total*100:.1f}%)")
print(f"\nOrtalama RestDaysDiff: {tourney_rest['RestDaysDiff'].mean():.2f}")

print("\n" + "-"*80)
print("Dosyada yazılan:")
print("  - Kazanan daha fazla: 753 (29.1%)")
print("  - Eşit: 541 (20.9%)")
print("  - Kazanan daha az: 1291 (49.9%)")
print("  - Ortalama: -0.86")
print("-"*80)

if winner_more == 753:
    print("✓ KAZANAN DAHA FAZLA DİNLENMİŞ SAYISI DOĞRU")
else:
    print(f"✗ YANLIŞ (Hesaplanan: {winner_more})")

if equal == 541:
    print("✓ EŞİT DİNLENME SAYISI DOĞRU")
else:
    print(f"✗ YANLIŞ (Hesaplanan: {equal})")

if winner_less == 1291:
    print("✓ KAZANAN DAHA AZ DİNLENMİŞ SAYISI DOĞRU")
else:
    print(f"✗ YANLIŞ (Hesaplanan: {winner_less})")

if abs(tourney_rest['RestDaysDiff'].mean() - (-0.86)) < 0.01:
    print("✓ ORTALAMA DOĞRU")
else:
    print(f"✗ YANLIŞ (Hesaplanan: {tourney_rest['RestDaysDiff'].mean():.2f})")

print("\n" + "="*80)
print("MANUEL KONTROL TAMAMLANDI")
print("="*80)
