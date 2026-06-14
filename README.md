# hitter

Top-down abstract extraction game built with pygame.

## Premise
Sneak through black-and-white facilities, steal the objective, and extract. Stay in shadows, avoid enemy sight cones, and avoid triggering full alerts.

## Features
- Two handcrafted levels with patrol routes, objective, and extraction zones
- Stealth with shadow coverage and enemy vision cones
- Shared enemy alert behavior with last-known-position rushes and return fire
- Combat with pistol shots and thrown daggers
- Color disguise system from downed enemies to bypass colored gates
- Puzzle flow with keys, buttons, and static security cameras

## Controls
- `WASD` / arrow keys: move
- Left mouse: shoot
- Right mouse: throw dagger
- `C`: take enemy color disguise from nearby downed enemy

## Local run
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python game/main.py
```

## GitHub Pages publish
A GitHub Actions workflow at `.github/workflows/publish-game.yml` builds the pygame project with `pygbag` and deploys to GitHub Pages on pushes to `main`.
