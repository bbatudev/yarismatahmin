# Season Features (MSeasons.csv)

## Mevcut Değişkenler
- Season: Yıl
- DayZero: Sezon başlangıç tarihi
- RegionW, RegionX, RegionY, RegionZ: Turnuva bölgeleri

## Türetilebilecek Feature'lar

### 1. Sezon Uzunluğu
- DayZero'dan bir sonraki sezonun DayZero'suna kadar gün sayısı
- Kısa sezon = daha az maç = daha az veri?

### 2. Bölge Gücü
- Hangi bölgeden çıkan takımlar daha başarılı?
- RegionW/X/Y/Z bazında kazanma oranları
- Bölge bazında ortalama seed performansı

### 3. Sezon Başlangıç Tarihi Etkisi
- Erken başlayan sezonlar vs geç başlayan
- Tatil dönemleri etkisi?

## Nasıl Hesaplayacağız?

### Adım 1: Sezon Uzunluğu Hesaplama
```python
# MSeasons.csv'yi oku
seasons = pd.read_csv('MSeasons.csv')

# DayZero'yu datetime'a çevir
seasons['DayZero'] = pd.to_datetime(seasons['DayZero'])

# Bir sonraki sezonun DayZero'suna kadar gün sayısı
seasons['SeasonLength'] = seasons['DayZero'].shift(-1) - seasons['DayZero']
seasons['SeasonLength'] = seasons['SeasonLength'].dt.days
```

### Adım 2: Bölge Gücü Hesaplama
```python
# Turnuva sonuçlarını oku
tourney = pd.read_csv('MNCAATourneyCompactResults.csv')
seeds = pd.read_csv('MNCAATourneySeeds.csv')

# Seed'den bölge bilgisini çıkar (W01 -> W, X16 -> X)
seeds['Region'] = seeds['Seed'].str[0]

# Her bölgeden kaç takım kazandı?
# Kazanan takımların bölgelerini say
# Bölge başına ortalama kazanma oranı hesapla
```

### Adım 3: Turnuva Verisine Ekle
```python
# processed_features.csv'ye Season bazlı feature'ları ekle
# Her maç için o sezonun uzunluğunu ekle
# Her takım için bölge bilgisini ekle
```

### Adım 4: Korelasyon Analizi
```python
# Target ile korelasyonları hesapla
correlations = df[['Target', 'SeasonLength', 'RegionStrength']].corr()
print(correlations['Target'])
```

## Korelasyon Analizi
- [ ] Season vs Target
- [ ] Sezon uzunluğu vs Target
- [ ] Bölge vs Target

## Notlar
- 2020 COVID-19 (NA değerler)
- 2026 henüz TBD

## Sorular
1. Sezon uzunluğunu nasıl hesaplayacağız? (Yukarıdaki yöntem uygun mu?)
2. Bölge gücünü nasıl ölçeceğiz? (Kazanma oranı mı, ortalama seed mi?)
3. Bu feature'ları mevcut processed_features.csv'ye mi ekleyeceğiz yoksa yeni dosya mı?
