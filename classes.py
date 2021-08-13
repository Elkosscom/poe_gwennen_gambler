import webbrowser
from configparser import ConfigParser
from os import getcwd, listdir
from string import capwords

import pandas as pd
from requests import get


class Config:
    def __init__(self) -> None:
        self.base_defaults = {
            "Hotkey": "F6",
            "RefreshPricesOnStart": "True",
            "MouseMoveDelay": "0.01",
            "Language": "EN",
            "League": "Expedition",
            "WindowTitle": "Path of Exile",
        }
        self.prices_defaults = {
            "UnlinkedOnly": "True",
            "MinimumMeanChaosValue": "0.0",
            "IgnoreFatedUniques": "True",
            "UseBlacklist": "True",
            "MinItemLevelRestriction": "False",
            "SortBy": "Chaos Average",
        }
        self.screen_defaults = {
            "GridTopLeftCornerX": "310",
            "GridTopLeftCornerY": "262",
            "GridBottomRightCornerX": "943",
            "GridBottomRightCornerY": "841",
        }
        self.sections = {
            "Base": self.base_defaults,
            "Prices": self.prices_defaults,
            "Screen": self.screen_defaults,
        }
        if "config.ini" not in listdir(getcwd()):
            self.create_config()
        self.verify_config()

    def create_config(self) -> None:
        cfg = ConfigParser()
        cfg.optionxform = str
        for key in self.sections:
            cfg.add_section(key)
            cfg[key].update(self.sections[key])
        self.save_config(cfg)

    @staticmethod
    def load_config() -> ConfigParser:
        cfg = ConfigParser()
        cfg.optionxform = str
        cfg.read(filenames="config.ini")
        return cfg

    @staticmethod
    def save_config(config) -> None:
        with open("config.ini", "w") as f:
            config.write(f)

    def verify_config(self) -> None:
        cfg = self.load_config()
        for section in self.sections:
            section_dict = self.sections[section]
            for key in section_dict:
                if key not in cfg[section].keys():
                    cfg[section].update({key: section_dict[key]})
        self.save_config(cfg)

    @staticmethod
    def get_display_size() -> tuple:
        import tkinter

        root = tkinter.Tk()
        root.update_idletasks()
        root.attributes("-fullscreen", True)
        root.state("iconic")
        height = root.winfo_screenheight()
        width = root.winfo_screenwidth()
        root.destroy()
        return width, height

    def get_grid_position(self, screen_x: int = None, screen_y: int = None) -> dict:
        width, height = screen_x, screen_y
        if screen_x is None or screen_y is None:
            width, height = self.get_display_size()

        ratios = {
            16
            / 9: {
                "GridTopLeftCornerX": str(0.1613 * width),
                "GridTopLeftCornerY": str(0.2418 * height),
                "GridBottomRightCornerX": str(0.4914 * width),
                "GridBottomRightCornerY": str(0.7793 * height),
            },
            24
            / 10: {
                "GridTopLeftCornerX": str(0.2487 * width),
                "GridTopLeftCornerY": str(0.2406 * height),
                "GridBottomRightCornerX": str(0.4948 * width),
                "GridBottomRightCornerY": str(0.7813 * height),
            },
            16
            / 10: {
                "GridTopLeftCornerX": str(0.1238 * width),
                "GridTopLeftCornerY": str(0.2429 * height),
                "GridBottomRightCornerX": str(0.4893 * width),
                "GridBottomRightCornerY": str(0.7781 * height),
            },
        }
        if not width / height in ratios:
            return {
                "GridTopLeftCornerX": "310",
                "GridTopLeftCornerY": "262",
                "GridBottomRightCornerX": "943",
                "GridBottomRightCornerY": "841",
            }
        return ratios[width / height]


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

    def parse(self) -> None:
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
        if "prices.json" not in listdir(getcwd()):
            self.fetch_prices()

    def fetch_prices(self, league: str = "Standard", language: str = "EN") -> None:
        categories = ["UniqueWeapon", "UniqueArmour", "UniqueAccessory", "UniqueJewel"]
        df = pd.DataFrame()
        for cat in categories:
            req = get(
                f"https://poe.ninja/api/data/ItemOverview?league={league}&type={cat}&language={language.lower()}"
            )
            df = df.append(pd.DataFrame.from_records(req.json()["lines"]))
        df.reset_index(inplace=True, drop=True)
        df.to_json("prices.json")

    def load_prices(self, show_ignored: bool = False) -> pd.DataFrame:
        prices = pd.read_json("prices.json")
        prices["name"] = prices["name"].str.strip()
        prices["name"] = prices["name"].apply(capwords)
        prices["Items"] = 1
        cfg = Config().load_config()
        ignores = Blacklist().read_ignore_lists()
        prices["Fated"] = False
        prices["Blacklisted"] = False
        if cfg["Prices"].get("UnlinkedOnly") == "True":
            prices = prices.loc[prices["links"].isna()]
        if cfg["Prices"].get("IgnoreFatedUniques") == "True":
            prices.loc[prices["name"].isin(set(ignores["fated"])), "Fated"] = True
        if cfg["Prices"].get("UseBlacklist") == "True":
            print(set(ignores["blacklist"]))
            prices.loc[
                prices["name"].isin(set(ignores["blacklist"])), "Blacklisted"
            ] = True
        if show_ignored:
            return prices
        return prices.loc[(prices["Fated"] == False) & (prices["Blacklisted"] == False)]


class Blacklist:
    def __init__(self) -> None:
        if not "fated_uniques.txt" in listdir(getcwd()):
            self.set_up_fated_uniques()
        if not "blacklist.txt" in listdir(getcwd()):
            self.set_up_blacklist()

    @staticmethod
    def set_up_fated_uniques() -> None:
        with open("fated_uniques.txt", "w") as f:
            f.write(
                "Hyrri's Demise\nNgamahu Tiki\nTimetwist\nFrostferno\nDuskblight\nDoomfletch's Prism\nThe Iron Fortress\nGeofri's Devotion\nThe Effigon\nCorona Solaris\nDreadsurge\nWinterweave\nCameria's Avarice\nSanguine Gambol\nThe Dancing Duo\nFox's Fortune\nWindshriek\nDeidbellow\nCrystal Vault\nChaber Cairn\nThe Signal Fire\nHrimburn\nVoidheart\nGreedtrap\nCragfall\nWildwrap\nThirst for Horrors\nThe Oak\nMartyr's Crown\nAmplification Rod\nThe Cauteriser\nAsenath's Chant\nSunspite\nThe Gryphon\nRealm Ender\nGeofri's Legacy\nEzomyte Hold\nDeath's Opus\nDreadbeak\nPanquetzaliztli\nShavronne's Gambit\nThe Nomad\nThe Tactician\nKarui Charge\nWall of Brambles\nKaom's Way\nDoedre's Malevolence\nWhakatutuki o Matua\nQueen's Escape\nMalachai's Awakening\nAtziri's Reflection\nThe Tempest\nSilverbough\nKaltensoul\nThe Stormwall\nMirebough\nHrimnor's Dirge"
            )

    @staticmethod
    def set_up_blacklist() -> None:
        with open("blacklist.txt", "w"):
            pass

    @staticmethod
    def read_ignore_lists() -> dict:
        with open("blacklist.txt", "r") as f:
            blacklist = f.readlines()
        with open("fated_uniques.txt", "r") as f:
            fated = f.readlines()
        return {
            "fated": [capwords(item) for item in fated],
            "blacklist": [capwords(item) for item in blacklist],
        }

    @staticmethod
    def add_to_blacklist(item_names: list) -> None:
        with open("blacklist.txt", "a") as f:
            for item in item_names:
                f.write(f"\n{item}")

    def remove_from_blacklist(self, item_names: list) -> None:
        existing = [item.strip(" \n") for item in self.read_ignore_lists()["blacklist"]]
        new_blacklist = [item for item in existing if item not in item_names]
        with open("blacklist.txt", "w") as f:
            for item in new_blacklist:
                f.write(f"\n{item}")


class VersionCheck:
    def __init__(self) -> None:
        self.version = 1.2
        self.latest_version = self.get_latest_version()

    @staticmethod
    def get_latest_version() -> float:
        req = get("https://api.github.com/repos/Elkosscom/poe_gwennen_gambler/releases")
        releases = [float(release["tag_name"]) for release in req.json()]
        releases.sort()
        return float(releases[-1])

    def perform_version_check(self) -> bool:
        return self.version >= self.latest_version

    def open_latest_version_page(self) -> None:
        webbrowser.open(
            f"https://github.com/Elkosscom/poe_gwennen_gambler/releases/tag/{self.latest_version}"
        )
