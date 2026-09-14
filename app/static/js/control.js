"use strict";

const workspace = document.querySelector("#workspace");
const notice = document.querySelector("#notice");
const labels = { idle: "Idle", pregame: "Pre-game", ingame: "In-game" };
let state;
let busy = false;

function element(tag, className, text) {
  const node = document.createElement(tag);
  node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function render({ teams = false, game = false } = {}) {
  if (game) {
    const select = document.querySelector("#game");
    select.replaceChildren(...state.games.map(name => new Option(name, name)));
    select.value = state.game_key;
  }
  document.querySelectorAll("[data-scene]").forEach(button => {
    button.setAttribute("aria-pressed", String(button.dataset.scene === state.scene));
  });
  const components = state.components[state.scene];
  document.querySelector("#enabled-count").textContent = `${components.filter(item => item.enabled).length} enabled`;
  document.querySelector("#component-heading").textContent = `${labels[state.scene]} components`;
  const list = document.querySelector("#components");
  list.replaceChildren(...components.map(component => {
    const button = element("button", "component");
    button.type = "button";
    button.dataset.component = component.name;
    button.setAttribute("aria-pressed", String(component.enabled));
    const name = element("span", "component-name", component.name);
    name.append(element("small", "", component.position.replace(/([a-z])([A-Z])/g, "$1 $2")));
    const toggle = element("span", "toggle");
    toggle.setAttribute("aria-hidden", "true");
    button.append(name, element("span", "component-state", component.enabled ? "Enabled" : "Disabled"), toggle);
    button.addEventListener("click", async () => {
      await send({ action: "toggle_component", scene: state.scene, component: component.name }, "Component state updated.");
      [...list.children].find(item => item.dataset.component === component.name)?.focus();
    });
    return button;
  }));
  if (!components.length) list.append(element("p", "muted", "No components are configured for this scene."));

  state.teams.forEach((team, index) => {
    const side = index === 0 ? "left" : "right";
    document.querySelector(`#summary-${side}`).textContent = team.Name || `Team ${index + 1}`;
    document.querySelector(`#score-${side}`).textContent = team.Score;
    const card = document.querySelector(`[data-team="${index + 1}"]`);
    if (teams) {
      card.querySelector('[name="name"]').value = team.Name;
      card.querySelector('[name="score"]').value = team.Score;
    }
    card.querySelector(".player-count").textContent = `${team.Players.length} player${team.Players.length === 1 ? "" : "s"}`;
    const roster = card.querySelector(".players");
    roster.replaceChildren(...team.Players.map((player, playerIndex) => {
      const row = element("li", "player");
      const remove = element("button", "remove-player", "Remove");
      remove.type = "button";
      remove.setAttribute("aria-label", `Remove ${player} from team ${index + 1}`);
      remove.addEventListener("click", async () => {
        await send({ action: "remove_player", team: index + 1, player }, "Player removed.");
        card.querySelector('[name="player"]').focus();
      });
      row.append(element("span", "player-index", String(playerIndex + 1).padStart(2, "0")), element("span", "player-name", player), remove);
      return row;
    }));
    if (!team.Players.length) roster.append(element("li", "empty-roster", "An empty bench. Add your first player below."));
  });
}

async function send(payload, message, options = {}) {
  if (busy) return false;
  busy = true;
  workspace.disabled = true;
  workspace.setAttribute("aria-busy", "true");
  try {
    const response = await fetch("/api/control", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "The change could not be saved.");
    state = data;
    render(options);
    notice.className = "";
    notice.textContent = message;
    return true;
  } catch (error) {
    notice.className = "error";
    notice.textContent = error.message || "Unable to reach the server. Try again.";
    return false;
  } finally {
    busy = false;
    workspace.disabled = false;
    workspace.setAttribute("aria-busy", "false");
  }
}

document.querySelector("#game-form").addEventListener("submit", event => {
  event.preventDefault();
  send({ action: "load_game", game: document.querySelector("#game").value }, "Game loaded. Components reset; match details retained.", { game: true });
});
document.querySelectorAll("[data-scene]").forEach(button => {
  button.addEventListener("click", () => send({ action: "select_scene", scene: button.dataset.scene }, `${labels[button.dataset.scene]} scene selected.`));
});
document.querySelector("#swap-sides").addEventListener("click", () => {
  send({ action: "swap_sides" }, "Team names, scores, and rosters swapped.", { teams: true });
});
document.querySelectorAll(".team-card").forEach(card => {
  const team = Number(card.dataset.team);
  card.querySelector(".team-form").addEventListener("submit", event => {
    event.preventDefault();
    const form = event.currentTarget;
    send({ action: "update_team", team, name: form.elements.name.value, score: Number(form.elements.score.value) }, `Team ${team} details saved.`);
  });
  card.querySelector(".player-form").addEventListener("submit", async event => {
    event.preventDefault();
    const form = event.currentTarget;
    if (await send({ action: "add_player", team, player: form.elements.player.value }, "Player added to roster.")) form.reset();
    form.elements.player.focus();
  });
});

async function initialize() {
  try {
    const response = await fetch("/api/state", { cache: "no-store" });
    if (!response.ok) throw new Error("Could not load the workspace. Refresh to try again.");
    state = await response.json();
    render({ teams: true, game: true });
    workspace.disabled = false;
    document.querySelector("#connection").textContent = "Server connected";
    document.querySelector("#connection").classList.add("connected");
    notice.textContent = `${state.game} loaded. Ready when you are.`;
  } catch (error) {
    notice.className = "error";
    notice.textContent = error.message;
    document.querySelector("#connection").textContent = "Connection unavailable";
  }
}
initialize();
