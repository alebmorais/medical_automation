import time
import json
import os
import threading
import datetime
import requests
from urllib.parse import urljoin
from pynput import keyboard
import pyperclip
import tkinter as tk
from tkinter import ttk

SERVER_URL = "https://192.168.0.34:5000"  # Changed to HTTPS
MEDICAL_SERVER_URL = "https://192.168.0.34:8080" # Changed to HTTPS
CACHE_FILE = "snippets_cache.json"

class PhraseSelector(tk.Toplevel):
    """A GUI for selecting phrases from categories."""
    def __init__(self, parent, category_name, controller):
        super().__init__(parent)
        self.category_name = category_name
        self.kb_controller = controller
        self.selected_phrase = None

        safe_category_name = "".join(c for c in category_name if c.isalnum() or c in (" ", "_", "-"))
        self.title(f"Select Phrase from '{safe_category_name}'")
        self.geometry("600x400")
        self.attributes("-topmost", True)

        self.create_widgets()
        self.load_data()
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.grab_set()
        self.focus_force()

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Filter:").pack(anchor="w")
        self.search_entry = ttk.Entry(main_frame)
        self.search_entry.pack(fill=tk.X, pady=(0, 10))
        self.search_entry.bind("<KeyRelease>", self.filter_phrases)

        ttk.Label(main_frame, text="Available Phrases:").pack(anchor="w")
        self.phrase_list = tk.Listbox(main_frame)
        self.phrase_list.pack(fill=tk.BOTH, expand=True)
        self.phrase_list.bind("<Double-1>", self.on_select)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(btn_frame, text="Select", command=self.on_select).pack(side=tk.RIGHT)
        ttk.Button(btn_frame, text="Cancel", command=self.cancel).pack(side=tk.RIGHT, padx=5)

    def load_data(self):
        """Load all phrases for the given category."""
        try:
            # Fetch all phrases for the given category
            params = {'categoria': self.category_name}
            url = urljoin(MEDICAL_SERVER_URL, "api/frases")
            phrases_res = requests.get(url, params=params, timeout=10)
            phrases_res.raise_for_status()
            self.phrases = phrases_res.json()
            
            self.populate_list()

        except requests.RequestException as e:
            print(f"Error loading medical data: {e}")
            self.cancel()

    def populate_list(self, query=""):
        """Populate the listbox with phrases, optionally filtering by a query."""
        self.phrase_list.delete(0, tk.END)
        
        filtered_phrases = self.phrases
        if query:
            query = query.lower()
            filtered_phrases = [
                p for p in self.phrases 
                if query in p.get('nome', '').lower() or query in p.get('conteudo', '').lower()
            ]

        if not filtered_phrases:
            self.phrase_list.insert(tk.END, "No matching phrases found.")
            return

        # Sort phrases by subcategory and then by order
        filtered_phrases.sort(key=lambda p: (p.get('subcategoria', ''), p.get('ordem', 0)))

        last_subcategory = None
        for p in filtered_phrases:
            # Add a subcategory header if it changes
            subcategory = p.get('subcategoria', 'Uncategorized')
            if subcategory != last_subcategory:
                self.phrase_list.insert(tk.END, f"--- {subcategory} ---")
                self.phrase_list.itemconfig(tk.END, {'fg': 'grey'}) # Make header distinct
                last_subcategory = subcategory
            
            self.phrase_list.insert(tk.END, f"  {p.get('nome', 'Unnamed Phrase')}")
    
    def filter_phrases(self, event=None):
        """Filter the phrases in the listbox based on search entry."""
        self.populate_list(self.search_entry.get())

    def on_select(self, event=None):
        selected_indices = self.phrase_list.curselection()
        if not selected_indices: return
        
        selected_text = self.phrase_list.get(selected_indices[0]).strip()

        # If a header was clicked, do nothing
        if selected_text.startswith("---"):
            return

        # Find the corresponding phrase object to get the full content
        for p in self.phrases:
            if p.get('nome', 'Unnamed Phrase') == selected_text:
                self.selected_phrase = p.get('conteudo')
                self.destroy()
                return

    def cancel(self):
        self.selected_phrase = None
        self.destroy()

class SnippetExpander:
    def __init__(self):
        self.kb_controller = keyboard.Controller()
        self.snippets = {}
        self.buffer = ""
        self.trigger = "//"
        self.is_enabled = True
        self.load_snippets_from_cache()
        self.root = tk.Tk() # Hidden root for dialogs
        self.root.withdraw()

    def sync_from_server(self):
        """Fetch snippets from the server and update local cache."""
        try:
            url = urljoin(SERVER_URL, "snippets")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            self.snippets = response.json()
            with open(CACHE_FILE, 'w') as f:
                json.dump(self.snippets, f)
            print("Snippets synced from server.")
        except requests.RequestException as e:
            print(f"Error syncing from server: {e}")

    def load_snippets_from_cache(self):
        """Load snippets from the local cache file."""
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as f:
                self.snippets = json.load(f)
            print("Snippets loaded from cache.")
        else:
            self.sync_from_server()

    def process_template(self, text):
        """Process template variables in the expansion text."""
        now = datetime.datetime.now()
        replacements = {
            "{date}": now.strftime("%Y-%m-%d"),
            "{time}": now.strftime("%H:%M"),
            "{datetime}": now.strftime("%Y-%m-%d %H:%M"),
            "{day}": now.strftime("%A"),
            "{month}": now.strftime("%B"),
            "{year}": str(now.year),
            "{clipboard}": pyperclip.paste(),
        }
        for var, value in replacements.items():
            text = text.replace(var, value)
        return text

    def expand(self, abbr, expansion):
        """Delete the abbreviation and type the expansion."""
        # Check for special selector syntax
        if expansion.startswith("{{SEARCH_PHRASES:") and expansion.endswith("}}"):
            # Schedule the GUI to run in the main thread
            self.root.after(0, self.show_phrase_selector, abbr, expansion, "SEARCH_PHRASES")
            return
        if expansion.startswith("{{SELECT_PHRASE:") and expansion.endswith("}}"):
            # Schedule the GUI to run in the main thread
            self.root.after(0, self.show_phrase_selector, abbr, expansion, "SELECT_PHRASE")
            return

        # Delete abbreviation plus the commit character (space/tab/enter)
        for _ in range(len(abbr) + 1):
            self.kb_controller.press(keyboard.Key.backspace)
            self.kb_controller.release(keyboard.Key.backspace)
        
        # Type expansion
        processed_text = self.process_template(expansion)
        self.kb_controller.type(processed_text)
        self.buffer = ""

    def show_phrase_selector(self, abbr, expansion, mode):
        """Creates and shows the phrase selector dialog."""
        category_name = expansion.replace(f"{{{{{mode}:", "").replace("}}", "")
        
        # First, delete the typed abbreviation
        for _ in range(len(abbr) + 1):
            self.kb_controller.press(keyboard.Key.backspace)
            self.kb_controller.release(keyboard.Key.backspace)
        
        # Show selector dialog
        selector = PhraseSelector(self.root, category_name, self.kb_controller)
        self.root.wait_window(selector) # Wait for it to close
        
        if selector.selected_phrase:
            self.kb_controller.type(selector.selected_phrase)
        self.buffer = ""

    def on_press(self, key):
        """Handle key press events."""
        if not self.is_enabled:
            return

        # Check for expansion on commit keys
        if key in {keyboard.Key.space, keyboard.Key.enter, keyboard.Key.tab}:
            if self.buffer in self.snippets:
                self.expand(self.buffer, self.snippets[self.buffer])
            else:
                self.buffer = ""
            return

        try:
            char = key.char
            if char:
                self.buffer += char
        except AttributeError:
            # Handle other special keys
            if key == keyboard.Key.backspace:
                self.buffer = self.buffer[:-1]
            else:
                # Any other special key also clears the buffer
                self.buffer = ""

    def toggle_expansion(self):
        """Enable or disable snippet expansion."""
        self.is_enabled = not self.is_enabled
        status = "enabled" if self.is_enabled else "disabled"
        print(f"Snippet expansion {status}.")

    def start(self):
        """Start the keyboard listener and hotkeys."""
        # Hotkeys for control
        hotkeys = keyboard.GlobalHotKeys({
            '<ctrl>+<shift>+r': self.sync_from_server,
            '<ctrl>+<shift>+t': self.toggle_expansion,
        })
        hotkeys.start()

        # Keyboard listener for expansion (runs in a background thread)
        listener = keyboard.Listener(on_press=self.on_press)
        listener.daemon = True
        listener.start()
        
        print("Snippet expander running...")
        print("Hotkeys: Ctrl+Shift+R (Sync), Ctrl+Shift+T (Toggle)")
        
        # Run the Tkinter main loop in the main thread
        self.root.mainloop()

if __name__ == "__main__":
    expander = SnippetExpander()
    expander.start()
