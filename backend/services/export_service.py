import io
import re
import urllib.parse
from typing import List, Tuple
import pandas as pd

def build_safe_dataframe(columns: List[str], rows: List[List[str]]) -> pd.DataFrame:
    """
    Sütun ve satır sayıları tam uyuşmasa bile hataya düşmeden
    güvenli bir pandas DataFrame oluşturur.
    """
    if not columns and not rows:
        return pd.DataFrame()
        
    num_cols = len(columns)
    if num_cols == 0 and rows:
        num_cols = max(len(r) for r in rows)
        columns = [f"Sütun {i+1}" for i in range(num_cols)]
        
    clean_rows = []
    for r in rows:
        if len(r) < num_cols:
            clean_rows.append(r + [""] * (num_cols - len(r)))
        else:
            clean_rows.append(r[:num_cols])
            
    return pd.DataFrame(clean_rows, columns=columns)

def generate_safe_filename(title: str, extension: str) -> str:
    """
    HTTP başlığı ve dosya sistemine uygun güvenli dosya adı üretir.
    """
    safe_title = re.sub(r'[\r\n\\/*?:"<>|]', "", title).strip()[:40] or "grafik_tablosu"
    return urllib.parse.quote(f"{safe_title}.{extension}")

def export_to_excel(columns: List[str], rows: List[List[str]], title: str) -> Tuple[io.BytesIO, str]:
    """
    Verileri in-memory .xlsx dosyasına dönüştürür.
    """
    df = build_safe_dataframe(columns, rows)
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False, engine="openpyxl")
    buffer.seek(0)
    encoded_name = generate_safe_filename(title, "xlsx")
    return buffer, encoded_name

def export_to_csv(columns: List[str], rows: List[List[str]], title: str) -> Tuple[io.BytesIO, str]:
    """
    Türkçe Excel uyumlu (noktalı virgül ve UTF-8-SIG) CSV üretir.
    """
    df = build_safe_dataframe(columns, rows)
    csv_data = df.to_csv(sep=";", index=False, encoding="utf-8-sig")
    buffer = io.BytesIO(csv_data.encode("utf-8-sig"))
    buffer.seek(0)
    encoded_name = generate_safe_filename(title, "csv")
    return buffer, encoded_name
