from pyflowlauncher import JsonRPCAction, Result, ResultResponse, send_results, api
from pynab.api import Api
import json
import os
from typing import TypedDict
import logging


import plugin.constants as constants


def configure_logging():
    # Custom logging filter to ignore API error logs from pynab
    class IgnoreApiErrorFilter(logging.Filter):
        def filter(self, record):
            # Only allow logs that are NOT about API errors
            return "api error" not in record.getMessage()

    logging.basicConfig(level=logging.ERROR)
    logging.getLogger().addFilter(IgnoreApiErrorFilter())


def send_simple_result(
    title: str, subtitle: str, JsonRPCAction: JsonRPCAction | None = None
) -> ResultResponse:
    return send_results(
        [
            Result(
                Title=title,
                SubTitle=subtitle,
                IcoPath=constants.ICO_PATH,
                JsonRPCAction=JsonRPCAction,
            )
        ]
    )


def get_budget_url(budget_id: str) -> str:
    return f"{constants.YNAB_URL}/{budget_id}/budget"


def get_active_budget_id(state_settings_path: str) -> str:
    active_budget_id = "last-used"

    if os.path.exists(state_settings_path):
        with open(state_settings_path, "r") as f:
            state_settings = json.load(f)
            active_budget_id = state_settings.get("active_budget", active_budget_id)
    else:
        set_active_budget_id(active_budget_id, state_settings_path)

    return active_budget_id


def set_active_budget_id(budget_id: str, state_settings_path: str):
    with open(state_settings_path, "w") as f:
        json.dump({"active_budget": budget_id}, f)


def get_active_budget(pynab_api: Api, active_budget_id: str, state_settings_path: str):
    try:
        return pynab_api.get_budget(budget_id=active_budget_id)
    except Exception as e:
        err = parse_ynab_error(e)
        if err.get("code") == 404.2:
            try:
                budget = pynab_api.get_budget(budget_id="last-used")
                set_active_budget_id(budget.id, state_settings_path)
                return budget
            except Exception as e:
                err = parse_ynab_error(e)
                if err.get("code") == 404.2:
                    return None


class ErrorResult(TypedDict):
    message: str
    code: int | float | None
    name: str | None
    detail: str | None
    error: str | None


def parse_ynab_error(e: Exception) -> ErrorResult:
    message = str(e)

    if not message.startswith("api error:"):
        raise e

    results: ErrorResult = {
        "message": message,
        "code": None,
        "name": None,
        "detail": None,
        "error": None,
    }

    error_type = message.split(":", maxsplit=1)
    if len(error_type) < 2:
        results["error"] = "Unexpected YNAB API error format"
        return results

    error_items = error_type[1].split("-", maxsplit=2)
    if len(error_items) < 3:
        results["error"] = "Unexpected YNAB API error structure"
        return results

    error_code_str = error_items[0].strip()
    try:
        results["code"] = int(error_code_str)
    except ValueError:
        try:
            results["code"] = float(error_code_str)
        except ValueError:
            results["error"] = "Unexpected YNAB API error code format"
            return results

    results["name"] = error_items[1].strip()
    results["detail"] = error_items[2].strip()

    return results


def handle_ynab_error(e: Exception) -> ResultResponse:
    err = parse_ynab_error(e)

    if err.get("error") is not None:
        title = err.get("error") or "YNAB API error"
        subtitle = (
            err.get("message") or "An error occurred while accessing the YNAB API"
        )
        return send_simple_result(
            title=title,
            subtitle=subtitle,
        )

    error_code = err.get("code")
    error_name = err.get("name")
    error_detail = err.get("detail")

    if error_code == 401:
        return send_simple_result(
            title="Your YNAB Personal Access Token is invalid",
            subtitle=f"Error code: {error_code}. Error message: {error_detail}",
            JsonRPCAction=api.open_setting_dialog(),
        )

    if error_code == 404.2:
        return send_simple_result(
            title="The YNAB resource you are trying to access does not exist",
            subtitle=f"Error code: {error_code}. Error message: {error_detail}",
            JsonRPCAction=api.open_url("https://api.ynab.com/#errors"),
        )

    if error_code == 429:
        return send_simple_result(
            title="You have made too many requests. Please wait and try again",
            subtitle=f"Error code: {error_code}. Error message: {error_detail}",
            JsonRPCAction=api.open_url("https://api.ynab.com/#rate-limiting"),
        )

    return send_simple_result(
        title="An error occurred while accessing the YNAB API",
        subtitle=f"Error code: {error_code}. Error name: {error_name}. Error message: {error_detail}",
        JsonRPCAction=api.open_url("https://api.ynab.com/#errors"),
    )
