import pytest
from qor.ai import PendingProvider, allowed_tools
def test_pending_provider_is_not_mocked_live_response():
 assert not PendingProvider.capabilities.verified
 with pytest.raises(RuntimeError): PendingProvider().ask("make order",[])
def test_allowed_tools_are_bounded(): assert set(allowed_tools())=={"inspect_data","calculate_plan","simulate_policy","explain_sku"}
