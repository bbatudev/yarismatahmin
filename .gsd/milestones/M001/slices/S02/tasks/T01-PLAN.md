---
estimated_steps: 4
estimated_files: 3
---

# T01: Implement split/leakage validator contracts + unit tests

**Slice:** S02 — Split/Leakage Contract Gates
**Milestone:** M001

## Description

R002 ve R004 için validator çekirdeğini orchestration’dan bağımsız, deterministic bir modül olarak kurar. Bu görev sonunda split/leakage ihlalleri aynı gate result şemasıyla (`pass`, `blocking_rule`, `reason`, `evidence`) üretilebilir ve unit testlerle kilitlenmiş olur.

## Steps

1. `mania_pipeline/scripts/split_leakage_contracts.py` dosyasında split ve leakage doğrulayıcı fonksiyonlarını ekle; çıktı şemasını tek helper ile standartlaştır.
2. Split validator’da sezon→split eşleşmesini authority mapping ile kontrol et; contiguity zorlamadan yalnızca kontrat ihlallerini fail et.
3. Leakage validator’da exact forbidden column set + required column contract kontrollerini ekle; false-positive üretebilecek keyword taramasından kaçın.
4. `mania_pipeline/tests/test_split_leakage_contracts.py` içinde pass ve fail-path testlerini ekle; `blocking_rule` ve `evidence` alanlarını assertion ile doğrula.

## Must-Haves

- [ ] Split validator `Train<=2022`, `Val=2023`, `Test={2024,2025}` dışı eşleşmeleri deterministic olarak fail eder.
- [ ] Leakage validator exact forbidden raw/post-game kolonları yakalar ve ihlali `blocking_rule` ile raporlar.
- [ ] Unit testler hem pass hem fail sonuçlarında gate payload şemasını (`pass`, `reason`, `blocking_rule`, `evidence`) doğrular.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_split_leakage_contracts.py`
- Testlerde en az şu senaryolar geçer: valid dataframe, split season mismatch, unknown split etiketi, forbidden leakage column.

## Observability Impact

- Signals added/changed: Standart gate payload şeması ve rule-level failure evidence.
- How a future agent inspects this: Unit test çıktıları + validator dönüş payload’ı.
- Failure state exposed: Hangi kuralın (`blocking_rule`) hangi kolon/season örnekleriyle kırıldığı açık görünür.

## Inputs

- `mania_pipeline/scripts/02_feature_engineering.py` — `assign_split` authority mapping ve final matrix split kolonu davranışı.
- `.gsd/milestones/M001/slices/S02/S02-RESEARCH.md` — contiguity false-fail riski ve leakage kontrol sınırları.

## Expected Output

- `mania_pipeline/scripts/split_leakage_contracts.py` — S02 gate contract fonksiyonları.
- `mania_pipeline/tests/test_split_leakage_contracts.py` — split/leakage unit contract testleri.
- `mania_pipeline/scripts/02_feature_engineering.py` — gerekirse validator authority importunu destekleyen minimal non-breaking düzenleme.
