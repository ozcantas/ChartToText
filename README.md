# ChartToText 📊 ➡️ 📋

> **Görsel Grafikleri Yapay Zeka ile Canlı Tablolara Dönüştürme Platformu**

ChartToText; PDF'lerde, raporlarda, haberlerde veya web sitelerinde yer alan statik grafik görsellerini (çubuk, çizgi, pasta vb.) gelişmiş Vision-Language yapay zeka modelleriyle okuyup doğrudan **Excel (.xlsx)**, **CSV** ve **JSON** tablo formatlarına dönüştüren yerel bir masaüstü/web uygulamasıdır.

---

## 🌟 Öne Çıkan Özellikler

* **Çoklu Model Desteği:** 
  * **Google DePlot (LoRA v2):** Standart, tek serili çubuk ve çizgi grafiklerinde yüksek sayısal hassasiyet (MAE: 459.25).
  * **Qwen2-VL-2B (LoRA & 4-bit):** Çok serili, yoğun etiketli ve karmaşık grafiklerde üstün bağlamsal kavrama ve aykırı değer direnci (RMSE: 5,258.28).
  * **Orijinal (Ham) Modeller:** LoRA adaptörlerini kapatıp (`disable_adapter`) temel modellerle kıyaslama yapabilme.
* **Düşük VRAM Tüketimi (~1.5 GB):** 4-bit (NF4) nicelleştirme sayesinde 4 GB VRAM'e sahip dizüstü GPU'larda (NVIDIA RTX 3050 vb.) akıcı çalışır.
* **%100 Yerel ve Güvenli:** Verileriniz hiçbir dış sunucuya veya bulut API'ına gönderilmez.
* **Türkçe Excel Uyumu:** Sütunların tek hücreye sıkışmasını önleyen noktalı virgüllü (`;`) UTF-8-BOM CSV ve yerel `.xlsx` dışa aktarımı.
* **Anında İptal Desteği (Cancellation):** Uzun süren çıkarımları tek tıkla arayüzden ve GPU belleğinden durdurabilme (`StoppingCriteria`).

---

## 🏗️ Mimari Yapı

```
grafik_okuyucu/
├── backend/
│   ├── config.py              # Model kayıtları ve donanım ayarları
│   ├── schemas.py             # Pydantic modelleri
│   ├── routers/
│   │   ├── predict_router.py  # Model çıkarım ve iptal uç noktaları
│   │   └── export_router.py   # Excel ve CSV dışa aktarım uç noktaları
│   └── services/
│       ├── model_service.py   # PyTorch / PEFT / 4-bit model yöneticisi
│       ├── parser_service.py  # Markdown / DePlot / Sözlük tablo ayrıştırıcısı
│       └── export_service.py  # openpyxl ve CSV üretim motoru
├── frontend/                  # React 19 + Tailwind CSS + Vite arayüzü
│   ├── src/
│   └── dist/                  # Derlenmiş statik üretim dosyaları
├── deplot_lora_finetuned_2/   # Fine-tune edilmiş DePlot LoRA adaptörü
├── qwen2_vl_lora_finetuned/   # Fine-tune edilmiş Qwen2-VL LoRA adaptörü
├── main.py                    # FastAPI uygulama sunucusu
├── baslat.bat                 # Tek tıkla yerel başlatıcı
└── requirements.txt           # Python bağımlılıkları
```

---

## 🚀 Hızlı Başlangıç

### 1. Gereksinimler
* Windows 10/11
* Python 3.10 veya 3.11
* NVIDIA GPU (Önerilen: 4 GB+ VRAM) veya CPU

### 2. Kurulum
```bash
# Repoyu klonlayın
git clone https://github.com/KULLANICI_ADINIZ/ChartToText.git
cd ChartToText

# Sanal ortam oluşturup aktif edin
python -m venv env
.\env\Scripts\activate

# Bağımlılıkları yükleyin
pip install -r requirements.txt
```

### 3. Çalıştırma
Uygulamayı tek komutla veya `baslat.bat` dosyasına çift tıklayarak başlatabilirsiniz:

```bash
.\baslat.bat
```

Sunucu hazır olduğunda varsayılan tarayıcınızda otomatik olarak açılacaktır:
👉 `http://127.0.0.1:8000`

---

## 📈 Değerlendirme Metrikleri

Statista Chart-to-Text test kümesi üzerinde elde edilen sonuçlar:

| Model | MAE (Ortalama Mutlak Hata) $\downarrow$ | RMSE (Aykırı Değer Hatası) $\downarrow$ | Yapısal Hücre Koruma $\uparrow$ |
| :--- | :---: | :---: | :---: |
| **DePlot (Baseline)** | 664.53 | 30,868.62 | %56.7 |
| **DePlot (LoRA v2)** | **459.25** *(-%31)* | 13,924.31 *(-%55)* | **%69.0** *(+%12.3)* |
| **Qwen2-VL-2B (LoRA)** | 482.64 | **5,258.28** *(Lider)* | **VLM Optimize** |

---

## 📄 Lisans
Bu proje açık kaynaklıdır ve MIT lisansı altında dağıtılmaktadır.
