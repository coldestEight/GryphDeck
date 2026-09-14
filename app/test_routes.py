"""Integration tests: python -m unittest app.test_routes app.classes.test_classes."""

import unittest
from unittest.mock import patch

from app import create_app


class ControlTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.manager = self.app.extensions["state_manager"]

    def action(self, action, **data):
        response = self.client.post("/api/control", json={"action": action, **data})
        self.assertEqual(response.status_code, 200, response.get_json())
        return response.get_json()

    def test_dashboard_and_default_game(self):
        for path in ("/", "/UI", "/static/css/control.css", "/static/js/control.js"):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            response.close()
        state = self.client.get("/api/state").get_json()
        self.assertEqual(state["game"], "Valorant")
        self.assertEqual(state["scene"], "idle")
        self.assertIn("Overwatch", state["games"])

    def test_toggle_conflicts_and_scene_independence(self):
        self.action("select_scene", scene="pregame")
        self.assertEqual(self.manager.current_scene, "pregame")
        for name in ("Sponsorships Badge", "Team Roster", "Score Pregame"):
            state = self.action("toggle_component", scene="pregame", component=name)
        self.assertEqual({c["name"] for c in state["components"]["pregame"] if c["enabled"]},
                         {"Sponsorships Badge", "Score Pregame"})
        self.assertFalse(any(c["enabled"] for c in state["components"]["idle"]))
        state = self.action("toggle_component", scene="pregame", component="Score Pregame")
        self.assertEqual({c["name"] for c in state["components"]["pregame"] if c["enabled"]},
                         {"Sponsorships Badge"})
        self.action("select_scene", scene="ingame")
        state = self.action("toggle_component", scene="ingame", component="Score Ingame")
        self.assertTrue(next(c for c in state["components"]["ingame"] if c["name"] == "Score Ingame")["enabled"])

    def test_match_edit_and_swap_uses_existing_method(self):
        for team, name, score in ((1, "Gryphons", 3), (2, "Rivals", 1)):
            self.action("update_team", team=team, name=name, score=score)
            self.action("add_player", team=team, player=f"Player {team}")
        self.action("add_player", team=1, player="Reserve")
        self.action("remove_player", team=1, player="Reserve")
        before = self.client.get("/api/state").get_json()["teams"]
        with patch.object(self.manager.match_info, "swap_sides", wraps=self.manager.match_info.swap_sides) as swap:
            after = self.action("swap_sides")
            swap.assert_called_once_with()
        self.assertEqual(after["teams"], before[::-1])
        self.assertEqual(self.manager.match_info.team_info(1), before[1])
        scene = self.client.get("/api/scenes/ingame").get_json()
        self.assertEqual(scene["teams"], ["Rivals", "Gryphons"])
        self.assertEqual(scene["score"], {"home": 1, "away": 3})
        self.assertEqual(scene["players"], [["Player 2"], ["Player 1"]])

    def test_game_load_keeps_match_and_resets_components(self):
        self.action("update_team", team=1, name="Gryphons", score=5)
        self.action("add_player", team=1, player="Captain")
        match = self.manager.match_info
        games = self.client.get("/api/state").get_json()["games"]
        for game in games:
            with self.subTest(game=game):
                self.action("toggle_component", scene="idle", component="Starting Soon")
                state = self.action("load_game", game=game)
                self.assertEqual(state["game_key"], game)
                self.assertIn(state["game_key"], state["games"])
                self.assertIs(self.manager.match_info, match)
                self.assertEqual(state["teams"][0], {"Name": "Gryphons", "Score": 5, "Players": ["Captain"]})
                self.assertFalse(any(c["enabled"] for components in state["components"].values() for c in components))

    def test_invalid_requests_do_not_mutate_state(self):
        before = self.client.get("/api/state").get_json()
        payloads = [None, [], {}, {"action": "unknown"},
                    {"action": "load_game", "game": "../classes/MatchInfo"},
                    {"action": "select_scene", "scene": "unknown"},
                    {"action": "toggle_component", "scene": "idle", "component": "Team Roster"},
                    {"action": "add_player", "team": 1, "player": "   "},
                    {"action": "add_player", "team": True, "player": "Player"},
                    {"action": "remove_player", "team": 1, "player": "Missing"}]
        for score in (-1, 1000, 1.5, "3", True, None):
            payloads.append({"action": "update_team", "team": 1, "name": "Do not save", "score": score})
        for payload in payloads:
            with self.subTest(payload=payload):
                response = self.client.post("/api/control", json=payload)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(self.client.get("/api/state").get_json(), before)

    def test_failed_load_retains_current_game(self):
        before = self.client.get("/api/state").get_json()
        with patch("app.classes.StateManager.GameInfo", side_effect=KeyError("enabled_components")):
            with self.assertLogs(self.app.logger, level="ERROR"):
                response = self.client.post("/api/control", json={"action": "load_game", "game": "Overwatch"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.client.get("/api/state").get_json(), before)

    def test_state_is_shared_between_clients_but_not_app_instances(self):
        self.action("update_team", team=1, name="Shared", score=1)
        self.assertEqual(self.app.test_client().get("/api/state").get_json()["teams"][0]["Name"], "Shared")
        self.assertEqual(create_app().test_client().get("/api/state").get_json()["teams"][0]["Name"], "")


if __name__ == "__main__":
    unittest.main()
