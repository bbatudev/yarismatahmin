# M001/S01 — Canonical Run Orchestrator — Research

**Date:** 2026-03-14

## Summary

S01 bu milestone içinde doğrudan **R001 (Canonical end-to-end run command)** requirement’ını sahipleniyor. Bu slice ayrıca dolaylı olarak sonraki slice’ların ihtiyaç duyduğu temel altyapıyı (stage lifecycle, run context, deterministic seed taşıma) sağlayarak R002/R004/R005/R006/R010/R011/R018/R019 için zemin hazırlıyor.

Kod tabanında bugün iki ayrı script akışı var: `02_feature_engineering.py` feature üretimini yapıyor, `03_lgbm_train.py` eğitim/eval yapıyor. Ancak henüz tek bir canonical entrypoint, run metadata kontratı, stage bazlı lifecycle log’u yok. Daha kritik sürpriz: notebook (`03_model_training.ipynb`) ayrı bir eğitim gerçekliği üretiyor (farklı split/feature seçimi/hyperparam) ve bu D001 “single reality” kararını zayıflatıyor.

Öneri: S01’de yeni bir script-first orchestrator (`run_pipeline` CLI entrypoint) eklenmeli; mevcut script fonksiyonları yeniden kullanılmalı; tüm run için tek bir context (`run_id`, `seed`, `git_commit`, timestamp, command) oluşturulmalı; stage sonuçları makine-okunur formatta yazılmalı. Bunu yaparken notebook eğitim yolunu “disabled as authority” olarak işaretlemek S03’e bırakılabilir ama S01 araştırma çıktısına kritik risk olarak girilmeli.

## Recommendation

**Yaklaşım:**
1. `mania_pipeline/scripts/` altında canonical bir CLI entrypoint tanımla (örn. `run_pipeline.py`).
2. Orchestrator yalnızca şu stage sırasını çalıştırsın: `feature -> train -> eval/report summary -> artifact bookkeeping`.
3. Run başında standard context üret: `run_id`, `seed`, `git_commit`, `started_at`, `command`, `cwd`.
4. Her stage için standart lifecycle event yaz: `stage_name`, `status(started|succeeded|failed)`, `started_at`, `finished_at`, `duration_ms`, `error`.
5. Mevcut scriptleri yeniden kullan; shell ile script çağırma yerine mümkünse Python-level function import/call tercih et (hata yönetimi ve event logging için daha güvenli).

**Neden bu yaklaşım:**
- S01 hedefi “tek komut tetikleyici”yi en düşük riskle verir.
- S02+ için gereken gate hook noktalarını netleştirir (stage lifecycle).
- S03’te single execution path enforcement’i teknik olarak bağlamak kolaylaşır.

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| CLI arg parsing ve usage contract | Python `argparse` (stdlib) | Ek bağımlılık gerektirmez, deterministic ve sürdürülebilir. |
| Run metadata serialization | Python `json` + `pathlib` + `datetime` + `uuid` | Basit, denetlenebilir, artifact contract için yeterli. |
| Stage lifecycle logging | JSON Lines (`*.jsonl`) structured events | S02/S06 gate entegrasyonunda grep/parse kolaylığı sağlar. |

## Existing Code and Patterns

- `mania_pipeline/scripts/02_feature_engineering.py` — Reusable çekirdek: `run_pipeline(gender)` feature üretimini zaten yapıyor; walk-forward split ve leakage hassasiyetine dair mantık burada.
- `mania_pipeline/scripts/03_lgbm_train.py` — Reusable çekirdek: `train_baseline(df, gender)` mevcut; ancak model/metadata persist etmiyor ve CLI contract yok.
- `mania_pipeline/scripts/03_model_training.ipynb` — **Avoid as authority**: scriptten bağımsız eğitim yolu içeriyor (farklı split: test=2024, farklı feature subset/hyperparam), single-reality hedefiyle çelişiyor.
- `mania_pipeline/scripts/analyze_weak_features.py` — Avoid pattern: absolute path hardcode (`c:/Users/...`) canonical orchestrator için taşınabilir değil.

## Constraints

- S01 owner requirement: **R001**. Tek canonical komutla E2E tetikleme sağlanmalı.
- Mevcut runtime gözlemi: `03_lgbm_train.py` default Windows code page (cp1254) altında Unicode box-drawing print yüzünden crash edebiliyor; canonical komut için terminal encoding bağımsız output gerekli.
- Data ve artifact path’leri şu an script içinde gömülü (`DATA_DIR = "march-machine-leraning-mania-2026"`, `mania_pipeline/artifacts/...`); orchestrator bu pathleri tek bir run config üzerinden yönetmeli.
- Henüz test/contract harness yok; stage-level başarısızlıklar makine-okunur event olarak üretilmezse S02/S06 doğrulamaları zorlaşır.

## Common Pitfalls

- **Notebook parity drift** — Notebook ve script farklı split/feature parametreleriyle “iki doğru” üretir; orchestrator authority’si scriptte sabitlenmeli.
- **Silent non-reproducibility** — Seed run context’e yazılmazsa reproducibility gate (S06) için geçmiş karşılaştırma yapılamaz.
- **Human-only logs** — Sadece `print()` logu ile stage pass/fail izlenirse gate entegrasyonu kırılgan olur; structured event zorunlu.
- **Encoding-coupled CLI** — Terminal kodlama farkında kırılan çıktı canonical run güvenilirliğini düşürür.

## Open Risks

- `03_lgbm_train.py` şu an model dosyası/feature listesi/metadata yazmıyor; artifact contract tarafında S01 çıktısı “tetikleme var ama audit zayıf” seviyesinde kalabilir.
- Notebook training path aktif kaldığı sürece D001/D019 riskte kalır (S03 kapanışına kadar).
- Feature script Men+Women’ı birlikte koşuyor; orchestrator’da stage izolasyonu net tanımlanmazsa hata ayrıştırma zorlaşır.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| LightGBM | `tondevrel/scientific-agent-skills@xgboost-lightgbm` | available (68 installs) · install: `npx skills add tondevrel/scientific-agent-skills@xgboost-lightgbm` |
| Kaggle workflow | `shepsci/kaggle-skill@kaggle` | available (35 installs) · install: `npx skills add shepsci/kaggle-skill@kaggle` |
| Scikit-learn metrics/splits | `davila7/claude-code-templates@scikit-learn` | available (297 installs) · install: `npx skills add davila7/claude-code-templates@scikit-learn` |
| Pandas data ops | `jeffallan/claude-skills@pandas-pro` | available (858 installs) · install: `npx skills add jeffallan/claude-skills@pandas-pro` |
| Python performance (installed set) | `python-performance-optimization` | installed (indirectly relevant, not core for S01 scope) |

## Sources

- Feature pipeline already has reusable function boundary + split/leakage logic (source: [02_feature_engineering.py](mania_pipeline/scripts/02_feature_engineering.py))
- Baseline train script has no canonical CLI contract and can crash on Windows encoding (source: [03_lgbm_train.py](mania_pipeline/scripts/03_lgbm_train.py))
- Notebook creates divergent training reality (split/feature/hyperparam differences) (source: [03_model_training.ipynb](mania_pipeline/scripts/03_model_training.ipynb))
- Existing weak-feature analysis script demonstrates non-portable absolute-path anti-pattern (source: [analyze_weak_features.py](mania_pipeline/scripts/analyze_weak_features.py))
- Project-level current-state confirms canonical path is still missing (source: [.gsd/PROJECT.md](.gsd/PROJECT.md))
- Environment/dependency baseline for orchestration decisions (source: [environment.yml](mania_pipeline/environment.yml))
