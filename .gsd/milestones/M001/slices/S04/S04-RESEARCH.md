# M001/S04 — Research

**Date:** 2026-03-14

## Summary

S04 bu milestone içinde aktif requirement olarak doğrudan **R007 (Calibration + overconfidence/drift report)** sahibidir. S03 sonrası canonical runtime artık Men/Women için `metrics_table` ve `side_by_side_summary` üretiyor; ancak calibration bins CSV, ECE/W-MAE ve high-prob overconfidence/drift özeti henüz yok. Canlı smoke (`20260314T155110Z_s04_research_probe`) bunu doğruluyor: `eval_report.json` sadece metrik tablosu ve side-by-side özet içeriyor.

Mevcut mimaride calibration hesabı için gerekli ham sinyal (`y_true`, `y_prob`) run artifact’larında persist edilmiyor. Buna rağmen gerekli seam hazır: `stage_outputs.train.genders.{men,women}` içinde model path + feature snapshot var, feature CSV’leri de canonical data dir’de mevcut. En düşük-risk yaklaşım: `eval_report` stage içinde modelleri yükleyip canonical splitler için yeniden `predict_proba` üretmek, sonra calibration raporlarını `run_dir` içine yazmak. Böylece stage order korunur ve `run_metadata` şişmez.

Araştırmadaki sürpriz: high-prob drift için `p>=0.9` women tarafında Val/Test’te boş bin üretirken `p>=0.8` anlamlı örnek sayısı veriyor (Val: 22, Test: 44). Bu yüzden “üst olasılık bini” eşik tanımı kontratta açık olmalı; aksi durumda bazı koşularda drift özeti `null` kalır ve S06 calibration gate’i için zayıf sinyal üretir.

## Recommendation

S04’ü **reporting-layer** olarak kurgula (model retrain veya calibrator-fit yapmadan):

1. `stage_eval_report` içinde Men/Women model dosyalarını (`stage_outputs.train.genders.*.model_path`) yükle.
2. `feature_snapshot.feature_columns` ile split bazında (`Train/Val/Test`) tekrar olasılık üret.
3. Sabit bin contract’ı ile calibration bins tabloyu üret (öneri: `[0.0, 0.1, ..., 1.0]` uniform bins, non-empty binlerde metrik).
4. Split+gender bazında `ECE` ve `W-MAE` hesapla; ayrıca high-prob band için (`p>=0.8`) `pred_mean`, `actual_rate`, `gap`, `sample_count` özeti çıkar.
5. `run_dir` altına en az:
   - `calibration_bins.csv`
   - `calibration_report.json`
   yaz; `stage_outputs.eval_report` altında path + özet payload’ı persist et.

Neden bu yol: S03’ün contract’ına eklenir, stage topology bozulmaz, S06’da calibration degradation gate için makine-okunur bir temel üretir.

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| Reliability/Calibration curve temel hesapları | `sklearn.calibration.calibration_curve` | Doğrulanmış API; `n_bins` ve `strategy` ile standart davranış sağlar. |
| Olasılık binleri ve destek sayılarıyla CSV üretimi | `pandas.cut` + `groupby` | Bin sınırlarını ve `sample_count` alanını açık/denetlenebilir tutar; high-prob band özetine direkt bağlanır. |
| İleride gerçek probability calibration (isotonic/platt) | `sklearn.calibration.CalibratedClassifierCV` | Isotonic/sigmoid’i elle implement etme riskini kaldırır; S04 sonrası policy deneyleri için hazır seam sunar. |

## Existing Code and Patterns

- `mania_pipeline/scripts/run_pipeline.py` — Canonical stage order sabit (`feature -> train -> eval_report -> artifact`); S04 bu sırayı bozmadan `eval_report` stage’ini zenginleştirmeli.
- `mania_pipeline/scripts/run_pipeline.py::stage_eval_report` — Halihazırda `metrics_table` + `side_by_side_summary` üretiyor; calibration payload’ı aynı report pattern’iyle genişletmek en düşük sürtünmeli yol.
- `mania_pipeline/scripts/run_pipeline.py::stage_train` — `stage_outputs.train.genders.{men,women}` altında `model_path`, `metrics_by_split`, `feature_snapshot` persist ediyor; S04 için scoring girdisi burada hazır.
- `mania_pipeline/scripts/03_lgbm_train.py` — `predict_proba` tabanlı metrik hesapları var ama split olasılıklarını persist etmiyor; S04 bu yüzden eval aşamasında modeli yeniden score etmeli.
- `mania_pipeline/tests/test_run_pipeline_cli.py` — Stage order/lifecycle event contract testle kilitli; yeni stage eklemek kırıcı olur.
- `mania_pipeline/tests/test_run_pipeline_s03_eval_contract.py` — `eval_report.json` schema’sı (`metrics_table`, `side_by_side_summary`) zaten testli; S04 ek alanları backward-compatible eklemeli.

## Constraints

- Canonical stage topology değişmemeli; test contract’ları `feature/train/eval_report/artifact` sırasını zorunlu kılıyor.
- S04 çıktısı Men/Women ayrı ve split-aware olmalı; R005’in ayrık track davranışı korunmalı.
- Leakage-safe yaklaşım korunmalı: scoring yalnızca canonical feature outputs (`processed_features_men/women.csv`) üzerinden yapılmalı.
- Val split satır sayısı düşük (`134`); aşırı dar/çok yüksek threshold binleri boş kalabilir.
- `run_metadata.json` zaten büyük (`feature_snapshot.feature_columns` uzun); per-row probability’leri metadata içine gömmek artifact şişmesi yaratır.

## Common Pitfalls

- **Metadata şişmesi** — Per-row `y_prob`/`y_true` dizilerini `run_metadata` içine koymak dosyayı hızla büyütür; ayrı CSV/JSON artifact yaz.
- **Feature kolon sırası kayması** — Model skorlamada `feature_snapshot.feature_columns` kullanılmazsa kolon-order mismatch sessiz hata üretebilir.
- **Yanlış high-prob eşiği** — `>=0.9` women’de boş bin üretiyor; kontratta fallback/empty-bin reason olmadan drift raporu kırılgan olur.
- **Bin stratejisi belirsizliği** — Quantile bins doluluk sağlar ama “üst olasılık bandı” semantiğini zayıflatır; uniform bins + empty-bin handling daha izlenebilir.

## Open Risks

- S06 regression gate için calibration ana metriği (ECE mi W-MAE mi) netleşmezse fail/pass kuralı belirsiz kalır.
- Uniform bins’te küçük splitlerde (özellikle Val) yüksek varyanslı gap’ler yanlış alarm üretebilir; minimum sample guard gerekecek.
- `eval_report` stage’inde model reload + scoring runtime maliyetini artırır; büyük veri/çoklu model senaryosunda optimize edilmesi gerekebilir.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| LightGBM | `tondevrel/scientific-agent-skills@xgboost-lightgbm` | available (not installed) — `npx skills add tondevrel/scientific-agent-skills@xgboost-lightgbm` |
| scikit-learn | `davila7/claude-code-templates@scikit-learn` | available (not installed) — `npx skills add davila7/claude-code-templates@scikit-learn` |
| Pandas | `jeffallan/claude-skills@pandas-pro` | available (not installed) — `npx skills add jeffallan/claude-skills@pandas-pro` |
| Kaggle workflow | `shepsci/kaggle-skill@kaggle` | available (not installed) — `npx skills add shepsci/kaggle-skill@kaggle` |
| Python profiling | `python-performance-optimization` | installed (available skills list) |

## Sources

- Canonical eval output currently lacks calibration artifacts; contains only split metrics table + side-by-side summary (source: [`mania_pipeline/artifacts/runs/20260314T155110Z_s04_research_probe/eval_report.json`](mania_pipeline/artifacts/runs/20260314T155110Z_s04_research_probe/eval_report.json))
- `stage_outputs.train` provides model paths and feature snapshots needed for post-train scoring in eval stage (source: [`mania_pipeline/artifacts/runs/20260314T155110Z_s04_research_probe/run_metadata.json`](mania_pipeline/artifacts/runs/20260314T155110Z_s04_research_probe/run_metadata.json))
- Canonical stage order contract is fixed by tests (source: [`mania_pipeline/tests/test_run_pipeline_cli.py`](mania_pipeline/tests/test_run_pipeline_cli.py))
- S03 eval report contract currently checks only `metrics_table`/`side_by_side_summary` presence (source: [`mania_pipeline/tests/test_run_pipeline_s03_eval_contract.py`](mania_pipeline/tests/test_run_pipeline_s03_eval_contract.py))
- Trainer computes split metrics from `predict_proba` but does not persist per-row probabilities (source: [`mania_pipeline/scripts/03_lgbm_train.py`](mania_pipeline/scripts/03_lgbm_train.py))
- Scikit-learn calibration APIs and method guidance (`calibration_curve`, `CalibratedClassifierCV`, isotonic vs sigmoid) (source: [scikit-learn dev calibration docs](https://scikit-learn.org/dev/modules/calibration.html))
- High-prob bin sparsity check (`p>=0.9` women empty; `p>=0.8` non-empty) confirmed via local probe command on latest run artifacts (source: local command output, 2026-03-14)
