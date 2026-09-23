from __future__ import annotations
import io
from pathlib import Path
import pandas as pd

ALIASES = {"sku": ["sku", "1с", "код", "артикул", "номенклатура"], "unit": ["unit", "ед", "ед. изм", "единица"], "quantity": ["qty", "quantity", "количество", "кол-во", "продажи"], "date": ["date", "дата"], "free_stock": ["free stock", "свободный остаток", "остаток"], "eta": ["eta", "дата поставки", "дата прихода"], "inbound_qty": ["inbound", "в пути", "количество в пути"], "moq": ["moq", "минимальный заказ"], "pack_multiple": ["кратность", "pack multiple"]}

def load_table(source: str | Path | bytes, sheet_name: str | int = 0) -> pd.DataFrame:
    if isinstance(source, bytes):
        return pd.read_excel(io.BytesIO(source), sheet_name=sheet_name, dtype=str)
    path = Path(source)
    if path.suffix.lower() == ".csv": return pd.read_csv(path, dtype=str)
    return pd.read_excel(path, sheet_name=sheet_name, dtype=str)

def normalize_columns(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    normalized = {str(c).strip().lower(): c for c in result.columns}
    rename = {}
    for target, names in ALIASES.items():
        for name in names:
            if name in normalized: rename[normalized[name]] = target; break
    result = result.rename(columns=rename)
    if "sku" in result: result["sku"] = result["sku"].astype("string")
    if "unit" in result: result["unit"] = result["unit"].astype("string")
    for col in ("quantity", "free_stock", "inbound_qty", "moq", "pack_multiple"):
        if col in result: result[col] = pd.to_numeric(result[col].str.replace(",", ".", regex=False), errors="coerce")
    for col in ("date", "eta"):
        if col in result: result[col] = pd.to_datetime(result[col], errors="coerce").dt.date
    return result

def validate_table(frame: pd.DataFrame, required: list[str]) -> list[str]:
    issues = [f"missing column: {c}" for c in required if c not in frame.columns]
    if "sku" in frame and frame["sku"].isna().any(): issues.append("missing SKU values")
    if "unit" in frame and frame["unit"].isna().any(): issues.append("missing unit values")
    return issues
