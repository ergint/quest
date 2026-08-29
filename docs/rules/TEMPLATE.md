# Kural Dökümü — <Servis Adı>

> Bu dosya `CLAUDE.md` §2'de tanımlanan keşif sürecinin çıktısıdır. Doldurmadan
> önce en az 3 aylık gerçek nöbet listesi, sorumlu hemşireyle satır satır
> gözden geçirilmiş olmalı. Her satır için soru: "Bunu neden böyle yaptın?"

## Servis bilgisi

- **Servis adı:**
- **Servis tipi:** (yoğun bakım / normal servis / diğer)
- **Sorumlu hemşire:**
- **Görüşme tarihi/tarihleri:**
- **İncelenen dönemler:** (ör. 2026-05, 2026-06, 2026-07)
- **Personel sayısı:**
- **Vardiya deseni:** (ör. 3 vardiya 08-16/16-24/24-08, ya da 24 saat nöbet + izin)

## Vardiya profili

| Vardiya | Başlangıç | Bitiş | Süre (saat) | Gereken personel | Gereken deneyimli personel |
|---|---|---|---|---|---|
| | | | | | |

- **Ardışık çalışma günü üst sınırı:**
- **Gece sonrası minimum dinlenme:**
- **Dönemsel toplam çalışma saati üst sınırı:**

## Kurallar

Her kural aşağıdaki formatta, `CLAUDE.md` §3'teki sınıflardan biriyle etiketlenerek
yazılır. Katı kısıtlar mümkün olduğunda `H<n>` koduna, esnek kısıtlar `S<n>` koduna
eşlenir; eşlenemeyen kural servise özgü yeni bir kod alır (ör. `H-<servis>-1`).

### Kural şablonu

> **Kod:** `H1` / `S3` / vb.
> **Sınıf:** katı | esnek | tercih
> **Kural:** (bir cümlede, net)
> **Kanıt:** Bu kural geçmiş listenin hangi satırında/hangi ayda gözlendi?
> **Sorumlunun açıklaması:** ("Bunu neden böyle yaptın?" sorusuna verilen cevap,
> mümkün olduğunca kendi cümleleriyle)
> **Esnek ise ağırlık önerisi:** (varsayılana göre daha mı yüksek/düşük olmalı, neden)
> **Belirsizlik notu:** Kuralın kapsamı/istisnaları netse boş bırak; net değilse
> burada işaretle ve tekrar sorulacaklar listesine ekle.

---

<!-- Kuralları buradan itibaren ekleyin, her biri yukarıdaki şablonla. -->

## Katı kısıtlar (özet tablo)

| Kod | Kural | Kanıt |
|---|---|---|
| | | |

## Esnek kısıtlar (özet tablo)

| Kod | Kural | Varsayılan ağırlık | Bu serviste önerilen ağırlık |
|---|---|---|---|
| | | | |

## Tercihler

| Kural | Açıklama |
|---|---|
| | |

## Kişiye özel kısıtlamalar (H8)

> Yalnızca "bu kişi bu vardiyaya/tarih aralığına atanamaz" bilgisi tutulur.
> Sebep (sağlık, gebelik, vb.) buraya **yazılmaz** — bkz. `CLAUDE.md` §3 ve §9.

| Personel (anonimleştirilmiş kod) | Kısıtlama | Geçerlilik başlangıcı | Geçerlilik bitişi |
|---|---|---|---|
| | | | |

## Doğrulama notu

- [ ] Bu servisin geçmiş listeleri `backend/tests/fixtures/<servis>/` altına
      (anonimleştirilerek) regresyon vakası olarak eklendi mi? (Aşama 1'de yapılır,
      şimdilik işaretlemeyin.)
- [ ] Motor bu kural setiyle geçmiş listeyi katı kısıt ihlali olmadan yeniden
      üretebiliyor mu? (Aşama 2, henüz uygulanamaz.)

## Açık sorular / tekrar görüşülecekler

- [ ]
