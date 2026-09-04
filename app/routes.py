from flask import Blueprint, jsonify


main = Blueprint("main", __name__, url_prefix="/api")

SCENES = {
    "idle": {
        "title": "Stream starting soon",
        "message": "The broadcast will begin shortly.",
        "status": "idle",
    },
    "pregame": {
        "title": "Get ready",
        "message": "Players are preparing for the next match.",
        "teams": ["Gryphons", "Opponent"],
        "theme": "pregame",
    },
    "ingame": {
        "title": "Match in progress",
        "message": "Live match data will appear here.",
        "score": {"home": 0, "away": 0},
        "teams": ["Gryphons", "Opponent"],
        "theme": "ingame",
    },
    "ui": {
        "title": "GryphDeck control UI",
        "message": "Choose a scene to preview.",
        "routes": ["/idle", "/pregame", "/ingame", "/UI"],
        "theme": "ui",
    },
}


@main.route("/")
def index():
    return jsonify(
        name="GryphDeck API",
        endpoints=["/api/health", "/api/scenes/<scene>"],
    )


@main.route("/health")
def health():
    return jsonify(status="ok")


@main.route("/scenes/<string:scene>")
def scene(scene):
    scene_data = SCENES.get(scene.lower())
    if scene_data is None:
        return jsonify(error="Scene not found"), 404

    return jsonify(scene=scene.lower(), **scene_data)
