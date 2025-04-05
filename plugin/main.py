from pyflowlauncher import Plugin, Result, ResultResponse, send_results
from pyflowlauncher.settings import settings
from pyflowlauncher.api import open_setting_dialog
import ynab


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
        return send_results([])

    configuration = ynab.Configuration(access_token=access_token)

    with ynab.ApiClient(configuration) as api_client:
        budgets_api = ynab.BudgetsApi(api_client)
        budgets_response = budgets_api.get_budgets()
        budgets = budgets_response.data.budgets

        results = [
            Result(
                Title=budget.name,
                SubTitle="Click to select this budget",
                IcoPath=ICO_PATH,
            )
            for budget in budgets
        ]

        return send_results(results)
