## Gorselden_Ozete

# Proje nedir?
Bir görseldeki asıl objeyi tespit edip o obje hakkında internetten araştırma yapan ve kısa bir özet sunan komut
satırı programı. Kullanıcı URL veya dosya yolu verir; program objeyi bulur (ör. "backpack"), 3 anahtar kelime
üretir, web'de arar, güvenilir sayfaları süzer ve özeti gösterir.
Birden fazla obje varsa büyüklük ve güven skoruyla asıl obje seçilir, karar net değilse kullanıcıya sorulur. Özet
kaynak metinden seçilen cümlelerden oluşur, yeniden yazılmaz. Son 3 obje hatırlanır ve sonuçlar JSONL'e
kaydedilir.

# Geliştirme süreci ve teknik kapsam
Proje bir haftada Claude Code ile Python'da geliştirildi. Her aşama ayrı bir modülde; bileşenler main.py'de
kurulup pipeline'a dışarıdan veriliyor.

Algoritma ve veri yapıları tarafında asıl obje skoru, Luhn tabanlı cümle puanlama ve küme örtüşmesiyle tekrar
eleme; API ve HTTP tarafında requests ile timeout, tekrar deneme ve paralel sayfa indirme; embeddings ve
semantic search tarafında ise MobileCLIP2 ile anlamsal anahtar kelime eşleştirme kullanıldı. Claude Code'un
ürettiği kod test edilerek incelendi; masanın üstündeki sandviçin önüne geçmesi ve ticari sayfaların özete sızması
gibi hatalar tespit edilip giderildi.

Süre kısıtı nedeniyle özet ve anahtar kelime üretiminde LLM kullanılmadı; daha uzun bir sürede bu iki aşamaya
LLM eklenmesi planlanıyordu.
