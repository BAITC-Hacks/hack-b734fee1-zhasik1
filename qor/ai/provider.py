from qor.contracts import ProviderCapabilities

def allowed_tools(): return ["inspect_data","calculate_plan","simulate_policy","explain_sku","build_order_draft"]

class PendingProvider:
    """Truthful no-entitlement state; never fakes a model response."""
    capabilities=ProviderCapabilities(provider="unverified",verified=False)
    def ask(self, prompt, tools):
        raise RuntimeError("AI integration pending: participant endpoint, authorized model ID, and credential are not verified")
