import ctypes
import platform
from queue import Queue
from threading import Thread

import PySimpleGUI as sg
from loguru import logger

import classes
import logic

sg.theme("DarkTanBlue")


def make_dpi_aware():
    if int(platform.release()) >= 8:
        ctypes.windll.shcore.SetProcessDpiAwareness(True)


logger.add("log.log", rotation="1 MB", enqueue=True, backtrace=True, diagnose=True)


class MainWindow:
    def __init__(self) -> None:
        self.cfg = classes.Config().load_config()
        table = logic.output_dataframe[
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
        data = table.values.tolist()
        headers = table.columns.tolist()
        self.layout = [
            [
                sg.Button("Start program", k="start"),
                sg.Button("Stop program", k="stop", disabled=True),
                sg.Button("Edit Config", k="config"),
            ],
            [sg.Text("Status:"), sg.Text("Stopped", k="status")],
            [
                sg.Table(
                    values=data,
                    headings=headers,
                    display_row_numbers=False,
                    auto_size_columns=False,
                    num_rows=20,
                    col_widths=[26, 10, 5, 10, 10, 10, 12],
                    select_mode=sg.TABLE_SELECT_MODE_BROWSE,
                    k="table",
                )
            ],
            [sg.Button("View details", k="details")],
        ]
        self.window = sg.Window(
            "Gwennen Gambler",
            layout=self.layout,
            resizable=True,
            finalize=True,
            size=(800, 500),
        )
        self.window["table"].expand(True, True, True)
        self.window["start"].expand(True, True)
        self.window["stop"].expand(True, True)
        self.window["details"].expand(True, True)
        self.window["config"].expand(True, True)

        self.prices = classes.Prices().load_prices(True)

    def main_loop(self) -> None:
        while True:
            event, values = self.window.read(timeout=1000)
            try:
                selected = values["table"]
            except (IndexError, TypeError):
                selected = None
            if logic.refresh:
                self.window["table"].update(
                    values=logic.output_dataframe.values.tolist(),
                    select_rows=selected,
                )
                logic.refresh = False

            if event in [sg.WIN_CLOSED, "Quit"]:
                ver = classes.VersionCheck()
                is_latest = ver.perform_version_check()
                if not is_latest:
                    ask_for_update = sg.PopupYesNo(
                        "New version detected. Would you like to open latest release?",
                        title="New Version Available",
                    )
                    if ask_for_update == "Yes":
                        ver.open_latest_version_page()
                break

            if event == "start":
                self.window["start"].update(disabled=True)
                self.window["stop"].update(disabled=False)
                self.window["config"].update(disabled=True)
                q = Queue(maxsize=1)
                t = Thread(target=logic.main, daemon=True, kwargs={"queue": q})
                t.start()
                while True:
                    if logic.status is True:
                        self.window["status"].update("Running")
                        break

            if event == "stop":
                self.window["start"].update(disabled=False)
                self.window["stop"].update(disabled=True)
                self.window["config"].update(disabled=False)
                q.put(True, block=False)
                t.join(timeout=0)
                while 1:
                    if logic.status is False:
                        self.window["status"].update("Stopped")
                        break

            if event == "details":
                try:
                    df = logic.output_dataframe
                    prices = classes.Prices().load_prices(True)
                    item_name = df.iloc[values["table"][0]]["Base"]
                    item_level = 100
                    if self.cfg["Prices"].get("MinItemLevelRestriction") == "True":
                        item_level = df.iloc[values["table"][0]]["Item Level"]
                    ViewDetailsBaseType(
                        prices=prices, basetype=item_name, item_level=item_level
                    ).main_loop()
                except Exception:
                    logger.exception("exc")

            if event == "config":
                ConfigEditor().main_loop()


class ViewDetailsBaseType:
    def __init__(self, basetype, prices, item_level) -> None:
        table = self.format_prices(prices=prices, basetype=basetype)
        table["levelRequired"] = table["levelRequired"].fillna(0)
        if item_level:
            table = table.loc[table["levelRequired"] <= int(item_level)]
        table = table[["Name", "Chaos Price", "Listings", "Fated", "Blacklisted"]]
        self.table = table
        headers = table.columns.tolist()
        data = table.values.tolist()
        self.layout = [
            [
                sg.Button("Add selection to blacklist", k="ignore"),
                sg.Button("Remove selection from blacklist", k="unignore"),
            ],
            [
                sg.Table(
                    values=data,
                    headings=headers,
                    display_row_numbers=False,
                    auto_size_columns=True,
                    num_rows=min(25, len(data)),
                )
            ],
        ]
        self.window = sg.Window("Base type details", layout=self.layout, finalize=True)
        self.window["ignore"].expand(True, True)
        self.window["unignore"].expand(True, True)

    def main_loop(self) -> None:
        while True:
            event, values = self.window.read()

            if event == sg.WIN_CLOSED:
                break

            if event == "ignore":
                self.add_items_to_blacklist(self.table, values[0])

            if event == "unignore":
                self.remove_items_from_blacklist(self.table, values[0])

    @staticmethod
    def format_prices(prices, basetype):
        prices = prices.loc[prices["baseType"] == basetype]
        prices = prices[
            [
                "name",
                "chaosValue",
                "listingCount",
                "Fated",
                "Blacklisted",
                "levelRequired",
            ]
        ]
        prices.rename(
            columns={
                "name": "Name",
                "chaosValue": "Chaos Price",
                "listingCount": "Listings",
            },
            inplace=True,
        )
        return prices

    @staticmethod
    def add_items_to_blacklist(table, indices: list):
        table = table.iloc[indices]
        item_list = table["Name"].values
        classes.Blacklist().add_to_blacklist(item_list)

    @staticmethod
    def remove_items_from_blacklist(table, indices: list):
        table = table.iloc[indices]
        item_list = table["Name"].values
        classes.Blacklist().remove_from_blacklist(item_list)


class ConfigEditor:
    def __init__(self) -> None:
        self.config = classes.Config()
        cfg = self.config.load_config()
        self.loaded_config = cfg
        input_fields = {
            "Hotkey": sg.Input(cfg["Base"].get("Hotkey"), size=(10, 1), k="Hotkey"),
            "RefreshPricesOnStart": sg.Combo(
                ["True", "False"],
                cfg["Base"].get("RefreshPricesOnStart"),
                readonly=True,
                k="RefreshPricesOnStart",
            ),
            "MouseMoveDelay": sg.Input(
                cfg["Base"].get("MouseMoveDelay"), size=(5, 1), k="MouseMoveDelay"
            ),
            "Language": sg.Combo(
                ["EN", "GE", "FR", "RU", "ES"],
                cfg["Base"].get("Language"),
                readonly=True,
                k="Language",
            ),
            "League": sg.Combo(
                ["Expedition", "Hardcore Expedition", "Standard", "Hardcore"],
                cfg["Base"].get("League"),
                readonly=True,
                k="League",
            ),
            "WindowTitle": sg.Input(
                cfg["Base"].get("WindowTitle"), size=(25, 1), k="WindowTitle"
            ),
            "UnlinkedOnly": sg.Combo(
                ["True", "False"],
                cfg["Prices"].get("UnlinkedOnly"),
                readonly=True,
                k="UnlinkedOnly",
            ),
            "MinimumMeanChaosValue": sg.Input(
                cfg["Prices"].get("MinimumMeanChaosValue"),
                size=(5, 1),
                k="MinimumMeanChaosValue",
            ),
            "IgnoreFatedUniques": sg.Combo(
                ["True", "False"],
                cfg["Prices"].get("IgnoreFatedUniques"),
                readonly=True,
                k="IgnoreFatedUniques",
            ),
            "UseBlacklist": sg.Combo(
                ["True", "False"],
                cfg["Prices"].get("UseBlacklist"),
                readonly=True,
                k="UseBlacklist",
            ),
            "MinItemLevelRestriction": sg.Combo(
                ["True", "False"],
                cfg["Prices"].get("MinItemLevelRestriction"),
                readonly=True,
                k="MinItemLevelRestriction",
            ),
            "SortBy": sg.Combo(
                ["Average Chaos", "Expected Chaos"],
                cfg["Prices"].get("SortBy"),
                readonly=True,
                k="SortBy",
            ),
            "GridTopLeftCornerX": sg.Input(
                cfg["Screen"].get("GridTopLeftCornerX"),
                size=(4, 1),
                k="GridTopLeftCornerX",
            ),
            "GridTopLeftCornerY": sg.Input(
                cfg["Screen"].get("GridTopLeftCornerY"),
                size=(4, 1),
                k="GridTopLeftCornerY",
            ),
            "GridBottomRightCornerX": sg.Input(
                cfg["Screen"].get("GridBottomRightCornerX"),
                size=(4, 1),
                k="GridBottomRightCornerX",
            ),
            "GridBottomRightCornerY": sg.Input(
                cfg["Screen"].get("GridBottomRightCornerY"),
                size=(4, 1),
                k="GridBottomRightCornerY",
            ),
        }
        layout = [[[sg.Text(key), input_fields[key]] for key in input_fields]]
        layout.append(
            [sg.Cancel(), sg.Button("Autodetect resolution", k="auto"), sg.Save()]
        )
        self.window = sg.Window("Config Editor", layout=layout)

    def main_loop(self) -> None:
        while True:
            event, values = self.window.read()

            if event in ["Cancel", sg.WIN_CLOSED]:
                break

            if event == "auto":
                grid_dict = self.config.get_grid_position()
                for k in grid_dict:
                    self.window[k].update(str(int(float(grid_dict[k]))))
                self.window.refresh()
            if event == "Save":
                for section in self.loaded_config:
                    for item in self.loaded_config[section]:
                        self.loaded_config[section].update({item: values[item]})
                self.config.save_config(self.loaded_config)
                sg.Popup("Config Saved!")


if __name__ == "__main__":
    try:
        MainWindow().main_loop()
    except Exception:
        logger.exception("Uncaught Exception happened")
