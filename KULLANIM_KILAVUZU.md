# Otonom Zapret - Kullanım Kılavuzu

"Beni uğraştırma, tak-çalıştır olsun" diyenler için basitleştirilmiş kurulum rehberi.

## Gereksinimler

Sistemin düzgün çalışması için `netfilter-queue` kütüphanesine ihtiyacı var.

**Terminali aç ve şu komutu yapıştır:**
```bash
sudo apt update
sudo apt install libnetfilter-queue-dev python3-pip
```

## Kurulum

1. Proje klasörüne gir (eğer orada değilsen):
   ```bash
   cd /home/void0x14/Belgeler/Vibe-coding/zapret-autonomous
   ```

2. Gerekli Python paketlerini yükle:
   ```bash
   pip3 install -r requirements.txt
   ```

## Çalıştırma (Hızlı Test)

Simülasyon modunu çalıştırmak istersen (sisteme müdahale etmez, sadece gösterir):

```bash
python3 simulate_block.py
```
*Bu komut "blocked-site.com" için tarama yapar ve sonucu gösterir.*

## Ana Servisi Çalıştırma (Gerçek Kullanım)

Tüm sistemi devreye almak için **root (yönetici)** izni gerekir.

```bash
sudo python3 autonomous_zapret.py
```

Not: Şu anlık proje "prototip" aşamasında olduğu için gerçek trafiği kesmez (Intercept modülü güvenli modda açıldı). Tam aktif etmek için `autonomous_zapret.py` içindeki `interceptor.start_threaded()` satırının başındaki `#` işaretini kaldırman gerekir (Riskli olabilir, önce simülasyonu dene).

## Git Kullanımı Hakkında
Bu proje `git` ile versiyonlanmıştır. Kritik dosyalar (`strategies.db` gibi) gizlenmiştir, rahatça commit atabilirsin.

---
**Önemli:** Veritabanı dosyası (`strategies.db`) sen sitelere girdikçe kendi kendine dolacak ve akıllanacaktır. Silersen öğrendiklerini unutur.
