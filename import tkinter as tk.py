import tkinter as tk
from tkinter import messagebox, simpledialog
import requests

SERVER_URL = "https://pi.local:5000"  # Change to your Pi's IP if needed. HTTPS is recommended.

class SnippetManager(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Snippet Manager")
        self.geometry("800x600")

        self.snippets = []

        # Main frame
        main_frame = tk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Button frame
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        tk.Button(btn_frame, text="Refresh", command=self.load_snippets).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Add Snippet", command=self.add_snippet).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Edit Snippet", command=self.edit_snippet).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Delete Snippet", command=self.delete_snippet).pack(side=tk.LEFT, padx=5)

        # Snippets list
        self.listbox = tk.Listbox(main_frame, font=("Consolas", 10))
        self.listbox.pack(fill=tk.BOTH, expand=True)
        
        self.load_snippets()

    def load_snippets(self):
        """Load snippets from the server and populate the listbox."""
        try:
            response = requests.get(f"{SERVER_URL}/snippets/all", timeout=5)
            response.raise_for_status()
            self.snippets = response.json()
            
            self.listbox.delete(0, tk.END)
            for snippet in self.snippets:
                self.listbox.insert(tk.END, f"{snippet['abbreviation']:<20} -> {snippet['phrase']}")
        except requests.RequestException as e:
            messagebox.showerror("Error", f"Could not connect to server: {e}")

    def add_snippet(self):
        """Show dialog to add a new snippet."""
        abbr = simpledialog.askstring("Add Snippet", "Enter abbreviation:")
        if not abbr: return
        
        phrase = simpledialog.askstring("Add Snippet", f"Enter phrase for '{abbr}':")
        if not phrase: return

        try:
            requests.post(f"{SERVER_URL}/snippets", json={"abbreviation": abbr, "phrase": phrase}, timeout=5).raise_for_status()
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
            requests.put(f"{SERVER_URL}/snippets/{snippet['abbreviation']}", json={"phrase": new_phrase}, timeout=5).raise_for_status()
            self.load_snippets()
        except requests.RequestException as e:
            messagebox.showerror("Error", f"Failed to edit snippet: {e}")

    def delete_snippet(self):
        """Delete the selected snippet."""
        snippet = self.get_selected_snippet()
        if not snippet: return

        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{snippet['abbreviation']}'?"):
            try:
                requests.delete(f"{SERVER_URL}/snippets/{snippet['abbreviation']}", timeout=5).raise_for_status()
                self.load_snippets()
            except requests.RequestException as e:
                messagebox.showerror("Error", f"Failed to delete snippet: {e}")

if __name__ == "__main__":
    app = SnippetManager()
    app.mainloop()
