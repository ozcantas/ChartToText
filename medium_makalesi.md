# Grafik Görsellerinden Tablo Çıkarımı: DePlot ve Qwen2-VL Modellerinde LoRA ile Fine-Tuning Deneyimi

**Önceden eğitilmiş görme modellerini grafik okuma görevine uyarlamak: Fine-tuning nedir, PEFT/LoRA nasıl çalışır ve Statista veri seti üzerinde modellerimizi nasıl eğittik?**

---

## 1. Projenin Amacı Nedir?

Bu projenin tek ve net bir hedefi vardır: **Görsel formatındaki grafikleri (çubuk, çizgi, pasta vb.) analiz ederek doğrudan satır ve sütunlardan oluşan yapılandırılmış tablo formatına (Markdown, CSV, Excel) dönüştürmek.**

Grafikler görsel olarak insan gözü için tasarlanmıştır; ancak bu verilerin analiz edilmesi, veri tabanlarına kaydedilmesi veya hesaplamalara dahil edilebilmesi için ham sayısal tabloya dönüştürülmesi gerekir. Bu çalışmada, grafik görsellerini girdi olarak alıp altta yatan veri tablosunu çıktı olarak üreten uçtan uca bir yapay zeka sistemi kurduk.

---

## 2. Fine-Tuning (İnce Ayar) Nedir?

Büyük yapay zeka modelleri (Foundation Models) internetteki milyarlarca genel metin ve görsel verisiyle eğitilir. Bu modeller genel dünyayı, dilleri ve nesneleri tanır; ancak belirli bir niş görevde (örneğin bir grafikteki eksen koordinatını okuyup tablo matrisi üretmek) doğrudan en yüksek başarıyı gösteremezler.

**Fine-Tuning (İnce Ayar)**; genel amaçlı önceden eğitilmiş (pre-trained) bir temel modelin ağırlıklarını, belirli bir alana ait özel bir veri kümesi (bizim durumumuzda grafik-tablo çiftleri) ile yeniden eğiterek o görevde uzmanlaştırma işlemidir.

---

## 3. Neden LoRA (Parameter-Efficient Fine-Tuning) Kullandık?

Geleneksel ince ayarda (Full Fine-Tuning), modelin sahip olduğu yüz milyonlarca veya milyarlarca parametrenin tamamı güncellenir. Bu yöntem:
* Çok yüksek GPU belleği (VRAM) ve donanım gücü gerektirir.
* Modelin bildiği genel yetenekleri unutmasına (*catastrophic forgetting*) yol açabilir.
* Her ince ayar için modelin tamamını (gigabaytlarca) diskte saklamayı gerektirir.

Bu kısıtları aşmak için **PEFT (Parameter-Efficient Fine-Tuning)** yöntemlerinden biri olan **LoRA (Low-Rank Adaptation)** mimarisini kullandık.

### LoRA Nasıl Çalışır?
LoRA, orijinal modelin milyarlarca parametrelik devasa matrislerini dondurur (freeze eder) ve bunların yanına çok küçük, düşük dereceli (low-rank) iki küçük matris ekler ($A$ ve $B$ matrisleri). Eğitim sırasında sadece bu minik adaptör matrisleri öğrenir.

Projemizde elde ettiğimiz parametre verimliliği şu şekildedir:
* **Google DePlot:** 285 Milyon toplam parametrenin yalnızca **3.5 Milyonu (%1.24)** eğitildi.
* **Qwen2-VL-2B:** 2.2 Milyar toplam parametrenin yalnızca **4.3 Milyonu (%0.20)** eğitildi.

Bu sayede tüm modeli baştan eğitmek yerine sadece **7 MB ile 17 MB** boyutunda küçük adaptör dosyaları üreterek aynı başarıyı sağladık.

---

## 4. Projede Ne Yaptık? (Eğitim Adımları ve Parametreler)

Projemizde grafik okuma alanında iki farklı mimariyi ele aldık:
1. **Google DePlot (282M):** Pix2Struct tabanlı, doğrudan görseli tablo metnine çevirmeye odaklı kompakt encoder-decoder modeli.
2. **Alibaba Qwen2-VL-2B (2.2B):** Yeni nesil çok modlu (Vision-Language) model.

### Eğitim Veri Seti
Modellerimizi, akademik alanda standart kabul edilen **Statista Chart-to-Text** veri kümesi (farklı tiplerdeki binlerce grafik ve bunlara karşılık gelen zemin doğruluk / ground-truth tabloları) üzerinde eğittik.

### LoRA Hiperparametreleri
* **LoRA Rank ($r$):** `16` (Düşük dereceli matrisin boyutu; temsil gücü ile hız dengesi)
* **LoRA Alpha ($\alpha$):** `32` (Öğrenilen ağırlıkların ana modele etki ölçeği)
* **LoRA Dropout:** `0.05` (Aşırı uyumu / ezberlemeyi önleyici regülarizasyon)
* **Hedef Modüller:** Transformer dikkat katmanlarındaki `query` ve `value` projeksiyonları
* **Öğrenme Oranı (Learning Rate):** `5e-5` (Ağırlıkların sarsılmadan kararlı öğrenmesi için düşük adım boyutu)
* **Epoch Sayısı:** `4` Epoch

---

## 5. Eğitim Dinamikleri ve Kayıp (Loss) Analizi

Modelin öğrenme sürecini adım ve epoch bazında takip ettiğimizde:
* **Başlangıç:** Eğitim kaybı (loss) ilk adımlarda `30+` seviyelerindeyken, modelin grafik şablonuna hızla uyum sağlamasıyla ilk 200 adımda `~5.0` bandına geriledi.
* **Epoch Bazlı Gelişim:**
  * Epoch 1: `5.90`
  * Epoch 2: `4.49`
  * Epoch 3: `4.42`
  * Epoch 4: `4.40`
* **Sonuç:** Kaybın 2. epoch'tan itibaren 4.4 bandında plato çizmesi, modelin aşırı ezberleme (overfitting) yapmadan verimli ve dengeli bir şekilde genelleme kabiliyeti kazandığını kanıtladı.

---

## 6. Elde Ettiğimiz Değerlendirme Sonuçları

Eğitilen modelleri 300 test grafiği üzerinde temel (ham) modellerle kıyasladığımızda şu somut sonuçlara ulaştık:

### 1. Sayısal Hata Düşüşü (MAE ve RMSE)

| Model Konfigürasyonu | MAE (Ortalama Mutlak Hata) $\downarrow$ | RMSE (Kök Ortalama Kare Hata) $\downarrow$ |
| :--- | :---: | :---: |
| **DePlot (Ham / Baseline)** | 664.53 | 30,868.62 |
| **DePlot (LoRA İnce Ayarlı)** | **459.25** *(-%30.9 Düşüş)* | **13,924.31** *(-%54.9 Düşüş)* |
| **Qwen2-VL-2B (LoRA İnce Ayarlı)** | 482.64 | **5,258.28** *(Outlier Lideri)* |

* **MAE (Ortalama Mutlak Hata):** DePlot LoRA, 664'ten **459'a** inerek ortalama sayısal değer çıkarmada %31 iyileşme gösterdi.
* **RMSE ve Aykırı Değerler:** DePlot ham haliyle bazı grafiklerde büyük sapmalar yaparken, LoRA ince ayarı bunu yarıdan fazla düşürdü. Ancak asıl sürprizi **Qwen2-VL** yaptı; **5,258 RMSE** ile aykırı değerleri filtrelemede sınıf lideri olduğunu ve saçmalamadığını gösterdi.
* **MedAE = 0.0:** Her iki ince ayarlı modelde de medyan mutlak hata sıfır çıktı. Yani tipik grafiklerin büyük çoğunluğunda sayılar tam isabetle yakalandı.

### 2. Tablo Formatını ve Hücreleri Koruma Oranı
Bir grafik modelinin sadece sayıları doğru bilmesi yetmez; kaç satır ve kaç sütun olduğunu da doğru kurması gerekir:
* **Ham DePlot:** %56.7 Hücre Eşleşmesi (4,440 / 7,826 hücre)
* **İnce Ayarlı DePlot LoRA:** **%69.0 Hücre Eşleşmesi** (5,401 / 7,826 hücre)
* İnce ayar sayesinde model, doğru formatta **yaklaşık 1,000 ek hücreyi** daha eksiksiz üretmeyi başardı.

---

## 7. Donanım Optimizasyonu: 4-bit (NF4) Nicelleştirme

2.2 Milyar parametreli Qwen2-VL modelini 4 GB VRAM'e sahip mütevazı bir GPU'da (RTX 3050 Laptop) çalıştırabilmek için modeli **BitsAndBytes 4-bit (NF4)** formatında yükledik. 

Bu optimizasyon sayesinde modelin VRAM tüketimi **1.46 GB** seviyesine indi ve yerel bir bilgisayarda donanım sınırlarına takılmadan akıcı bir şekilde çıkarım yapabilir hale geldi.

---

## 8. Özet

Bu çalışmada:
1. Görsel grafikleri tabloya çevirme görevine odaklandık.
2. Google DePlot ve Qwen2-VL modellerine PEFT/LoRA yöntemiyle parametrelerinin %1'inden azını güncelleyerek ince ayar uyguladık.
3. LoRA ince ayarı ile sayısal hatada (MAE/RMSE) %30 ila %55 arasında belirgin bir iyileşme sağladık ve yapısal hücre koruma oranını %56.7'den %69.0'a çıkardık.
4. Modelleri 4-bit nicelleştirerek standart tüketici donanımlarında yerel olarak çalıştırılabilir hale getirdik.
