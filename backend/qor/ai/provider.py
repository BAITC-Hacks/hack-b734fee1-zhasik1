"""An unavailable participant model is explicit; deterministic tools remain usable."""
from qor.contracts import ProviderCapabilities, ToolRequest, Policy
from qor.service import calculate_plan
from qor.planning import explain_row

def allowed_tools():
    return ["inspect_data", "calculate_plan", "simulate_policy", "explain_sku"]

class PendingProvider:
    capabilities=ProviderCapabilities()
    def ask(self,prompt,tools):
        raise RuntimeError("Live AI blocked: organizer provider/endpoint, authorized model ID, participant credential and successful live probe required")

class ToolRouter:
    """No approval, export, arbitrary Python, SQL, paths or external messaging tool."""
    def __init__(self,bundle,policy=None):
        self.bundle=bundle
        self.policy=policy or Policy()
        self.calls=0

    def call(self,arguments):
        req=ToolRequest.model_validate(arguments)
        self.calls+=1
        if self.calls>4:
            raise ValueError("Tool-call budget exceeded")
        if req.operation=="inspect_data":
            return dict(transaction_rows=len(self.bundle.sales),files=len(self.bundle.manifest),warnings=self.bundle.warnings[:10])
        if not req.sku:
            raise ValueError("A specific SKU is required to bound data exposure")
        policy=Policy.model_validate(dict(self.policy.model_dump(),lead_days=req.lead_days))
        rows=calculate_plan(self.bundle,policy,keys={(req.supplier,req.sku)})
        return [explain_row(r) for r in rows]
