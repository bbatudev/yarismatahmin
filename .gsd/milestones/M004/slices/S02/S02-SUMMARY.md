# S02: CV-Strengthened HPO Selection

HPO seçiminde tek-split Val yerine CV destekli objective kullanılmaya başlandı.

## Yapılanlar
- CV objective helper eklendi.
- Trial candidate payload’ları objective + cv diagnostics içeriyor.
- Best trial seçimi objective-score tabanlı hale geldi.
- Yeni contract test ve runtime smoke proof tamamlandı.

## Sonuç
HPO seçim sinyali daha stabil ve izlenebilir.
