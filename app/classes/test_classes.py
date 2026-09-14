"""Run with `python app/classes/test_classes.py`; add --demo to print examples."""

import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import sys
import unittest

if __package__:
    from .GameInfo import GameInfo
    from .MatchInfo import MatchInfo
    from .StateManager import StateManager
else:
    from GameInfo import GameInfo
    from MatchInfo import MatchInfo
    from StateManager import StateManager


CONFIG_DIR = Path(__file__).resolve().parent.parent / "json"


class GameInfoTests(unittest.TestCase):
    def test_load_every_game_configuration(self):
        paths = list(CONFIG_DIR.glob("*.json"))
        self.assertTrue(paths, "No game configurations found")
        for path in paths:
            with self.subTest(game=path.stem):
                data = json.loads(path.read_text(encoding="utf-8"))
                game = GameInfo(path.stem)
                for field in ("name", "element_positions", "enabled_components", "maps", "chars"):
                    self.assertEqual(getattr(game, field), data[field])

    def test_reload_replaces_configuration(self):
        game = GameInfo("Valorant")
        game.load_game_info("Miscellaneous")
        expected = GameInfo("Miscellaneous")
        self.assertEqual(vars(game), vars(expected))

    def test_missing_game_raises_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            GameInfo("__missing_test_game__")


class MatchInfoTests(unittest.TestCase):
    def setUp(self):
        self.match = MatchInfo()

    def test_initial_teams(self):
        for team in (1, 2):
            self.assertEqual(self.match.team_info(team), {
                "Name": "", "Score": 0, "Players": [],
            })

    def test_update_names_and_scores(self):
        for team, name, score in ((1, "Gryphons", 3), (2, "Rivals", 1)):
            self.assertTrue(self.match.update_team_name(team, name))
            self.assertTrue(self.match.update_team_score(team, score))
            self.assertEqual(self.match.team_info(team), {
                "Name": name, "Score": score, "Players": [],
            })

    def test_add_and_remove_players(self):
        self.assertTrue(self.match.add_player(1, "Player One"))
        self.assertTrue(self.match.add_player(1, "Player Two"))
        self.assertTrue(self.match.add_player(2, "Opponent"))
        self.assertTrue(self.match.remove_player(1, "Player One"))
        self.assertFalse(self.match.remove_player(1, "Missing Player"))
        self.assertEqual(self.match.team_info(1)["Players"], ["Player Two"])
        self.assertEqual(self.match.team_info(2)["Players"], ["Opponent"])

    def test_invalid_team_numbers_leave_match_unchanged(self):
        before = str(self.match)
        for team in (-1, 0, 3):
            with self.subTest(team=team):
                self.assertIsNone(self.match.team_info(team))
                self.assertFalse(self.match.update_team_name(team, "Invalid"))
                self.assertFalse(self.match.update_team_score(team, 10))
                self.assertFalse(self.match.add_player(team, "Invalid"))
                self.assertFalse(self.match.remove_player(team, "Invalid"))
        self.assertEqual(str(self.match), before)

    def test_swap_sides_moves_names_scores_and_players(self):
        for team in (1, 2):
            self.match.update_team_name(team, f"Team {team}")
            self.match.update_team_score(team, team * 2)
            self.match.add_player(team, f"Player {team}")
        before = [self.match.team_info(1), self.match.team_info(2)]
        self.match.swap_sides()
        self.assertEqual(self.match.team_info(1), before[1])
        self.assertEqual(self.match.team_info(2), before[0])
        self.match.swap_sides()
        self.assertEqual(self.match.team_info(1), before[0])
        self.assertEqual(self.match.team_info(2), before[1])


class StateManagerTests(unittest.TestCase):
    def setUp(self):
        self.state = StateManager("Valorant")

    def test_initial_game_and_match(self):
        self.assertIsInstance(self.state.game_info, GameInfo)
        self.assertEqual(self.state.game_info.name, "Valorant")
        self.assertIsInstance(self.state.match_info, MatchInfo)

    def test_scene_assignment_for_every_game(self):
        for path in CONFIG_DIR.glob("*.json"):
            state = StateManager(path.stem)
            for scene in ("idle", "pregame", "ingame"):
                with self.subTest(game=path.stem, scene=scene):
                    expected = [
                        [component["Name"], component["Position"], False]
                        for component in state.game_info.element_positions
                        if component["Name"] in state.game_info.enabled_components
                        and component["Scene"].lower() in (scene, "all")
                    ]
                    self.assertCountEqual(
                        getattr(state, f"current_{scene}_components"), expected,
                    )

    def test_enable_and_disable_in_each_scene(self):
        for scene, name in (
            ("idle", "Starting Soon"),
            ("pregame", "Team Roster"),
            ("ingame", "Score Ingame"),
        ):
            with self.subTest(scene=scene):
                components = getattr(self.state, f"current_{scene}_components")
                component = next(item for item in components if item[0] == name)
                self.state.enable_component(scene, name)
                self.assertTrue(component[2])
                self.state.disable_component(scene, name)
                self.assertFalse(component[2])

    def test_same_position_conflict_preserves_other_positions(self):
        self.state.enable_component("pregame", "Sponsorships Badge")
        self.state.enable_component("pregame", "Team Roster")
        self.state.enable_component("pregame", "Score Pregame")
        enabled = {
            name for name, position, active in self.state.current_pregame_components
            if active
        }
        self.assertEqual(enabled, {"Score Pregame", "Sponsorships Badge"})

    def test_shared_components_have_independent_scene_state(self):
        self.state.enable_component("idle", "Sponsorships Badge")
        for scene in ("idle", "pregame", "ingame"):
            components = getattr(self.state, f"current_{scene}_components")
            badge = next(item for item in components if item[0] == "Sponsorships Badge")
            self.assertEqual(badge[2], scene == "idle")

    def test_unknown_scene_or_component_is_a_no_op(self):
        self.state.enable_component("idle", "Starting Soon")
        before = str(self.state)
        for operation in (self.state.enable_component, self.state.disable_component):
            operation("unknown", "Starting Soon")
            operation("idle", "Unknown Component")
        self.assertEqual(str(self.state), before)

    def test_reloading_resets_state_without_duplicates(self):
        before = str(self.state)
        self.state.enable_component("idle", "Starting Soon")
        self.state.load_components(self.state.game_info)
        self.assertEqual(str(self.state), before)

    def test_instances_do_not_share_mutable_state(self):
        other = StateManager("Valorant")
        before = str(other)
        self.state.match_info.add_player(1, "Player One")
        self.state.enable_component("idle", "Starting Soon")
        self.state.game_info.maps.append("Test Map")
        self.assertEqual(str(other), before)
        self.assertNotIn("Test Map", other.game_info.maps)


class PrintInfoTests(unittest.TestCase):
    def test_print_info_and_builtin_print_show_readable_state(self):
        state = StateManager("Valorant")
        state.match_info.update_team_name(1, "Gryphons")
        state.match_info.add_player(1, "Player One")
        for instance, expected_text in (
            (state.game_info, ("Valorant", "maps", "chars", "Team Roster")),
            (state.match_info, ("Gryphons", "Player One", "Score")),
            (state, ("Valorant", "Gryphons", "Player One", "idle", "pregame", "ingame")),
        ):
            with self.subTest(class_name=type(instance).__name__):
                output = io.StringIO()
                with redirect_stdout(output):
                    instance.print_info()
                    print(instance)
                self.assertEqual(output.getvalue(), (str(instance) + "\n") * 2)
                for value in expected_text:
                    self.assertIn(value, output.getvalue())


def print_demo():
    """Show a populated match and the result of switching overlapping components."""
    state = StateManager("Valorant")
    print("\nGame configuration:")
    state.game_info.print_info()

    match = state.match_info
    match.update_team_name(1, "Gryphons")
    match.update_team_name(2, "Rivals")
    match.update_team_score(1, 3)
    match.update_team_score(2, 1)
    match.add_player(1, "Player One")
    match.add_player(2, "Player Two")
    print("\nMatch before swapping sides:")
    match.print_info()
    match.swap_sides()
    print("\nMatch after swapping sides:")
    match.print_info()

    state.enable_component("pregame", "Team Roster")
    state.enable_component("pregame", "Sponsorships Badge")
    print("\nState with roster and sponsorship badge enabled:")
    state.print_info()
    state.enable_component("pregame", "Score Pregame")
    print("\nState after Score Pregame replaces Team Roster at Center:")
    state.print_info()
    state.disable_component("pregame", "Score Pregame")
    print("\nState after disabling Score Pregame:")
    state.print_info()


if __name__ == "__main__":
    show_demo = "--demo" in sys.argv
    if show_demo:
        sys.argv.remove("--demo")
    result = unittest.main(verbosity=2, exit=False).result
    if show_demo and result.wasSuccessful():
        print_demo()
    sys.exit(0 if result.wasSuccessful() else 1)
