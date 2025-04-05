from pyflowlauncher import Plugin, Result, ResultResponse, send_results
from pyflowlauncher.settings import settings
from pyflowlauncher.api import open_setting_dialog
from pynab.pynab import Pynab
from pynab.schemas import Budget


ICO_PATH = "icon.png"


plugin = Plugin()


@plugin.on_method
def query(query: str) -> ResultResponse:
    access_token = settings().get("access_token")
    if not access_token:
        return send_results(
            [
                Result(
                    Title="YNAB Personal Access Token is missing",
                    SubTitle="Click here or press Enter to go to the plugin settings",
                    IcoPath=ICO_PATH,
                    JsonRPCAction=open_setting_dialog(),
                )
            ]
        )

    if not query:
        return send_results(
            [
                Result(
                    Title="budget",
                    SubTitle="ynab budget <budget_name>",
                    IcoPath=ICO_PATH,
                )
            ]
        )

    if query.startswith("budget"):
        pynab = Pynab(access_token)

        budgets = pynab.budgets

        results = []

        for budget_id in budgets:
            budget: Budget = budgets[budget_id]
            results.append(
                Result(
                    Title=budget.name,
                    SubTitle=f"ID: {budget.id}",
                    IcoPath=ICO_PATH,
                )
            )

        return send_results(results)

    return send_results([])
