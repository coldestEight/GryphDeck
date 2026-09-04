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
