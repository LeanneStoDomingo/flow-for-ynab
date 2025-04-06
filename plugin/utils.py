from pyflowlauncher import JsonRPCAction, Result, ResultResponse, send_results
from pyflowlauncher.api import open_setting_dialog, open_url

from constants import ICO_PATH


def send_simple_result(
    title: str, subtitle: str, JsonRPCAction: JsonRPCAction | None = None
) -> ResultResponse:
    return send_results(
        [
            Result(
                Title=title,
                SubTitle=subtitle,
                IcoPath=ICO_PATH,
                JsonRPCAction=JsonRPCAction,
            )
        ]
    )


def handle_ynab_error(e: Exception) -> ResultResponse:
    message = str(e)

    if not message.startswith("api error:"):
        raise e

    items = message.split(":")[1].split("-")
    error_code = float(items[0].strip())
    error_name = items[1].strip()
    error_detail = items[2].strip()

    if error_code == 401:
        return send_simple_result(
            title="Your YNAB Personal Access Token is invalid",
            subtitle=f"Error code: {error_code}. Error message: {error_detail}",
            JsonRPCAction=open_setting_dialog(),
        )

    if error_code == 429:
        return send_simple_result(
            title="You have made too many requests. Please wait and try again",
            subtitle=f"Error code: {error_code}. Error message: {error_detail}",
            JsonRPCAction=open_url("https://api.ynab.com/#rate-limiting"),
        )

    return send_simple_result(
        title="An error occurred while accessing the YNAB API",
        subtitle=f"Error code: {error_code}. Error name: {error_name}. Error message: {error_detail}",
        JsonRPCAction=open_url("https://api.ynab.com/#errors"),
    )
