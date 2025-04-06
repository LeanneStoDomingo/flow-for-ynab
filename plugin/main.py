from pyflowlauncher import Plugin, Result, ResultResponse, send_results, api
from pyflowlauncher.settings import settings
from pyflowlauncher.api import open_setting_dialog
from pynab.pynab import Pynab
from pynab.schemas import Budget
import logging
import os
import json

from plugin.utils import send_simple_result, handle_ynab_error
from plugin.constants import ICO_PATH


# Custom logging filter to ignore API error logs from pynab
class IgnoreApiErrorFilter(logging.Filter):
    def filter(self, record):
        # Only allow logs that are NOT about API errors
        return "api error" not in record.getMessage()


logging.basicConfig(level=logging.ERROR)
logging.getLogger().addFilter(IgnoreApiErrorFilter())


plugin = Plugin()


@plugin.on_method
def query(query: str) -> ResultResponse:
    access_token = settings().get("access_token")
    if not access_token:
        return send_simple_result(
            title="YNAB Personal Access Token is missing",
            subtitle="Click here or press Enter to go to the plugin settings",
            JsonRPCAction=open_setting_dialog(),
        )

    active_budget_id = "last-used"

    state_settings_path = os.path.join(
        plugin.root_dir(), "..", "..", "Settings", "flow-for-ynab.json"
    )
    if os.path.exists(state_settings_path):
        with open(state_settings_path, "r") as f:
            state_settings = json.load(f)
            active_budget_id = state_settings.get("active_budget", active_budget_id)
    else:
        with open(state_settings_path, "w") as f:
            json.dump({"active_budget": active_budget_id}, f)

    try:
        pynab = Pynab(access_token)

        active_budget: Budget = pynab.budgets.by(field="id", value=active_budget_id)

        if not query or (
            query.lower() in "budget" and not query.lower().startswith("budget")
        ):
            results = [
                Result(
                    Title="budget",
                    SubTitle="ynab budget <budget_name>",
                    IcoPath=ICO_PATH,
                ),
                Result(
                    Title=f"Active Budget: {active_budget.name}",
                    SubTitle=f"ID: {active_budget.id}",
                    IcoPath=ICO_PATH,
                    ContextData={
                        "budget_url": f"https://app.ynab.com/{active_budget.id}/budget"
                    },
                ),
            ]

            return send_results(results)

        if query.lower().startswith("budget"):
            budgets = pynab.budgets

            query_items = query.split(" ", maxsplit=1)
            search = ""
            if len(query_items) > 1:
                search = query_items[1].strip().lower()

            results = []

            for budget_id in budgets:
                budget: Budget = budgets[budget_id]

                if search not in budget.name.lower():
                    continue

                results.append(
                    Result(
                        Title=budget.name,
                        SubTitle=f"ID: {budget.id}",
                        IcoPath=ICO_PATH,
                        JsonRPCAction={
                            "method": "select_budget_action",
                            "parameters": [budget.id, state_settings_path],
                        },
                        ContextData={
                            "budget_url": f"https://app.ynab.com/{budget.id}/budget"
                        },
                    )
                )

            return send_results(results)

    except Exception as e:
        return handle_ynab_error(e)

    return send_results([])


@plugin.on_method
def context_menu(context_data: dict) -> ResultResponse:
    budget_url = context_data.get("budget_url", None)

    if budget_url != None:
        return send_simple_result(
            title="Open budget in browser",
            subtitle=budget_url,
            JsonRPCAction=api.open_url(budget_url),
        )

    return send_results([])


@plugin.on_method
def select_budget_action(budget_id: str, state_settings_path: str):
    with open(state_settings_path, "w") as f:
        json.dump({"active_budget": budget_id}, f)
