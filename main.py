import os
import subprocess
import tkinter as tk
from tkinter import scrolledtext, messagebox
from langchain_google_genai import GoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import threading

# Configure the Gemini API key
GOOGLE_API_KEY = ""  # Replace with your actual API key

class NaturalLanguageTerminal:
    def __init__(self, root):
        self.root = root
        self.root.title("Natural Language Terminal")
        self.root.configure(bg='black')
        
        # Set up the terminal appearance
        self.terminal_font = ('Courier', 10)
        self.text_color = '#00FF00'  # Green text
        self.bg_color = 'black'
        
        # Command history
        self.command_history = []
        self.history_index = 0
        
        # Current working directory
        self.current_directory = os.getcwd()
        
        # Create the terminal text area
        self.terminal = scrolledtext.ScrolledText(
            root, 
            bg=self.bg_color, 
            fg=self.text_color, 
            font=self.terminal_font,
            insertbackground=self.text_color
        )
        self.terminal.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Setup prompt for the command entry
        self.display_prompt()
        
        # Set up LangChain with Gemini
        self.setup_langchain()
        
        # Bind events
        self.terminal.bind('<Return>', self.process_command)
        self.terminal.bind('<Up>', self.navigate_history_up)
        self.terminal.bind('<Down>', self.navigate_history_down)
        self.terminal.bind('<Control-c>', self.handle_interrupt)
        
        # Welcome message
        welcome_msg = "Welcome to Natural Language Terminal\n"
        welcome_msg += "Type commands in natural language (e.g., 'list all files' instead of 'ls')\n"
        welcome_msg += "Type 'exit' or 'quit' to close the terminal\n\n"
        self.terminal.insert(tk.END, welcome_msg)
        
        self.display_prompt()

    def setup_langchain(self):
        """Set up LangChain with Gemini Flash 1.5"""
        try:
            # Initialize the Gemini model through LangChain
            self.llm = GoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=GOOGLE_API_KEY,
                temperature=0.1
            )
            
            # Create the prompt template
            template = """
            You are an expert in translating natural language queries into bash commands.
            
            Current working directory: {current_dir}
            
            User query: {query}
            
            Translate this query into a valid bash command that would run in a Linux terminal.
            Provide ONLY the bash command without any explanations or comments.
            Do not include markdown formatting or code blocks in your response.
            If the query cannot be translated to a valid bash command, respond with 'ERROR: Unable to translate to a valid bash command.'
            If the query is asking for something that could be harmful or destructive, respond with 'ERROR: This command could be potentially harmful.'
            """
            
            self.prompt = PromptTemplate(
                input_variables=["query", "current_dir"],
                template=template
            )
            
            self.chain = LLMChain(llm=self.llm, prompt=self.prompt)
            
        except Exception as e:
            self.append_text(f"Error initializing LangChain: {str(e)}\n")

    def display_prompt(self):
        """Display the terminal prompt with current directory"""
        prompt = f"\n{self.current_directory}$ "
        self.terminal.insert(tk.END, prompt)
        self.terminal.see(tk.END)
        self.prompt_position = self.terminal.index(tk.INSERT)

    def get_current_command(self):
        """Get the current command from the terminal"""
        current_line = self.terminal.get(self.prompt_position, tk.END)
        return current_line.strip()

    def append_text(self, text):
        """Append text to the terminal"""
        self.terminal.insert(tk.END, text)
        self.terminal.see(tk.END)

    def translate_to_bash(self, nl_command):
        """Translate natural language to bash command using Gemini"""
        try:
            response = self.chain.invoke({
                "query": nl_command,
                "current_dir": self.current_directory
            })
            return response['text'].strip()
        except Exception as e:
            return f"ERROR: Failed to translate command: {str(e)}"

    def execute_bash_command(self, bash_command):
        """Execute a bash command and return the output"""
        try:
            # For built-in commands like cd that affect the process state
            if bash_command.startswith("cd "):
                directory = bash_command[3:].strip()
                # Handle special case for home directory
                if directory == "~":
                    directory = os.path.expanduser("~")
                # Handle relative paths
                if not os.path.isabs(directory):
                    directory = os.path.join(self.current_directory, directory)
                    
                if os.path.exists(directory) and os.path.isdir(directory):
                    self.current_directory = os.path.abspath(directory)
                    return f"Changed directory to {self.current_directory}"
                else:
                    return f"Error: Directory '{directory}' does not exist"
            
            # For all other commands
            process = subprocess.Popen(
                bash_command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.current_directory
            )
            stdout, stderr = process.communicate()
            
            if stderr:
                return stderr
            return stdout
        except Exception as e:
            return f"Error executing command: {str(e)}"

    def process_command(self, event=None):
        """Process the command entered by the user"""
        nl_command = self.get_current_command()
        self.append_text("\n")
        
        if not nl_command:
            self.display_prompt()
            return "break"
        
        # Add command to history
        self.command_history.append(nl_command)
        self.history_index = len(self.command_history)
        
        # Exit command handling
        if nl_command.lower() in ['exit', 'quit', 'close']:
            self.root.quit()
            return "break"
        
        # Process the command in a separate thread to prevent GUI freezing
        threading.Thread(target=self.process_command_thread, args=(nl_command,), daemon=True).start()
        
        return "break"

    def process_command_thread(self, nl_command):
        """Process command in a separate thread"""
        # Display the natural language command
        self.append_text(f"Translating: {nl_command}\n")
        
        # Translate to bash
        bash_command = self.translate_to_bash(nl_command)
        
        # Check for errors in translation
        if bash_command.startswith("ERROR:"):
            self.append_text(f"{bash_command}\n")
            self.display_prompt()
            return
        
        # Display the translated bash command
        self.append_text(f"Executing: {bash_command}\n")
        
        # Execute the bash command
        output = self.execute_bash_command(bash_command)
        
        # Display the command output
        if output:
            self.append_text(f"{output}\n")
        
        # Display a new prompt
        self.display_prompt()

    def navigate_history_up(self, event=None):
        """Navigate up through command history"""
        if not self.command_history:
            return "break"
            
        if self.history_index > 0:
            self.history_index -= 1
            self.terminal.delete(self.prompt_position, tk.END)
            self.terminal.insert(tk.END, self.command_history[self.history_index])
            
        return "break"

    def navigate_history_down(self, event=None):
        """Navigate down through command history"""
        if not self.command_history:
            return "break"
            
        if self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            self.terminal.delete(self.prompt_position, tk.END)
            self.terminal.insert(tk.END, self.command_history[self.history_index])
        else:
            self.history_index = len(self.command_history)
            self.terminal.delete(self.prompt_position, tk.END)
            
        return "break"

    def handle_interrupt(self, event=None):
        """Handle Ctrl+C interrupt"""
        self.append_text("\n^C\n")
        self.display_prompt()
        return "break"

def main():
    root = tk.Tk()
    root.geometry("800x600")
    app = NaturalLanguageTerminal(root)
    root.mainloop()

if __name__ == "__main__":
    main()
