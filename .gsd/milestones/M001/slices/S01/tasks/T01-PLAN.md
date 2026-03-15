---
estimated_steps: 4
estimated_files: 4
---

# T01: Establish orchestrator contract tests and pytest baseline

**Slice:** S01 — Canonical Run Orchestrator
**Milestone:** M001

## Description

S01’in boundary contract’ını koddan önce testlerle sabitle. Bu task, projeye pytest tabanını ekler ve canonical orchestrator için zorunlu run context + lifecycle event alanlarını assert eden testleri getirir. Böylece T02 implementasyonu “print odaklı” değil, doğrulanabilir kontrata bağlı ilerler.

## Steps

1. `pytest` kullanımını proje ortamına ekle (`environment.yml`) ve `mania_pipeline/pytest.ini` ile test discovery/sane defaults tanımla.
2. `mania_pipeline/tests/test_run_context_contract.py` dosyasında run context şemasını (zorunlu alanlar, tip/format, seed taşınması) doğrulayan testleri yaz.
3. `mania_pipeline/tests/test_run_pipeline_cli.py` dosyasında stage lifecycle event sözleşmesini (`started/succeeded/failed`, duration, error alanları) doğrulayan CLI odaklı testleri (stage stub/monkeypatch ile) yaz.
4. Testleri çalıştırıp kırılgan veya belirsiz assertion’ları temizle; T02 için net kırmızı/yeşil sinyal bırak.

## Must-Haves

- [ ] Test runner kurulumu repo içinde kalıcıdır ve tek komutla çalışır.
- [ ] Run context için zorunlu alanlar açık assertion’larla korunur.
- [ ] Stage lifecycle event’lerinde başarı ve hata yolu ayrı assertion’larla doğrulanır.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_context_contract.py mania_pipeline/tests/test_run_pipeline_cli.py -q`
- Negatif yol doğrulaması: gerekli context/event alanlarından biri kaldırıldığında ilgili test fail eder.

## Observability Impact

- Yeni sinyaller: `pytest` tabanı ile orchestrator contract kırılmaları (eksik run context alanı, eksik/yanlış lifecycle event alanı) test seviyesinde doğrudan görünür hale gelir.
- Gelecek agent için inspeksiyon yüzeyi: `mania_pipeline/tests/test_run_context_contract.py` ve `mania_pipeline/tests/test_run_pipeline_cli.py` dosyaları kontratın yaşayan spesifikasyonu olarak okunur; `pytest -q` çıktısı hangi alanın eksik/uyumsuz olduğunu açıkça gösterir.
- Görünür failure state: run context zorunlu alanı (`run_id`, `seed`, `git_commit`, `started_at`, `command`, `cwd`) veya lifecycle event zorunlu alanı (`stage`, `status`, `started_at`, `finished_at`, `duration_ms`, `error`) eksik/kırık olduğunda testler deterministic olarak fail eder ve regresyon erken yakalanır.

## Inputs

- `.gsd/milestones/M001/slices/S01/S01-PLAN.md` — S01 contract ve verification hedefleri.
- `mania_pipeline/environment.yml` — mevcut dependency tabanı.

## Expected Output

- `mania_pipeline/pytest.ini` — test runner konfigürasyonu.
- `mania_pipeline/tests/test_run_context_contract.py` — run context contract testleri.
- `mania_pipeline/tests/test_run_pipeline_cli.py` — lifecycle + CLI davranış testleri.
- `mania_pipeline/environment.yml` — pytest dependency güncellemesi.
