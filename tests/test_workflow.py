import csv
from io import BytesIO, StringIO
from openpyxl import load_workbook
import pytest
from qor.storage import Repository
from qor.contracts import Policy
from qor.data.demo import demo_bundle
from qor.service import calculate_plan
from qor.ai.provider import ToolRouter


def draft(tmp_path):
    repo=Repository(tmp_path/"qor.sqlite3")
    rows=calculate_plan(demo_bundle(),Policy(),keys={("Systeme Electric","SYN-0007_")})
    run=repo.create(rows,{"provenance":"synthetic"},"planner")
    return repo,run


def approve(repo,run):
    repo.transition(run,repo.latest(run)["version"],"review","reviewer")
    repo.transition(run,repo.latest(run)["version"],"approved","approver")


def test_export_requires_persisted_latest_approval(tmp_path):
    repo,run=draft(tmp_path)
    with pytest.raises(ValueError): repo.export(run,1,"csv","operator")
    with pytest.raises(ValueError): repo.transition(run,1,"approved","operator")
    approve(repo,run)
    with pytest.raises(ValueError): repo.export(run,1,"csv","operator")
    with pytest.raises(ValueError): repo.transition(run,3,"exported","operator")


def test_manager_edit_requires_reason_and_resets_approval(tmp_path):
    repo,run=draft(tmp_path)
    approve(repo,run)
    edit=dict(supplier="Systeme Electric",sku="SYN-0007_",manager_qty=240,reason="")
    with pytest.raises(ValueError): repo.edit(run,3,[edit],"manager")
    edit["reason"]="Verified project demand"
    repo.edit(run,3,[edit],"manager")
    assert repo.latest(run)["state"]=="draft"
    assert repo.latest(run)["rows"][0]["manager_qty"]==240
    with pytest.raises(ValueError): repo.export(run,4,"xlsx","manager")
    with pytest.raises(ValueError): repo.edit(run,3,[edit],"manager")


def test_restart_exports_csv_xlsx_same_approved_values_and_approver(tmp_path):
    repo,run=draft(tmp_path)
    row=repo.latest(run)["rows"][0]
    edit=dict(supplier=row["supplier"],sku=row["sku"],manager_qty=240,reason="=FORMULA is text")
    repo.edit(run,1,[edit],"planner")
    approve(repo,run)
    reopened=Repository(tmp_path/"qor.sqlite3")
    csv_bytes=reopened.export(run,4,"csv","exporter")
    records=list(csv.DictReader(StringIO(csv_bytes.decode("utf-8-sig"))))
    assert float(records[0]["manager_qty"])==240
    assert records[0]["edit_reason"].startswith("'=")
    xlsx=reopened.export(run,5,"xlsx","another exporter")
    values=list(load_workbook(BytesIO(xlsx),data_only=False).active.values)
    record=dict(zip(values[0],values[1]))
    assert record["sku"]=="SYN-0007_" and record["manager_qty"]==240
    assert record["approved_by"]=="approver" and record["order_version"]==4
    assert len(reopened.audit(run))==6


def test_incomplete_or_mixed_supplier_draft_cannot_be_approved(tmp_path):
    repo=Repository(tmp_path/"qor.sqlite3")
    rows=calculate_plan(demo_bundle(),Policy())
    with pytest.raises(ValueError): repo.create(rows,{},"planner")
    incomplete=[r for r in rows if r["supplier"]=="IEK"]
    run=repo.create(incomplete,{},"planner")
    repo.transition(run,1,"review","planner")
    with pytest.raises(ValueError): repo.transition(run,2,"approved","manager")


def test_inputs_persist_per_dataset(tmp_path):
    repo=Repository(tmp_path/"qor.sqlite3")
    repo.record_input("one","stock",{"qty":10})
    assert repo.inputs("two","stock")==[]
    assert Repository(tmp_path/"qor.sqlite3").inputs("one","stock")==[{"qty":10}]


def test_ai_router_rejects_write_actions_and_limits_calls():
    router=ToolRouter(demo_bundle())
    with pytest.raises(ValueError): router.call({"operation":"approve","supplier":"IEK"})
    with pytest.raises(ValueError): router.call({"operation":"calculate_plan","supplier":"IEK","lead_days":-1})
    for _ in range(4):
        assert router.call({"operation":"inspect_data","supplier":"IEK"})["transaction_rows"]>0
    with pytest.raises(ValueError): router.call({"operation":"inspect_data","supplier":"IEK"})
