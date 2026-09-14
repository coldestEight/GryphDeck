# GryphDeck

Gryphon Esports/Gryphon Gaming stream overlay software with a Flask JSON API
and a Next.js frontend.

## Development

Start the Flask API from the project root:

```powershell
.\Scripts\python.exe run.py
```

In a second terminal, start Next.js:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`. The available frontend routes are `/idle`,
`/pregame`, `/ingame`, and `/UI`. The API runs at `http://localhost:5000/api`.

## Flask control page

Open `http://localhost:5000` (or `/UI`) after starting Flask. This control page
does not require Next.js. It loads Valorant by default and lists game JSON files
from `app/json` in the game selector.

- Choose a game and click **Load game** to reset its component toggles while
  retaining team names, scores, rosters, and the selected scene.
- Select **Idle**, **Pre-game**, or **In-game**, then click a component to enable
  or disable it. The same button displays its state. Components at the same
  position replace each other; toggles are independent between scenes.
- Edit team names and scores, then click **Save team details**. Add or remove
  players individually. **Swap sides** calls `MatchInfo.swap_sides()` to swap
  the saved team names, scores, and rosters.

The page modifies one `StateManager` per Flask app instance, shared by clients.
State is held in memory and resets when the server restarts; use one server
process for this local control workspace. Refresh another open control page to
see the latest state. `/api/state` returns the full state, `/api/control` accepts
JSON actions, and the scene endpoints include the current match and components.

Run the control API and class tests together:

```powershell
.\Scripts\python.exe -m unittest app.test_routes app.classes.test_classes -v
```

## Class tests

Run the `GameInfo`, `MatchInfo`, and `StateManager` tests from the project root:

```powershell
.\Scripts\python.exe app/classes/test_classes.py
```

Add `--demo` to also print example game configuration, team updates, side swaps,
and component changes after the tests pass. Each class supports `print(instance)`
and `instance.print_info()` for inspecting its current state.
