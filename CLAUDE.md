# Nöbet — Hemşire Nöbet ve Vardiya Çizelgeleme
Bu dosya projenin tek referans kaynağıdır. Claude Code her oturumda bunu okur.
---
## 1. Ürün
Servis sorumlusu hemşirenin her ay Excel'de elle yaptığı nöbet listesini, kısıt
tabanlı bir çözücüyle dakikalar içinde üreten uygulama.
**Kullanan:** Servis sorumlusu hemşire, başhemşire.
**Ödeyen:** Hastane / özel sağlık kuruluşu.
**Değer önerisi:** Ayda 4-8 saatlik tekrarlı iş, birkaç dakikaya iner. Nöbet
dağılımının adil olduğu sayısal olarak gösterilebilir — bu, ekip içi huzursuzluğun
en sık sebebidir.
**Konumlandırma:** Bu bir İK sistemi değil. Bordro, özlük, puantaj yok. Tek bir işi
çok iyi yapar: listeyi üretir. Kapsam genişletme baskısına direnilecek.
---
## 2. Kod öncesi zorunlu aşama: keşif
**Bu aşama tamamlanmadan çözücü yazılmayacak.**
1. En az 3 farklı servisten (biri yoğun bakım, biri normal servis olsun) geçmiş
   3 aylık gerçek nöbet listesi toplanır.
2. Her liste sorumlu hemşireyle birlikte satır satır gözden geçirilir. Sorulacak
   soru: "Bunu neden böyle yaptın?" Yazılı olmayan kurallar burada çıkar.
3. Çıkan her kural `docs/rules/<servis>.md` dosyasına yazılır ve şu üç sınıftan
   birine konur: **katı** (ihlal edilemez), **esnek** (ihlal edilebilir, ceza alır),
   **tercih** (mümkünse).
4. Doğrulama hedefi: motor, geçmiş listeleri benzer kalitede yeniden üretebilmeli.
   Birebir aynı olması gerekmez ve beklenmemeli; katı kısıtları ihlal etmemesi ve
   adalet metriklerinde geçmiş listeden kötü olmaması yeterlidir.
Bu aşamanın çıktısı olmadan yazılan kısıt modeli tahmine dayanır ve ürün sahada
çalışmaz.
---
## 3. Kısıt modeli
### Karar değişkeni
```
x[nurse, day, shift] ∈ {0, 1}
```
Vardiya tipleri konfigüre edilebilir. Yaygın desenler:
- 3 vardiya: `08-16`, `16-24`, `24-08`
- 2 vardiya: `08-16`, `16-08` (16 saatlik nöbet)
- 24 saatlik nöbet + ertesi gün izin
Vardiya tipleri, süreleri ve dinlenme kuralları **kodda sabit olmayacak**, servis
profilinden okunacak.
### Katı kısıtlar (hard)
| Kod | Kısıt |
|---|---|
| `H1` | Her gün her vardiyada gereken personel sayısı karşılanır |
| `H2` | Bir kişi günde en fazla bir vardiya |
| `H3` | Gece vardiyasından sonra minimum dinlenme süresi (gece → ertesi sabah yasak) |
| `H4` | Ardışık çalışma günü üst sınırı |
| `H5` | İzinli / raporlu / eğitimde olan kişiye atama yapılmaz |
| `H6` | Dönemsel toplam çalışma saati üst sınırı |
| `H7` | Beceri karışımı: her vardiyada en az N deneyimli personel |
| `H8` | Kişiye özel çalışma kısıtlamaları (gece çalışamayan personel) |
`H8` için önemli tasarım kararı: sistem **sebebi** saklamaz. Gebelik, sağlık raporu,
emzirme gibi bilgiler özel nitelikli kişisel veridir. Veri modelinde yalnızca
"bu kişi bu vardiyaya atanamaz, geçerlilik tarihi şu" tutulur. Sebep alanı yoktur.
### Esnek kısıtlar (soft — ağırlıklı ceza)
| Kod | Kısıt | Varsayılan ağırlık |
|---|---|---|
| `S1` | Gece nöbeti sayısı kişiler arasında dengeli | 100 |
| `S2` | Hafta sonu nöbeti dengeli | 100 |
| `S3` | Kişisel talepler (istenen / istenmeyen gün) | 60 |
| `S4` | Geceler blok halinde (dağınık gece cezalandırılır) | 40 |
| `S5` | İki izin arasında tek çalışma günü cezalandırılır | 40 |
| `S6` | Vardiya deseni tutarlılığı (ileri rotasyon tercih edilir) | 30 |
| `S7` | Birlikte çalışması istenmeyen / istenen kişi eşleşmeleri | 20 |
Ağırlıklar arayüzden ayarlanabilir olmalı. Farklı servisler farklı önceliklendirir
ve bu, ürünün uyarlanabilirliğinin ana kaynağıdır.
**Amaç fonksiyonu:** ağırlıklı ceza toplamının minimizasyonu.
**Adalet ölçütü:** Kişi başına gece/hafta sonu sayısının dönemsel hedeften sapması
minimize edilir. Yalnızca maksimum-minimum farkını kullanmak yetersizdir; tek bir
kişinin durumu tüm çözümü domine eder. Sapmaların toplamı ve maksimum sapma birlikte
cezalandırılır.
**Dönemler arası devir:** Geçen ay çok gece nöbeti tutan kişi bu ay az tutmalı.
Her kişi için taşınan bakiye saklanır ve hedef değere katılır. Bu özellik, tek
seferlik bir araçla sürekli kullanılan bir ürün arasındaki farktır.
---
## 4. Çözülemezlik açıklaması
**Kritik özellik.** "Uygun çözüm bulunamadı" mesajı ürünü kullanılamaz hale getirir.
Yaklaşım:
1. Katı kısıtlar CP-SAT'a assumption literal'leri ile eklenir.
2. Çözüm bulunamazsa çözücünün döndürdüğü yeterli olmayan varsayım kümesi
   (`SufficientAssumptionsForInfeasibility`) alınır.
3. Bu küme insan diline çevrilir.
İstenen çıktı formatı:
> 23 Mart gece vardiyası için 3 kişi gerekiyor, ancak o gün izinli olmayan ve gece
> çalışabilen 2 kişi var. Şu seçenekler var: izinlerden birini kaydırın, gereken
> personel sayısını düşürün, ya da o güne dış kaynaklı personel ekleyin.
Ek olarak: katı kısıtlardan bir kısmını geçici olarak esnetip "şu kuralı gevşetirsem
çözüm bulunur" önerisi üretilebilir.
---
## 5. Kilitleme ve yeniden çözme
Sorumlu hemşire nihai karar mercii. Ürün onun yerine geçmez.
- Herhangi bir hücre elle değiştirilebilir.
- Elle yapılan atamalar kilitlenir (`locked = true`), yeniden çözümde sabit kalır.
- Yeniden çözüm, kilitli atamaları koruyarak kalan kısmı optimize eder.
- Elle yapılan bir değişiklik katı kısıt ihlal ediyorsa engellenmez, uyarı gösterilir.
  Sebebi: sorumlu hemşire sistemin bilmediği bir şey biliyor olabilir.
- Değişiklik geçmişi tutulur, geri alınabilir.
---
## 6. Excel köprüsü
Hedef kullanıcı Excel'de yaşıyor. Ürünün benimsenmesi buna bağlı.
- **İçe aktarma:** Personel listesi, izinler ve talepler Excel'den alınabilir.
  Sütun eşleştirme ekranı olmalı; herkesin şablonu farklı.
- **Dışa aktarma:** Üretilen liste, kurumun hâlihazırda kullandığı görünüme yakın
  bir Excel dosyası olarak çıkar. İlk sürümde tek bir makul format yeterli.
- Ayrıca kişi başına PDF/paylaşılabilir görünüm (kendi vardiyalarını görmek isteyen
  hemşire için).
---
## 7. Teknik mimari
```
backend/   Python 3.11, FastAPI
  solver/
    model.py         # CP-SAT model kurulumu
    constraints/     # hard.py, soft.py — her kısıt ayrı fonksiyon
    fairness.py      # hedef hesabı, devir bakiyesi
    explain.py       # çözülemezlik açıklaması
    profiles.py      # servis profili → kısıt konfigürasyonu
  api/
  tests/
frontend/  React + TypeScript + Vite + Tailwind
  features/roster/   # takvim ızgarası, sürükle-bırak, kilitleme
  features/staff/
  features/requests/
```
- Çözücü: `ortools` CP-SAT. Zaman sınırı varsayılan 60 sn, arayüzden ayarlanabilir.
  Çözücü ilk uygun çözümü bulur bulmaz gösterilir, iyileştirme arka planda sürer.
- Çözüm işi asenkron çalışır (arka plan görevi + durum sorgulama). Kullanıcı bekleme
  ekranında ilerlemeyi görür.
- Veritabanı: PostgreSQL.
- `solver/` saf Python'dur, web katmanından bağımsızdır, tek başına test edilir.
---
## 8. Test stratejisi
- **Regresyon vakaları:** Keşif aşamasında toplanan gerçek geçmiş listeler test
  fixture'ı olur. Her sürümde motor bu senaryolarda çalıştırılır, adalet metrikleri
  ve katı kısıt ihlalleri raporlanır.
- **Katı kısıt testleri:** Üretilen her çözüm için tüm katı kısıtlar bağımsız bir
  doğrulayıcı fonksiyonla kontrol edilir. Çözücüye güvenilmez, çıktı doğrulanır.
- **Çözülemezlik testleri:** Bilerek çelişkili senaryolar kurulur, açıklamanın doğru
  kısıtı işaret ettiği kontrol edilir.
- **Ölçek testi:** 60 personel, 31 gün, 3 vardiya. Bu boyutta kabul edilebilir sürede
  iyi bir çözüm üretilmeli.
---
## 9. Veri ve gizlilik
- Sistem personelin sağlık bilgisi, gebelik durumu, izin gerekçesi gibi verileri
  **saklamaz**. Yalnızca "şu tarihte müsait değil" bilgisi tutulur.
- Kişisel veri işlendiği için KVKK kapsamındadır: aydınlatma metni, saklama süresi,
  erişim yetkilendirmesi ve veri işleyen sıfatıyla kurumla sözleşme gerekir. Bu
  konuda hukuki danışmanlık alınmalıdır; teknik tarafta veri minimizasyonu
  varsayılan tasarım ilkesidir.
- Çalışma süresi ve dinlenme sürelerine ilişkin yasal sınırlar **kodda sabitlenmez**,
  servis profilinde parametre olarak tutulur ve varsayılan değerler kurumun İK
  birimiyle teyit edilerek girilir. Uygulama yasal uygunluğu garanti etmez, kurumun
  tanımladığı kuralları uygular. Bu, arayüzde açıkça belirtilir.
---
## 10. Yol haritası
| Aşama | Çıktı |
|---|---|
| 0 | Keşif: 3 servis, gerçek listeler, kural dökümü. Kod yok. |
| 1 | `solver/` — katı kısıtlar + temel adalet. CLI ile çalışır, UI yok. |
| 2 | Geçmiş listelerle doğrulama. Kural seti düzeltilir. |
| 3 | Çözülemezlik açıklaması |
| 4 | Arayüz: takvim ızgarası, elle düzenleme, kilitleme, yeniden çözme |
| 5 | Excel içe/dışa aktarma → ilk pilot kurum |
| 6 | Dönemler arası devir, talep toplama ekranı, çok servisli yapı |
Aşama 5'e kadar tek bir pilot kurumla çalışılır. Genelleştirme, ikinci kurum
geldiğinde yapılır — daha önce değil.
---
## 11. Çalışma kuralları (Claude Code için)
- Aşama 0 tamamlanmadan çözücü yazma.
- Her kısıt ayrı bir fonksiyon, ayrı test. Kısıtlar tek bir dev fonksiyona yığılmaz.
- Vardiya tipleri, saat sınırları, dinlenme süreleri kodda sabit değer olarak
  yazılmaz — profilden okunur.
- Çözücü çıktısı her zaman bağımsız doğrulayıcıdan geçirilir.
- Bir kuralın gerçekte nasıl işlediğinden emin değilsen dur ve sor. Bu alanda
  tahmin edilmiş kural, sahada çalışmayan ürün demektir.
- Türkçe konuş, kodda ve tanımlayıcılarda İngilizce kullan.
