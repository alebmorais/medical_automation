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
Copy the necessary server files to a directory on your Raspberry Pi. This includes the server script, requirements, and the SQL data files.

```bash
# Example using scp from your local machine
scp server.py server_requirements.txt SQL2.sql snippets_data.sql pi@<raspberry_pi_ip>:/home/pi/medical_automation/
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

### Step 4: Populate Databases
The server uses two separate databases.

1.  **Medical Phrases Database (`automation.db`)**:
    This database is created and populated automatically from `SQL2.sql` the first time the server runs. No manual action is needed for this part, as long as `SQL2.sql` was copied to the server.

2.  **Snippets Database (`snippets.db`)**:
    This database contains the text expansion snippets. After the server runs for the first time (which creates the empty database file), you must populate it using the `snippets_data.sql` script.

    Run the following command on your Raspberry Pi:
    ```bash
    sqlite3 /home/pi/medical_automation/snippets.db < /home/pi/medical_automation/snippets_data.sql
    ```
    This command will delete any existing snippets and populate the table with a fresh set from your SQL file.

### Step 5: Create a Systemd Service
To ensure the unified server runs automatically on boot, we will create a `systemd` service.

1.  Create a new service file:
    ```bash
    sudo nano /etc/systemd/system/medical-server.service
    ```

2.  Add the following content. Note that `ExecStart` now points to the `server.py` script.

    ```ini
    [Unit]
    Description=Medical Automation Unified Server
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

### Step 6: Enable and Start the Service
1.  Reload the systemd daemon to recognize the new service:
    ```bash
    sudo systemctl daemon-reload
    ```
2.  Enable the service to start on boot:
    ```bash
    sudo systemctl enable medical-server.service
    ```
3.  Start the service immediately:
    ```bash
    sudo systemctl start medical-server.service
    ```
4.  Check the status to ensure it's running without errors:
    ```bash
    sudo systemctl status medical-server.service
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

## 3. Troubleshooting

### "Connection Refused" Error

If you see an error like `ConnectionRefusedError` or `target machine actively refused it`, it means the server is not responding. Follow these steps on your **Raspberry Pi** to diagnose the issue.

#### Step 1: Check if the Server Service is Running

Use `systemctl` to check the status of the service you created.

```bash
sudo systemctl status snippet-server.service
```

-   If the status is `active (running)`, the server is running. Proceed to Step 2.
-   If the status is `inactive (dead)` or `failed`, the service is not running. Try restarting it:
    ```bash
    sudo systemctl restart snippet-server.service
    ```
    If it fails again, check the logs for errors:
    ```bash
    journalctl -u snippet-server.service -n 50 --no-pager
    ```
    This will show the last 50 log entries, which usually contain the reason for the failure.

#### Step 2: Check if the Server is Listening on the Network

The server must listen on `0.0.0.0` to be accessible from other devices, not `127.0.0.1` (localhost).

1.  Use the `netstat` command to see which ports are open:
    ```bash
    sudo netstat -tulpn | grep 5000
    ```

2.  **Analyze the output:**
    -   **Correct:** `tcp        0      0 0.0.0.0:5000            0.0.0.0:*               LISTEN      ...`
        This means the server is correctly listening on all network interfaces.
    -   **Incorrect:** `tcp        0      0 127.0.0.1:5000          0.0.0.0:*               LISTEN      ...`
        This means the server is only listening for local connections. Ensure `server.py` contains `app.run(host='0.0.0.0', port=5000)`.
    -   **No Output:** If you see no output, the server application is not running on port 5000. Go back to Step 1.

#### Step 3: Check the Firewall

If the server is running and listening correctly, a firewall might be blocking the connection.

1.  Check the status of the Uncomplicated Firewall (`ufw`):
    ```bash
    sudo ufw status
    ```

2.  **If the status is `active`**, you must explicitly allow traffic on port 5000:
    ```bash
    sudo ufw allow 5000/tcp
    sudo ufw reload
    ```
    This command opens the port for incoming TCP connections.

### Service is Active but Not Listening on Port

You may encounter a situation where `systemctl status` shows the service is `active (running)`, but `netstat -tulpn` shows nothing listening on the expected port. This usually means the Python script started but failed internally before the web server could launch.

To diagnose this, you need to view the detailed logs from your service.

#### Step 1: View the Service Logs

Use the `journalctl` command to see the full output from your service, including any Python error messages.

```bash
# View the last 100 log entries for the service
journalctl -u snippet-server.service -n 100 --no-pager
```

Look for a `Traceback` (Python error) in the output. This will tell you exactly what went wrong inside the `server.py` script.

#### Step 2: Common Causes and Solutions

-   **Database Errors**: The script might be failing to connect to or initialize the `snippets.db` database. Ensure the `snippets.db` file and the directory containing it are owned by the `pi` user and have the correct permissions.
    ```bash
    # To fix permissions in your project directory
    sudo chown -R pi:pi /home/pi/medical_automation
    ```

-   **Syntax Errors**: A simple typo in `server.py` can cause it to fail on startup. The `journalctl` log will show the exact line number of the error.

-   **Dependency Issues**: If a required package (like `Flask`) was not installed correctly in the virtual environment, the script will fail. The log will show an `ImportError`.

After fixing the issue found in the logs, restart the service to apply the changes:
```bash
sudo systemctl restart snippet-server.service
```

### Service Fails with "No such file or directory"

If the `journalctl` log shows an error like `can't open file ... [Errno 2] No such file or directory`, it means the `systemd` service cannot find your Python script.

#### Step 1: Verify the File Name and Location

First, confirm the exact name and location of your server script on the Raspberry Pi.

1.  Connect to your Raspberry Pi and navigate to the project directory:
    ```bash
    cd /home/pi/medical_automation
    ```

2.  List the files in the directory:
    ```bash
    ls -l
    ```

3.  Look for your server script in the output. Is it named `server.py`, `ServidorCode2`, or something else? Make sure it's actually there.

#### Step 2: Verify the Systemd Service File

Next, ensure the `ExecStart` path in your service file matches the actual path and filename from Step 1.

1.  Display the contents of your service file:
    ```bash
    cat /etc/systemd/system/snippet-server.service
    ```

2.  Check the `ExecStart` line. For example:
    `ExecStart=/home/pi/medical_automation/venv/bin/python /home/pi/medical_automation/server.py`

3.  If the path or filename is incorrect, edit the service file:
    ```bash
    sudo nano /etc/systemd/system/snippet-server.service
    ```
    Correct the filename to match what you found in Step 1.

#### Step 3: Reload and Restart the Service

After correcting the service file, you must reload `systemd` and restart the service.

```bash
sudo systemctl daemon-reload
sudo systemctl restart snippet-server.service
sudo systemctl status snippet-server.service
```

This should resolve the "No such file or directory" error.

### "Address already in use" Error

If you see an error like `OSError: [Errno 98] Address already in use` when starting a server, it means another process is already using the port (e.g., 5000 or 8080). This often happens if a previous server instance did not shut down correctly.

#### Step 1: Find the Process Using the Port

Use the `lsof` (list open files) command to find the Process ID (PID) that is occupying the port. Replace `<port_number>` with the port from the error message (e.g., `5000`).

```bash
# Example for port 5000
sudo lsof -i :5000
```

This command will show you a list of processes. Look for the one with a state of `LISTEN` and note its `PID`.

#### Step 2: Stop the Process

Once you have the PID, you can stop the process using the `kill` command.

```bash
# Replace <PID> with the process ID you found
kill <PID>
```

If the process does not stop, you can force it to stop with `kill -9`:

```bash
kill -9 <PID>
```

#### Step 3: Check for a Running Service

If you configured the server to run as a `systemd` service, that service might be the one holding the port. In that case, you should manage it with `systemctl`.

```bash
# Stop the service if it's running
sudo systemctl stop snippet-server.service

# Then try running your script manually for testing
source venv/bin/activate
python server.py
```

After stopping the conflicting process, you should be able to start your server script without the "Address already in use" error.


