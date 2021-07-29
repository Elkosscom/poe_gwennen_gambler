from configparser import ConfigParser
from os import getcwd, listdir

import pandas as pd
from requests import get


class Config:
    def __init__(self) -> None:
        if not "config.ini" in listdir(getcwd()):
            self.create_config()

    @staticmethod
    def create_config():
        print('Setting up config.')
        cfg = ConfigParser()
        cfg.optionxform = str
        cfg.add_section("Base")
        cfg["Base"].update(
            {
                "Hotkey": "F6",
                "RefreshPricesOnStart": "True",
                "MouseMoveDelay": "0.01",
                "Language": "EN",
                "League": "Expedition",
            }
        )
        cfg.add_section("Prices")
        cfg["Prices"].update(
            {"UnlinkedOnly": "True", "MinimumMeanChaosValue": "0.0",}
        )
        cfg.add_section("Screen")
        cfg["Screen"].update(
            {
                "GridTopLeftCornerX": "310",
                "GridTopLeftCornerY": "262",
                "GridBottomRightCornerX": "943",
                "GridBottomRightCornerY": "841",
            }
        )
        with open("config.ini", "w") as f:
            cfg.write(f)

    @staticmethod
    def load_config() -> ConfigParser:
        cfg = ConfigParser()
        cfg.read(filenames="config.ini")
        return cfg


class TradingWindow:
    def __init__(self) -> None:
        cfg = Config().load_config()["Screen"]
        self.top_left_corner = (
            int(cfg.get("GridTopLeftCornerX")),
            int(cfg.get("GridTopLeftCornerY")),
        )
        self.bottom_right_corner = (
            int(cfg.get("GridBottomRightCornerX")),
            int(cfg.get("GridBottomRightCornerY")),
        )
        self.square_width = (
            abs(self.bottom_right_corner[0] - self.top_left_corner[0]) / 12
        )
        self.square_height = (
            abs(self.bottom_right_corner[1] - self.top_left_corner[1]) / 11
        )

    def get_grid(self) -> list:
        out = []
        y = self.top_left_corner[1] + self.square_height // 2
        for _ in range(11):
            x = self.top_left_corner[0] + self.square_width // 2
            for __ in range(12):
                out.append((x, y))
                x += self.square_width
            y += self.square_height
        return out


class Item:
    def __init__(self, text: str = None) -> None:
        self.text = text
        self.parse()

    def parse(self):
        sections = self.text.split("--------")
        section_1 = sections[0].split("\n")
        base_type = section_1[2].strip("\n \r")
        properties = {"base": base_type}
        for line in self.text.split("\n"):
            if ":" in line:
                vals = line.split(":")
                properties[vals[0].strip("\n \r")] = vals[1].strip("\n \r")
        self.properties = properties


class Prices:
    def __init__(self) -> None:
        if not "prices.json" in listdir(getcwd()):
            self.fetch_prices()

    def fetch_prices(self, league: str = "Standard", language: str = "EN"):
        print('Fetching prices from poe.ninja')
        categories = ["UniqueWeapon", "UniqueArmour", "UniqueAccessory", "UniqueJewel"]
        df = pd.DataFrame()
        for cat in categories:
            req = get(
                f"https://poe.ninja/api/data/ItemOverview?league={league}&type={cat}&language={language.lower()}"
            )
            df = df.append(pd.DataFrame.from_records(req.json()["lines"]))
        df.reset_index(inplace=True, drop=True)
        df.to_json("prices.json")

    def load_prices(self):
        print('Loading saved prices')
        return pd.read_json("prices.json")

