# Medical Automation Suite

This project is a suite of tools designed to accelerate medical documentation and writing. It consists of two main components: a phrase selection client and a text snippet expander.

## 1. Medical Automation Client (`ClienteWindows`)

### 🎯 Overview

A Windows desktop client for browsing a database of medical phrases organized by categories and subcategories. It allows for quick selection and insertion of phrases into other applications via auto-typing or copying to the clipboard.

### ✨ Features

*   **Dual UI Modes**:
    *   **Webview Mode**: A modern interface that loads the web front-end directly from the Raspberry Pi (requires `pywebview`).
    *   **Legacy Mode**: A native Tkinter interface that functions as a fallback if `pywebview` is not installed or the Pi is unreachable.
*   **Global Hotkeys**:
    *   `Ctrl+Alt+D`: Automatically type the selected phrase.
    *   `Ctrl+C`: Copy the selected phrase to the clipboard.
    *   `Ctrl+Alt+M`: Minimize or restore the application window.
*   **Zoom Control**: Use `Ctrl` + `+` (zoom in), `Ctrl` + `-` (zoom out), and `Ctrl` + `0` (reset zoom) to adjust font sizes.

### 📦 Setup

1.  **Backend Server**: This client requires a backend server running on a Raspberry Pi at `http://pi.local:8080`. The server should provide the necessary API endpoints for categories, subcategories, and phrases.

2.  **Install Dependencies**:
    ```bash
    pip install requests pynput pywebview pyautogui pyperclip
    ```
    *Note: These dependencies are optional and the application will gracefully handle their absence, though functionality will be limited.*

### 🚀 Usage

Run the client from your terminal:
```bash
python ClienteWindows
```
The application will launch, connect to the server, and allow you to navigate and use the medical phrases.

---

## 2. Snippet Expander

### 🎯 Overview

A powerful text expansion tool that automatically expands custom abbreviations into full text as you type. For example, typing `//email` can expand to your full email address. It supports dynamic template variables like `{date}` and `{clipboard}`.

### 🏛️ Architecture

*   **Server (`server.py`)**: A lightweight Flask application that runs on a network machine (like a Raspberry Pi) to store and manage snippets via a REST API.
*   **Client**:
    *   `snippet_expander.py`: A background script that monitors keyboard input and performs expansions.
    *   `snippet_manager_gui.py`: A GUI application for creating, editing, and deleting snippets.

### 📦 Installation

#### On the Server (e.g., Raspberry Pi)

1.  **Install Dependencies**:
    ```bash
    pip install Flask
    ```
2.  **Run the Server**:
    ```bash
    python3 server.py
    ```
    This will create a `snippets.db` file and start the server on port 5000.

#### On the Client (Windows)

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
2.  **Configure Server URL**:
    *   Open `snippet_expander.py` and `snippet_manager_gui.py`.
    *   If your server is not at `http://pi.local:5000`, change the `SERVER_URL` variable to your server's IP address (e.g., `http://192.168.1.100:5000`).

### 🚀 Usage

1.  **Manage Snippets**:
    Run the GUI manager to add, edit, or delete your snippets.
    ```bash
    python snippet_manager_gui.py
    ```

2.  **Start Text Expansion**:
    Run the expander script in the background. On Windows, this may require Administrator privileges.
    ```bash
    python snippet_expander.py
    ```

### Hotkeys & Templates

*   **Hotkeys**: `Ctrl+Shift+R` (Sync from server), `Ctrl+Shift+T` (Toggle expansion).
*   **Template Variables**: Use `{date}`, `{time}`, `{clipboard}`, etc., in your phrases for dynamic content.

| Variable      | Output                  |
| ------------- | ----------------------- |
| `{date}`      | Current date            |
| `{time}`      | Current time            |
| `{datetime}`  | Date and time           |
| `{day}`       | Full day name           |
| `{month}`     | Full month name         |
| `{year}`      | Four-digit year         |
| `{clipboard}` | Current clipboard content |


