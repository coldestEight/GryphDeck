class StateManager:

    def __init__(self, game_info, match_info):
        self.game_info = game_info
        self.match_info = match_info

        self.current_scene = None
        self.current_idle_screen = None
        self.current_pregame_screen = None
        self.current_ingame_screen = None

    def set_current_scene(self, scene):
        self.current_scene = scene

    def switch_screen(self, scene_type, screen):
        if scene_type == "idle":
            self.current_idle_screen = screen
        elif scene_type == "pregame":
            self.current_pregame_screen = screen
        elif scene_type == "ingame":
            self.current_ingame_screen = screen

    def create_post_request(self):
        # Create a post request for the current scene and screen based on the game_info and match_info
        pass