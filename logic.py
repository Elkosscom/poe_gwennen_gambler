import keyboard
import pandas as pd
import pyautogui as ag
import pyperclip
from win32gui import GetForegroundWindow, GetWindowText

import classes

output_dataframe = pd.DataFrame(
    columns=[
        "Base",
        "Item Level",
        "Items",
        "Chaos Min",
        "Chaos Average",
        "Chaos Max",
        "Expected Chaos",
    ],
    data=[["", "", "", "", "", "", ""]],
)
status = False
refresh = False


def get_items(grid) -> pd.DataFrame:
    item_list = []
    for t in grid:
        ag.moveTo(t[0], t[1])
        keyboard.press_and_release("ctrl+c")
        try:
            item_list.append(classes.Item(pyperclip.paste()).properties)
        except IndexError:
            pass
    items = pd.DataFrame().from_records(item_list)
    items.drop_duplicates(inplace=True)
    items = items[["base", "Item Level"]]
    return items


def format_final_df(df) -> pd.DataFrame:
    new_cols = []
    for col in df.columns:
        if isinstance(col, str):
            new_cols.append(col)
        else:
            new_cols.append(f"{col[0]} {col[1]}".strip())
    df.columns = new_cols
    df.rename(
        columns={
            "base": "Base",
            "Items sum": "Items",
            "chaosValue max": "Chaos Max",
            "chaosValue min": "Chaos Min",
            "chaosValue mean": "Chaos Average",
        },
        inplace=True,
    )
    return df[
        [
            "Base",
            "Item Level",
            "Items",
            "Chaos Min",
            "Chaos Average",
            "Chaos Max",
            "Expected Chaos",
        ]
    ]


def display_items(
    items: pd.DataFrame,
    prices: pd.DataFrame,
    cfg: classes.Config = classes.Config().load_config(),
) -> pd.DataFrame:

    global output_dataframe
    min_chaos = float(cfg["Prices"].get("MinimumMeanChaosValue"))
    prices["ev_helper"] = prices["chaosValue"] * prices["listingCount"]
    prices = prices.pivot_table(
        values=["chaosValue", "Items", "ev_helper", "listingCount"],
        index="baseType",
        aggfunc={
            "chaosValue": ["mean", "min", "max"],
            "Items": "sum",
            "ev_helper": "sum",
            "listingCount": "sum",
        },
    )
    prices["Expected Chaos"] = (
        prices[("ev_helper", "sum")] / prices[("listingCount", "sum")]
    )
    merge = pd.merge(
        items, prices.reset_index(), left_on="base", right_on="baseType", how="left"
    )
    merge = merge.loc[merge[("chaosValue", "mean")] >= min_chaos]
    merge = format_final_df(merge)
    sort_by = cfg["Prices"].get("SortBy")
    merge = merge.sort_values(by=sort_by, ascending=False)
    output_dataframe = merge[
        [
            "Base",
            "Item Level",
            "Items",
            "Chaos Min",
            "Chaos Average",
            "Chaos Max",
            "Expected Chaos",
        ]
    ].round({"Chaos Min": 1, "Chaos Average": 1, "Chaos Max": 1, "Expected Chaos": 3})


def main(queue) -> None:
    global status
    global refresh
    cfg = classes.Config().load_config()
    ag.PAUSE = float(cfg["Base"].get("MouseMoveDelay"))
    lang = cfg["Base"].get("Language", fallback="EN")
    league = cfg["Base"].get("League")

    if cfg["Base"].get("RefreshPricesOnStart", fallback="True") == "True":
        classes.Prices().fetch_prices(league=league, language=lang)

    prices = classes.Prices().load_prices()
    continue_on_key = cfg["Base"].get("Hotkey")
    grid = classes.TradingWindow().get_grid()
    pyperclip.copy(" ")
    status = True
    while True:
        try:
            stop_thread = queue.get(timeout=0.00001)
        except Exception:
            stop_thread = False
        if stop_thread:
            status = False
            return None
        if keyboard.is_pressed(continue_on_key) and GetWindowText(
            GetForegroundWindow()
        ) == cfg["Base"].get("WindowTitle"):
            items = get_items(grid=grid)
            display_items(items=items, prices=prices, cfg=cfg)
            refresh = True
