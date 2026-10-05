# YSK — 1994 / 1999 / 2004 belediye meclisi ve il genel meclisi ("Tumu" tabloları)

| Dosya | Kaynak URL | Sayfa |
|---|---|---:|
| `1994Mahalli-BelediyeMeclis-Tumu.pdf` | https://www.ysk.gov.tr/doc/dosyalar/docs/Mahalli/1994/BelediyeMeclis/Pdf/1994Mahalli-BelediyeMeclis-Tumu.pdf | 164 |
| `1994Mahalli-ilGenel-Tumu.pdf` | https://www.ysk.gov.tr/doc/dosyalar/docs/Mahalli/1994/ilGenel/Pdf/1994Mahalli-ilGenel-Tumu.pdf | 189 |
| `1999Mahalli-BelediyeMeclis-Tumu.pdf` | https://www.ysk.gov.tr/doc/dosyalar/docs/Mahalli/1999/BelediyeMeclis/Pdf/1999Mahalli-BelediyeMeclis-Tumu.pdf | 149 |
| `1999Mahalli-ilGenel-Tumu.pdf` | https://www.ysk.gov.tr/doc/dosyalar/docs/Mahalli/1999/ilGenel/Pdf/1999Mahalli-ilGenel-Tumu.pdf | 144 |
| `2004Mahalli-BelediyeMeclis-Tumu.pdf` | https://www.ysk.gov.tr/doc/dosyalar/docs/Mahalli/2004/BelediyeMeclis/Pdf/2004Mahalli-BelediyeMeclis-Tumu.pdf | 147 |
| `2004Mahalli-ilGenel-Tumu.pdf` | https://www.ysk.gov.tr/doc/dosyalar/docs/Mahalli/2004/ilGenel/Pdf/2004Mahalli-ilGenel-Tumu.pdf | 118 |

İndirilme: 2026-10-05 (kullanıcının tarayıcısından; YSK bu çalışma ortamından erişilemiyor). Değiştirilmedi.

İçerik: belediye meclisi il → ilçe belediyesi → belde; il genel meclisi il → ilçe, her biri Şehir/Köy
kırılımıyla. Sandık, kayıtlı seçmen, oy kullanan, katılım, geçerli oy, parti oyları ve yüzdeleri;
2004'te üyelik (sandalye) sayıları. Dijital metin (OCR yok).

Kaynağın kendi notu: "Türkiye toplamı Resmi Gazete'den, belediyelere [igm: ilçe toplamları] ait
bilgiler birleştirme tutanaklarından aynen alınmış, il toplamları ve oranlar birleştirme
tutanaklarından TÜİK tarafından hesaplanmıştır." Yani DİE kitaplarıyla (`../../tuik/mahalli-kitap/`)
aynı tutanaklardan hazırlanmış dijital tablolar.

Okuma: `scripts/pipelines/ysk_kesin/parse_mahalli_meclis_tumu.py` →
`data/kaynaklar/ysk/mahalli-meclis/<yıl>yerel_<bm|igm>.json`. Kullanım:
`scripts/pipelines/meclis_harita/build_meclis_harita.py` (DİE satırı okunamayan il/ilçeleri doldurur).

Doğrulama (2026-10-05): DİE kitabından okunup doğrulanmış satırlarla sandık+seçmen anahtarıyla
karşılaştırıldı; 15.600 satırın 1'i dışında (1994 Aydın Hıdırbeyli beldesi, DİE okumasının kimliği
şüpheli) bütün değerler birebir aynı.

Bilinen kaynak sorunları (değiştirilmedi): sayfaların bir kısmında sayılar "1234,0" biçiminde ve
yüzdeler tamsayı; yazılı yüzdeler yer yer yuvarlamayla açıklanamayacak kadar farklı (ör. 1994 Adana
SBP 1.082 / 663.336 = %0,16, yazılı %0,1); 1994 il genel meclisi Kayseri/Felahiye ilçe satırı
anlamsız (seçmen 58.460, Şehir+Köy toplamının 10 katı); 1994 belediye meclisi Tokat il toplamı
ilçe+belde satırlarının toplamından 38.174 geçerli oy fazla; 1999 belediye meclisinde Erzurum,
Muğla, Yozgat il satırlarında Bağımsız oyu yok, Kahramanmaraş, Mersin, Yozgat il toplamı satırların
toplamını parti bazında tutmuyor (bu illerin YSK satırları kullanılmadı).
