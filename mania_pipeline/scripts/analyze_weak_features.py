import pandas as pd
import numpy as np

# Load processed features
men = pd.read_csv("c:/Users/Gaming/Desktop/projects/yarismatahmin/mania_pipeline/artifacts/data/processed_features_men.csv")
women = pd.read_csv("c:/Users/Gaming/Desktop/projects/yarismatahmin/mania_pipeline/artifacts/data/processed_features_women.csv")

print("=" * 80)
print("MEVCUT FEATURE SAYISI")
print("=" * 80)
print(f"Erkekler: {len(men.columns)} toplam sütun")
print(f"Kadınlar: {len(women.columns)} toplam sütun")
print()

# Get feature columns (ending with _diff)
men_diff_cols = [c for c in men.columns if c.endswith("_diff")]
women_diff_cols = [c for c in women.columns if c.endswith("_diff")]

print(f"Erkekler: {len(men_diff_cols)} feature (_diff)")
print(f"Kadınlar: {len(women_diff_cols)} feature (_diff)")
print()

# Calculate correlations
men_corr = men[men_diff_cols + ["Target"]].corr()["Target"].sort_values(ascending=False)
women_corr = women[women_diff_cols + ["Target"]].corr()["Target"].sort_values(ascending=False)

print("=" * 80)
print("KORELASYON KARŞILAŞTIRMASI (Target ile)")
print("=" * 80)

# Get common features
common_features = list(set(men_diff_cols) & set(women_diff_cols))

# Create comparison table
comparison = pd.DataFrame({
    "Feature": common_features,
    "Men_Corr": [men_corr.get(f, 0) for f in common_features],
    "Women_Corr": [women_corr.get(f, 0) for f in common_features]
})

# Sort by absolute correlation average
comparison["Avg_Abs_Corr"] = (comparison["Men_Corr"].abs() + comparison["Women_Corr"].abs()) / 2
comparison = comparison.sort_values("Avg_Abs_Corr", ascending=False)

print(comparison.to_string(index=False))
print()

print("=" * 80)
print("ZAYIF FEATURE'LAR (< 0.10 her iki cinsiyet)")
print("=" * 80)
weak_features = comparison[
    (comparison["Men_Corr"].abs() < 0.10) &
    (comparison["Women_Corr"].abs() < 0.10)
].sort_values("Avg_Abs_Corr")

print(weak_features[["Feature", "Men_Corr", "Women_Corr"]].to_string(index=False))
print()

print("=" * 80)
print("DROP EDİLEBİLİR FEATURE'LAR (Analiz)")
print("=" * 80)

# Group 1: Very weak (< 0.05 both)
group1 = comparison[
    (comparison["Men_Corr"].abs() < 0.05) &
    (comparison["Women_Corr"].abs() < 0.05)
]

print("GRUP 1 - Kesin Drop (< 0.05):")
print(f"  {len(group1)} feature:")
for f in group1["Feature"]:
    print(f"    - {f}")
print()

# Group 2: Overtime features (negative correlation, per report)
ot_features = [f for f in comparison["Feature"] if "OT" in f.upper()]
print("GRUP 2 - Overtime Feature'ları (Rapora göre REDDEDİLMİŞ):")
print(f"  {len(ot_features)} feature:")
for f in ot_features:
    m_corr = men_corr.get(f, 0)
    w_corr = women_corr.get(f, 0)
    print(f"    - {f}: Men={m_corr:.3f}, Women={w_corr:.3f}")
print()

# Group 3: Weak features (0.05 - 0.10)
group3 = comparison[
    (comparison["Men_Corr"].abs() >= 0.05) &
    (comparison["Men_Corr"].abs() < 0.10) &
    (comparison["Women_Corr"].abs() < 0.10)
]

print("GRUP 3 - Sınırda (0.05-0.10, değerlendirilmeli):")
print(f"  {len(group3)} feature:")
for f in group3["Feature"]:
    print(f"    - {f}")
print()

print("=" * 80)
print("ÖZET DROP LISTESİ")
print("=" * 80)
drop_list = list(group1["Feature"]) + ot_features + list(group3["Feature"])
print(f"Toplam drop edilebilir: {len(drop_list)} feature")
print()
for i, f in enumerate(drop_list, 1):
    print(f"{i}. {f}")
