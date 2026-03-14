import os
import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score

# ─────────────────────────────────────────────────────────
# AYARLAR
# ─────────────────────────────────────────────────────────
DATA_DIR = "mania_pipeline/artifacts/data"
OUT_DIR = "mania_pipeline/artifacts/models"
os.makedirs(OUT_DIR, exist_ok=True)

CANONICAL_SPLITS = ("Train", "Val", "Test")
DROP_COLUMNS = ("Season", "TeamA", "TeamB", "Target", "Split")

TRAINING_PROFILES = {
    "baseline": {
        "learning_rate": 0.05,
        "num_leaves": 31,
        "max_depth": -1,
        "min_child_samples": 20,
        "colsample_bytree": 0.8,
        "subsample": 0.8,
        "n_estimators": 1000,
    },
    "quality_v1": {
        "learning_rate": 0.03,
        "num_leaves": 47,
        "max_depth": -1,
        "min_child_samples": 15,
        "colsample_bytree": 0.9,
        "subsample": 0.9,
        "n_estimators": 1400,
    },
}


# ─────────────────────────────────────────────────────────
# YARDIMCI FONKSİYONLAR
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


def _safe_auc(y_true, y_prob):
    """AUC hesapla; tek sınıf durumunda deterministik None + reason döndür."""
    if len(y_true) == 0:
        return None, "split_empty"

    unique_classes = np.unique(y_true)
    if len(unique_classes) < 2:
        only_class = int(unique_classes[0])
        return None, f"single_class_target:{only_class}"

    try:
        return float(roc_auc_score(y_true, y_prob)), None
    except ValueError as exc:
        return None, f"auc_error:{str(exc)}"


def _compute_split_metrics(model, split_df, feature_columns):
    """Tek bir split için brier/logloss/auc metriklerini üret."""
    if len(split_df) == 0:
        return {
            "brier": None,
            "logloss": None,
            "auc": None,
            "auc_reason": "split_empty",
            "row_count": 0,
        }

    X_split = split_df[feature_columns]
    y_split = split_df["Target"]
    probs_split = model.predict_proba(X_split)[:, 1]

    auc_value, auc_reason = _safe_auc(y_split, probs_split)

    return {
        "brier": float(brier_score(y_split, probs_split)),
        "logloss": float(log_loss(y_split, probs_split, labels=[0, 1])),
        "auc": auc_value,
        "auc_reason": auc_reason,
        "row_count": int(len(split_df)),
    }


def _compute_metrics_by_split(model, df, feature_columns):
    metrics_by_split = {}
    for split_label in CANONICAL_SPLITS:
        split_df = df[df["Split"] == split_label].copy()
        metrics_by_split[split_label] = _compute_split_metrics(model, split_df, feature_columns)
    return metrics_by_split


def resolve_training_params(*, profile: str, random_state: int) -> dict:
    profile_key = str(profile).strip().lower()
    if profile_key not in TRAINING_PROFILES:
        allowed = ", ".join(sorted(TRAINING_PROFILES.keys()))
        raise ValueError(f"unknown training profile: {profile}. allowed={allowed}")

    profile_params = TRAINING_PROFILES[profile_key]
    return {
        "objective": "binary",
        "metric": "binary_logloss",
        "boosting_type": "gbdt",
        "random_state": int(random_state),
        "verbose": -1,
        **profile_params,
    }


# ─────────────────────────────────────────────────────────
# MODEL EĞİTİMİ (LIGHTGBM)
# ─────────────────────────────────────────────────────────
def train_baseline(df, gender="M", random_state=42, profile="baseline"):
    tag = "Men" if gender == "M" else "Women"
    print(f"\n{'='*55}")
    print(f"  {tag.upper()} BASELINE MODEL EĞİTİMİ BAŞLIYOR")
    print(f"{'='*55}")

    # Veriyi Split'lere böl (Time-Series Leakage Koruması)
    train_df = df[df["Split"] == "Train"].copy()
    val_df = df[df["Split"] == "Val"].copy()
    test_df = df[df["Split"] == "Test"].copy()

    print("Bölünme Sonuçları:")
    print(f"  Train : {len(train_df):,} satır (1985-2022)")
    print(f"  Val   : {len(val_df):,} satır (2023)")
    print(f"  Test  : {len(test_df):,} satır (2024-2025)")

    if len(train_df) == 0 or len(val_df) == 0:
        raise ValueError("[HATA] Train veya Val verisi boş!")

    # Hedef (Y) ve Modeli yanıltabilecek kimlik/metadata (X_drop) sütunları
    features = [c for c in df.columns if c not in DROP_COLUMNS]

    training_profile = str(profile).strip().lower()
    params = resolve_training_params(profile=training_profile, random_state=random_state)

    print(f"Toplam özellik sayısı: {len(features)}")
    print(f"Training profile: {training_profile}")

    # Veriyi hazırla
    X_train, y_train = train_df[features], train_df["Target"]
    X_val, y_val = val_df[features], val_df["Target"]

    print("\nModel eğitiliyor (Early Stopping = 50)...")
    model = lgb.LGBMClassifier(**params)

    model.fit(
        X_train,
        y_train,
        eval_set=[(X_val, y_val)],
        callbacks=[lgb.early_stopping(stopping_rounds=50, verbose=False)],
    )

    best_iteration = model.best_iteration_
    print(f"En iyi İterasyon: {best_iteration}")

    # ─────────────────────────────────────────────────────────
    # DEĞERLENDİRME (BRIER SCORE & LOG LOSS & AUC)
    # ─────────────────────────────────────────────────────────
    print(f"\n{'-'*45}")
    print("PERFORMANS METRİKLERİ")
    print(f"{'-'*45}")

    metrics_by_split = _compute_metrics_by_split(model, df, features)
    for split_label in CANONICAL_SPLITS:
        split_metrics = metrics_by_split[split_label]
        if split_metrics["row_count"] == 0:
            print(f"{split_label:<5} metrikleri hesaplanamadı (split_empty).")
            continue

        auc_value = split_metrics["auc"]
        if auc_value is None:
            auc_text = f"None ({split_metrics['auc_reason']})"
        else:
            auc_text = f"{auc_value:.4f}"

        print(
            f"{split_label:<5} Brier: {split_metrics['brier']:.4f} | "
            f"LogLoss: {split_metrics['logloss']:.4f} | "
            f"AUC: {auc_text}"
        )

    # Eğer model olasılıkları 0/1 yerine hep 0.5 verseydi Brier Score 0.25 olurdu.
    # Bu yüzden 0.25'in altındaki her şey modelin bir şeyler öğrendiği anlamına gelir.

    # ─────────────────────────────────────────────────────────
    # ÖZELLİK ÖNEM SIRASI (FEATURE IMPORTANCE)
    # ─────────────────────────────────────────────────────────
    importance = model.feature_importances_
    feat_imp = pd.DataFrame({"Feature": features, "Importance": importance})
    feat_imp = feat_imp.sort_values(by="Importance", ascending=False).reset_index(drop=True)

    print("\nEn Önemli İlk 15 Özellik (Gain Tabanlı Değil, Split Tabanlı):")
    for i, row in feat_imp.head(15).iterrows():
        print(f"{i+1:2d}. {row['Feature']:<25} {row['Importance']:>5.0f}")

    # En etkisiz özelliklerin raporlanması
    useless_feats = feat_imp[feat_imp["Importance"] == 0]["Feature"].tolist()
    if useless_feats:
        print(f"\n[DİKKAT] Model tarafından HİÇ KULLANILMAYAN özellikler ({len(useless_feats)} adet):")
        print(", ".join(useless_feats))

    payload = {
        "gender": gender,
        "training_profile": training_profile,
        "training_params": {
            key: params[key]
            for key in (
                "learning_rate",
                "num_leaves",
                "max_depth",
                "min_child_samples",
                "colsample_bytree",
                "subsample",
                "n_estimators",
                "random_state",
            )
        },
        "metrics_by_split": metrics_by_split,
        "feature_snapshot": {
            "feature_columns": features,
            "feature_count": int(len(features)),
        },
        "best_iteration": int(best_iteration) if best_iteration is not None else None,
    }

    return model, payload


# ─────────────────────────────────────────────────────────
# ÇALIŞTIR
# ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    men_df = load_data("M")
    if men_df is not None:
        men_model, men_payload = train_baseline(men_df, "M")
        men_test_brier = men_payload["metrics_by_split"]["Test"]["brier"]
        print(f"Men Test Brier: {men_test_brier}")

    women_df = load_data("W")
    if women_df is not None:
        women_model, women_payload = train_baseline(women_df, "W")
        women_test_brier = women_payload["metrics_by_split"]["Test"]["brier"]
        print(f"Women Test Brier: {women_test_brier}")

    print("\n" + "=" * 55)
    print("  BASELINE MODEL EĞİTİMİ TAMAMLANDI.")
    print("=" * 55)
