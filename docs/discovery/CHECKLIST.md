# Aşama 0 İlerleme Takibi

Bu dosya, `README.md`'de tanımlanan keşif sürecinin hangi aşamada olduğunu izler.
Aşama 0, üç servis için de son satır işaretlenmeden kapanmaz.

> **Not (2026-08-29):** Proje sahibi, bu aşama tamamlanmadan `backend/solver/`
> kodunun yazılmasını açıkça talep etti; Aşama 1 bu onayla, gerçek servis verisi
> olmadan başlatıldı. Kullanılan servis profili (`solver/profiles.py` içindeki
> `EXAMPLE_PROFILE_3_SHIFT`) icat edilmiş, gösterim amaçlı değerlerdir — hiçbir
> gerçek hastanenin kuralını temsil etmez. Aşağıdaki liste hâlâ geçerlidir ve
> gerçek pilot kurumla çalışmaya başlamadan önce tamamlanmalıdır; o zamana kadar
> üretilen çözümler yalnızca mühendislik iskeleti olarak değerlendirilmelidir.

## Servis 1 — Yoğun Bakım

- **Servis adı:** _(doldurulmadı)_
- **Sorumlu hemşire:** _(doldurulmadı)_
- [ ] Geçmiş 3 aylık gerçek nöbet listesi toplandı (anonimleştirilmiş)
- [ ] Sorumlu hemşireyle satır satır görüşme yapıldı
- [ ] `docs/rules/<servis>.md` dolduruldu (katı / esnek / tercih sınıflandırması)
- [ ] Kişiye özel kısıtlamalar (H8) sebep içermeden kaydedildi
- [ ] Açık sorular kapatıldı (TEMPLATE.md altındaki liste boş)
- [ ] Sorumlu hemşire dosyayı onayladı ("nöbeti böyle tutuyorum")

## Servis 2 — Normal Servis

- **Servis adı:** _(doldurulmadı)_
- **Sorumlu hemşire:** _(doldurulmadı)_
- [ ] Geçmiş 3 aylık gerçek nöbet listesi toplandı (anonimleştirilmiş)
- [ ] Sorumlu hemşireyle satır satır görüşme yapıldı
- [ ] `docs/rules/<servis>.md` dolduruldu (katı / esnek / tercih sınıflandırması)
- [ ] Kişiye özel kısıtlamalar (H8) sebep içermeden kaydedildi
- [ ] Açık sorular kapatıldı (TEMPLATE.md altındaki liste boş)
- [ ] Sorumlu hemşire dosyayı onayladı ("nöbeti böyle tutuyorum")

## Servis 3 — (Yoğun bakım/normal servis dışında serbest seçim)

- **Servis adı:** _(doldurulmadı)_
- **Sorumlu hemşire:** _(doldurulmadı)_
- [ ] Geçmiş 3 aylık gerçek nöbet listesi toplandı (anonimleştirilmiş)
- [ ] Sorumlu hemşireyle satır satır görüşme yapıldı
- [ ] `docs/rules/<servis>.md` dolduruldu (katı / esnek / tercih sınıflandırması)
- [ ] Kişiye özel kısıtlamalar (H8) sebep içermeden kaydedildi
- [ ] Açık sorular kapatıldı (TEMPLATE.md altındaki liste boş)
- [ ] Sorumlu hemşire dosyayı onayladı ("nöbeti böyle tutuyorum")

## Servisler arası karşılaştırma

- [ ] 3 servisin kuralları yan yana karşılaştırıldı
- [ ] Ortak kurallar genel kod setine (`H1`-`H8`, `S1`-`S7`) eşlendi
- [ ] Servise özgü kurallar profil parametresi / servise özel kod olarak işaretlendi
- [ ] Çelişen sınıflandırmalar (bir serviste katı, diğerinde tercih) not edildi

## Kapanış

- [ ] Yukarıdaki tüm kutular işaretli
- [ ] `docs/rules/` altında 3 servis dosyası mevcut, hiçbiri şablon halinde değil

**Bu kutu işaretlenmeden Aşama 1'e (`backend/solver/` kodu) geçilmez:**

- [ ] **Aşama 0 tamamlandı.**
