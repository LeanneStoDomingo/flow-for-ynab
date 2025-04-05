from pyflowlauncher import Plugin, Result, ResultResponse, send_results
from pyflowlauncher.settings import settings


plugin = Plugin()

@plugin.on_method
def query(query: str) -> ResultResponse:
    r = Result(
        Title=f"This is a title! Your query is {query}",
        SubTitle="This is the subtitle!",
        IcoPath="icon.png"
    )
    return send_results([r])