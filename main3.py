import os
import re
import sys
import subprocess
import tkinter as tk
from tkinter import scrolledtext, messagebox
from langchain_google_genai import GoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import threading

# Configure the Google API key
GOOGLE_API_KEY = ""  # Replace with your actual API key

class NaturalLanguageTerminal:
    def __init__(self, root):
        self.root = root
        self.root.title("Easy Terminal")
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
        
        # Terminal state tracking
        self.input_start = "1.0"
        self.input_active = False
        self.current_command = ""
        
        # Setup LangChain with Gemini
        self.setup_langchain()
        
        # Bind events
        self.terminal.bind('<Key>', self.handle_keypress)
        self.terminal.bind('<Return>', self.handle_return)
        self.terminal.bind('<BackSpace>', self.handle_backspace)
        self.terminal.bind('<Delete>', self.handle_delete)
        self.terminal.bind('<Up>', self.handle_up)
        self.terminal.bind('<Down>', self.handle_down)
        self.terminal.bind('<Left>', self.handle_left)
        self.terminal.bind('<Right>', self.handle_right)
        self.terminal.bind('<Home>', self.handle_home)
        self.terminal.bind('<End>', self.handle_end)
        self.terminal.bind('<Control-c>', self.handle_interrupt)
        self.terminal.bind('<Control-l>', self.handle_clear)
        self.terminal.bind("<Tab>", self.handle_tab)
        
        # Welcome message
        welcome_msg = "Welcome to Natural Language Terminal\n"
        welcome_msg += "- Type normal bash commands OR natural language\n"
        welcome_msg += "- Natural language will be automatically detected and translated\n"
        welcome_msg += "- Type 'exit' or 'quit' to close the terminal\n\n"
        welcome_msg += "- __Created by Muzammil Haider with ♥__ \n\n"
        self.terminal.insert(tk.END, welcome_msg)
        
        # Initial prompt
        self.display_prompt()
        
        # Disable text widget configuration for proper terminal behavior
        self.terminal.config(state=tk.NORMAL)
        
        # Set focus on terminal
        self.terminal.focus_set()

    def setup_langchain(self):
        """Set up LangChain with Gemini"""
        try:
            # Initialize the Gemini model through LangChain
            self.llm = GoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=GOOGLE_API_KEY,
                temperature=0.1
            )
            
            # Create the prompt template - Updated to address translation issues
            template = """
            You are an expert in translating natural language queries into bash commands.
            
            Current working directory: {current_dir}
            
            User query: {query}
            
            Determine if this query is already a valid bash command. If it is, return "VALID_COMMAND".
            
            If it's natural language, translate it into a valid bash command that would run in a Linux terminal.
            Provide ONLY the bash command without any explanations, prefixes, or comments.
            Do not include ANY extra text, markdown formatting, or code blocks in your response.
            Your response must contain exactly one line with just the bash command.
            
            Be lenient with natural language queries and try to find the most reasonable bash equivalent.
            Only respond with "ERROR: Unable to translate to a valid bash command." if you're absolutely certain 
            there is no reasonable bash command that can satisfy the request.
            
            If the query is asking for something that could be harmful or destructive, respond with 
            "ERROR: This command could be potentially harmful."
            """
            
            self.prompt = PromptTemplate(
                input_variables=["query", "current_dir"],
                template=template
            )
            
            self.chain = LLMChain(llm=self.llm, prompt=self.prompt)
            
        except Exception as e:
            self.append_output(f"Error initializing LangChain: {str(e)}\n")

    def disable_text_widget(self):
        """Disable user editing in areas they shouldn't edit"""
        self.terminal.config(state=tk.DISABLED)

    def enable_text_widget(self):
        """Enable user editing"""
        self.terminal.config(state=tk.NORMAL)

    def display_prompt(self):
        """Display the terminal prompt with current directory"""
        self.enable_text_widget()
        prompt = f"{self.current_directory}$ "
        self.terminal.insert(tk.END, prompt)
        self.terminal.see(tk.END)
        self.input_start = self.terminal.index(tk.INSERT)
        self.input_active = True

    def append_output(self, text):
        """Append output text to the terminal"""
        self.enable_text_widget()
        self.terminal.insert(tk.END, text)
        self.terminal.see(tk.END)

    def get_current_command(self):
        """Get the current command from the terminal"""
        try:
            command = self.terminal.get(self.input_start, tk.END)
            return command.strip()
        except:
            return ""

    def handle_keypress(self, event):
        """Handle key press events"""
        # Ignore events like Shift, Control, etc.
        if len(event.char) == 0 or event.char == '\r' or event.char == '\t':
            return
            
        # Ignore if cursor is before input_start
        if self.terminal.compare(tk.INSERT, '<', self.input_start):
            self.terminal.mark_set(tk.INSERT, tk.END)
            
        # Check if we need to enable editing
        cursor_pos = self.terminal.index(tk.INSERT)
        if self.terminal.compare(cursor_pos, '<', self.input_start):
            self.terminal.mark_set(tk.INSERT, tk.END)

    def handle_return(self, event):
        """Handle Return key - process the command"""
        self.terminal.config(state=tk.NORMAL)
        command = self.get_current_command()
        self.terminal.insert(tk.END, "\n")
        
        if command:
            self.command_history.append(command)
            self.history_index = len(self.command_history)
            
            # Exit command handling
            if command.lower() in ['exit', 'quit']:
                self.root.quit()
                return "break"
                
            # Clear command handling
            if command.lower() in ['clear', 'cls']:
                self.clear_terminal()
                return "break"
                
            # Process command in a separate thread
            threading.Thread(target=self.process_command, args=(command,), daemon=True).start()
        else:
            self.display_prompt()
            
        return "break"

    def handle_backspace(self, event):
        """Handle backspace key"""
        if self.terminal.compare(tk.INSERT, '<=', self.input_start):
            return "break"
        return

    def handle_delete(self, event):
        """Handle delete key"""
        if self.terminal.compare(tk.INSERT, '<', self.input_start):
            return "break"
        return
        
    def handle_left(self, event):
        """Handle left arrow key"""
        if self.terminal.compare(tk.INSERT, '<=', self.input_start):
            return "break"
        return

    def handle_home(self, event):
        """Handle home key"""
        self.terminal.mark_set(tk.INSERT, self.input_start)
        return "break"

    def handle_end(self, event):
        """Handle end key"""
        self.terminal.mark_set(tk.INSERT, tk.END)
        return "break"

    def handle_right(self, event):
        """Handle right arrow key"""
        return

    def handle_up(self, event):
        """Handle up arrow key - navigate command history"""
        if not self.command_history or self.history_index <= 0:
            return "break"
            
        self.terminal.delete(self.input_start, tk.END)
        self.history_index -= 1
        self.terminal.insert(self.input_start, self.command_history[self.history_index])
        return "break"

    def handle_down(self, event):
        """Handle down arrow key - navigate command history"""
        if not self.command_history:
            return "break"
            
        self.terminal.delete(self.input_start, tk.END)
        if self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            self.terminal.insert(self.input_start, self.command_history[self.history_index])
        else:
            self.history_index = len(self.command_history)
        return "break"

    def handle_interrupt(self, event):
        """Handle Ctrl+C interrupt"""
        self.append_output("\n^C\n")
        self.display_prompt()
        return "break"
        
    def handle_clear(self, event):
        """Handle Ctrl+L (clear)"""
        self.clear_terminal()
        return "break"
        
    def handle_tab(self, event):
        """Handle tab completion"""
        command = self.get_current_command()
        
        # Basic implementation of tab completion for files in current directory
        if " " in command:
            parts = command.split(" ")
            prefix = parts[-1]
            
            try:
                files = os.listdir(self.current_directory)
                matches = [f for f in files if f.startswith(prefix)]
                
                if len(matches) == 1:
                    self.terminal.delete(f"{self.input_start}+{len(command) - len(prefix)}", tk.END)
                    self.terminal.insert(tk.INSERT, matches[0])
                elif len(matches) > 1:
                    # Show options
                    self.terminal.insert(tk.END, "\n" + "  ".join(matches) + "\n")
                    self.display_prompt()
                    self.terminal.insert(tk.INSERT, command)
            except Exception as e:
                # Silently handle tab completion errors
                pass
                
        return "break"

    def clear_terminal(self):
        """Clear the terminal screen"""
        self.terminal.delete("1.0", tk.END)
        self.display_prompt()

    def detect_command_type(self, command):
        """
        Detect if the command is a bash command or natural language
        Returns: 'bash' or 'natural'
        """
        # Common bash commands regex pattern - expanded to include more commands
        bash_pattern = r'^(cd|ls|mkdir|rmdir|rm|cp|mv|grep|cat|echo|pwd|sudo|apt|git|touch|chmod|chown|man|find|ps|kill|top|df|du|zip|unzip|tar|ssh|scp|ping|ifconfig|ip|curl|wget|history|nano|vim|vi|less|more|tail|head|sort|sed|awk|cut|tr|wc|who|w|whoami|date|cal|clear|cls|exit|quit|reboot|shutdown|uname|which|whereis|locate|ln|mount|umount|free|netstat|traceroute|source|xargs|env|export|chroot|fg|bg)( .*)?$'
        
        # Check if it's a recognized bash command
        if re.match(bash_pattern, command) or '|' in command or ';' in command or '>' in command or '&' in command:
            return 'bash'
            
        # Check if it contains flags or options (-a, --help)
        if ' -' in command or ' --' in command:
            return 'bash'
            
        # Check if it seems to be a path or has quotes
        if ('/' in command or '~' in command or 
            ('"' in command and '"' in command[command.index('"')+1:]) or
            ("'" in command and "'" in command[command.index("'")+1:])):
            return 'bash'
            
        # Check if it's a common shorthand command
        if command in ['..', '.', '!!', '!$']:
            return 'bash'
            
        # By default, try to interpret as natural language if it's more than one word
        # or contains certain natural language indicators
        natural_indicators = ['show', 'list', 'display', 'find', 'get', 'what', 'how', 'create', 
                              'make', 'write', 'search', 'tell', 'give', 'count', 'calculate', 
                              'please', 'help', 'can', 'could', 'would', 'do', 'does']
        
        command_words = command.lower().split()
        if len(command_words) > 1 or any(word in natural_indicators for word in command_words):
            return 'natural'
            
        # Default to bash if we're not sure
        return 'bash'

    def process_command(self, command):
        """Process the command entered by the user"""
        # Detect if it's a bash command or natural language
        command_type = self.detect_command_type(command)
        
        if command_type == 'bash':
            # Try to execute directly
            output = self.execute_bash_command(command)
            self.append_output(output)
        else:
            # Try to translate natural language to bash
            self.append_output(f"Translating: {command}\n")
            
            try:
                response = self.chain.invoke({
                    "query": command,
                    "current_dir": self.current_directory
                })
                
                translated_command = response['text'].strip()
                
                # Clean up response - remove any markdown or extra text that might appear
                translated_command = self.clean_llm_response(translated_command)
                
                # Check if it's already a valid command (no need for translation)
                if translated_command == "VALID_COMMAND":
                    self.append_output(f"Executing as-is: {command}\n")
                    output = self.execute_bash_command(command)
                # Check for errors in translation
                elif translated_command.startswith("ERROR:"):
                    self.append_output(f"{translated_command}\n")
                    self.display_prompt()
                    return
                # Execute the translated command
                else:
                    self.append_output(f"Executing: {translated_command}\n")
                    output = self.execute_bash_command(translated_command)
                    
                self.append_output(output)
                
            except Exception as e:
                self.append_output(f"Error processing command: {str(e)}\n")
                
        self.display_prompt()
    
    def clean_llm_response(self, response):
        """Clean LLM response from markdown, code blocks, or extra text"""
        # If it's already an error message, return it as is
        if response.startswith("ERROR:"):
            return response
            
        if response == "VALID_COMMAND":
            return response
            
        # Remove markdown code blocks if present
        response = re.sub(r'```(?:bash|shell)?\s*(.*?)\s*```', r'\1', response, flags=re.DOTALL)
        
        # If multiple lines, get only the first non-empty line that doesn't start with #
        lines = [line.strip() for line in response.split('\n') if line.strip() and not line.strip().startswith('#')]
        if lines:
            return lines[0]
            
        return response

    def execute_bash_command(self, bash_command):
        """Execute a bash command and return the output"""
        try:
            # Handle built-in commands like cd that affect the process state
            if bash_command.strip().startswith("cd ") or bash_command.strip() == "cd":
                dir_part = bash_command.strip()[3:].strip() if bash_command.strip() != "cd" else ""
                
                # Handle special case for home directory
                if dir_part == "~" or dir_part == "":
                    target_dir = os.path.expanduser("~")
                # Handle parent directory
                elif dir_part == "..":
                    target_dir = os.path.dirname(self.current_directory)
                # Handle absolute paths
                elif os.path.isabs(dir_part):
                    target_dir = dir_part
                # Handle relative paths
                else:
                    target_dir = os.path.join(self.current_directory, dir_part)
                    
                if os.path.exists(target_dir) and os.path.isdir(target_dir):
                    self.current_directory = os.path.abspath(target_dir)
                    return f"Changed directory to {self.current_directory}\n"
                else:
                    return f"bash: cd: {dir_part}: No such file or directory\n"
            
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
            elif stdout:
                return stdout
            else:
                return ""
                
        except Exception as e:
            return f"Error executing command: {str(e)}\n"

def main():
    root = tk.Tk()
    root.geometry("800x600")
    app = NaturalLanguageTerminal(root)
    root.mainloop()

if __name__ == "__main__":
    main()
