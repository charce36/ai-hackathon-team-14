from publisher_support.adapters.scenarios import detect_scenario
from publisher_support.adapters.mock import get_all_adapters
from publisher_support.adapters.base import MonitorContext


def test_detect_scenario_keywords():
    assert detect_scenario("No puedo publicar") == "account_blocked"
    assert detect_scenario("facturación desactualizada") == "sap_sync_failure"
    assert detect_scenario("error 503") == "gcp_service_down"


def test_monitor_post_fix_account_blocked():
    ctx_pre = MonitorContext("account_blocked", "pub-1", post_fix=False)
    ctx_post = MonitorContext("account_blocked", "pub-1", post_fix=True)
    adapters = {a.service: a for a in get_all_adapters()}
    assert adapters["account"].check(ctx_pre).healthy is False
    assert adapters["account"].check(ctx_post).healthy is True
