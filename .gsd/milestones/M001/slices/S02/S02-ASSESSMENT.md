---
date: 2026-03-14
triggering_slice: M001/S02
verdict: no-change
---

# Reassessment: M001/S02

## Success-Criterion Coverage Check

- Tek canonical komut gerçek veride feature → train → eval → calibration → governance → artifact akışını uçtan uca çalıştırır. → S03, S04, S05, S06, S07
- Men/Women için Train/Val/Test(2024-2025) metrikleri ve side-by-side özet satırı otomatik üretilir. → S03
- Calibration bins CSV + ECE/W-MAE + overconfidence/drift özeti üretilir. → S04, S06
- Governance raporu keep/drop/candidate + `default_action` + ablation delta etkisini içerir. → S05, S06
- Reproducibility ve regression gate (Brier zorunlu, calibration kötüleşmesi fail, AUC bilgi) otomatik pass/fail üretir. → S06
- Notebook ve script farklı eğitim yolu üretemez (single execution path enforcement). → S03, S07

Coverage check sonucu: **pass** (tüm kriterlerin en az bir kalan sahibi var).

## Changes Made

No changes.

S02 hedeflenen riski kapattı: split/leakage ihlali artık feature stage içinde fail-fast enforce ediliyor ve gate kanıtı `stage_outputs.feature.gates.{men,women}` altında persist ediliyor. Kalan risk emeklilik sırası (S03→S04/S05→S06→S07) hâlâ geçerli; boundary map varsayımları S02 çıktılarıyla uyumlu.

## Requirement Coverage Impact

None.

Gereksinim kapsaması hâlâ sound:
- R002/R004 validated durumda ve S02 kanıtlarıyla kalıcılandı.
- Aktif gereksinim sahipliği değişmedi: R003/R005/R006/R019→S03, R007→S04, R008/R009→S05, R010/R011/R018→S06, R012→S07.
- Launchability (R010/R012), continuity (R003/R011/R019), failure-visibility (R006/R018) zinciri kalan slicelarda eksiksiz kapsanıyor.

## Decision References

D002, D010, D011, D012
