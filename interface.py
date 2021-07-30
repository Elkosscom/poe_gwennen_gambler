import ctypes
import platform
from threading import Thread
from warnings import filterwarnings

import PySimpleGUI as sg
from loguru import logger

import classes
import logic

sg.theme("DarkTanBlue")


def make_dpi_aware():
    if int(platform.release()) >= 8:
        ctypes.windll.shcore.SetProcessDpiAwareness(True)


filterwarnings("ignore")

logger.add("log.log", rotation="1 MB", enqueue=True, backtrace=True, diagnose=True)

# try:
#     print("Starting function.")
#     logic.main()
# except Exception:
#     logger.exception("Uncaught Exception Happened")


class MainWindow:
    def __init__(self) -> None:
        self.layout = [
            [
                sg.Button("Start program", k="start", size=(70, 1)),
                sg.Button("Stop program", k="stop", size=(70, 1), disabled=True),
            ],
            [sg.Button("Clear output", k="clear", size=(142, 1))],
            [sg.Output(size=(160, 20), font="consolas 10", k="out")],
            [sg.Button("View details", k="details", size=(142, 1))],
        ]
        self.window = sg.Window("Gwennen Gambler", layout=self.layout)

    def main_loop(self):
        while True:
            event, values = self.window.read()

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

            if event == "clear":
                self.window["out"].update("")
            if event == "start":
                self.window["start"].update(disabled=True)
                self.window["stop"].update(disabled=False)
                print("Started")

            if event == "stop":
                self.window["start"].update(disabled=False)
                self.window["stop"].update(disabled=True)
                print("Stopped")

            if event == "details":
                try:
                    df = logic.output_dataframe
                    ViewDetailsWindow(df).main_loop()
                except Exception:
                    logger.exception("exc")


class ViewDetailsWindow:
    def __init__(self, df) -> None:
        self.layout = self.construct_layout(df=df)
        self.window = sg.Window("Select basetype", layout=self.layout)
        self.prices = classes.Prices().load_prices(show_ignored=True)

    @staticmethod
    def construct_layout(df) -> list:
        rows = [[sg.Text("Select Base Item:")]]
        for row in df.iterrows():
            rows.append([sg.Button(f"{row[1]['Base']}")])
        return rows

    def main_loop(self) -> None:
        while True:
            event, values = self.window.read()

            if event == sg.WIN_CLOSED:
                break
            if event is not None:
                ViewDetailsBaseType(event,self.prices).main_loop()


class ViewDetailsBaseType:
    def __init__(self, basetype, prices) -> None:
        table = self.format_prices(prices=prices, basetype=basetype)
        self.table = table
        headers = table.columns.tolist()
        data = table.values.tolist()
        self.layout = [
            [sg.Button("Add selection to blacklist", k="ignore"), sg.Button('Remove selection from blacklist')],
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
        self.window = sg.Window("Base type details", layout=self.layout)

    def main_loop(self) -> None:
        while True:
            event, values = self.window.read()

            if event == sg.WIN_CLOSED:
                break
            
            if event == 'ignore':
                self.add_items_to_blacklist(self.table, values[0])

    @staticmethod
    def format_prices(prices, basetype):
        prices = prices.loc[prices["baseType"] == basetype]
        prices = prices[["name", "chaosValue", "listingCount",'Fated','Blacklisted']]
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
    def add_items_to_blacklist(table, indices:list):
        table = table.iloc[indices]
        print(table['Name'].values)


MainWindow().main_loop()
