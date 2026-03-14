# M001/S02 — Split/Leakage Contract Gates — Research

**Date:** 2026-03-14

## Summary

S02 bu milestone içinde doğrudan **R002 (Deterministic walk-forward split standard)** ve **R004 (Leakage guardrails and checks)** requirement’larını sahipleniyor. Bu slice’ın çıktısı, S03/S07’deki daha üst katmanların güvenilirliği için blocker: split/leakage gate fail-fast çalışmazsa sonraki metrik, calibration ve governance çıktıları “yanlış iyileşme” üretebilir.

Kod tabanında split üretimi mevcut (`assign_split`: Train<=2022, Val=2023, Test=2024-2025), fakat şu an bu sadece feature üretiminde bir etiketleme adımı; **mekanik gate enforcement yok**. `run_pipeline.py` içinde stage-level fail mekanizması güçlü (structured `stage_events.jsonl` + non-zero exit) ama split/leakage kontrolleri bu mekanizmaya henüz bağlanmamış. Bu yüzden mevcut akışta ihlal durumları ya sessiz geçebilir ya da `03_lgbm_train.py` tarafında anlamsız/ikincil bir hataya dönüşebilir.

Bir diğer önemli gözlem: geçmiş run datasında Train sezonları **kontiguous değil** (örn. 2020 yok), bu da validator tasarımında “aralıksız yıl dizisi” gibi yanlış bir kuralın false fail üreteceği anlamına geliyor. Gate kontratı sezon aralığına ve split→season eşleşmesine bakmalı; contiguity şartı aramamalı.

## Recommendation

**Yaklaşım:** split/leakage gate’lerini yeni bir bağımsız validator katmanı olarak ekleyip mevcut S01 stage lifecycle’a bağla; fakat canonical stage sırasını değiştirme.

1. `run_pipeline.py` içinde `feature` stage sonunda (train başlamadan önce) Men/Women dataframe’leri için gate çalıştır:
   - `validate_split_contract(df, gender)`
   - `validate_leakage_contract(df, gender)`
2. Gate sonucu için standart şema üret:
   - `pass: bool`
   - `blocking_rule: str | null`
   - `reason: str`
   - `evidence: dict` (örn. offending seasons/columns/sample counts)
3. Fail durumunda `RuntimeError` mesajına `blocking_rule` + kısa reason koy; mevcut `_serialize_error` ile `stage_events.jsonl` içine taşınsın (S01’in oturmuş yüzeyini yeniden kullan).
4. Pass durumunda gate sonuçlarını `run_metadata.json -> stage_outputs.feature.gates` altında persist et (ayrı log yüzeyi açmadan).
5. Testlerde iki seviyeyi kilitle:
   - unit: split/leakage validator fonksiyonları
   - integration-contract: gate fail olduğunda pipeline non-zero + `feature` stage `failed` + `error.message` içinde `blocking_rule`.

**Neden:**
- S01 test seam’i ve lifecycle contract’ı zaten hazır; en düşük riskli entegrasyon noktası bu.
- Yeni stage eklemek yerine mevcut `feature` stage içinde gate çalıştırmak, S01’in canonical stage order kontratını bozmaz.
- R002 ve R004 çıktıları makine-okunur kalır ve sonraki slicelar aynı artifact yüzeyinden beslenir.

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| Split mapping drift riski | `assign_split()` in `02_feature_engineering.py` | Tek split otoritesi zaten var; validator aynı mapping’i referanslayarak kural çoğaltmayı önler. |
| Pipeline fail propagation | `run_pipeline.py` stage wrapper + `_serialize_error` + `stage_events.jsonl` | Gate fail’lerini mevcut contract yüzeyine doğal şekilde taşır, ikinci bir hata/log sistemi açmaz. |
| Contract regression detection | Mevcut `pytest` monkeypatch/desenleri (`test_run_pipeline_cli.py`) | S02 gate fail/success davranışını mevcut test stiline aynı seam üzerinden kilitlemek hızlı ve dayanıklı. |
| Dataframe contract checks | `pandas` column/set/value assertions | Basit, açıklanabilir, dependency eklemeden split/leakage kontratını doğrular. |

## Existing Code and Patterns

- `mania_pipeline/scripts/02_feature_engineering.py` — Split kaynağı burada (`assign_split`) ve final model matrisi burada üretiliyor (`build_matchup_matrix`); leakage checker için kolon namespace doğrulaması bu çıktı üzerinde yapılmalı.
- `mania_pipeline/scripts/run_pipeline.py` — S01’den gelen fail-fast stage lifecycle hazır; S02 gate outcome buraya bağlanmalı.
- `mania_pipeline/scripts/03_lgbm_train.py` — Train/Val/Test ayrımı burada tekrar tüketiliyor ama split doğrulaması yok; gate yoksa hatalar burada geç/geçersiz semptomla yüzeye çıkabiliyor.
- `mania_pipeline/tests/test_run_pipeline_cli.py` — Canonical stage order şu an contract: `feature -> train -> eval_report -> artifact`; S02 bunu kırmadan ilerlemeli.
- `mania_pipeline/artifacts/runs/<run_id>/run_metadata.json` — `stage_outputs` içine gate sonuçlarını eklemek için mevcut machine-readable yüzey.
- `mania_pipeline/artifacts/runs/<run_id>/stage_events.jsonl` — Fail durumunda authoritative blocker kanalı.

## Constraints

- S02 owner requirements: **R002 + R004**; gate ihlalinde run’ın fail etmesi zorunlu.
- S01 contract kısıtı: canonical stage order testlerle kilitli; stage eklemek/yeniden sıralamak test drift riski yaratır.
- Feature stage Men+Women’ı tek stage çağrısında üretiyor; gate çıktısı gender-bazlı evidence taşımalı.
- Gerçek veride sezon serisi kontiguous değil (ör. 2020 yok); validator yanlışlıkla “kesintisiz yıl” dayatmamalı.
- `03_lgbm_train.py` split anomaly durumunda anlamlı gate mesajı üretmüyor; bu nedenle gate train’den önce zorunlu.

## Common Pitfalls

- **Yeni stage ekleyip S01 contract’ı kırmak** — S02 gate’i mevcut `feature` stage’ine entegre et; canonical sıra sabit kalsın.
- **Keyword tabanlı agresif leakage filtresi** — `AvgScore_diff` gibi meşru kolonları yanlışlıkla engelleme; leakage için exact forbidden raw columns + namespace contract kullan.
- **Contiguous season varsayımı** — 2020 gibi doğal boşluklar false fail üretir; aralık/etiket eşleşmesi doğrula, süreklilik değil.
- **Opaque fail reason** — Gate fail’de `blocking_rule` ve kısa reason structured biçimde taşınmazsa operability düşer.

## Open Risks

- Veri güncellendiğinde (örn. 2026 sezonu) `assign_split` şu an `History` üretiyor; gate bu durumu net fail-politikasıyla ele almazsa sessiz kapsam kayması olur.
- Leakage checker sadece kolon-şema seviyesinde kalırsa bazı mantıksal leakage türlerini kaçırabilir; en azından split+namespace+forbidden raw feature kuralları zorunlu baseline olmalı.
- Notebook hâlâ alternatif split anlatısı içeriyor (örn. test=2024); S03 gelene kadar parity algı riski devam eder.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| LightGBM | `tondevrel/scientific-agent-skills@xgboost-lightgbm` | available (68 installs) · install: `npx skills add tondevrel/scientific-agent-skills@xgboost-lightgbm` |
| Kaggle workflow | `shepsci/kaggle-skill@kaggle` | available (35 installs) · install: `npx skills add shepsci/kaggle-skill@kaggle` |
| Pandas dataframe contracts | `jeffallan/claude-skills@pandas-pro` | available (858 installs) · install: `npx skills add jeffallan/claude-skills@pandas-pro` |
| Pytest contract testing | `github/awesome-copilot@pytest-coverage` | available (7.1K installs) · install: `npx skills add github/awesome-copilot@pytest-coverage` |
| Installed local skill check | `python-performance-optimization` | installed (tangential; S02 core scope için doğrudan gerekli değil) |

## Sources

- Split mapping ve final matchup dataset şeması (`assign_split`, `build_matchup_matrix`, `Split` üretimi) (source: [02_feature_engineering.py](mania_pipeline/scripts/02_feature_engineering.py))
- Canonical lifecycle/fail-fast yüzeyi ve stage contract kısıtı (source: [run_pipeline.py](mania_pipeline/scripts/run_pipeline.py))
- Train scriptin split tüketimi ve split-ihlaline özgü gate eksikliği (source: [03_lgbm_train.py](mania_pipeline/scripts/03_lgbm_train.py))
- CLI contract testlerinde stage order sabitlemesi (source: [test_run_pipeline_cli.py](mania_pipeline/tests/test_run_pipeline_cli.py))
- S01 ileri istihbarat: `stage_events.jsonl` gate outcome için önerilen insertion point (source: [S01-SUMMARY.md](.gsd/milestones/M001/slices/S01/S01-SUMMARY.md))
- Skill discovery outputs (source: [skills.sh search: lightgbm](https://skills.sh/tondevrel/scientific-agent-skills/xgboost-lightgbm))
- Skill discovery outputs (source: [skills.sh search: kaggle](https://skills.sh/shepsci/kaggle-skill/kaggle))
- Skill discovery outputs (source: [skills.sh search: pandas](https://skills.sh/jeffallan/claude-skills/pandas-pro))
- Skill discovery outputs (source: [skills.sh search: pytest](https://skills.sh/github/awesome-copilot/pytest-coverage))
