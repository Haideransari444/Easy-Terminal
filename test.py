import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import os
import google.generativeai as genai

# Hardcoded Gemini API key (replace with your actual key)
GEMINI_API_KEY = ""  # Replace with your key
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# Prompt for Bash script generation
bash_prompt = "Generate a Bash script that accomplishes the following task: {task}. Provide only the script content without additional explanations or markdown just give me the command only command"

class TerminalGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Custom Linux Terminal & Script Generator (Gemini)")
        self.geometry("800x500")

        # Create notebook (tabbed interface)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Terminal Tab
        self.terminal_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.terminal_frame, text="Terminal")

        # Script Generator Tab
        self.script_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.script_frame, text="Script Generator")

        # Setup Terminal
        self.setup_terminal()

        # Setup Script Generator
        self.setup_script_generator()

    # TERMINAL FUNCTIONS
    def setup_terminal(self):
        self.terminal_output = tk.Text(self.terminal_frame, bg="black", fg="red", font=("Courier", 12),
                                       insertbackground="white", wrap="word")
        self.terminal_output.pack(fill=tk.BOTH, expand=True)

        # Bind keys
        self.terminal_output.bind("<Return>", self.run_command)
        self.terminal_output.bind("<KeyPress>", self.enforce_typing_restrictions)
        self.terminal_output.bind("<BackSpace>", self.prevent_deletion)
        self.terminal_output.bind("<Delete>", self.prevent_deletion)

        # Initial message
        self.terminal_output.insert(tk.END, "Created by Haider ♥\n", "header")
        self.terminal_output.tag_config("header", foreground="red", font=("Courier", 14, "bold"))
        self.insert_prompt()

    def enforce_typing_restrictions(self, event):
        """Allow typing only after the last prompt, moving cursor if needed."""
        cursor_position = self.terminal_output.index(tk.INSERT)
        if float(cursor_position) < float(self.last_prompt_position):
            self.terminal_output.mark_set(tk.INSERT, self.last_prompt_position)
            return None  # Allow typing after moving cursor
        return None  # Allow typing if already in writable area

    def prevent_deletion(self, event):
        """Prevent deletion before the last prompt but allow within command area."""
        cursor_position = self.terminal_output.index(tk.INSERT)
        if float(cursor_position) <= float(self.last_prompt_position):
            return "break"  # Block deletion at or before prompt
        return None  # Allow deletion after prompt

    def insert_prompt(self):
        """Insert a new prompt and ensure Typing is possible."""
        current_path = os.getcwd()
        prompt = f"\n{current_path} $ "
        self.terminal_output.insert(tk.END, prompt, "prompt")
        self.terminal_output.tag_config("prompt", foreground="red", font=("Courier", 12, "bold"))
        self.terminal_output.see(tk.END)
        self.last_prompt_position = self.terminal_output.index(tk.END)
        self.terminal_output.mark_set(tk.INSERT, self.last_prompt_position)  # Set cursor precisely
        self.terminal_output.focus_set()

    def get_last_command(self):
        return self.terminal_output.get(self.last_prompt_position, tk.END).strip()

    def clear_terminal(self):
        self.terminal_output.delete("1.0", tk.END)
        self.terminal_output.insert(tk.END, "Created by Haider ♥\n", "header")
        self.insert_prompt()

    def run_command(self, event):
        command = self.get_last_command()
        self.terminal_output.insert(tk.END, "\n")
        if not command.strip():
            self.insert_prompt()
            return "break"
        if command == "clear":
            self.clear_terminal()
            return "break"
        try:
            process = subprocess.Popen(["bash", "-c", command], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate()
            if stdout:
                self.terminal_output.insert(tk.END, stdout)
            if stderr:
                self.terminal_output.insert(tk.END, stderr, "error")
                self.terminal_output.tag_config("error", foreground="red")
        except Exception as e:
            self.terminal_output.insert(tk.END, f"Error: {e}", "error")
        self.insert_prompt()
        return "break"

    # SCRIPT GENERATOR FUNCTIONS
    def setup_script_generator(self):
        tk.Label(self.script_frame, text="Enter your task (e.g., 'List all .txt files'):").pack(pady=5)
        self.script_entry = tk.Entry(self.script_frame, width=50)
        self.script_entry.pack(pady=5)

        tk.Button(self.script_frame, text="Generate Script", command=self.generate_script).pack(pady=5)

        tk.Label(self.script_frame, text="Generated Bash Script:").pack(pady=5)
        self.script_output = tk.Text(self.script_frame, height=10, width=60, bg="black", fg="red",
                                     font=("Courier", 12), insertbackground="white")
        self.script_output.pack(pady=5)

        tk.Button(self.script_frame, text="Save Script", command=self.save_script).pack(pady=5)

    def generate_script(self):
        task = self.script_entry.get()
        if not task:
            messagebox.showwarning("Input Error", "Please enter a task!")
            return
        try:
            response = model.generate_content(bash_prompt.format(task=task))
            script = response.text.strip()
            self.script_output.delete(1.0, tk.END)
            self.script_output.insert(tk.END, script)
        except Exception as e:
            messagebox.showerror("API Error", f"Failed to generate script: {e}")

    def save_script(self):
        script_content = self.script_output.get(1.0, tk.END).strip()
        if not script_content:
            messagebox.showwarning("Save Error", "No script to save!")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".sh", filetypes=[("Bash Script", "*.sh")])
        if file_path:
            with open(file_path, "w") as f:
                f.write("#!/bin/bash\n" + script_content)
            os.chmod(file_path, 0o755)
            messagebox.showinfo("Success", f"Script saved and made executable at {file_path}")

if __name__ == "__main__":
    app = TerminalGUI()
    app.mainloop()
