from io import BytesIO
from zipfile import ZipFile
import pandas as pd
from openpyxl import Workbook
from qor.data import load_sources, reconcile
from qor.contracts import SNAPSHOT, Policy
from qor.service import calculate_plan


def xlsx(headers, rows):
    book=Workbook(); sheet=book.active; sheet.title="Source"
    sheet.append(headers)
    for row in rows:
        sheet.append(row)
    stream=BytesIO(); book.save(stream)
    return stream.getvalue()


def source(name, headers, rows, supplier="Systeme Electric"):
    return name, xlsx(headers, rows), supplier


def test_repeated_file_not_multiplied_and_text_sku_preserved():
    data=source("sales.xlsx",["sku","unit","date","quantity","document"],[["0007_","pcs","2026-08-01",10,"A"]])
    bundle=load_sources([data,data])
    assert len(bundle.sales)==1
    assert bundle.sales.iloc[0].sku=="0007_"
    assert "!Source!2" in bundle.sales.iloc[0].source
    assert any("Repeated file" in w for w in bundle.warnings)


def test_missing_zero_return_are_distinct():
    bundle=load_sources([source("sales.xlsx",["sku","unit","date","quantity","document"],
        [["001","pcs","2026-08-01",v,str(i)] for i,v in enumerate([None,0,-5,10])])])
    assert set(bundle.sales.kind)=={"missing","zero","return","sale"}
    assert bundle.sales.quantity.isna().sum()==1


def test_monthly_overlap_reconciles_without_sum_and_blank_not_zero():
    b=load_sources([
        source("sales.xlsx",["sku","unit","date","quantity"],[["001","pcs","2026-08-01",10]]),
        source("monthly.xlsx",["sku","2026-08","2026-09"],[["001",12,None]])])
    r=reconcile(b)
    august=r[r.month.astype(str).eq("2026-08-01")].iloc[0]
    assert august.quantity==12 and august.transaction_net==10 and august.difference==-2
    assert b.monthly.iloc[1].partial and pd.isna(b.monthly.iloc[1].quantity)
    assert b.sales.quantity.sum()==10


def test_conflicting_lookup_rows_block_instead_of_cartesian_join():
    b=load_sources([source("stock.xlsx",["sku","unit","free_stock","as_of"],
        [["001","pcs",10,"2026-09-22"],["001","pcs",20,"2026-09-22"]])])
    assert ("Systeme Electric","001") in b.blocked_keys
    assert calculate_plan(b,Policy())[0]["urgency"]=="data_conflict"


def test_unit_conflict_in_purchase_data_blocks_sku():
    b=load_sources([
        source("stock.xlsx",["sku","unit","free_stock","as_of"],[["001","m",10,"2026-09-22"]]),
        source("moq.xlsx",["sku","unit","moq"],[["001","coil",2]])])
    assert ("Systeme Electric","001") in b.blocked_keys


def test_undated_stock_never_silently_assumed_current():
    b=load_sources([source("stock.xlsx",["sku","unit","free_stock"],[["001","pcs",0]])])
    assert b.stock.iloc[0].as_of is None
    assert calculate_plan(b,Policy())[0]["urgency"]=="needs_dated_stock"


def test_iek_monthly_opening_balance_is_not_current_stock():
    b=load_sources([source("остатки.xlsx",["sku","unit","2026-09"],[["001","pcs",100]],"IEK")])
    assert b.stock.empty and len(b.historical_stock)==1


def test_zip_is_read_in_memory_without_extracting_paths():
    workbook=xlsx(["sku","unit","date","quantity"],[["001","pcs","2026-08-01",10]])
    stream=BytesIO()
    with ZipFile(stream,"w") as archive:
        archive.writestr("../../sales.xlsx",workbook)
    b=load_sources([("IEK.zip",stream.getvalue(),"IEK")])
    assert len(b.sales)==1


def test_identical_document_reimport_deduplicates_across_files():
    headers=["sku","unit","date","quantity","document"]
    a=source("a.xlsx",headers,[["001","pcs","2026-08-01",10,"A"]])
    b=source("b.xlsx",headers,[["001","pcs","2026-08-01",10,"A"],["001","pcs","2026-08-02",20,"B"]])
    bundle=load_sources([a,b])
    assert len(bundle.sales)==2 and bundle.sales.quantity.sum()==30


def test_identical_lines_in_one_document_are_not_silently_deleted():
    headers=["sku","unit","date","quantity","document"]
    row=["001","pcs","2026-08-01",10,"A"]
    bundle=load_sources([source("a.xlsx",headers,[row,row])])
    assert len(bundle.sales)==2 and bundle.sales.quantity.sum()==20


def test_no_document_id_does_not_prove_duplicate_sales():
    headers=["sku","unit","date","quantity"]
    row=["001","pcs","2026-08-01",10]
    bundle=load_sources([source("a.xlsx",headers,[row,row])])
    assert len(bundle.sales)==2
