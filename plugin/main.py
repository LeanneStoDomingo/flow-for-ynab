from pyflowlauncher import Plugin, Result, ResultResponse, send_results, api
from pyflowlauncher.settings import settings
from pynab.pynab import Pynab
from pynab.api import Api
from pynab.schemas import Budget
import os

import plugin.utils as utils
import plugin.constants as constants


utils.configure_logging()

plugin = Plugin()

STATE_SETTINGS_PATH = os.path.join(
    plugin.root_dir(), "..", "..", "Settings", "flow-for-ynab.json"
)


@plugin.on_method
def query(query: str) -> ResultResponse:
    access_token = settings().get("access_token")
    if not access_token:
        return utils.send_simple_result(
            title="YNAB Personal Access Token is missing",
            subtitle="Click here or press Enter to go to the plugin settings",
            JsonRPCAction=api.open_setting_dialog(),
        )

    active_budget_id = utils.get_active_budget_id(STATE_SETTINGS_PATH)

    try:
        pynab = Pynab(access_token)
        pynab_api = Api(pynab)

        active_budget = utils.get_active_budget(
            pynab_api, active_budget_id, STATE_SETTINGS_PATH
        )
        if not active_budget:
            return utils.send_simple_result(
                title="No budgets found",
                subtitle="Please create a budget in YNAB",
                JsonRPCAction=api.open_url(constants.YNAB_URL),
            )

        if not query or (
            query.lower() in "budget" and not query.lower().startswith("budget")
        ):
            results = [
                Result(
                    Title="budget",
                    SubTitle="ynab budget <budget_name>",
                    IcoPath=constants.ICO_PATH,
                ),
                Result(
                    Title=f"Active Budget: {active_budget.name}",
                    SubTitle=f"ID: {active_budget.id}",
                    IcoPath=constants.ICO_PATH,
                    ContextData={"budget_url": utils.get_budget_url(active_budget.id)},
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
                        IcoPath=constants.ICO_PATH,
                        JsonRPCAction={
                            "method": "select_budget_action",
                            "parameters": [budget.id],
                        },
                        ContextData={"budget_url": utils.get_budget_url(budget.id)},
                    )
                )

            return send_results(results)

    except Exception as e:
        return utils.handle_ynab_error(e)

    return send_results([])


@plugin.on_method
def context_menu(context_data: dict) -> ResultResponse:
    budget_url = context_data.get("budget_url")

    if budget_url is not None:
        return utils.send_simple_result(
            title="Open budget in browser",
            subtitle=budget_url,
            JsonRPCAction=api.open_url(budget_url),
        )

    return send_results([])


@plugin.on_method
def select_budget_action(budget_id: str):
    utils.set_active_budget_id(budget_id, STATE_SETTINGS_PATH)
