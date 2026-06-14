# hitter

Top-down abstract extraction game built with pygame.

## Premise

Sneak through black-and-white facilities, steal the objective, and extract. Stay in shadows, avoid enemy sight cones, and avoid triggering full alerts.

## Features

- Two handcrafted levels with patrol routes, objective, and extraction zones
- Stealth with shadow coverage and enemy vision cones
- Three enemy difficulty tiers (grey, purple, blue) with escalating speed and detection range
- Enemy AI with patrol, investigate, and combat states and shared alertness
- Last-known-position rushes and shared alert between enemies
- Auto-lean near walls — player shape changes contextually when adjacent to a wall
- Color disguise system — take a downed enemy's color to reduce detection and bypass matching gates
- Gate system opened by keys or floor buttons
- Security cameras that trigger shared alerts
- Combat with pistol shots (36 rounds) and thrown daggers (7)
- Enemy return fire in combat state
- Health system — 5 hits before elimination
- Full mobile / touch controls in-browser (D-pad, shoot, dagger, disguise buttons)
- Level progression — advance after extracting from one level to the next
- Web build via pygbag, deployed to GitHub Pages on every push to `main`

## Controls

| Input | Action |
|---|---|
| `WASD` / arrow keys | Move |
| Left mouse / `SHOOT` | Fire pistol |
| Right mouse / `DAG` | Throw dagger |
| `C` / `CLR` | Take color disguise from a downed nearby enemy |

Lean is automatic — step close to a wall to peek from it.

## Objective

1. Reach the **yellow circle** to secure the objective.
2. Reach the **blue extraction zone** (top-left) to complete the level.

Gates are blocked by default. Open them by:
- Picking up a **key** (yellow rectangle) and walking into the matching key gate.
- Stepping on a **floor button** (green square) to toggle the matching button gate.
- Wearing a matching **color disguise** to walk straight through.

## Local run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python game/main.py
```

## Web build

A GitHub Actions workflow at `.github/workflows/publish-game.yml` builds the project with `pygbag` and deploys to GitHub Pages on every push to `main`.

Play online at: `https://chriswhitson.github.io/hitter`
