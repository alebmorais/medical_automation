import tkinter as tk
from tkinter import messagebox, simpledialog
import requests
from urllib.parse import urljoin, quote

SERVER_URL = "https://192.168.0.34:5000"
MEDICAL_SERVER_URL = "https://192.168.0.34:8080"

class SnippetManager(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Snippet Manager")
        self.geometry("800x600")

        self.snippets = []

        # Menu
        self.create_menu()

        # Main frame
        main_frame = tk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Button frame
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        tk.Button(btn_frame, text="Refresh", command=self.load_snippets).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Add Snippet", command=self.add_snippet).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Add Phrase Selector", command=self.add_phrase_selector).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Edit Snippet", command=self.edit_snippet).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Delete Snippet", command=self.delete_snippet).pack(side=tk.LEFT, padx=5)

        # Snippets list
        self.listbox = tk.Listbox(main_frame, font=("Consolas", 10))
        self.listbox.pack(fill=tk.BOTH, expand=True)
        
        self.load_snippets()

    def create_menu(self):
        """Creates the application menu."""
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="How to Use", command=self.show_help)

    def show_help(self):
        """Displays a help message box."""
        help_text = """
How to Configure Snippets:

1.  Add Snippet: Click 'Add' and enter a short abbreviation (e.g., '//email') and the full text you want it to expand to.

2.  Edit Snippet: Select a snippet from the list and click 'Edit' to change its expansion text.

3.  Delete Snippet: Select a snippet and click 'Delete' to remove it.

4.  Refresh: Click 'Refresh' to load the latest snippets from the server.

Your snippets are stored on the server and are available to the expander client after a refresh.

Available Template Variables:
- {date}: Current date (YYYY-MM-DD)
- {time}: Current time (HH:MM)
- {datetime}: Current date and time
- {day}: Full name of the day
- {month}: Full name of the month
- {year}: Current four-digit year
- {clipboard}: The current content of your clipboard
"""
        messagebox.showinfo("Help", help_text)

    def load_snippets(self):
        """Load snippets from the server and populate the listbox."""
        try:
            url = urljoin(SERVER_URL, "snippets/all")
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, list):
                raise ValueError("Server response is not a list of snippets.")
            self.snippets = data

            self.listbox.delete(0, tk.END)
            for snippet in self.snippets:
                abbr = snippet.get('abbreviation', '')
                phrase = snippet.get('phrase', '')
                self.listbox.insert(tk.END, f"{abbr:<25} -> {phrase}")
        except (requests.RequestException, ValueError, KeyError) as e:
            messagebox.showerror("Error", f"Could not load snippets: {e}")

    def add_snippet(self):
        """Show dialog to add a new snippet."""
        abbr = simpledialog.askstring("Add Snippet", "Enter abbreviation:")
        if not abbr: return
        
        phrase = simpledialog.askstring("Add Snippet", f"Enter phrase for '{abbr}':")
        if not phrase: return

        try:
            url = urljoin(SERVER_URL, "snippets")
            requests.post(url, json={"abbreviation": abbr, "phrase": phrase}, timeout=5).raise_for_status()
            self.load_snippets()
        except requests.RequestException as e:
            messagebox.showerror("Error", f"Failed to add snippet: {e}")

    def add_phrase_selector(self):
        """Show dialog to add a new phrase selector snippet."""
        abbr = simpledialog.askstring("Add Selector", "Enter abbreviation (e.g., '//crise'):")
        if not abbr: return
        
        # Fetch categories to show as options
        try:
            url = urljoin(MEDICAL_SERVER_URL, "api/categorias")
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            categories = response.json()
            if not isinstance(categories, list):
                raise ValueError("Server did not return a list of categories.")
        except (requests.RequestException, ValueError) as e:
            messagebox.showerror("Error", f"Could not fetch categories from medical server: {e}")
            return

        # Use a custom dialog to select a category
        cat_name = self.ask_category("Select Category", f"Choose a category for '{abbr}':", categories)
        if not cat_name: return

        # Use the new, more powerful SEARCH_PHRASES syntax
        phrase = f"{{{{SEARCH_PHRASES:{cat_name}}}}}"

        try:
            url = urljoin(SERVER_URL, "snippets")
            requests.post(url, json={"abbreviation": abbr, "phrase": phrase}, timeout=5).raise_for_status()
            self.load_snippets()
        except requests.RequestException as e:
            messagebox.showerror("Error", f"Failed to add snippet: {e}")

    def get_selected_snippet(self):
        """Get the currently selected snippet from the listbox."""
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Warning", "Please select a snippet first.")
            return None
        return self.snippets[selected_indices[0]]

    def edit_snippet(self):
        """Show dialog to edit the selected snippet."""
        snippet = self.get_selected_snippet()
        if not snippet: return

        new_phrase = simpledialog.askstring("Edit Snippet", "Enter new phrase:", initialvalue=snippet['phrase'])
        if not new_phrase: return

        try:
            encoded_abbr = quote(snippet['abbreviation'], safe='')
            url = urljoin(SERVER_URL, f"snippets/{encoded_abbr}")
            requests.put(url, json={"phrase": new_phrase}, timeout=5).raise_for_status()
            self.load_snippets()
        except requests.RequestException as e:
            messagebox.showerror("Error", f"Failed to edit snippet: {e}")

    def delete_snippet(self):
        """Delete the selected snippet."""
        snippet = self.get_selected_snippet()
        if not snippet: return

        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{snippet['abbreviation']}'?"):
            try:
                encoded_abbr = quote(snippet['abbreviation'], safe='')
                url = urljoin(SERVER_URL, f"snippets/{encoded_abbr}")
                requests.delete(url, timeout=5).raise_for_status()
                self.load_snippets()
            except requests.RequestException as e:
                messagebox.showerror("Error", f"Failed to delete snippet: {e}")

    def ask_category(self, title, prompt, options):
        """Shows a dialog to select from a list of options."""
        dialog = tk.Toplevel(self)
        dialog.title(title)
        dialog.geometry("350x200")
        
        tk.Label(dialog, text=prompt, wraplength=330).pack(pady=10)
        
        listbox = tk.Listbox(dialog)
        for option in options:
            listbox.insert(tk.END, option)
        listbox.pack(fill=tk.BOTH, expand=True, padx=10)

        result = {"value": None}

        def on_ok():
            selected_indices = listbox.curselection()
            if selected_indices:
                result["value"] = options[selected_indices[0]]
            dialog.destroy()

        ok_button = tk.Button(dialog, text="OK", command=on_ok)
        ok_button.pack(pady=10)

        self.wait_window(dialog)
        
        return result["value"]


if __name__ == "__main__":
    app = SnippetManager()
    app.mainloop()
