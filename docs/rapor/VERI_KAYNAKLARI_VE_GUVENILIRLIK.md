# Veri kaynakları, sınır/köy kırılımı ve güvenilirlik raporu

*8 Kasım 2026 · Kaynak: hamiKumbasae/turkiye-secim-haritasi deposu (main, d561986) · Yalnızca depodaki bilgiye dayanır*

## 1. Özet

Bu rapor iki soruya cevap verir: (1) 46 seçimin hangi düzeyinin (il, ilçe, mahalle) verisi hangi kaynaktan geliyor, (2) kendi çizdiğimiz/türettiğimiz sınır ve köy kırılımı katmanlarında eksik ve güvenilirlik durumu ne. Bütün yüzdeler depodaki veri dosyalarından bu rapor için yeniden hesaplandı; projenin eski raporlarındaki sayılar kopyalanmadı.

- **Oy verisinin kaynağı.** 46 seçimin ilçe düzeyi kayıtlarında (toplam 34.927 kayıt) resmî birincil kaynak (YSK, TÜİK/DİE) payı %70,6, resmî kaynakla teyitli veya düzeltilmiş ikincil kaynak payı %23,1, hiçbir resmî kaynakla karşılaştırılmamış (Vikipedi/GitHub tabanlı) kayıt payı %4,7; geri kalan %1,6 il merkezi belediyesinin il kaydıyla aynı olduğu satırlar.

- **Zayıf nokta oy verisinde.** Teyitsiz kayıtlar ağırlıkla 1950–1989 yerel seçimlerinde (en kötüleri 1950, 1955 ve 1963; 2024 yerelde de %2,8 Vikipedi etiketli ilçe var). 1950 ve 1955 yerel ilçe satırlarında yalnızca kazanan parti var (oy yok). 2009 sonrası seçimlerin hemen hepsi YSK sandık sonuçlarından toplandı.

- **Mahalle/köy düzeyi yalnız 2009 sonrası var** ve tamamı YSK sandık verisi. Asıl sorun oyda değil haritaya oturtmada: 2023 genel seçimde ilçe seçmeninin %94,6 kadarı bir sınır poligonuna bağlı, %5,4 kadarı (3.264.996 seçmen) boş kalıyor. 81 ilin 38'inde bu oran %90'ın altında; en düşükler: Aksaray %67,3, Iğdır %68,6, Yozgat %71,0, Ağrı %72,2, Niğde %73,4, Siirt %73,6.

- **Çizim kaynakları (mahalle/köy poligonu, 2023):** TKGM kadastro %53,1, ttezer (belediye/MAKS) %31,8, OpenStreetMap %11,4, belediye açık verisi %3,7 (poligon sayısı üzerinden; seçmen ağırlıklı payları 4. bölümde).

- **Tarihsel (kendi türettiğimiz) sınırlar:** 1961–1987 genel seçim, referandum ve 1963–1984 yerel seçimlerde seçmenin yaklaşık %54–70'i, bugünkü ilçelerin birleştirilmesiyle türetilmiş (HIST/HISTK) poligonlarda gösteriliyor. Projenin kendi etiketiyle bu eşlemelerin büyük kısmı "kesin" (örn. 1961'de 973 ilçenin 935'i, %96,1); kalanı yaklaşık/kaba/şüpheli. Bugünkü 973 ilçenin 191'inde (%19,6) kuruluş öncesi köy düzeyi sınır soyu kaynaklarda çözülmemiş (90 ilçede soy bilgisi hiç yok).

- **Bağımsız hakeme göre ilçe sınırı uyumu:** Güncel ilçe sınırları TKGM idari birimleriyle karşılaştırıldı: 971 ilçede medyan örtüşme (IoU) 0,886; 421 ilçede ≥0,90, 99 ilçede \<0,70.

**Önemli not:** "Yüzde kaç doğru" sorusunun tek bir sayısal cevabı yok; elimizde gerçek değer yok. Bu yüzden üç ölçülebilir gösterge ayrı veriliyor (kaynak payı, tutarlılık, geometri uyumu) ve her seçim için kurala bağlı bir güven notu (Yüksek/Orta/Düşük) ekleniyor. Notların eşikleri bu rapor için seçilmiştir, 2. bölümde yazılıdır ve değiştirilebilir.

## 2. Yöntem ve tanımlar

#### Kaynak payı

Her il ve ilçe kaydının kaynağı şu sırayla belirlendi: kaydın kendi "kaynak.ana" etiketi varsa o; yoksa sources.yml'deki o seçim ve düzey için tanımlı birincil kaynak. Etiket yoksa varsayım seçim düzeyindedir, satır düzeyinde doğrulanmış değildir (bu özellikle 2009 sonrası YSK seçimlerinde böyle ve beklenen durum).

#### Güven sınıfları (oy verisi)

- **Resmî:** kayıt doğrudan YSK veya TÜİK/DİE kaynaklı.

- **İkincil+teyitli:** kaynak Vikipedi veya mertnuhoglu; kayıtta resmî kaynakla karşılaştırma işareti (teyit) var ya da resmî kaynakla karşılaştırıldığı için eksik alan eklenmiş.

- **İkincil+resmîyle düzeltilmiş:** ikincil kaynağın oyları TÜİK/DİE ile değiştirilmiş.

- **İkincil teyitsiz:** tek kaynak, ikincil, resmî karşılaştırma işareti yok.

- **İl merkezi satırı:** yerel seçimde il merkezi belediyesinin ilçe listesinde il kaydıyla aynı değerle tekrarı (çift saymamak için ayrı sınıf).

#### Sınır ve harita göstergeleri

- **Türetilmiş poligon payı:** seçimin ilçe satırlarından geometrisi HIST/HISTK ile başlayan (bugünkü ilçelerin birleştirilmesiyle üretilmiş) olanların geçerli oydaki payı. Bu, oyların yanlış olduğu anlamına gelmez; oyun haritada hangi sınıra oturtulduğuna dair bizim türetmemize bağımlılığı ölçer. 1950/1955 yerel için oy olmadığından satır payı verilmiştir.

- **Eşleme güveni:** projenin geo/historical/idari/ilce_eslesme dosyalarındaki kesin / yaklaşık / kaba / şüpheli etiketleri. Etiketler projenin kendi değerlendirmesidir, bağımsız doğrulanmadı.

- **Seçmen kapsamı:** ilçe düzeyi seçmenin kaçının bir mahalle/köy poligonuna bağlandığı (geometri denetimi dosyası).

- **TKGM uyumu:** bugünkü ilçe sınırı ile TKGM birimlerinin birleşiminin IoU'su; TKGM bağımsız hakem olarak kullanıldı, ama kendisi de kusursuz değildir.

#### Güven notu kuralları (bu rapor için seçilen eşikler)

| **Not**       | **Kural**                                                                      |
|---------------|--------------------------------------------------------------------------------|
| Oy: Yüksek    | İlçe (ilçe yoksa il) kayıtlarında teyitsiz pay ≤ %2                            |
| Oy: Orta      | Teyitsiz pay %2–30                                                             |
| Oy: Düşük     | Teyitsiz pay \> %30 veya kayıtların yarısından fazlasında yalnızca kazanan var |
| Sınır: Yüksek | Türetilmiş poligon payı ≤ %5 (ve varsa seçmen kapsamı ≥ %90)                   |
| Sınır: Orta   | Türetilmiş payı %5–75, ya da kapsam %90'ın altı                                |
| Sınır: Düşük  | Türetilmiş payı \> %75 veya yaklaşık/kaba/şüpheli eşleme \> %5                 |

## 3. Seçim bazında kaynak dökümü

Aşağıdaki tablolar dönemlere ayrılmıştır. "Kaynak" sütunu kayıtların yüzde kaçının hangi kaynaktan geldiğini, "Güven sınıfı" sütunu aynı kayıtların resmî kaynakla teyit durumunu gösterir. Birim: il kaydı veya ilçe/belediye kaydı sayısı. Yurtdışı oyları (8 seçim) ayrı panelde tutulur ve bu tablolara dahil değildir.

### 3.1 Dönem özeti (ilçe düzeyi kayıtlar)

| **Dönem** | **İlçe kaydı** | **Resmî %** | **İkincil + teyitli %** | **İkincil + resmîyle düzeltilmiş %** | **Teyitsiz %** | **İl merkezi satırı %** |
|-----------|----------------|-------------|-------------------------|--------------------------------------|----------------|-------------------------|
| 1950–1977 | 7.346          | 52,0        | 22,5                    | 1,0                                  | 20,8           | 3,6                     |
| 1982–2007 | 12.962         | 48,1        | 43,4                    | 5,4                                  | 0,7            | 2,3                     |
| 2009–2024 | 14.619         | 99,8        | 0,0                     | 0,0                                  | 0,2            | 0,0                     |
| Tümü      | 34.927         | 70,6        | 20,8                    | 2,2                                  | 4,7            | 1,6                     |

Not: 1950, 1954 ve 1957 genel seçimlerinde ilçe verisi yoktur (yalnız il, kaynağı YSK arşivi); bu üç seçim yukarıdaki ilçe toplamlarına girmez.

### 3.2 1950–1977 dönemi

<table>
<colgroup>
<col style="width: 19%" />
<col style="width: 7%" />
<col style="width: 8%" />
<col style="width: 30%" />
<col style="width: 34%" />
</colgroup>
<thead>
<tr class="header">
<th><strong>Seçim</strong></th>
<th><strong>Düzey</strong></th>
<th><strong>Birim</strong></th>
<th><strong>Kaynak (%)</strong></th>
<th><strong>Güven sınıfı (%)</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>1950 Genel</td>
<td>il</td>
<td>63</td>
<td>YSK 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="even">
<td>1950 Genel</td>
<td>ilçe</td>
<td>0</td>
<td>Veri yok</td>
<td>–</td>
</tr>
<tr class="odd">
<td>1950 Yerel</td>
<td>il</td>
<td>63</td>
<td>Vikipedi 100,0</td>
<td>İkincil teyitsiz 100,0</td>
</tr>
<tr class="even">
<td>1950 Yerel</td>
<td>ilçe</td>
<td>496</td>
<td>Vikipedi 100,0</td>
<td>İkincil teyitsiz 100,0</td>
</tr>
<tr class="odd">
<td>1954 Genel</td>
<td>il</td>
<td>64</td>
<td>YSK 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="even">
<td>1954 Genel</td>
<td>ilçe</td>
<td>0</td>
<td>Veri yok</td>
<td>–</td>
</tr>
<tr class="odd">
<td>1955 Yerel</td>
<td>il</td>
<td>66</td>
<td>Vikipedi 100,0</td>
<td>İkincil teyitsiz 100,0</td>
</tr>
<tr class="even">
<td>1955 Yerel</td>
<td>ilçe</td>
<td>547</td>
<td>Vikipedi 100,0</td>
<td>İkincil teyitsiz 100,0</td>
</tr>
<tr class="odd">
<td>1957 Genel</td>
<td>il</td>
<td>67</td>
<td>YSK 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="even">
<td>1957 Genel</td>
<td>ilçe</td>
<td>0</td>
<td>Veri yok</td>
<td>–</td>
</tr>
<tr class="odd">
<td>1961 Genel</td>
<td>il</td>
<td>67</td>
<td>YSK 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="even">
<td>1961 Genel</td>
<td>ilçe</td>
<td>636</td>
<td>TÜİK/DİE 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="odd">
<td>1961 Referandum</td>
<td>il</td>
<td>67</td>
<td>YSK 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="even">
<td>1961 Referandum</td>
<td>ilçe</td>
<td>636</td>
<td>TÜİK/DİE 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="odd">
<td>1963 Yerel</td>
<td>il</td>
<td>67</td>
<td>Vikipedi 100,0</td>
<td><p>İkincil teyitsiz 76,1</p>
<p>İkincil+teyitli 20,9</p>
<p>İkincil+resmîyle düzeltilmiş 3,0</p></td>
</tr>
<tr class="even">
<td>1963 Yerel</td>
<td>ilçe</td>
<td>620</td>
<td><p>Vikipedi 89,2</p>
<p>İl satırından türetilen 10,8</p></td>
<td><p>İkincil teyitsiz 67,3</p>
<p>İkincil+teyitli 20,5</p>
<p>İl merkezi satırı 10,8</p>
<p>İkincil+resmîyle düzeltilmiş 1,5</p></td>
</tr>
<tr class="odd">
<td>1965 Genel</td>
<td>il</td>
<td>67</td>
<td>YSK 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="even">
<td>1965 Genel</td>
<td>ilçe</td>
<td>637</td>
<td>TÜİK/DİE 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="odd">
<td>1968 Yerel</td>
<td>il</td>
<td>67</td>
<td>Vikipedi 100,0</td>
<td><p>İkincil+teyitli 80,6</p>
<p>İkincil teyitsiz 14,9</p>
<p>İkincil+resmîyle düzeltilmiş 4,5</p></td>
</tr>
<tr class="even">
<td>1968 Yerel</td>
<td>ilçe</td>
<td>619</td>
<td><p>Vikipedi 89,2</p>
<p>İl satırından türetilen 10,8</p></td>
<td><p>İkincil+teyitli 84,0</p>
<p>İl merkezi satırı 10,8</p>
<p>İkincil teyitsiz 3,2</p>
<p>İkincil+resmîyle düzeltilmiş 1,9</p></td>
</tr>
<tr class="odd">
<td>1969 Genel</td>
<td>il</td>
<td>67</td>
<td>YSK 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="even">
<td>1969 Genel</td>
<td>ilçe</td>
<td>638</td>
<td>TÜİK/DİE 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="odd">
<td>1973 Genel</td>
<td>il</td>
<td>67</td>
<td>YSK 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="even">
<td>1973 Genel</td>
<td>ilçe</td>
<td>638</td>
<td>TÜİK/DİE 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="odd">
<td>1973 Yerel</td>
<td>il</td>
<td>67</td>
<td>Vikipedi 100,0</td>
<td><p>İkincil+teyitli 59,7</p>
<p>İkincil+resmîyle düzeltilmiş 31,3</p>
<p>İkincil teyitsiz 9,0</p></td>
</tr>
<tr class="even">
<td>1973 Yerel</td>
<td>ilçe</td>
<td>620</td>
<td><p>Vikipedi 89,2</p>
<p>İl satırından türetilen 10,8</p></td>
<td><p>İkincil+teyitli 77,4</p>
<p>İl merkezi satırı 10,8</p>
<p>İkincil+resmîyle düzeltilmiş 6,0</p>
<p>İkincil teyitsiz 5,8</p></td>
</tr>
<tr class="odd">
<td>1977 Genel</td>
<td>il</td>
<td>67</td>
<td>YSK 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="even">
<td>1977 Genel</td>
<td>ilçe</td>
<td>638</td>
<td>TÜİK/DİE 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="odd">
<td>1977 Yerel</td>
<td>il</td>
<td>67</td>
<td>Vikipedi 100,0</td>
<td><p>İkincil+teyitli 89,6</p>
<p>İkincil+resmîyle düzeltilmiş 6,0</p>
<p>İkincil teyitsiz 4,5</p></td>
</tr>
<tr class="even">
<td>1977 Yerel</td>
<td>ilçe</td>
<td>621</td>
<td><p>Vikipedi 89,2</p>
<p>İl satırından türetilen 10,8</p></td>
<td><p>İkincil+teyitli 84,2</p>
<p>İl merkezi satırı 10,8</p>
<p>İkincil+resmîyle düzeltilmiş 3,1</p>
<p>İkincil teyitsiz 1,9</p></td>
</tr>
</tbody>
</table>

### 3.3 1982–2007 dönemi (1982 referandumu dahil)

<table>
<colgroup>
<col style="width: 19%" />
<col style="width: 7%" />
<col style="width: 8%" />
<col style="width: 30%" />
<col style="width: 34%" />
</colgroup>
<thead>
<tr class="header">
<th><strong>Seçim</strong></th>
<th><strong>Düzey</strong></th>
<th><strong>Birim</strong></th>
<th><strong>Kaynak (%)</strong></th>
<th><strong>Güven sınıfı (%)</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>1982 Referandum</td>
<td>il</td>
<td>67</td>
<td>YSK 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="even">
<td>1982 Referandum</td>
<td>ilçe</td>
<td>640</td>
<td>TÜİK/DİE 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="odd">
<td>1983 Genel</td>
<td>il</td>
<td>67</td>
<td>YSK 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="even">
<td>1983 Genel</td>
<td>ilçe</td>
<td>640</td>
<td>TÜİK/DİE 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="odd">
<td>1984 Yerel</td>
<td>il</td>
<td>67</td>
<td>Vikipedi 100,0</td>
<td><p>İkincil+teyitli 50,7</p>
<p>İkincil+resmîyle düzeltilmiş 37,3</p>
<p>İkincil teyitsiz 11,9</p></td>
</tr>
<tr class="even">
<td>1984 Yerel</td>
<td>ilçe</td>
<td>644</td>
<td><p>Vikipedi 90,1</p>
<p>İl satırından türetilen 9,9</p></td>
<td><p>İkincil+teyitli 57,5</p>
<p>İkincil+resmîyle düzeltilmiş 21,0</p>
<p>İkincil teyitsiz 11,6</p>
<p>İl merkezi satırı 9,9</p></td>
</tr>
<tr class="odd">
<td>1987 Genel</td>
<td>il</td>
<td>67</td>
<td>YSK 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="even">
<td>1987 Genel</td>
<td>ilçe</td>
<td>646</td>
<td>TÜİK/DİE 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="odd">
<td>1987 Referandum</td>
<td>il</td>
<td>67</td>
<td>YSK 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="even">
<td>1987 Referandum</td>
<td>ilçe</td>
<td>645</td>
<td>TÜİK/DİE 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="odd">
<td>1988 Referandum</td>
<td>il</td>
<td>67</td>
<td>YSK 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="even">
<td>1988 Referandum</td>
<td>ilçe</td>
<td>674</td>
<td>TÜİK/DİE 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="odd">
<td>1989 Yerel</td>
<td>il</td>
<td>67</td>
<td>Vikipedi 100,0</td>
<td><p>İkincil+teyitli 53,7</p>
<p>İkincil+resmîyle düzeltilmiş 46,3</p></td>
</tr>
<tr class="even">
<td>1989 Yerel</td>
<td>ilçe</td>
<td>752</td>
<td><p>Vikipedi 92,3</p>
<p>İl satırından türetilen 7,7</p></td>
<td><p>İkincil+teyitli 54,9</p>
<p>İkincil+resmîyle düzeltilmiş 37,2</p>
<p>İl merkezi satırı 7,7</p>
<p>İkincil teyitsiz 0,1</p></td>
</tr>
<tr class="odd">
<td>1991 Genel</td>
<td>il</td>
<td>74</td>
<td>YSK 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="even">
<td>1991 Genel</td>
<td>ilçe</td>
<td>894</td>
<td><p>mertnuhoglu (TÜİK teyitli) 99,8</p>
<p>TÜİK/DİE 0,2</p></td>
<td><p>İkincil+teyitli 99,7</p>
<p>Resmî 0,2</p>
<p>İkincil+resmîyle düzeltilmiş 0,1</p></td>
</tr>
<tr class="odd">
<td>1994 Yerel</td>
<td>il</td>
<td>76</td>
<td>YSK 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="even">
<td>1994 Yerel</td>
<td>ilçe</td>
<td>931</td>
<td><p>YSK 39,4</p>
<p>TÜİK/DİE 38,0</p>
<p>Vikipedi 16,4</p>
<p>İl satırından türetilen 6,1</p></td>
<td><p>Resmî 77,4</p>
<p>İkincil+teyitli 9,1</p>
<p>İkincil+resmîyle düzeltilmiş 7,2</p>
<p>İl merkezi satırı 6,1</p>
<p>İkincil teyitsiz 0,1</p></td>
</tr>
<tr class="odd">
<td>1995 Genel</td>
<td>il</td>
<td>79</td>
<td>YSK 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="even">
<td>1995 Genel</td>
<td>ilçe</td>
<td>918</td>
<td><p>mertnuhoglu (TÜİK teyitli) 99,9</p>
<p>TÜİK/DİE 0,1</p></td>
<td><p>İkincil+teyitli 99,8</p>
<p>Resmî 0,1</p>
<p>İkincil+resmîyle düzeltilmiş 0,1</p></td>
</tr>
<tr class="odd">
<td>1999 Genel</td>
<td>il</td>
<td>80</td>
<td>YSK 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="even">
<td>1999 Genel</td>
<td>ilçe</td>
<td>921</td>
<td><p>mertnuhoglu (TÜİK teyitli) 99,9</p>
<p>TÜİK/DİE 0,1</p></td>
<td><p>İkincil+teyitli 99,8</p>
<p>Resmî 0,1</p>
<p>İkincil+resmîyle düzeltilmiş 0,1</p></td>
</tr>
<tr class="odd">
<td>1999 Yerel</td>
<td>il</td>
<td>80</td>
<td>YSK 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="even">
<td>1999 Yerel</td>
<td>ilçe</td>
<td>943</td>
<td><p>TÜİK/DİE 38,9</p>
<p>YSK 33,0</p>
<p>Vikipedi 21,6</p>
<p>İl satırından türetilen 6,5</p></td>
<td><p>Resmî 71,9</p>
<p>İkincil+resmîyle düzeltilmiş 10,5</p>
<p>İkincil+teyitli 10,1</p>
<p>İl merkezi satırı 6,5</p>
<p>İkincil teyitsiz 1,1</p></td>
</tr>
<tr class="odd">
<td>2002 Genel</td>
<td>il</td>
<td>81</td>
<td>YSK 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="even">
<td>2002 Genel</td>
<td>ilçe</td>
<td>923</td>
<td><p>mertnuhoglu (TÜİK teyitli) 99,9</p>
<p>TÜİK/DİE 0,1</p></td>
<td><p>İkincil+teyitli 99,8</p>
<p>Resmî 0,1</p>
<p>İkincil+resmîyle düzeltilmiş 0,1</p></td>
</tr>
<tr class="odd">
<td>2004 Yerel</td>
<td>il</td>
<td>81</td>
<td>YSK 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="even">
<td>2004 Yerel</td>
<td>ilçe</td>
<td>945</td>
<td><p>TÜİK/DİE 45,9</p>
<p>YSK 24,7</p>
<p>Vikipedi 22,8</p>
<p>İl satırından türetilen 6,7</p></td>
<td><p>Resmî 70,6</p>
<p>İkincil+resmîyle düzeltilmiş 12,6</p>
<p>İkincil+teyitli 10,2</p>
<p>İl merkezi satırı 6,7</p></td>
</tr>
<tr class="odd">
<td>2007 Genel</td>
<td>il</td>
<td>81</td>
<td>YSK 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="even">
<td>2007 Genel</td>
<td>ilçe</td>
<td>923</td>
<td><p>mertnuhoglu (TÜİK teyitli) 99,9</p>
<p>TÜİK/DİE 0,1</p></td>
<td><p>İkincil+teyitli 99,8</p>
<p>Resmî 0,1</p>
<p>İkincil+resmîyle düzeltilmiş 0,1</p></td>
</tr>
<tr class="odd">
<td>2007 Referandum</td>
<td>il</td>
<td>81</td>
<td>YSK 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="even">
<td>2007 Referandum</td>
<td>ilçe</td>
<td>923</td>
<td>YSK 100,0</td>
<td>Resmî 100,0</td>
</tr>
</tbody>
</table>

### 3.4 2009–2024 dönemi

<table>
<colgroup>
<col style="width: 19%" />
<col style="width: 7%" />
<col style="width: 8%" />
<col style="width: 30%" />
<col style="width: 34%" />
</colgroup>
<thead>
<tr class="header">
<th><strong>Seçim</strong></th>
<th><strong>Düzey</strong></th>
<th><strong>Birim</strong></th>
<th><strong>Kaynak (%)</strong></th>
<th><strong>Güven sınıfı (%)</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>2009 Yerel</td>
<td>il</td>
<td>81</td>
<td>YSK 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="even">
<td>2009 Yerel</td>
<td>ilçe</td>
<td>981</td>
<td><p>YSK 99,3</p>
<p>Vikipedi 0,7</p></td>
<td><p>Resmî 99,3</p>
<p>İkincil teyitsiz 0,7</p></td>
</tr>
<tr class="odd">
<td>2010 Referandum</td>
<td>il</td>
<td>81</td>
<td>YSK 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="even">
<td>2010 Referandum</td>
<td>ilçe</td>
<td>981</td>
<td>YSK 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="odd">
<td>2011 Genel</td>
<td>il</td>
<td>81</td>
<td>YSK 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="even">
<td>2011 Genel</td>
<td>ilçe</td>
<td>981</td>
<td>YSK 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="odd">
<td>2014 Cumhurbaşkanlığı</td>
<td>il</td>
<td>81</td>
<td>YSK 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="even">
<td>2014 Cumhurbaşkanlığı</td>
<td>ilçe</td>
<td>973</td>
<td>YSK 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="odd">
<td>2014 Yerel</td>
<td>il</td>
<td>81</td>
<td>YSK 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="even">
<td>2014 Yerel</td>
<td>ilçe</td>
<td>973</td>
<td>YSK 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="odd">
<td>2015 Haziran Genel</td>
<td>il</td>
<td>81</td>
<td>YSK 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="even">
<td>2015 Haziran Genel</td>
<td>ilçe</td>
<td>973</td>
<td>YSK 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="odd">
<td>2015 Kasım Genel</td>
<td>il</td>
<td>81</td>
<td>YSK 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="even">
<td>2015 Kasım Genel</td>
<td>ilçe</td>
<td>973</td>
<td>YSK 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="odd">
<td>2017 Referandum</td>
<td>il</td>
<td>81</td>
<td>YSK 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="even">
<td>2017 Referandum</td>
<td>ilçe</td>
<td>973</td>
<td>YSK 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="odd">
<td>2018 Genel</td>
<td>il</td>
<td>81</td>
<td>YSK 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="even">
<td>2018 Genel</td>
<td>ilçe</td>
<td>973</td>
<td>YSK 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="odd">
<td>2018 Cumhurbaşkanlığı</td>
<td>il</td>
<td>81</td>
<td>YSK 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="even">
<td>2018 Cumhurbaşkanlığı</td>
<td>ilçe</td>
<td>973</td>
<td>YSK 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="odd">
<td>2019 Yerel</td>
<td>il</td>
<td>81</td>
<td>YSK 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="even">
<td>2019 Yerel</td>
<td>ilçe</td>
<td>973</td>
<td><p>YSK 99,8</p>
<p>Vikipedi 0,2</p></td>
<td><p>Resmî 99,8</p>
<p>İkincil teyitsiz 0,2</p></td>
</tr>
<tr class="odd">
<td>2023 Genel</td>
<td>il</td>
<td>81</td>
<td>YSK 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="even">
<td>2023 Genel</td>
<td>ilçe</td>
<td>973</td>
<td>YSK 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="odd">
<td>2023 Cumhurbaşkanlığı 1. tur</td>
<td>il</td>
<td>81</td>
<td>YSK 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="even">
<td>2023 Cumhurbaşkanlığı 1. tur</td>
<td>ilçe</td>
<td>973</td>
<td>YSK 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="odd">
<td>2023 Cumhurbaşkanlığı 2. tur</td>
<td>il</td>
<td>81</td>
<td>YSK 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="even">
<td>2023 Cumhurbaşkanlığı 2. tur</td>
<td>ilçe</td>
<td>973</td>
<td>YSK 100,0</td>
<td>Resmî 100,0</td>
</tr>
<tr class="odd">
<td>2024 Yerel</td>
<td>il</td>
<td>81</td>
<td><p>YSK 96,3</p>
<p>Vikipedi 3,7</p></td>
<td><p>Resmî 96,3</p>
<p>İkincil teyitsiz 3,7</p></td>
</tr>
<tr class="even">
<td>2024 Yerel</td>
<td>ilçe</td>
<td>973</td>
<td><p>YSK 97,2</p>
<p>Vikipedi 2,8</p></td>
<td><p>Resmî 97,2</p>
<p>İkincil teyitsiz 2,8</p></td>
</tr>
</tbody>
</table>

Notlar: (a) 1994, 1999 ve 2004 yerel ilçe kayıtları karışık kaynaklıdır: YSK arşiv PDF'leri, TÜİK/DİE kitapları ve kalan Vikipedi satırları. (b) 1963–1989 yerel seçimlerinde Vikipedi satırlarının önemli kısmının oyları DİE kitaplarıyla değiştirilmiş veya teyit edilmiştir. (c) 2011–2023 genel ve yerel seçimlerde "Diğer" sütunu YSK parti sütunlarına ayrıştırılmış, kalan fark ayrıca "Diğer tamamlama" olarak işaretlenmiştir; kaynak yine YSK'dır. (d) 2024 yerel seçimde il ve ilçe kayıtlarının küçük bir kısmı (il %3,7, ilçe %2,8) Vikipedi etiketlidir.

## 4. Mahalle ve köy düzeyi (2009 sonrası, 15 seçim)

Mahalle/köy oy verisinin tamamı YSK sandık sonuçlarından muhtarlık bazında toplanmıştır (toplam 396 bine yakın seçim × muhtarlık kaydı). Sınır poligonları ise ayrı kaynaklardan gelir ve her muhtarlığa eşleştirme betiğiyle bağlanır. Eşleşemeyen muhtarlık haritada boş bırakılır (proje kuralı: tahmin yok).

### 4.1 Poligon kaynağı (haritada çizilen mahalle/köy kayıtları)

<table>
<colgroup>
<col style="width: 19%" />
<col style="width: 10%" />
<col style="width: 17%" />
<col style="width: 17%" />
<col style="width: 17%" />
<col style="width: 16%" />
</colgroup>
<thead>
<tr class="header">
<th><strong>Seçim</strong></th>
<th><strong>Çizilen kayıt</strong></th>
<th><p><strong>TKGM kadastro</strong></p>
<p><strong>(kayıt % / oy %)</strong></p></th>
<th><p><strong>ttezer (belediye/MAKS)</strong></p>
<p><strong>(kayıt % / oy %)</strong></p></th>
<th><p><strong>OpenStreetMap</strong></p>
<p><strong>(kayıt % / oy %)</strong></p></th>
<th><p><strong>Belediye açık veri</strong></p>
<p><strong>(kayıt % / oy %)</strong></p></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>2009 Yerel</td>
<td>12.380</td>
<td>32,7 / 10,5</td>
<td>38,7 / 57,6</td>
<td>24,1 / 26,2</td>
<td>4,7 / 5,7</td>
</tr>
<tr class="even">
<td>2011 Genel</td>
<td>44.887</td>
<td>55,2 / 17,6</td>
<td>30,1 / 53,9</td>
<td>11,1 / 22,9</td>
<td>3,7 / 5,5</td>
</tr>
<tr class="odd">
<td>2014 Yerel</td>
<td>28.583</td>
<td>36,1 / 12,3</td>
<td>42,9 / 57,9</td>
<td>15,0 / 24,0</td>
<td>6,0 / 5,8</td>
</tr>
<tr class="even">
<td>2018 Genel</td>
<td>45.453</td>
<td>52,8 / 15,9</td>
<td>32,0 / 55,3</td>
<td>11,4 / 23,4</td>
<td>3,8 / 5,5</td>
</tr>
<tr class="odd">
<td>2019 Yerel</td>
<td>28.985</td>
<td>36,0 / 12,2</td>
<td>43,0 / 58,1</td>
<td>15,0 / 23,8</td>
<td>5,9 / 5,9</td>
</tr>
<tr class="even">
<td>2023 Genel</td>
<td>46.032</td>
<td>53,1 / 14,6</td>
<td>31,8 / 56,6</td>
<td>11,4 / 23,1</td>
<td>3,7 / 5,6</td>
</tr>
<tr class="odd">
<td>2024 Yerel</td>
<td>29.133</td>
<td>36,1 / 12,0</td>
<td>42,9 / 58,9</td>
<td>15,1 / 23,2</td>
<td>5,9 / 5,9</td>
</tr>
</tbody>
</table>

Diğer 8 seçimin (2010 ref., 2014 CB, 2015 Haz./Kas., 2017 ref., 2018 CB, 2023 CB 1./2. tur) dağılımı, aynı muhtarlık kümesini kullandıkları için yukarıdakilerle neredeyse aynıdır. Oy yüzdesi sütunu poligonun bağlı olduğu muhtarlığın geçerli oyuna göre ağırlıklıdır.

### 4.2 Eşleştirme yöntemi ve eşleşemeyenler

Tablo, eşleştirme betiğinin raporladığı muhtarlıkları gösterir. Betik, ttezer'den hazır sınırı gelen illeri (ör. İstanbul'dan yalnız birkaç kayıt görünüyor) büyük ölçüde işlemediği için buradaki kayıt sayısı, 4.1'deki çizilen kayıt sayısından küçüktür; bu yüzden aşağıdaki oranlar tüm ülke için değil, betiğin işlediği muhtarlıklar için geçerlidir. "Yakın ad" ve "OSM konumu" eşleşmeleri kesin değil yaklaşık eşleşmelerdir; bunlar bizim tahminimize en yakın kalemdir.

<table>
<colgroup>
<col style="width: 17%" />
<col style="width: 9%" />
<col style="width: 11%" />
<col style="width: 11%" />
<col style="width: 11%" />
<col style="width: 11%" />
<col style="width: 12%" />
<col style="width: 15%" />
</colgroup>
<thead>
<tr class="header">
<th><strong>Seçim</strong></th>
<th><strong>Betik kaydı</strong></th>
<th><strong>TKGM, ad tam %</strong></th>
<th><strong>TKGM, yakın ad %</strong></th>
<th><strong>TKGM, OSM konumu %</strong></th>
<th><strong>Belediye %</strong></th>
<th><p><strong>Eşleşmedi %</strong></p>
<p><strong>(seçmen %)</strong></p></th>
<th><strong>Köylerde eşleşmedi %</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>2009 Yerel</td>
<td>10.828</td>
<td>22,7</td>
<td>14,1</td>
<td>0,5</td>
<td>5,3</td>
<td>54,8 (43,6)</td>
<td>68,9 (347 köy)</td>
</tr>
<tr class="even">
<td>2010 Referandum</td>
<td>34.505</td>
<td>61,5</td>
<td>7,9</td>
<td>2,2</td>
<td>4,8</td>
<td>22,5 (31,9)</td>
<td>8,2 (23.850 köy)</td>
</tr>
<tr class="odd">
<td>2011 Genel</td>
<td>34.582</td>
<td>61,5</td>
<td>7,9</td>
<td>2,2</td>
<td>4,8</td>
<td>22,5 (32,0)</td>
<td>8,2 (23.893 köy)</td>
</tr>
<tr class="even">
<td>2014 Cumhurbaşkanlığı</td>
<td>30.335</td>
<td>72,2</td>
<td>6,6</td>
<td>2,6</td>
<td>5,6</td>
<td>12,2 (19,4)</td>
<td>5,5 (15.772 köy)</td>
</tr>
<tr class="odd">
<td>2014 Yerel</td>
<td>15.151</td>
<td>58,3</td>
<td>7,7</td>
<td>2,3</td>
<td>11,3</td>
<td>19,2 (22,9)</td>
<td>16,5 (588 köy)</td>
</tr>
<tr class="even">
<td>2015 Haziran Genel</td>
<td>30.383</td>
<td>72,2</td>
<td>6,6</td>
<td>2,6</td>
<td>5,6</td>
<td>12,2 (19,7)</td>
<td>5,6 (15.802 köy)</td>
</tr>
<tr class="odd">
<td>2015 Kasım Genel</td>
<td>30.385</td>
<td>72,2</td>
<td>6,6</td>
<td>2,6</td>
<td>5,6</td>
<td>12,2 (19,7)</td>
<td>5,6 (15.801 köy)</td>
</tr>
<tr class="even">
<td>2017 Referandum</td>
<td>30.459</td>
<td>72,2</td>
<td>6,6</td>
<td>2,6</td>
<td>5,6</td>
<td>12,3 (20,1)</td>
<td>5,6 (15.824 köy)</td>
</tr>
<tr class="odd">
<td>2018 Genel</td>
<td>29.563</td>
<td>72,0</td>
<td>6,7</td>
<td>2,6</td>
<td>5,8</td>
<td>12,2 (20,1)</td>
<td>5,3 (15.153 köy)</td>
</tr>
<tr class="even">
<td>2018 Cumhurbaşkanlığı</td>
<td>29.563</td>
<td>72,0</td>
<td>6,7</td>
<td>2,6</td>
<td>5,8</td>
<td>12,2 (20,1)</td>
<td>5,3 (15.153 köy)</td>
</tr>
<tr class="odd">
<td>2019 Yerel</td>
<td>15.197</td>
<td>58,9</td>
<td>7,7</td>
<td>2,3</td>
<td>11,3</td>
<td>19,1 (22,8)</td>
<td>16,9 (592 köy)</td>
</tr>
<tr class="even">
<td>2023 Genel</td>
<td>30.063</td>
<td>72,3</td>
<td>6,5</td>
<td>2,6</td>
<td>5,7</td>
<td>12,4 (20,2)</td>
<td>5,6 (15.414 köy)</td>
</tr>
<tr class="odd">
<td>2023 Cumhurbaşkanlığı 1. tur</td>
<td>30.063</td>
<td>72,3</td>
<td>6,5</td>
<td>2,6</td>
<td>5,7</td>
<td>12,4 (20,2)</td>
<td>5,6 (15.414 köy)</td>
</tr>
<tr class="even">
<td>2023 Cumhurbaşkanlığı 2. tur</td>
<td>30.063</td>
<td>72,3</td>
<td>6,5</td>
<td>2,6</td>
<td>5,7</td>
<td>12,4 (20,2)</td>
<td>5,6 (15.414 köy)</td>
</tr>
<tr class="odd">
<td>2024 Yerel</td>
<td>15.302</td>
<td>58,9</td>
<td>7,6</td>
<td>2,3</td>
<td>11,3</td>
<td>19,4 (23,7)</td>
<td>17,3 (594 köy)</td>
</tr>
</tbody>
</table>

2009 yerel seçimde eşleşmeyen payının yüksek olması (%54,8) o yılın muhtarlık adlarının sonraki yıllardan farklı olmasından kaynaklanıyor olabilir; bu bir tahmindir, depodaki raporlarda gerekçesi ayrıca yazılı değil.

### 4.3 Haritaya bağlanan seçmen payı

| **Seçim**                    | **İlçe düzeyi seçmen** | **Poligonu olan seçmen** | **Kapsam %** |
|------------------------------|------------------------|--------------------------|--------------|
| 2009 Yerel                   | 39.714.508             | 34.741.153               | 87,48        |
| 2010 Referandum              | 49.495.493             | 44.019.363               | 88,94        |
| 2011 Genel                   | 50.237.343             | 44.703.207               | 88,98        |
| 2014 Cumhurbaşkanlığı        | 52.920.981             | 49.896.658               | 94,29        |
| 2014 Yerel                   | 48.906.096             | 46.080.244               | 94,22        |
| 2015 Haziran Genel           | 53.772.719             | 50.704.863               | 94,29        |
| 2015 Kasım Genel             | 54.084.541             | 51.013.925               | 94,32        |
| 2017 Referandum              | 55.408.773             | 52.240.782               | 94,28        |
| 2018 Genel                   | 56.406.836             | 53.177.627               | 94,28        |
| 2018 Cumhurbaşkanlığı        | 56.406.836             | 53.177.627               | 94,28        |
| 2019 Yerel                   | 53.238.624             | 50.370.376               | 94,61        |
| 2023 Genel                   | 60.774.566             | 57.509.570               | 94,63        |
| 2023 Cumhurbaşkanlığı 1. tur | 60.774.566             | 57.509.570               | 94,63        |
| 2023 Cumhurbaşkanlığı 2. tur | 60.823.248             | 57.555.183               | 94,63        |
| 2024 Yerel                   | 57.665.936             | 54.706.132               | 94,87        |

### 4.4 Kapsamı düşük iller: ayrıntı

Eksik olan oy verisi değil sınır poligonudur: bu muhtarlıkların oyları YSK verisinde vardır, ama çizecek sınır bulunamadığı için haritada boş kalırlar. İl ve ilçe toplamları etkilenmez. Eşleştirme betiğinin işlediği 30.063 muhtarlıkta (15,1 milyon seçmen) 3.715 muhtarlık (3,05 milyon seçmen) eşleşmemiştir. Bu seçmenin %93,7'si mahallelerde, %6,3'ü köylerdedir; %68,6'sı 1.000 ve üzeri seçmenli mahallelerde, %21,2'si "Merkez" ilçelerdedir. Yani eksik ağırlıkla şehir merkezlerindeki büyük, yeni ya da bölünmüş idari mahallelerdir.

| **İl**        | **2023 kapsam %** | **Eşleşmeyen muhtarlık** | **Köy / mahalle** | **Eşleşmeyen seçmen** | **En çok etkilenen ilçeler (seçmen)**                                |
|---------------|-------------------|--------------------------|-------------------|-----------------------|----------------------------------------------------------------------|
| Hatay         | 76,5              | 122                      | 5 / 117           | 248.165               | İskenderun 84.473, Kırıkhan 55.219, Reyhanlı 48.312, Samandağ 24.369 |
| Kahramanmaraş | 83,1              | 98                       | 2 / 96            | 119.847               | Dulkadiroğlu 62.946, Pazarcık 21.930                                 |
| Van           | 84,1              | 137                      | 3 / 134           | 112.326               | Erciş 39.772, Edremit 22.102                                         |
| Elazığ        | 77,0              | 92                       | 21 / 71           | 99.006                | Merkez 76.560                                                        |
| Aksaray       | 67,3              | 117                      | 24 / 93           | 97.102                | Merkez 53.878, Eskil 11.259                                          |
| Yozgat        | 71,0              | 82                       | 19 / 63           | 86.231                | Merkez 35.416, Sorgun 19.536                                         |
| Ağrı          | 72,2              | 104                      | 58 / 46           | 84.811                | Doğubayazıt 44.675, Patnos 22.048                                    |
| Niğde         | 73,4              | 58                       | 2 / 56            | 53.487                | Merkez 25.540, Bor 18.422                                            |
| Siirt         | 73,6              | 50                       | 26 / 24           | 53.344                | Merkez 25.370, Kurtalan 16.420                                       |
| Iğdır         | 68,6              | 42                       | 28 / 14           | 41.357                | Merkez 36.397                                                        |

#### Neden bu iller?

- Fark, sınırların kaynağından gelir. Kapsamı yüksek illerde sınırlar belediye açık verisinden geliyor (2023 oy payıyla Ankara %98 ve İzmir %92 ttezer kaynaklı, Bursa %100 belediye verisi). Zayıf illerde yalnız TKGM ve OSM var (Hatay TKGM %41 / OSM %59; Van %39 / %61; Ağrı %65 / %35; Aksaray %67 / %33).

- Depo notlarına göre TKGM kadastro mahalleleri bugünkü idari mahallelerle örtüşmüyor; şehir merkezlerindeki yeni mahallelerin hiçbir açık kaynakta sınırı yok. Hatay için OSM'de de sınır yok. Hatay, Van ve Kahramanmaraş için açık kamu kaynağı bulunamadı; TUCBS yalnız e-Devlet başvurusuyla veri veriyor; TKGM'nin boş döndürdüğü 2.768 birim yeniden sorulmuş, dolmamış.

- Mahalle adlarına tek tek inilip her eşleşmezliğin sebebi kontrol edilmedi. Depremin Hatay'daki muhtarlık yapısını etkilemiş olması denenmemiş bir varsayımdır.

#### Bölgesel okuma ve görsel çarpıklık riski

- Doğu ve Güneydoğu Anadolu'dan sayılan 23 ilin 16'sında (%70) kapsam %90'ın altında; diğer 58 ilde 22'sinde (%38). Ortalama kapsam %87,2'ye karşı %91,1 (bu bölge gruplaması rapora aittir).

- Buna karşılık %90 altı 38 ilin 22'si bu grubun dışındadır (Aksaray, Yozgat, Niğde, Tokat, Kırşehir, Nevşehir, Kütahya, Manisa gibi). Mekanizma coğrafya değil, belediye açık verisinin bulunup bulunmamasıdır.

- Merkez mahalleleri boş olan illerde mahalle haritasında görünen alan ağırlıkla köylerdir (örn. Iğdır'da eşleşmeyen seçmenin %88'i Merkez'de). Bu bir çıkarımdır, görsel olarak denenmemiştir. Haritada "boş = sınır yok, oy verisi var" notu ve il bazında kapsam yüzdesi bu riski azaltır.

#### Öncelik sırası

- YSK'dan muhtarlık ile mahalle kodu (MAKS) eşleştirmesi istenebilir; ad uyuşmazlığını kökten çözer (verip vermeyeceği doğrulanmadı).

- Hatay, Kahramanmaraş ve Van için TUCBS e-Devlet başvurusu (toplam yaklaşık 490 bin seçmen).

- Büyük boşluklu iller için belediyelere doğrudan başvuru (Manisa, Mersin, Adana, Diyarbakır, Samsun). Mutlak boşluk en büyük 12 ilin toplamı ülkedeki boşluğun %48'idir.

## 5. İl ve ilçe sınırları: bugünkü katman ve tarihsel türetme

### 5.1 Bugünkü ilçe ve il katmanı

973 ilçenin sınırı şu kaynaklardan oluşur: 803 ilçe OpenStreetMap (admin_level=6), 131 ilçe HDX COD-AB-TUR, 39 İstanbul ilçesi eski katmandan aynen korunmuştur. Kaynak seçimi, TKGM birimlerine yakınlığa göre ilçe ilçe yapılmıştır. İl sınırları ilçelerin birleşimidir.

| **Ölçü (TKGM ile karşılaştırma)** | **Değer**     |
|-----------------------------------|---------------|
| Karşılaştırılan ilçe              | 971           |
| Medyan IoU / ortalama IoU         | 0,886 / 0,852 |
| IoU ≥ 0,90 olan ilçe              | 421 (%43,4)   |
| IoU ≥ 0,80 olan ilçe              | 756 (%77,9)   |
| IoU \< 0,70 olan ilçe             | 99 (%10,2)    |

TKGM sınırlarını biz çizmedik, lisansı açık olmadığından yalnız hakem olarak kullandık. Düşük IoU her zaman bizim hatamız değildir: TKGM birimi ile idari ilçe sınırı farklı ayrıntıda çizilebilir.

### 5.2 Köy kırılımı ve yeni kurulan ilçeler: soy durumu

Seçimden sonra kurulan bir ilçenin alanı, kuruluşundan önceki seçimlerde başka bir ilçenin sonucunda gösterilmelidir. Bunun için ilçenin hangi eski ilçenin hangi köy/bucak/mahallelerinden kurulduğu bilinmelidir. Depo bu bilgiyi şu durumlarla kaydediyor (973 bugünkü ilçe):

| **Durum**               | **Anlamı**                                                                        | **İlçe** | **%** |
|-------------------------|-----------------------------------------------------------------------------------|----------|-------|
| 1950_oncesi_mevcut      | Kuruluşu 1950 öncesi; sorun yok (sınırı sonradan ayrılanlarla küçülmüş olabilir)  | 436      | 44,8  |
| repo_dogrulanmis        | Depoda kaynakla doğrulanmış birleşim poligonu var                                 | 78       | 8,0   |
| kanun_tek_kaynak        | Kanun ekine göre tüm birimler tek eski ilçeden; kuruluş öncesi o ilçeye katılıyor | 235      | 24,2  |
| merkez_ilce             | Sonradan il olan yerin merkez ilçesi                                              | 33       | 3,4   |
| kanun_cok_kaynak        | Birden çok eski ilçeden birim almış; köy düzeyinde bölüşüm çözülmedi              | 48       | 4,9   |
| kanun_dogrulanmadi      | Kanun listesi okundu ama güven orta (zayıf tarama)                                | 49       | 5,0   |
| kanun_kaynak_yazilmamis | Kanun ekinde birimlerin eski ilçesi yazılmamış                                    | 4        | 0,4   |
| unresolved              | 1950 sonrası kurulmuş, soy bilgisi henüz kaynaklanmadı                            | 90       | 9,2   |

**Köy düzeyi belirsizlik ölçüsü:** kanun_cok_kaynak + kanun_dogrulanmadi + kanun_kaynak_yazilmamis + unresolved = 191 ilçe (%19,6). Bu ilçelerde kuruluş öncesi seçimlerde alanın hangi eski ilçeye ait olduğu ya hiç ya da yalnızca kısmen biliniyor. Bu sayılar idari katman dosyasının kayıtlı durumudur; sonradan eklenen bazı birleşimler (district_splits.json: 75 ilde 919 kayıt) bu durum alanına tam yansımamış olabilir.

### 5.3 Seçim bazında türetilmiş poligon payı ve eşleme güveni

Sütunlar: ilçe satırlarından HIST/HISTK geometrili olanların sayısı ve geçerli oydaki payı; ardından 973 bugünkü ilçenin o seçimdeki birimle eşleme güveni (projenin kendi etiketleri). 1950–1957 genel seçimlerinde ilçe verisi olmadığından yer almaz.

| **Seçim**             | **İlçe satırı** | **Türetilmiş poligonlu satır** | **Türetilmiş oy payı %** | **Kesin** | **Yaklaşık** | **Kaba** | **Şüpheli** |
|-----------------------|-----------------|--------------------------------|--------------------------|-----------|--------------|----------|-------------|
| 1950 Yerel            | 496             | 178                            | (oy yok)                 | –         | –            | –        | –           |
| 1955 Yerel            | 547             | 172                            | (oy yok)                 | –         | –            | –        | –           |
| 1961 Genel            | 636             | 220                            | 53,8                     | 935       | 20           | 17       | 1           |
| 1961 Referandum       | 636             | 220                            | 53,7                     | 935       | 20           | 17       | 1           |
| 1963 Yerel            | 620             | 210                            | 66,7                     | 934       | 20           | 18       | 1           |
| 1965 Genel            | 637             | 220                            | 54,3                     | 935       | 20           | 17       | 1           |
| 1968 Yerel            | 619             | 210                            | 65,8                     | 934       | 20           | 19       | –           |
| 1969 Genel            | 638             | 219                            | 54,7                     | 937       | 20           | 16       | –           |
| 1973 Genel            | 638             | 219                            | 57,8                     | 937       | 20           | 16       | –           |
| 1973 Yerel            | 620             | 208                            | 66,4                     | 934       | 20           | 19       | –           |
| 1977 Genel            | 638             | 219                            | 59,1                     | 937       | 20           | 16       | –           |
| 1977 Yerel            | 621             | 209                            | 70,1                     | 936       | 20           | 17       | –           |
| 1982 Referandum       | 640             | 217                            | 62,1                     | 938       | 20           | 15       | –           |
| 1983 Genel            | 640             | 217                            | 61,9                     | 938       | 20           | 15       | –           |
| 1984 Yerel            | 644             | 213                            | 63,2                     | 938       | 19           | 16       | –           |
| 1987 Genel            | 646             | 217                            | 60,4                     | 943       | 14           | 16       | –           |
| 1987 Referandum       | 645             | 216                            | 60,1                     | 943       | 14           | 16       | –           |
| 1988 Referandum       | 674             | 203                            | 54,5                     | 943       | 15           | 15       | –           |
| 1989 Yerel            | 752             | 161                            | 50,1                     | 952       | 11           | 10       | –           |
| 1991 Genel            | 894             | 54                             | 27,6                     | 969       | –            | 4        | –           |
| 1994 Yerel            | 931             | 39                             | 23,9                     | 943       | –            | 4        | 26          |
| 1995 Genel            | 918             | 45                             | 25,1                     | 969       | –            | 4        | –           |
| 1999 Genel            | 921             | 43                             | 25,3                     | 969       | –            | 4        | –           |
| 1999 Yerel            | 943             | 31                             | 23,7                     | 942       | –            | 4        | 27          |
| 2002 Genel            | 923             | 42                             | 25,6                     | 969       | –            | 4        | –           |
| 2004 Yerel            | 945             | 30                             | 23,0                     | 942       | –            | 4        | 27          |
| 2007 Genel            | 923             | 42                             | 26,1                     | 969       | –            | 4        | –           |
| 2007 Referandum       | 923             | 41                             | 23,5                     | 966       | –            | 7        | –           |
| 2009 Yerel            | 981             | 17                             | 6,4                      | –         | –            | –        | –           |
| 2010 Referandum       | 981             | 17                             | 7,1                      | –         | –            | –        | –           |
| 2011 Genel            | 981             | 17                             | 7,1                      | –         | –            | –        | –           |
| 2014 Cumhurbaşkanlığı | 973             | 3                              | 0,4                      | –         | –            | –        | –           |
| 2014 Yerel            | 973             | 3                              | 0,3                      | –         | –            | –        | –           |
| 2015 Haziran Genel    | 973             | 3                              | 0,4                      | –         | –            | –        | –           |
| 2015 Kasım Genel      | 973             | 3                              | 0,4                      | –         | –            | –        | –           |
| 2017 Referandum       | 973             | 3                              | 0,4                      | –         | –            | –        | –           |
| 2018 Genel            | 973             | 1                              | 0,1                      | –         | –            | –        | –           |
| 2018 Cumhurbaşkanlığı | 973             | 1                              | 0,1                      | –         | –            | –        | –           |

## 6. Güvenilirlik özeti: seçim bazında notlar

Notlar 2. bölümdeki kurallardan türetilmiştir. Kolonlardaki sayılar notun dayanağıdır. "Teyitsiz %" ilçe (ilçe yoksa il) kayıtlarına aittir.

| **Seçim**                    | **Oy güveni** | **Sınır güveni** | **Teyitsiz %** | **Türetilmiş oy payı %** | **Kapsam %** | **Not**           |
|------------------------------|---------------|------------------|----------------|--------------------------|--------------|-------------------|
| 1950 Genel                   | Yüksek        | –                | 0,0            | –                        | –            | Yalnız il verisi. |
| 1950 Yerel                   | Düşük         | Orta             | 100,0          | (178 satır)              | –            | Yalnız kazanan.   |
| 1954 Genel                   | Yüksek        | –                | 0,0            | –                        | –            | Yalnız il verisi. |
| 1955 Yerel                   | Düşük         | Orta             | 100,0          | (172 satır)              | –            | Yalnız kazanan.   |
| 1957 Genel                   | Yüksek        | –                | 0,0            | –                        | –            | Yalnız il verisi. |
| 1961 Genel                   | Yüksek        | Orta             | 0,0            | 53,8                     | –            |                   |
| 1961 Referandum              | Yüksek        | Orta             | 0,0            | 53,7                     | –            |                   |
| 1963 Yerel                   | Düşük         | Orta             | 67,3           | 66,7                     | –            |                   |
| 1965 Genel                   | Yüksek        | Orta             | 0,0            | 54,3                     | –            |                   |
| 1968 Yerel                   | Orta          | Orta             | 3,2            | 65,8                     | –            |                   |
| 1969 Genel                   | Yüksek        | Orta             | 0,0            | 54,7                     | –            |                   |
| 1973 Genel                   | Yüksek        | Orta             | 0,0            | 57,8                     | –            |                   |
| 1973 Yerel                   | Orta          | Orta             | 5,8            | 66,4                     | –            |                   |
| 1977 Genel                   | Yüksek        | Orta             | 0,0            | 59,1                     | –            |                   |
| 1977 Yerel                   | Yüksek        | Orta             | 1,9            | 70,1                     | –            |                   |
| 1982 Referandum              | Yüksek        | Orta             | 0,0            | 62,1                     | –            |                   |
| 1983 Genel                   | Yüksek        | Orta             | 0,0            | 61,9                     | –            |                   |
| 1984 Yerel                   | Orta          | Orta             | 11,6           | 63,2                     | –            |                   |
| 1987 Genel                   | Yüksek        | Orta             | 0,0            | 60,4                     | –            |                   |
| 1987 Referandum              | Yüksek        | Orta             | 0,0            | 60,1                     | –            |                   |
| 1988 Referandum              | Yüksek        | Orta             | 0,0            | 54,5                     | –            |                   |
| 1989 Yerel                   | Yüksek        | Orta             | 0,1            | 50,1                     | –            |                   |
| 1991 Genel                   | Yüksek        | Orta             | 0,0            | 27,6                     | –            |                   |
| 1994 Yerel                   | Yüksek        | Orta             | 0,1            | 23,9                     | –            |                   |
| 1995 Genel                   | Yüksek        | Orta             | 0,0            | 25,1                     | –            |                   |
| 1999 Genel                   | Yüksek        | Orta             | 0,0            | 25,3                     | –            |                   |
| 1999 Yerel                   | Yüksek        | Orta             | 1,1            | 23,7                     | –            |                   |
| 2002 Genel                   | Yüksek        | Orta             | 0,0            | 25,6                     | –            |                   |
| 2004 Yerel                   | Yüksek        | Orta             | 0,0            | 23,0                     | –            |                   |
| 2007 Genel                   | Yüksek        | Orta             | 0,0            | 26,1                     | –            |                   |
| 2007 Referandum              | Yüksek        | Orta             | 0,0            | 23,5                     | –            |                   |
| 2009 Yerel                   | Yüksek        | Orta             | 0,7            | 6,4                      | 87,5         |                   |
| 2010 Referandum              | Yüksek        | Orta             | 0,0            | 7,1                      | 88,9         |                   |
| 2011 Genel                   | Yüksek        | Orta             | 0,0            | 7,1                      | 89,0         |                   |
| 2014 Cumhurbaşkanlığı        | Yüksek        | Yüksek           | 0,0            | 0,4                      | 94,3         |                   |
| 2014 Yerel                   | Yüksek        | Yüksek           | 0,0            | 0,3                      | 94,2         |                   |
| 2015 Haziran Genel           | Yüksek        | Yüksek           | 0,0            | 0,4                      | 94,3         |                   |
| 2015 Kasım Genel             | Yüksek        | Yüksek           | 0,0            | 0,4                      | 94,3         |                   |
| 2017 Referandum              | Yüksek        | Yüksek           | 0,0            | 0,4                      | 94,3         |                   |
| 2018 Genel                   | Yüksek        | Yüksek           | 0,0            | 0,1                      | 94,3         |                   |
| 2018 Cumhurbaşkanlığı        | Yüksek        | Yüksek           | 0,0            | 0,1                      | 94,3         |                   |
| 2019 Yerel                   | Yüksek        | Yüksek           | 0,2            | –                        | 94,6         |                   |
| 2023 Genel                   | Yüksek        | Yüksek           | 0,0            | –                        | 94,6         |                   |
| 2023 Cumhurbaşkanlığı 1. tur | Yüksek        | Yüksek           | 0,0            | –                        | 94,6         |                   |
| 2023 Cumhurbaşkanlığı 2. tur | Yüksek        | Yüksek           | 0,0            | –                        | 94,6         |                   |
| 2024 Yerel                   | Orta          | Yüksek           | 2,8            | –                        | 94,9         |                   |

Dağılım: oy güveni Yüksek 39, Orta 4, Düşük 3 seçim; sınır güveni Yüksek 12, Orta 31, Düşük 0 seçim (3 seçimde ilçe verisi olmadığından not verilmedi).

### 6.1 Dahili tutarlılık denetimi (il ve ilçe düzeyi)

Projenin denetim betiğinin kayıtlı bulguları (docs/rapor/veri_denetimi); mahalle düzeyindeki bulgular çok kalabalık olduğundan yalnız il ve ilçe sayıları verilmiştir. Bu bulgular veri tutarlılığına (kaynak tabloların iç uyumu, "Diğer" ve bağımsız toplamları, seçmen kütüğü farkları) ilişkindir; seçim sonuçlarının doğruluğu hakkında bir yargı içermez ve nedenleri tek tek araştırılmamıştır.

| **Bulgu türü**                                   | **İl** | **İlçe** | **Diğer birimler (belde/meclis birimi/TÜİK)** |
|--------------------------------------------------|--------|----------|-----------------------------------------------|
| İl toplamı ilçelerin toplamını tutmuyor          | 53     | 0        | 0                                             |
| Yazılı oran, oy sayısından hesaplananla tutmuyor | 180    | 10       | 0                                             |
| Parti oyları toplamı geçerli oyu tutmuyor        | 323    | 541      | 2.664                                         |
| Geçerli oy kayıtlı seçmenden fazla               | 1      | 95       | 216                                           |
| Seçmen sayısı yok, oy var                        | 57     | 212      | 253                                           |
| Kazanan en çok oy alan değil                     | 26     | 53       | 0                                             |
| Kazanan "Diğer"                                  | 0      | 10       | 0                                             |

Dikkat: bu CSV'lerdeki toplam bulgu sayıları, projenin 21 Ekim tarihli yönetim raporundaki sayılardan (ör. katılım %100 üstü 8.067 kayıt) çok farklıdır; CSV'ler sonradan yeniden üretilmiş görünüyor. Burada CSV'lerin güncel hali esas alındı.

## 7. Eksikler ve kime sorulabilir

Aşağıdaki tablo depoda belgelenmiş eksikleri ve ölçülen büyüklüklerini listeler. "Muhtemel muhatap" sütunu bu raporun önerisidir; kurumların ilgili veriyi gerçekten verip vermediği doğrulanmadı.

| **Eksik**                                              | **Depodaki dayanak ve büyüklük**                                                                                                                                                          | **Muhtemel muhatap (öneri)**                                                                       |
|--------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| 1950, 1954, 1957 genel seçim ilçe sonuçları            | İlçe verisi hiç yok (478/506/560 ilçe). Depodaki araştırma kaydına göre kaynak araması kapatıldı.                                                                                         | YSK arşivi, TÜİK kütüphanesi (DİE yayınları), Cumhuriyet Arşivi                                    |
| 1950–1977 yerel seçim ilçe ve meclis sonuçları         | 1950 ve 1955 yerel ilçe satırlarında yalnız kazanan parti (1.038 satır); 1950/1955 belediye meclisi ve il genel meclisi sonuçları araştırılmadı.                                          | TÜİK/DİE yayınları, Cumhuriyet Arşivi, YSK                                                         |
| 1991–2007 genel seçim ilçe sonuçları                   | Resmî ilçe arşivi bulunamadı; taban GitHub kaynağı (mertnuhoglu) TÜİK ile satır satır karşılaştırıldı, ana risk düşük.                                                                    | YSK (ilçe bazlı arşiv var mı?), TÜİK                                                               |
| Mahalle/köy sınırı bağlanamayan seçmen                 | 2023'te ilçe seçmeninin %5,4 kadarı (3.264.996 seçmen); 38 ilde kapsam %90'ın altı. Sebep: muhtarlık adı ile TKGM/OSM birim adının eşleşmemesi.                                           | YSK (muhtarlık ile adres/MAKS mahalle kodu eşleştirmesi), TKGM (TUCBS erişimi), ilgili belediyeler |
| Hatay ve Van sınırları                                 | Depo notuna göre TUCBS e-Devlet başvurusu yapılmadı (bkz. 4.4). 2023 kapsamı Hatay %76,5, Van %84,1.                                                                                      | TKGM (TUCBS)                                                                                       |
| Gaziantep belediye sınırları                           | Belediye veri kaynağına bağlanırken SSL hatası alındı (depo notu).                                                                                                                        | Gaziantep Büyükşehir Belediyesi                                                                    |
| İstanbul: Arnavutköy, Başakşehir, Esenyurt, Sultangazi | Kuruluş öncesi mahalle soyu birincil kaynakla çözülemedi; Sultangazi'de Esenler kaynaklı bir parsel parçası (Habipler) parsel/kadastro verisi olmadan çözülemiyor.                        | İstanbul Büyükşehir ve ilçe belediyeleri, TKGM (parsel), İçişleri Bakanlığı                        |
| 13 ilde 1994–2004 yerel için bölünmüş merkez ilçeler   | Samsun, Eskişehir, Antalya vb.: HIST-Merkez poligonu var ama yerel 1994–2004'e güvenle genişletilemedi (depo notu, 2026-09-24).                                                           | İçişleri Bakanlığı, ilgili belediyeler (mahalle listeleri)                                         |
| Soyu çözülmemiş 191 ilçe                               | 90 ilçede soy bilgisi yok, 48 ilçede birden çok eski ilçeden pay alınmış ama köy bölüşümü bilinmiyor, 49 ilçede kanun listesi zayıf taranmış, 4 ilçede kanun ekinde eski ilçe yazılmamış. | Resmî Gazete (orijinal tarama), TBMM mevzuat arşivi, İçişleri Bakanlığı (kuruluş listeleri)        |
| İl toplamı ilçe toplamını tutmayan 53 kayıt            | TÜİK il satırı kendi ilçe satırlarını tutmuyor (kaynağın kendisinde); 1965–2002 genel ve 1987–1988 referandum.                                                                            | TÜİK                                                                                               |
| Katılımı %100'ü aşan mahalleler                        | Kaynak veride bazı mahallelerde seçmen sayısı ile oy kullanan sayısı tutarsız görünüyor; sebebi depoda doğrulanmadı, kaynağın açıklaması istenebilir.                                     | YSK                                                                                                |
| Sakarya 1950–1961 (YSK arşivi)                         | YSK arşivinde Sakarya yok; veri eski Vikipedi kaynağında kaldı, 1957/1961 il toplamı bu yüzden eksik.                                                                                     | YSK                                                                                                |

## 8. Sınırlamalar

- YSK açık veri API'sine bu ortamdan erişilemediği için hiçbir sayı canlı YSK verisiyle yeniden karşılaştırılmadı; ölçülen, depodaki verinin kendi etiketleri ve iç tutarlılığıdır.

- Depo shallow klonlandı (commit geçmişi yok); "ne zaman eklendi" bilgisi yalnız PROVENANCE belgelerinden alınabilir.

- Satır düzeyinde kaynak etiketi olmayan kayıtlarda (özellikle 2009 sonrası YSK seçimleri) kaynak, sources.yml'deki seçim düzeyi tanımdan varsayıldı.

- "Eşleme güveni" ve "soy durumu" etiketleri projenin kendi değerlendirmesidir; bağımsız doğrulama yapılmadı.

- Mahalle eşleştirme tablosu (4.2) betiğin raporladığı muhtarlıkları kapsar; ttezer kaynaklı illerin eşleşme durumu bu tabloda yoktur. Tüm ülke kapsamı için 4.3'teki seçmen kapsamı esas alınmalıdır.

- Güven notlarının eşikleri keyfî seçilmiştir; farklı eşiklerle notlar değişebilir. Notlar doğruluk yüzdesi değildir.

- Bu rapor depoda hiçbir dosyayı değiştirmedi.

## Ek: İl bazında özet

Sütunlar: ilçe sayısı (bugünkü); kuruluş öncesi sınır soyu çözülmemiş/belirsiz ilçe sayısı (5.2'deki dört durumun toplamı); 2009, 2023 ve 2024 seçimlerinde ilçe seçmeninin mahalle/köy poligonuna bağlanan payı; 1999 yerel seçimde ilçe satırı Vikipedi etiketli olan ilçe sayısı.

| **Plaka** | **İl**         | **İlçe** | **Soy belirsiz ilçe** | **2009 kapsam %** | **2023 kapsam %** | **2024 kapsam %** | **1999 yerel Vikipedi ilçe** |
|-----------|----------------|----------|-----------------------|-------------------|-------------------|-------------------|------------------------------|
| 1         | Adana          | 15       | 5                     | 90,4              | 90,8              | 90,7              | 11                           |
| 2         | Adıyaman       | 9        | 4                     | 82,9              | 84,5              | 83,1              | 0                            |
| 3         | Afyonkarahisar | 18       | 5                     | 76,5              | 89,5              | 93,9              | 1                            |
| 4         | Ağrı           | 8        | 2                     | 66,1              | 72,2              | 64,4              | 0                            |
| 5         | Amasya         | 7        | 2                     | 87,8              | 94,8              | 94,4              | 0                            |
| 6         | Ankara         | 25       | 7                     | 94,1              | 100,0             | 100,0             | 16                           |
| 7         | Antalya        | 19       | 4                     | 84,3              | 98,8              | 98,8              | 14                           |
| 8         | Artvin         | 9        | 1                     | 87,0              | 93,6              | 90,4              | 1                            |
| 9         | Aydın          | 17       | 4                     | 77,7              | 96,9              | 97,0              | 0                            |
| 10        | Balıkesir      | 20       | 3                     | 84,5              | 99,9              | 99,9              | 0                            |
| 11        | Bilecik        | 8        | 1                     | 94,4              | 96,9              | 96,0              | 0                            |
| 12        | Bingöl         | 8        | 1                     | 88,7              | 89,5              | 86,2              | 0                            |
| 13        | Bitlis         | 7        | 1                     | 78,1              | 82,2              | 80,1              | 0                            |
| 14        | Bolu           | 9        | 1                     | 96,2              | 98,0              | 97,3              | 1                            |
| 15        | Burdur         | 11       | 4                     | 68,6              | 82,9              | 79,4              | 0                            |
| 16        | Bursa          | 17       | 1                     | 97,0              | 100,0             | 100,0             | 14                           |
| 17        | Çanakkale      | 12       | 0                     | 88,9              | 95,4              | 94,0              | 0                            |
| 18        | Çankırı        | 12       | 4                     | 73,8              | 84,2              | 81,9              | 0                            |
| 19        | Çorum          | 14       | 3                     | 81,5              | 89,1              | 87,2              | 0                            |
| 20        | Denizli        | 19       | 3                     | 81,6              | 99,6              | 99,6              | 0                            |
| 21        | Diyarbakır     | 17       | 5                     | 90,9              | 89,4              | 87,3              | 13                           |
| 22        | Edirne         | 9        | 2                     | 87,4              | 94,4              | 95,1              | 1                            |
| 23        | Elazığ         | 11       | 3                     | 75,3              | 77,0              | 72,1              | 0                            |
| 24        | Erzincan       | 9        | 1                     | 75,1              | 87,2              | 83,6              | 0                            |
| 25        | Erzurum        | 20       | 4                     | 47,2              | 95,3              | 95,3              | 16                           |
| 26        | Eskişehir      | 14       | 3                     | 90,4              | 91,9              | 91,9              | 12                           |
| 27        | Gaziantep      | 9        | 2                     | 94,8              | 100,0             | 100,0             | 7                            |
| 28        | Giresun        | 16       | 3                     | 90,9              | 94,3              | 93,9              | 0                            |
| 29        | Gümüşhane      | 6        | 1                     | 75,4              | 80,9              | 74,9              | 0                            |
| 30        | Hakkari        | 5        | 2                     | 83,5              | 85,9              | 85,6              | 0                            |
| 31        | Hatay          | 15       | 1                     | 44,8              | 76,5              | 76,2              | 1                            |
| 32        | Isparta        | 13       | 4                     | 77,5              | 88,6              | 86,9              | 0                            |
| 33        | Mersin         | 13       | 1                     | 81,8              | 88,6              | 88,6              | 9                            |
| 34        | İstanbul       | 39       | 8                     | 99,4              | 99,8              | 99,9              | 6                            |
| 35        | İzmir          | 30       | 3                     | 98,1              | 100,0             | 100,0             | 19                           |
| 36        | Kars           | 8        | 3                     | 87,2              | 94,3              | 91,6              | 0                            |
| 37        | Kastamonu      | 20       | 6                     | 90,1              | 93,5              | 90,9              | 0                            |
| 38        | Kayseri        | 16       | 5                     | 82,4              | 97,5              | 99,0              | 14                           |
| 39        | Kırklareli     | 8        | 3                     | 89,7              | 95,7              | 97,2              | 0                            |
| 40        | Kırşehir       | 7        | 1                     | 67,5              | 78,2              | 74,6              | 0                            |
| 41        | Kocaeli        | 12       | 1                     | 94,4              | 99,3              | 99,3              | 5                            |
| 42        | Konya          | 31       | 5                     | 72,5              | 95,5              | 99,7              | 27                           |
| 43        | Kütahya        | 13       | 2                     | 68,2              | 77,3              | 71,9              | 0                            |
| 44        | Malatya        | 13       | 1                     | 80,5              | 99,9              | 99,8              | 1                            |
| 45        | Manisa         | 17       | 4                     | 69,2              | 85,8              | 85,7              | 0                            |
| 46        | Kahramanmaraş  | 11       | 1                     | 65,6              | 83,1              | 82,2              | 0                            |
| 47        | Mardin         | 10       | 3                     | 73,8              | 89,2              | 89,0              | 0                            |
| 48        | Muğla          | 13       | 1                     | 62,0              | 95,9              | 95,9              | 0                            |
| 49        | Muş            | 6        | 0                     | 58,9              | 80,4              | 69,7              | 0                            |
| 50        | Nevşehir       | 8        | 2                     | 67,1              | 81,0              | 76,7              | 0                            |
| 51        | Niğde          | 6        | 0                     | 56,2              | 73,4              | 73,6              | 0                            |
| 52        | Ordu           | 19       | 8                     | 84,3              | 99,9              | 99,9              | 0                            |
| 53        | Rize           | 12       | 3                     | 88,4              | 95,4              | 93,7              | 0                            |
| 54        | Sakarya        | 16       | 2                     | 95,6              | 99,1              | 99,1              | 0                            |
| 55        | Samsun         | 17       | 2                     | 84,2              | 89,9              | 89,9              | 13                           |
| 56        | Siirt          | 7        | 0                     | 71,2              | 73,6              | 65,8              | 1                            |
| 57        | Sinop          | 9        | 3                     | 90,3              | 93,6              | 92,7              | 0                            |
| 58        | Sivas          | 17       | 2                     | 94,6              | 96,3              | 97,4              | 0                            |
| 59        | Tekirdağ       | 11       | 3                     | 82,8              | 100,0             | 100,0             | 1                            |
| 60        | Tokat          | 12       | 3                     | 65,7              | 76,7              | 74,6              | 0                            |
| 61        | Trabzon        | 18       | 4                     | 79,9              | 99,8              | 99,8              | 0                            |
| 62        | Tunceli        | 8        | 0                     | 80,4              | 87,3              | 80,4              | 0                            |
| 63        | Şanlıurfa      | 13       | 1                     | 92,0              | 97,9              | 97,8              | 0                            |
| 64        | Uşak           | 6        | 4                     | 93,2              | 97,8              | 97,9              | 0                            |
| 65        | Van            | 13       | 2                     | 74,4              | 84,1              | 84,2              | 0                            |
| 66        | Yozgat         | 14       | 2                     | 64,8              | 71,0              | 64,8              | 0                            |
| 67        | Zonguldak      | 8        | 0                     | 81,8              | 93,5              | 93,0              | 0                            |
| 68        | Aksaray        | 8        | 3                     | 51,4              | 67,3              | 61,9              | 0                            |
| 69        | Bayburt        | 3        | 1                     | 80,0              | 93,1              | 91,0              | 0                            |
| 70        | Karaman        | 6        | 0                     | 82,3              | 84,3              | 80,1              | 0                            |
| 71        | Kırıkkale      | 9        | 2                     | 86,8              | 92,7              | 93,6              | 0                            |
| 72        | Batman         | 6        | 0                     | 95,4              | 93,6              | 96,2              | 0                            |
| 73        | Şırnak         | 7        | 2                     | 88,2              | 88,2              | 89,3              | 0                            |
| 74        | Bartın         | 4        | 1                     | 79,2              | 89,8              | 82,3              | 0                            |
| 75        | Ardahan        | 6        | 1                     | 71,5              | 87,8              | 74,6              | 0                            |
| 76        | Iğdır          | 4        | 1                     | 59,9              | 68,6              | 63,2              | 0                            |
| 77        | Yalova         | 6        | 0                     | 83,6              | 86,6              | 98,1              | 0                            |
| 78        | Karabük        | 6        | 2                     | 92,1              | 89,2              | 87,3              | 0                            |
| 79        | Kilis          | 4        | 0                     | 94,1              | 97,4              | 96,9              | 0                            |
| 80        | Osmaniye       | 7        | 1                     | 88,8              | 90,1              | 88,7              | 0                            |
| 81        | Düzce          | 8        | 1                     | 94,4              | 97,1              | 96,5              | 0                            |
