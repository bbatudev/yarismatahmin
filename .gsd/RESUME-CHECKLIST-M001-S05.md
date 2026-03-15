# Resume Checklist — M001 / S05 (Yeni Bilgisayarda Devam)

Bu doküman, projeyi başka bir bilgisayarda **sıfırdan açıp kaldığın yerden güvenli şekilde devam etmek** için adım adım kontrol listesidir.

---

## 1) Repo'yu çek

```bash
git clone https://github.com/bbatudev/yarismatahmin.git
cd yarismatahmin
```

## 2) Branch'leri güncelle

```bash
git fetch --all --prune
git branch -a
```

## 3) Devam branch'ine geç

S05 üzerinden devam için:

```bash
git checkout gsd/M001/S05
git pull origin gsd/M001/S05
```

Kontrol:

```bash
git branch --show-current
git status --branch --short
git rev-list --left-right --count @{u}...HEAD
```

Beklenen:
- branch: `gsd/M001/S05`
- working tree clean
- ahead/behind: `0 0`

---

## 4) Environment hazırla

Conda kullanıyorsan:

```bash
conda env create -f mania_pipeline/environment.yml
conda activate march_mania
```

Venv kullanıyorsan:

```bash
python -m venv venv
# Windows
./venv/Scripts/activate
```

---

## 5) "Nerede kaldık" dosyalarını sırayla oku

1. `.gsd/PROJECT.md`
2. `.gsd/REQUIREMENTS.md`
3. `.gsd/DECISIONS.md`
4. `.gsd/milestones/M001/M001-ROADMAP.md`
5. `.gsd/milestones/M001/slices/S05/S05-PLAN.md`
6. `.gsd/milestones/M001/slices/S05/tasks/T01-SUMMARY.md`
7. `.gsd/milestones/M001/slices/S05/tasks/T02-PLAN.md`
8. `.gsd/milestones/M001/slices/S05/tasks/T03-PLAN.md`

---

## 6) S05 beklenen task durumu

`S05-PLAN.md` içinde:
- `T01` -> `[x]`
- `T02` -> `[ ]`
- `T03` -> `[ ]`

Bu durumda bir sonraki iş: **T02**.

---

## 7) Hızlı doğrulama testleri

```bash
./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_cli.py
./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s04_calibration_contract.py
./venv/Scripts/python -m pytest mania_pipeline/tests/test_feature_governance_ledger.py
./venv/Scripts/python -m pytest mania_pipeline/tests/test_feature_governance_ablation.py
./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s05_governance_contract.py
```

---

## 8) Ajan/GSD başlangıç prompt'u

Ajan'a başlangıçta şunu ver:

> You are executing GSD auto-mode. Resume Milestone M001 Slice S05 from Task T02. Read and follow: `.gsd/milestones/M001/slices/S05/S05-PLAN.md`, `.gsd/milestones/M001/slices/S05/tasks/T01-SUMMARY.md`, `.gsd/milestones/M001/slices/S05/tasks/T02-PLAN.md`. Work on branch `gsd/M001/S05`.

---

## 9) Oturum bitişi (zorunlu)

1. İlgili task summary yaz (`T0X-SUMMARY.md`)
2. `S05-PLAN.md` task checkbox güncelle
3. Gerekliyse `.gsd/STATE.md` güncelle
4. Commit + push

```bash
git add .
git commit -m "M001/S05/T0X: <kısa özet>"
git push origin gsd/M001/S05
```

---

## 10) Kritik notlar

- `git stash` lokaldir, başka bilgisayara otomatik gitmez.
- Devralma için tek güvenli kaynak: **commitlenmiş dosyalar**.
- "Nerede kaldık" kaynağı: `S05-PLAN` + `T0X-SUMMARY` dosyaları.
