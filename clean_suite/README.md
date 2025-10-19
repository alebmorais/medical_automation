# Medical Automation Suite (Clean Deployable Set)

This folder contains the production-ready pieces of the Medical Automation Suite, separated from
legacy experiments and unfinished refactors. It is meant to serve as a focused bundle you can copy
to a fresh repository, Raspberry Pi, or workstation without digging through historical artifacts.

## Folder structure

```
clean_suite/
├── README.md                     # This overview
├── raspberry_pi_server/          # Files required to run the Raspberry Pi service
└── windows_clients/              # Windows automation tools
```

### raspberry_pi_server/

| File | Purpose |
| --- | --- |
| `server.py` | Combined HTTP + Flask service that exposes the phrase browser and snippet API. |
| `server_requirements.txt` | Pip requirements for the Raspberry Pi virtual environment. |
| `SQL2.sql` | Reference dataset for the medical phrases database (`automation.db`). |
| `snippets_data.sql` | Optional seed data for the snippets database (`snippets.db`). |

Deployment steps mirror the instructions in the top-level `README.md`:

1. Copy this directory to the Pi (e.g., `/opt/medical_automation`).
2. Create a Python virtual environment and install `server_requirements.txt`.
3. Run `python server.py` once to bootstrap `automation.db`, or import `SQL2.sql` manually.
4. (Optional) Load initial snippets with `sqlite3 snippets.db < snippets_data.sql`.
5. Configure environment variables in `/etc/medical_automation.env` for logging and snippet admin.
6. Place a reverse proxy (Nginx, Caddy, etc.) in front of port 5000/8080 to terminate HTTPS.

### windows_clients/

| File | Purpose |
| --- | --- |
| `ClienteWindows` | Desktop GUI for browsing and copying phrases from the Pi. |
| `snippet_expander.py` | Background text expander that fetches snippets from the Pi. |
| `snippet_manager_gui.py` | Optional admin GUI for managing snippets (requires admin API). |
| `requirements.txt` | Shared Windows dependencies (Tk, pynput, pyautogui, etc.). |

Usage on Windows:

1. Create and activate a virtual environment.
2. Install `pip install -r requirements.txt`.
3. Edit each script near the top to point `SERVER_URL`/`MEDICAL_SERVER_URL` (or similar constants)
   to your HTTPS endpoint (e.g., `https://pi.example.com`).
4. Run the scripts as documented in the repository README. The expander must run with elevated
   privileges to capture global hotkeys.

## What was intentionally left out

The rest of the repository retains legacy prototypes, partial refactors, and scratch files for
historical reference. They are **not** required for the current deployment workflow; this folder is
the authoritative minimal set.

If you are creating a new repository, you can copy only the contents of `clean_suite/` and add your
own README and licensing as needed.
