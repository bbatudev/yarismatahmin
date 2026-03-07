import os
import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.metrics import brier_score_loss, log_loss

# ─────────────────────────────────────────────────────────
# AYARLAR
# ─────────────────────────────────────────────────────────
DATA_DIR = "mania_pipeline/artifacts/data"
OUT_DIR  = "mania_pipeline/artifacts/models"
os.makedirs(OUT_DIR, exist_ok=True)

# ─────────────────────────────────────────────────────────
# YARDIMCI FONSİYONLAR
# ─────────────────────────────────────────────────────────
def brier_score(y_true, y_prob):
    """Kaggle'ın değerlendirme metriği"""
    return brier_score_loss(y_true, y_prob)

def load_data(gender="M"):
    filename = f"processed_features_{'men' if gender == 'M' else 'women'}.csv"
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        print(f"[HATA] {filepath} bulunamadı. Lütfen önce 02_feature_engineering.py çalıştırın.")
        return None
    return pd.read_csv(filepath)

# ─────────────────────────────────────────────────────────
# MODEL EĞİTİMİ (LIGHTGBM)
# ─────────────────────────────────────────────────────────
def train_baseline(df, gender="M"):
    tag = "Men" if gender == "M" else "Women"
    print(f"\n{'='*55}")
    print(f"  {tag.upper()} BASELINE MODEL EĞİTİMİ BAŞLIYOR")
    print(f"{'='*55}")

    # Veriyi Split'lere böl (Time-Series Leakage Koruması)
    train_df = df[df["Split"] == "Train"].copy()
    val_df   = df[df["Split"] == "Val"].copy()
    test_df  = df[df["Split"] == "Test"].copy()
    
    print(f"Bölünme Sonuçları:")
    print(f"  Train : {len(train_df):,} satır (1985-2022)")
    print(f"  Val   : {len(val_df):,} satır (2023)")
    print(f"  Test  : {len(test_df):,} satır (2024-2025)")
    
    if len(train_df) == 0 or len(val_df) == 0:
        print(f"[HATA] Train veya Val verisi boş!")
        return None

    # Hedef (Y) ve Modeli yanıltabilecek kimlik/metadata (X_drop) sütunları
    drop_cols = ["Season", "TeamA", "TeamB", "Target", "Split"]
    features = [c for c in df.columns if c not in drop_cols]
    
    print(f"Toplam özellik sayısı: {len(features)}")

    # Veriyi hazırla
    X_train, y_train = train_df[features], train_df["Target"]
    X_val, y_val     = val_df[features], val_df["Target"]
    
    # LGBM Parametreleri (Daha sonra Optuna ile optimize edilecek, şimdilik sabit "iyi" değerler)
    params = {
        'objective': 'binary',
        'metric': 'binary_logloss', # Logloss üzerinden optimize edip olasılık çıkarıyoruz
        'boosting_type': 'gbdt',
        'learning_rate': 0.05,
        'num_leaves': 31,
        'max_depth': -1,
        'min_child_samples': 20,
        'colsample_bytree': 0.8,
        'subsample': 0.8,
        'random_state': 42,
        'n_estimators': 1000,
        'verbose': -1
    }

    print("\nModel eğitiliyor (Early Stopping = 50)...")
    model = lgb.LGBMClassifier(**params)
    
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        callbacks=[lgb.early_stopping(stopping_rounds=50, verbose=False)]
    )
    
    print(f"En iyi İterasyon: {model.best_iteration_}")

    # ─────────────────────────────────────────────────────────
    # DEĞERLENDİRME (BRIER SCORE & LOG LOSS)
    # ─────────────────────────────────────────────────────────
    print(f"\n{'─'*45}")
    print(f"PERFORMANS METRİKLERİ")
    print(f"{'─'*45}")
    
    probs_train = model.predict_proba(X_train)[:, 1]
    brier_train = brier_score(y_train, probs_train)
    ll_train    = log_loss(y_train, probs_train)
    print(f"Train Brier Score : {brier_train:.4f} (LogLoss: {ll_train:.4f})")
    
    probs_val = model.predict_proba(X_val)[:, 1]
    brier_val = brier_score(y_val, probs_val)
    ll_val    = log_loss(y_val, probs_val)
    print(f"Val   Brier Score : {brier_val:.4f} (LogLoss: {ll_val:.4f})")
    
    if len(test_df) > 0:
        X_test, y_test = test_df[features], test_df["Target"]
        probs_test = model.predict_proba(X_test)[:, 1]
        brier_test = brier_score(y_test, probs_test)
        ll_test    = log_loss(y_test, probs_test)
        print(f"Test  Brier Score : {brier_test:.4f} (LogLoss: {ll_test:.4f})  <-- NİHAİ BAŞARI")
    else:
        print(f"Test verisi olmadığı için Test Brier ölçülemedi.")
        brier_test = None
        
    # Eğer model olasılıkları 0/1 yerine hep 0.5 verseydi Brier Score 0.25 olurdu.
    # Bu yüzden 0.25'in altındaki her şey modelin bir şeyler öğrendiği anlamına gelir.
    
    # ─────────────────────────────────────────────────────────
    # ÖZELLİK ÖNEM SIRASI (FEATURE IMPORTANCE)
    # ─────────────────────────────────────────────────────────
    importance = model.feature_importances_
    feat_imp = pd.DataFrame({'Feature': features, 'Importance': importance})
    feat_imp = feat_imp.sort_values(by='Importance', ascending=False).reset_index(drop=True)
    
    print(f"\nEn Önemli İlk 15 Özellik (Gain Tabanlı Değil, Split Tabanlı):")
    for i, row in feat_imp.head(15).iterrows():
        print(f"{i+1:2d}. {row['Feature']:<25} {row['Importance']:>5.0f}")

    # En etkisiz özelliklerin raporlanması
    useless_feats = feat_imp[feat_imp['Importance'] == 0]['Feature'].tolist()
    if useless_feats:
        print(f"\n[DİKKAT] Model tarafından HİÇ KULLANILMAYAN özellikler ({len(useless_feats)} adet):")
        print(", ".join(useless_feats))

    return model, brier_test

# ─────────────────────────────────────────────────────────
# ÇALIŞTIR
# ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    men_df = load_data("M")
    if men_df is not None:
        men_model, men_test_brier = train_baseline(men_df, "M")
        
    women_df = load_data("W")
    if women_df is not None:
        women_model, women_test_brier = train_baseline(women_df, "W")
        
    print("\n" + "="*55)
    print("  BASELINE MODEL EĞİTİMİ TAMAMLANDI.")
    print("="*55)
