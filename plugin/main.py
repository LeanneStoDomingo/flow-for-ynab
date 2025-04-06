from pyflowlauncher import Plugin, Result, ResultResponse, send_results
from pyflowlauncher.settings import settings
from pyflowlauncher.api import open_setting_dialog
from pynab.pynab import Pynab
from pynab.schemas import Budget
import logging

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

    if not query:
        return send_simple_result(
            title="budget",
            subtitle="ynab budget <budget_name>",
        )

    try:
        pynab = Pynab(access_token)

        if query.startswith("budget"):
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

    except Exception as e:
        return handle_ynab_error(e)

    return send_results([])
