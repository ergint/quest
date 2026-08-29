# Aşama 0 — Keşif Süreci

`CLAUDE.md` §2 ve §11 gereği: **bu aşama tamamlanmadan çözücü kodu yazılmaz.**
Bu dizin, keşfin nasıl yürütüleceğini ve ilerlemenin nasıl izleneceğini tanımlar.
Kod içermez.

## Neden bu kadar katı?

Nöbet kuralları büyük ölçüde yazılı değildir; sorumlu hemşirenin kafasında, yıllar
içinde oluşmuş, "bunu böyle yapmazsan olmaz" bilgisidir. Bu bilgi toplanmadan
yazılan bir kısıt modeli tahmine dayanır ve sahada ilk ay içinde reddedilir.
Keşfin amacı tahmini ortadan kaldırmaktır.

## Süreç

1. **Servis seçimi.** En az 3 farklı servis: en az biri yoğun bakım, en az biri
   normal servis. Farklı vardiya desenlerine sahip servisler tercih edilir (ör.
   biri 3 vardiyalı, biri 24 saat nöbetli) — bu, profil parametreleştirmesinin
   (§3, §7) gerçekten farklı ihtiyaçları karşıladığını erken doğrular.

2. **Veri toplama.** Her servisten geçmiş 3 aylık gerçek nöbet listesi (Excel
   dosyası, elle tutulan çizelge, ne varsa) toplanır. Anonimleştirme kişisel veri
   minimizasyonu ilkesi gereği (§9) mümkün olan en erken noktada yapılır: personel
   adları kod isimlere (H1, H2, ...) çevrilir, ham dosya saklanmaz.

3. **Satır satır görüşme.** Liste, sorumlu hemşireyle birlikte gözden geçirilir.
   Standart soru: **"Bunu neden böyle yaptın?"** Görüşme sırasında dikkat edilecek
   sinyaller:
   - Sorumlunun tereddüt ettiği ya da "hep böyle yaptık" dediği yerler — yazılı
     olmayan bir kural olabilir, ama zayıf/tartışmalı olabilir de. İkisini ayırt
     etmek için ısrarla sor.
   - Aynı desenin tekrar ettiği ama sorumlunun net bir gerekçe veremediği yerler
     — bu bir tercih olabilir, katı kısıt değil. Yanlış sınıflandırma motoru
     gereksiz kısıtlar.
   - İstisnalar: "genelde böyle ama şu durumda değil" cümleleri — istisna koşulu
     mutlaka yazılır, aksi halde kural yanlış uygulanır.
   - Kişiye özel kısıtlamalarda (H8) sebep sorulmaz/kaydedilmez, yalnızca kısıtın
     kendisi ve geçerlilik tarihi (bkz. `docs/rules/TEMPLATE.md`).

4. **Kural dökümü.** Çıkan her kural `docs/rules/<servis>.md` dosyasına, şablonu
   (`docs/rules/TEMPLATE.md`) kullanarak, üç sınıftan birinde yazılır: **katı**,
   **esnek**, **tercih**. Kanıt (geçmiş listenin hangi noktasında gözlendiği) ve
   sorumlunun kendi ifadesiyle açıklaması birlikte tutulur — sonradan "bu kural
   gerçekten böyle miydi?" sorusuna geri dönülebilmesi için.

5. **Karşılaştırma ve çelişki kontrolü.** 3 servisin kuralları yan yana konur.
   Ortak olanlar muhtemelen genel kısıt (`H1`-`H8`, `S1`-`S7`) haline gelir;
   servise özgü olanlar profil parametresi veya servise özel kod olarak kalır.
   Çelişen kurallar (bir serviste katı olan, diğerinde tercih olan) not edilir —
   bu, aynı kodun farklı ağırlıkla/parametreyle her iki servise de uygulanabildiğini
   gösterir; kısıt modelinin doğru esnekliğe sahip olduğunun kanıtıdır.

6. **Kapanış kriteri.** Aşama 0, aşağıdaki `CHECKLIST.md` tamamlandığında biter:
   3 servis, her biri için doldurulmuş kural dosyası, sorumlu hemşirenin dosyayı
   "evet, nöbeti böyle tutuyorum" diyerek onayladığı bir not.

## Aşama 0 bitmeden yapılmayacaklar

- Çözücü kodu (`backend/solver/`) yazılmaz.
- Kısıt ağırlıkları (§3 tablosundaki varsayılanlar) kesinleştirilmez — bunlar
  yalnızca başlangıç noktasıdır, keşif sonrası servis bazında revize edilir.
- Veri modeli (H8 dahil) uygulanmaz; yalnızca dokümante edilir.

## Sonraki adım

Bu üç dosya tamamlanıp `CHECKLIST.md`'deki kapanış kriteri karşılandığında,
Aşama 1'e (`backend/solver/`, CLI, katı kısıtlar + temel adalet) geçilir.
