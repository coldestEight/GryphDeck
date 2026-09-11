import json

class GameInfo:

    def __init__(self, name):
        self.name = name
        self.element_positions = []
        self.enabled_screens = []

        self.maps = []
        self.chars = []

    def load_game_info(self, game_name):
        with open(f"json\\{game_name}.json", mode="r", encoding="utf-8") as json_file:
            data = json.load(json_file)
            self.name = data["name"]
            self.element_positions = data["element_positions"]
            self.enabled_screens = data["enabled_screens"]
            self.maps = data["maps"]
            self.chars = data["chars"] 