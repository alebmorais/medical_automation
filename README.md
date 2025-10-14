# Medical Automation Suite - Deployment Guide

This guide provides step-by-step instructions for deploying the Medical Automation Suite, which includes the **Medical Phrase Client** and the **Snippet Expander**.

## Dependency Management

This project uses two separate files to manage dependencies for the server and the client:

-   `server_requirements.txt`: Contains packages needed only for the server (e.g., `Flask`).
-   `requirements.txt`: Contains packages needed for the client applications on Windows (e.g., `pynput`, `pywebview`).

## 1. Server Deployment (Raspberry Pi)

The server component runs on a Raspberry Pi or any Linux machine on your network. It hosts the REST APIs for both the medical phrases and the text snippets.

### Prerequisites
- A Raspberry Pi with Raspberry Pi OS (or any Debian-based Linux).
- Python 3 installed.
- Network connectivity between the server and client machines.

### Step 1: Copy Project Files to Server
Copy the necessary server files to a directory on your Raspberry Pi.

```bash
# Example using scp from your local machine to copy the server script and its requirements
scp server.py server_requirements.txt pi@<raspberry_pi_ip>:/home/pi/medical_automation/
```

### Step 2: Set Up Python Virtual Environment
Using a virtual environment is highly recommended to manage dependencies.

1.  **Connect to your Raspberry Pi** (e.g., via SSH) and navigate to your project directory:
    ```bash
    cd /home/pi/medical_automation
    ```

2.  **Create a virtual environment**:
    ```bash
    python3 -m venv venv
    ```
    This creates a `venv` folder in your project directory.

3.  **Activate the virtual environment**:
    ```bash
    source venv/bin/activate
    ```
    Your terminal prompt should now be prefixed with `(venv)`.

### Step 3: Install Server Dependencies
With the virtual environment active, install the required packages from `server_requirements.txt`.

```bash
pip install -r server_requirements.txt
```

### Step 4: Create a Systemd Service
To ensure the snippet server runs automatically on boot using the virtual environment, we will create a `systemd` service.

1.  Create a new service file:
    ```bash
    sudo nano /etc/systemd/system/snippet-server.service
    ```

2.  Add the following content. Note that `ExecStart` now points to the Python executable **inside the virtual environment**.

    ```ini
    [Unit]
    Description=Snippet Expansion Server
    After=network.target

    [Service]
    Type=simple
    User=pi
    WorkingDirectory=/home/pi/medical_automation
    ExecStart=/home/pi/medical_automation/venv/bin/python /home/pi/medical_automation/server.py
    Restart=always

    [Install]
    WantedBy=multi-user.target
    ```

### Step 5: Enable and Start the Service
1.  Reload the systemd daemon to recognize the new service:
    ```bash
    sudo systemctl daemon-reload
    ```
2.  Enable the service to start on boot:
    ```bash
    sudo systemctl enable snippet-server.service
    ```
3.  Start the service immediately:
    ```bash
    sudo systemctl start snippet-server.service
    ```
4.  Check the status to ensure it's running without errors:
    ```bash
    sudo systemctl status snippet-server.service
    ```

## 2. Client Deployment (Windows)

The client applications run on your primary Windows machine.

### Prerequisites
- Windows 10 or 11.
- Python 3 installed.

### Step 1: Set Up Python Virtual Environment
1.  Copy all project files to a folder on your Windows machine.
2.  Open a Command Prompt or PowerShell and navigate to the project directory.
3.  **Create a virtual environment**:
    ```powershell
    python -m venv venv
    ```
4.  **Activate the virtual environment**:
    ```powershell
    .\venv\Scripts\activate
    ```
    Your terminal prompt should now be prefixed with `(venv)`.

### Step 2: Install Client Dependencies
With the virtual environment active, install all required Python packages using `requirements.txt`:
```bash
pip install -r requirements.txt
```
*Note: This will install `requests`, `pynput`, `pyperclip`, `pyautogui`, and `pywebview`.*

### Step 3: Configure Server URLs
Before running the client applications, you **must** configure them to point to your server's IP address.

1.  Find your Raspberry Pi's IP address (e.g., `192.168.1.100`).
2.  Open the following files in a text editor:
    -   `ClienteWindows`
    -   `snippet_expander.py`
    -   `snippet_manager_gui.py`
3.  In each file, find the URL variables and replace `pi.local` with your server's IP address.
    -   `pi_url = "http://192.168.1.100:8080"`
    -   `SERVER_URL = "http://192.168.1.100:5000"`
    -   `MEDICAL_SERVER_URL = "http://192.168.1.100:8080"`

### Step 4: Running the Applications

Make sure your virtual environment is active before running the applications.

*   **Medical Phrase Client**:
    ```bash
    python ClienteWindows
    ```
*   **Snippet Manager GUI**:
    ```bash
    python snippet_manager_gui.py
    ```
*   **Snippet Expander** (requires Administrator rights):
    1.  Open Command Prompt **as Administrator**.
    2.  Navigate to the project directory and activate the virtual environment (`.\venv\Scripts\activate`).
    3.  Run the script:
        ```bash
        python snippet_expander.py
        ```

### (Optional) Step 5: Creating Executables for Easy Access

For easier daily use, you can package the Python scripts into standalone `.exe` files using `PyInstaller`.

1.  **Install PyInstaller** (in your activated virtual environment):
    ```bash
    pip install pyinstaller
    ```

2.  **Create the Executables**:
    Run these commands from your project directory.

    *   **For GUI Applications** (this hides the console window):
        ```bash
        pyinstaller --onefile --windowed ClienteWindows
        pyinstaller --onefile --windowed snippet_manager_gui.py
        ```

    *   **For the Background Snippet Expander**:
        ```bash
        pyinstaller --onefile snippet_expander.py
        ```

3.  **Find the Executables**:
    The `.exe` files will be located in the `dist` folder inside your project directory. You can create shortcuts to these files on your Desktop or Start Menu for easy access. Remember to run the `snippet_expander.exe` **as Administrator**.


