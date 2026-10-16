"""LangChain tool wrappers around the insurance backend API.

Each tool mirrors one of the original call_* functions from the pre-LangGraph
version of this bot: same backend request, same return shape, same docstring
content (the docstring IS the tool description LangChain sends to the model,
replacing the old TOOL_DECLARATIONS list).

The only addition is an optional `config` parameter. LangChain auto-injects
the current RunnableConfig into any tool argument typed as RunnableConfig
without exposing it to the model's tool schema. We use it to push a UI
"widget" descriptor into a per-turn sink list -- see graph.py / chatbot.py
for where that sink comes from and gets read back out.
"""
import requests
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

BACKEND = "http://127.0.0.1:8000"


def _record_widget(config: RunnableConfig, tool_name: str, result: dict) -> None:
    """Append a UI widget descriptor to this turn's sink, if the result warrants one.

    This is the same decision logic as the original _make_widget() -- just
    invoked from inside the tool instead of by the caller after the fact.
    """                                                                             
    sink = (config.get("configurable") or {}).get("widget_sink") if config else None
    if sink is None:
        return
    if isinstance(result, dict) and ("error" in result or "detail" in result):
        return

    widget = None
    if tool_name == "list_policies" and isinstance(result, list):
        widget = {"type": "policies", "data": result}
    elif tool_name == "confirm_application":
        widget = {"type": "policy_issued", "data": result}
    elif tool_name == "confirm_claim":
        widget = {"type": "claim_filed", "data": result}
    elif tool_name == "claim_status":
        widget = {"type": "claim_status", "data": result}

    if widget:
        sink.append(widget)


@tool
def create_application(
    name: str, email: str, phone_number: str, address: str,
    make: str, model: str, year: int, mileage: int, vin: str,
    coverage_type: str, rent_a_car: bool = False,
    config: RunnableConfig = None,
) -> dict:
    """Create a draft insurance application once you have ALL of: customer name,
    email, phone, address, vehicle make, model, year, mileage, VIN, coverage type
    ('Full' or 'Third Party'), and whether they want the rent-a-car add-on.
    Do not call until everything is known."""
    payload = {
        "customer_details": {"name": name, "email": email, "phone_number": phone_number, "address": address},
        "vehicle_details": {"make": make, "model": model, "year": year, "mileage": mileage, "vin": vin},
        "coverage_type": coverage_type,
        "rent_a_car": rent_a_car,
    }
    result = requests.post(f"{BACKEND}/applications", json=payload).json()
    _record_widget(config, "create_application", result)
    return result


@tool
def list_policies(application_id: str, config: RunnableConfig = None) -> dict:
    """List the policies a draft application qualifies for, with features and
    premiums. Call after create_application."""
    result = requests.get(f"{BACKEND}/applications/{application_id}/policies").json()
    _record_widget(config, "list_policies", result)
    return result


@tool
def select_policy(application_id: str, policy_id: str, config: RunnableConfig = None) -> dict:
    """Record the customer's chosen policy on the application. policy_id must be
    one returned by list_policies."""
    result = requests.post(
        f"{BACKEND}/applications/{application_id}/select-policy",
        json={"policy_id": policy_id},
    ).json()
    _record_widget(config, "select_policy", result)
    return result


@tool
def confirm_application(application_id: str, config: RunnableConfig = None) -> dict:
    """Confirm and submit the application after a policy is selected. Returns the
    issued policy number."""
    result = requests.post(f"{BACKEND}/applications/{application_id}/confirm").json()
    _record_widget(config, "confirm_application", result)
    return result


@tool
def create_claim(
    policy_number: str, accident_time: str, accident_location: str, description: str,
    config: RunnableConfig = None,
) -> dict:
    """Create a draft insurance claim. Needs a valid policy_number plus accident
    date, location, and a description of what happened."""
    payload = {
        "policy_number": policy_number,
        "accident_details": {
            "accident_time": accident_time,
            "accident_location": accident_location,
            "description": description,
        },
    }
    result = requests.post(f"{BACKEND}/claims", json=payload).json()
    _record_widget(config, "create_claim", result)
    return result


@tool
def confirm_claim(claim_id: str, config: RunnableConfig = None) -> dict:
    """Confirm and submit a draft claim. Returns the issued claim number. claim_id
    comes from create_claim."""
    result = requests.post(f"{BACKEND}/claims/{claim_id}/confirm").json()
    _record_widget(config, "confirm_claim", result)
    return result


@tool
def claim_status(claim_number: str, config: RunnableConfig = None) -> dict:
    """Check the status of a submitted claim by its claim_number."""
    result = requests.get(f"{BACKEND}/claims/{claim_number}/status").json()
    _record_widget(config, "claim_status", result)
    return result


ALL_TOOLS = [
    create_application,
    list_policies,
    select_policy,
    confirm_application,
    create_claim,
    confirm_claim,
    claim_status,
]