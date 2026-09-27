# Görüntülü Sohbet Uygulaması

Bir görsel (URL ya da dosya) alıp içindeki objeyi tespit eden, o obje hakkında internetten araştırma yapıp kısa bir özet sunan komut satırı programı.

## Gereksinimler

- Python 3.11 veya üzeri
- İlk çalıştırmada internet bağlantısı (model dosyaları otomatik indirilir, ~330 MB)

## Kurulum

```bash
pip install -r requirements.txt
```

## Çalıştırma

```bash
python main.py
```

Program açıldığında bir görsel adresi (URL) ya da dosya yolu ister. Çıkmak için `q`, `quit` ya da `exit` yazabilirsiniz.

## Önemli

`data/models/keyword_pool.pt` dosyası projeyle birlikte gelmelidir — bu dosya hiçbir yerden otomatik indirilemez, eksikse program hata verir. Diğer model dosyaları (`yoloe-26l-seg.pt`, `mobileclip2_b.ts`) ilk çalıştırmada kendiliğinden iner.
