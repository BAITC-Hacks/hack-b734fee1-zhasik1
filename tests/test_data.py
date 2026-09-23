import pandas as pd
from qor.data import normalize_columns, validate_table
def test_text_sku_and_zero_are_preserved():
 d=normalize_columns(pd.DataFrame({"Код":["0007_"],"Ед":["pcs"],"Количество":["0"]})); assert d.loc[0,"sku"]=="0007_" and d.loc[0,"quantity"]==0
def test_missing_not_zero():
 d=normalize_columns(pd.DataFrame({"Код":["1"],"Количество":[None]})); assert pd.isna(d.loc[0,"quantity"])
