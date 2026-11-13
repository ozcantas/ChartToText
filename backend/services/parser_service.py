import re
from typing import Dict, Any, List

def parse_asterisk_stream(text: str, fallback_title: str = "Başlık Tespit Edilemedi") -> Dict[str, Any]:
    """
    Qwen gibi modellerin pasta grafiklerde ürettiği satırsız ve '*' / '**' ile ayrılmış
    akış halindeki metinleri (Örn: * Title ** 37% ** coal ** ...) düzgün bir tabloya çevirir.
    """
    clean = text.replace("```", "").strip()
    parts = [p.strip() for p in clean.split("**") if p.strip()]

    title_parts = []
    data_parts = []
    found_data = False

    for p in parts:
        # Sayı veya yüzde tespiti (Örn: 37.4%, 50, 12.3 vb.)
        if re.search(r"^\d+(\.\d+)?%?$", p) or (re.search(r"\d+%", p) and len(p) < 12):
            found_data = True
        if not found_data:
            title_parts.append(p.lstrip("*").strip())
        else:
            data_parts.append(p.strip())

    title = " ".join(title_parts).strip() if title_parts else fallback_title
    title = re.sub(r"^[`*#\s]+", "", title).strip()
    if not title:
        title = fallback_title

    # data_parts içindeki çiftleri (Kategori, Değer) eşle
    rows = []
    i = 0
    while i < len(data_parts):
        if i + 1 < len(data_parts):
            item1 = data_parts[i]
            item2 = data_parts[i + 1]
            # Sayı olanı 2. sütuna al
            if re.search(r"\d", item1) and not re.search(r"\d", item2):
                rows.append([item2, item1])
            else:
                rows.append([item1, item2])
            i += 2
        else:
            item = data_parts[i]
            if re.search(r"\d", item):
                rows.append(["Diğer / Değer", item])
            else:
                rows.append([item, "-"])
            i += 1

    return {
        "title": title,
        "columns": ["Kategori", "Değer"],
        "rows": rows
    }

def parse_dict_structure(text: str) -> Dict[str, Any]:
    """
    DePlot / PlotQA modellerinin çok serili (grouped bar / multi-line) grafiklerde
    ürettiği iç içe geçmiş Python sözlüğü formatını (Örn: {'Coca Cola': {'Diet': [83, 69]...}})
    düzgün bir 2D matris tablosuna çevirir.
    """
    clean = text.strip()
    brand_matches = list(re.finditer(r"'([^']+)'\s*:\s*\{", clean))
    if not brand_matches:
        return None

    columns_set = []
    brand_data = {}

    for i, match in enumerate(brand_matches):
        brand_name = match.group(1).replace("\t", " ").strip()
        start = match.end()
        end = brand_matches[i+1].start() if i + 1 < len(brand_matches) else len(clean)
        block = clean[start:end]
        closing_idx = block.rfind("}")
        if closing_idx != -1:
            block = block[:closing_idx]

        brand_data[brand_name] = {}
        
        # Regex to find: 'Series Name': [vals]
        item_matches = list(re.finditer(r"(?:^|[\t,\}\s])'(.+?)':\s*\[([^\]]*)\]", block))
        if not item_matches:
            raw_entries = re.split(r"\]\s*[\t,]\s*'", block)
            for entry in raw_entries:
                p = entry.split("': [")
                if len(p) == 2:
                    s_name = p[0].lstrip("' \t").replace("\t", ", ").strip()
                    v_str = p[1].rstrip("]")
                    nums = re.findall(r"\d+(?:\.\d+)?%?", v_str)
                    val = " / ".join(nums) if nums else ""
                    if s_name not in columns_set:
                        columns_set.append(s_name)
                    brand_data[brand_name][s_name] = val
        else:
            for m in item_matches:
                s_name = m.group(1).replace("\t", ", ").strip()
                v_str = m.group(2)
                nums = re.findall(r"\d+(?:\.\d+)?%?", v_str)
                val = " / ".join(nums) if nums else ""
                if s_name not in columns_set:
                    columns_set.append(s_name)
                brand_data[brand_name][s_name] = val

    if not columns_set:
        return None

    headers = ["Kategori"] + columns_set
    rows = []
    for brand, s_dict in brand_data.items():
        row = [brand] + [s_dict.get(s, "") for s in columns_set]
        rows.append(row)

    return {
        "title": "Çok Serili Grafik Verisi",
        "columns": headers,
        "rows": rows
    }

def parse_deplot(text: str) -> Dict[str, Any]:
    """
    DePlot veya Qwen2-VL modellerinin ürettiği metinleri (TITLE, <0x0A>,
    Markdown '| col1 | col2 |', çok satırlı Title:, sözlük akışları veya Çince girişli tabloları)
    hatasız şekilde başlık, sütunlar ve satırlara dönüştürür.
    """
    # Özel Durum 1: Çok serili / iç içe Python sözlüğü formatı (DePlot / PlotQA çıktısı)
    if text.strip().startswith("{") and "': {" in text:
        dict_res = parse_dict_structure(text)
        if dict_res:
            return dict_res

    # Özel Durum 2: Metin '|' içermiyor ama yoğun '**' ayracı içeriyorsa (Qwen pasta grafik çıktısı)
    if text.count("|") < 2 and text.count("**") >= 4:
        return parse_asterisk_stream(text)

    # 1. <0x0A> ve satır sonlarını standart alt satıra çevir
    normalized = text.replace("<0x0A>", "\n").replace("\r\n", "\n")
    lines = [line.strip() for line in normalized.split("\n") if line.strip()]
    
    title = "Başlık Tespit Edilemedi"
    cleaned_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # 1. TITLE | ... formatı
        if "TITLE |" in line:
            title = line.split("TITLE |")[-1].strip()
            i += 1
            continue
            
        # 2. Çok satırlı 'Title:' veya 'Title' kontrolü (Örn: Qwen çıktısı)
        if line.lower() in ["title:", "title"]:
            if i + 1 < len(lines) and "|" not in lines[i + 1]:
                title = lines[i + 1].strip()
                i += 2
                continue
            else:
                i += 1
                continue
        elif line.lower().startswith("title:"):
            val = line.split(":", 1)[-1].strip()
            if val:
                title = val
            elif i + 1 < len(lines) and "|" not in lines[i + 1]:
                title = lines[i + 1].strip()
                i += 1
            i += 1
            continue

        # 3. Qwen'in eklediği Çince / İngilizce sohbet giriş cümlelerini filtrele
        if ("以下" in line or "数据表" in line or "here is" in line.lower() or "table:" in line.lower()) and "|" not in line:
            i += 1
            continue

        # 4. Markdown ayraç çizgilerini (|---|---|) atla
        if re.match(r"^\|?(\s*:?-+:?\s*\|?)+$", line):
            i += 1
            continue

        cleaned_lines.append(line)
        i += 1

    if not cleaned_lines:
        return {"title": title, "columns": [], "rows": []}

    def split_row(line_str: str) -> List[str]:
        s = line_str.strip()
        # Kenarlardaki dış '|' işaretlerini buda
        if s.startswith("|") and s.endswith("|") and len(s) > 1:
            s = s[1:-1]
        elif s.startswith("|"):
            s = s[1:]
        elif s.endswith("|"):
            s = s[:-1]

        if "|" in s:
            return [c.strip() for c in s.split("|")]
        elif "\t" in s:
            return [c.strip() for c in s.split("\t")]
        elif "," in s:
            return [c.strip() for c in s.split(",")]
        return [s.strip()]

    # Başlık ve tablo satırlarını birbirinden ayır
    # Gerçek tablo satırları mutlaka ayraç (| veya \t) içermelidir
    table_lines = []
    title_parts = [title] if title != "Başlık Tespit Edilemedi" else []

    for line in cleaned_lines:
        if "|" in line or "\t" in line:
            table_lines.append(line)
        else:
            # Tablo henüz başlamadıysa bu satır başlığın/alt başlığın devamıdır
            if not table_lines:
                if line not in title_parts:
                    title_parts.append(line)

    if title_parts:
        title = " - ".join(title_parts).strip()

    if not table_lines:
        return {"title": title, "columns": [], "rows": []}

    # İlk geçerli ayraçlı satır sütun başlıklarıdır
    raw_columns = split_row(table_lines[0])
    raw_columns = [c for c in raw_columns if c]
    num_cols = len(raw_columns)
    
    rows: List[List[str]] = []
    for line_str in table_lines[1:]:
        row = split_row(line_str)
        if not any(row):
            continue
            
        # DePlot'un döngüye girip ardışık aynı satırı üretmesini engelle (deduplicate)
        if rows and row == rows[-1]:
            continue

        # Sütun sayısını garantiye al
        if len(row) >= num_cols:
            rows.append(row[:num_cols])
        else:
            rows.append(row + [""] * (num_cols - len(row)))

    if not raw_columns and rows:
        num_cols = max(len(r) for r in rows)
        raw_columns = [f"Sütun {i+1}" for i in range(num_cols)]

    return {
        "title": title,
        "columns": raw_columns,
        "rows": rows
    }
