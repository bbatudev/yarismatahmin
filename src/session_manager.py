"""
Oturum Yönetim Sistemi - Session Manager
=========================================
Otomatik olarak session_start.md oluşturur ve oturum takibi yapar.

Kullanım:
    python src/session_manager.py start    # Oturum başlat
    python src/session_manager.py end      # Oturum bitir
"""

import os
import re
from datetime import datetime
from pathlib import Path


# Proje kök dizini
PROJECT_ROOT = Path(__file__).parent.parent
PROGRESS_FILE = PROJECT_ROOT / "csv dosyaları analiz" / "progress.md"
SESSION_START_TEMPLATE = PROJECT_ROOT / "session_start.md"
SESSION_END_TEMPLATE = PROJECT_ROOT / "session_end.md"
DAILY_DIR_PATTERN = "{day:02d}-{month:02d}-{year}"


def get_turkish_date():
    """Türkiye formatında tarih döndürür: DD-MM-YYYY"""
    now = datetime.now()
    return {
        "day": now.day,
        "month": now.month,
        "year": now.year,
        "hour": now.hour,
        "minute": now.minute,
        "formatted": now.strftime("%d-%m-%Y"),
        "time_str": now.strftime("%H:%M")
    }


def read_progress_todos():
    """Progress.md'den yapılacaklar listesini okur"""
    if not PROGRESS_FILE.exists():
        return [], []

    content = PROGRESS_FILE.read_text(encoding="utf-8")

    # Yapılacakları ve yapılanları parse et
    todos = []
    dones = []

    in_todos = False
    in_dones = False

    for line in content.split("\n"):
        if "### ⏳ Yapılacaklar" in line or "### ⏳ Yapılacaklar" in line:
            in_todos = True
            in_dones = False
            continue
        if "### ✅ Yapılanlar" in line:
            in_dones = True
            in_todos = False
            continue
        if line.startswith("###") and (in_todos or in_dones):
            in_todos = False
            in_dones = False
            continue

        if in_todos and "| **" in line:
            # Öncelik ve görev adını çıkar
            match = re.search(r'\| \*\*(.+?)\*\* \| (.) (.+?) \| (.+?) \|', line)
            if match:
                task_name = match.group(1).strip()
                priority = match.group(2).strip()
                notes = match.group(3).strip()
                todos.append((task_name, priority, notes))

        if in_dones and "| **" in line:
            match = re.search(r'\| \*\*(.+?)\*\* \| (.+?) \| (.+?) \|', line)
            if match:
                task_name = match.group(1).strip()
                status = match.group(2).strip()
                notes = match.group(3).strip()
                dones.append((task_name, status, notes))

    return todos, dones


def read_yesterday_report():
    """Dünkü raporu okur ve 'Yarına Devredilenler' bölümünü döndürür"""
    date_info = get_turkish_date()

    # Dünü bul (basit yaklaşım: önceki gün)
    from datetime import timedelta
    yesterday = datetime.now() - timedelta(days=1)

    yesterday_dir = PROJECT_ROOT / f"{yesterday.day:02d}-{yesterday.month:02d}-{yesterday.year}"
    yesterday_file = yesterday_dir / "gunluk_rapor.md"

    if not yesterday_file.exists():
        return []

    content = yesterday_file.read_text(encoding="utf-8")

    # "Yarına Devredilenler" bölümünü bul
    carried_over = []
    in_section = False

    for line in content.split("\n"):
        if "## Yarına Devredilenler" in line:
            in_section = True
            continue
        if in_section and line.startswith("- [ ]"):
            task = line.replace("- [ ]", "").strip()
            carried_over.append(task)
        elif in_section and line.startswith("##"):
            break

    return carried_over


def read_problems():
    """Progress.md'den tespit edilen problemleri okur"""
    if not PROGRESS_FILE.exists():
        return []

    content = PROGRESS_FILE.read_text(encoding="utf-8")

    problems = []
    in_problems = False

    for line in content.split("\n"):
        if "## Tespit Edilen Problemler" in line or "## Tespit Edilen Problemler ve Riskler" in line:
            in_problems = True
            continue
        if in_problems and "| **" in line:
            match = re.search(r'\| \*\*(.+?)\*\* \| (.) (.+?) \| (.+?) \|', line)
            if match:
                problem = match.group(1).strip()
                priority = match.group(2).strip()
                solution = match.group(3).strip()
                problems.append((problem, priority, solution))
        elif in_problems and line.startswith("##"):
            break

    return problems


def create_session_start():
    """Yeni oturum için session_start.md oluşturur"""
    date_info = get_turkish_date()

    # Progress'tan bilgileri al
    todos, dones = read_progress_todos()
    carried_over = read_yesterday_report()
    problems = read_problems()

    # Önceliklere göre ayır
    high_priority = [t for t in todos if t[1] == "🔴"]
    medium_priority = [t for t in todos if t[1] == "🟡"]
    low_priority = [t for t in todos if t[1] == "🟢"]

    # Template'ten oku veya varsayılan kullan
    template_content = ""
    if SESSION_START_TEMPLATE.exists():
        template_content = SESSION_START_TEMPLATE.read_text(encoding="utf-8")

    # Yeni session_start.md oluştur
    output = f"""# Oturum Başı Raporu

## Tarih: {date_info['formatted']}

---

## ⚠️ ÖNEMLİ KURAL

**Kullanıcı ile onay almadan veya konuşulmadan hiçbir göreve başlanmaması gerekiyor.**
**Doğrudan kod yazmaya başlamak yerine, kullanıcı ile görüşerek iletişim halinde çalışılmalı.**

---

## 1. Progress MD Özeti

*(Aşağıdaki adımları sırayla yap)*

### Adım 1: Progress.md Oku
- [x] `csv dosyaları analiz/progress.md` dosyasını aç
- [x] "Yapılacaklar" bölümünü kontrol et
- [x] "Tespit Edilen Problemler" bölümünü oku

### Adım 2: Günlük Klasörü Oku (Varsa)
- [x] Bugünün tarihine ait klasörü kontrol et (örn: `{date_info['day']:02d}-{date_info['month']:02d}-{date_info['year']}/`)
- [x] Dünkü raporda "Yarına Devredilenler" bölümünü oku
- [x] Dünü bitmemiş görevleri listele

### Adım 3: Bugünkü Öncelikleri Çek (Progress'den)
- [x] Progress.md'den "⏳ Yapılacaklar" tablosunu kopyala
- [x] En yüksek öncelikli (🔴) görevleri bugüne ata
- [x] Orta öncelikli (🟡) görevleri zaman kalanlara ata

---

## 2. Dünden Devralınan Görevler

*(Dünkü raporun "Yarına Devredilenler" bölümünden buraya kopyala)*
"""

    if carried_over:
        for task in carried_over:
            output += f"- [ ] {task}\n"
    else:
        output += "\n*(Dünden devralınan görev bulunamadı)*\n"

    output += f"""

---

## 3. Bugünün Oturum Hedefleri (Öncelik Sırasıyla)

### 🔴 Yüksek Öncelik (Bugün mutlaka yapılacak)
"""

    if high_priority:
        for i, (task, priority, notes) in enumerate(high_priority, 1):
            output += f"{i}. **{task}**\n"
    else:
        output += "\n*(Yüksek öncelikli görev bulunamadı)*\n"

    output += "\n### 🟡 Orta Öncelik (Zaman olursa yapılacak)\n"
    if medium_priority:
        for i, (task, priority, notes) in enumerate(medium_priority, 1):
            output += f"{i}. **{task}**\n"
    else:
        output += "\n*(Orta öncelikli görev bulunamadı)*\n"

    output += "\n### 🟢 Düşük Öncelik (İmkân varsa)\n"
    if low_priority:
        for i, (task, priority, notes) in enumerate(low_priority, 1):
            output += f"{i}. **{task}**\n"
    else:
        output += "\n*(Düşük öncelikli görev bulunamadı)*\n"

    output += """

---

## 4. Devam Eden Görevler (Önceki Oturumdan)

"""

    # Carried over'dan devam eden görevleri de ekle
    if carried_over:
        for task in carried_over:
            output += f"- [ ] {task}\n"
    else:
        output += "\n*(Devam eden görev bulunamadı)*\n"

    output += f"""

---

## 5. Bilinmesi Gereken Problemler

*(Progress.md'deki "Tespit Edilen Problemler" bölümünden kopyala)*

| Problem | Öncelik |
|---------|---------|
"""

    if problems:
        for problem, priority, solution in problems:
            output += f"| {problem} | {priority} {priority} |\n"
    else:
        output += "| *(Problemler progress.md'de bulunamadı*) | - |\n"

    output += f"""

---

## 6. Notlar

* Otomasyon ile oluşturuldu: {date_info['time_str']}
* Oturum başlangıcı: {date_info['time_str']}

---

## 7. Oturum Planı

**İlk 30 dakika:** Dünden devralınan görevleri bitir
**Orta saat:** Yüksek öncelikli yeni görevler
**Son 30 dakika:** Oturum sonu raporu hazırla

---

*Oturum Başlangıcı: {date_info['time_str']}*
*Planlanan Bitiş: -*
*Not: Her değişiklikte saati not al!*
"""

    # Dosyaya yaz
    output_file = PROJECT_ROOT / "session_start.md"
    output_file.write_text(output, encoding="utf-8")

    print(f"✅ session_start.md oluşturuldu!")
    print(f"📅 Tarih: {date_info['formatted']}")
    print(f"🕐 Saat: {date_info['time_str']}")
    print(f"\n📋 Özet:")
    print(f"   - Yüksek öncelik: {len(high_priority)} görev")
    print(f"   - Orta öncelik: {len(medium_priority)} görev")
    print(f"   - Düşük öncelik: {len(low_priority)} görev")
    print(f"   - Dünden devralınan: {len(carried_over)} görev")
    print(f"   - Bilinmesi gereken problem: {len(problems)}")


def create_session_end():
    """Oturum sonu için günlük rapor oluşturur"""
    date_info = get_turkish_date()

    # Günlük klasörü oluştur
    daily_dir = PROJECT_ROOT / f"{date_info['day']:02d}-{date_info['month']:02d}-{date_info['year']}"
    daily_dir.mkdir(exist_ok=True)

    daily_report = daily_dir / "gunluk_rapor.md"

    if daily_report.exists():
        print(f"⚠️ Günlük rapor zaten var: {daily_report}")
        print("   Mevcut raporu okuyup güncellemek ister misiniz?")
        return

    # Template'ten oku veya varsayılan kullan
    template_content = ""
    if SESSION_END_TEMPLATE.exists():
        template_content = SESSION_END_TEMPLATE.read_text(encoding="utf-8")

    output = f"""# Günlük İlerleme Raporu - {date_info['day']} {['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık'][date_info['month']-1]} {date_info['year']}

## Tarih: {date_info['formatted']}

---

## Oturumlar

### Oturum #1
**Başlangıç:** {date_info['time_str']}
**Bitiş:** -
**Süre:** -

---

## Bugün Yapılanlar

### ✅ Tamamlanan Görevler

| Görev | Saat | Notlar |
|-------|------|-------|
| *(Görev giriniz)* | - | |

### ⏳ Devam Eden Görevler

| Görev | Durum |
|-------|--------|
| *(Görev giriniz)* | |

---

## Değişiklik Log'u (Bugün)

| Saat | Değişiklik | Dosya |
|------|------------|-------|
| {date_info['time_str']} | Oturum başladı | session_start.md |

---

## Tespit Edilen Yeni Sorunlar

| Problem | Öncelik | Çözüm Önerisi |
|---------|---------|---------------|
| *(Sorun giriniz)* | | |

---

## Öğrenilenler

- *(Öğrenilenleri buraya ekleyin)*

---

## Yarına Devredilenler

*(Bu bölümü bir sonraki oturumun "session_start.md" dosyasına "Dünden Devralınan Görevler" bölümüne kopyala)*

- [ ] *(Görev giriniz)*

---

## Yarınki Plan

- [ ] session_start.md ile günlük başlangıç yap
- [ ] *(Plan giriniz)*

---

## Notlar

- Otomasyon ile oluşturuldu: {date_info['time_str']}

---

## Commit Bilgileri (Bugün)

**Değişiklik Özeti:**
- *(Özet giriniz)*

**Commit Mesajı:**
```
feat: {date_info['formatted']} {date_info['time_str']} ozet

- detay 1
- detay 2

Cozumlenen sorunlar:
```

---

*Son Güncelleme: {date_info['formatted']} {date_info['time_str']}*
*Toplam Oturum: 1*
"""

    daily_report.write_text(output, encoding="utf-8")

    print(f"✅ Günlük rapor oluşturuldu: {daily_report}")
    print(f"📅 Tarih: {date_info['formatted']}")
    print(f"🕐 Saat: {date_info['time_str']}")


def main():
    """Ana fonksiyon"""
    import sys

    if len(sys.argv) < 2:
        print("Kullanım: python src/session_manager.py [start|end]")
        print("  start  - Oturum başlatır, session_start.md oluşturur")
        print("  end    - Oturum bitirir, günlük rapor oluşturur")
        return

    command = sys.argv[1].lower()

    if command == "start":
        create_session_start()
    elif command == "end":
        create_session_end()
    else:
        print(f"Bilinmeyen komut: {command}")
        print("Kullanım: python src/session_manager.py [start|end]")


if __name__ == "__main__":
    main()
