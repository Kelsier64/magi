import subprocess
import os

def execute_bash(command):
    """
    Executes a bash command and returns the output.
    
    Args:
        command (str): The bash command to execute (e.g., 'ls -la', 'git status'). (required)
    """
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)
        return f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    except Exception as e:
        return f"Error executing command: {e}"

#todo: 5 seconds check once 


def read_file(path, start_line=None, end_line=None):
    """
    Reads the content of a file, optionally within a specific line range.
    
    Args:
        path (str): The absolute path to the file to read. (required)
        start_line (int): The starting line number (1-indexed, inclusive). (optional)
        end_line (int): The ending line number (1-indexed, inclusive). (optional)
    """
    try:
        if not os.path.exists(path):
            return f"Error: File {path} does not exist."
        
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        total_lines = len(lines)
        
        if start_line is None:
            start_line = 1
        if end_line is None:
            end_line = total_lines
            
        # Validate ranges
        if start_line < 1: start_line = 1
        if end_line > total_lines: end_line = total_lines
        if start_line > end_line:
            return f"Error: Start line {start_line} is greater than end line {end_line}."

        # Adjust for 0-based indexing
        content = "".join(lines[start_line-1:end_line])
        
        return f"File: {path} (Lines {start_line}-{end_line} of {total_lines})\n{content}"
    except Exception as e:
        return f"Error reading file: {e}"

def write_to_file(path, content):
    """
    Writes content to a file, overwriting it.
    
    Args:
        path (str): The absolute path to the file. (required)
        content (str): The content to write to the file. (required)
    """
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing to file: {e}"

def edit_file(path, target_text, replacement_text):
    """
    Replaces the first occurrence of `target_text` with `replacement_text` in the file.
    
    Args:
        path (str): The absolute path to the file. (required)
        target_text (str): The exact text block to replace. (required)
        replacement_text (str): The new text to insert in place of target_text. (required)
    """
    try:
        if not os.path.exists(path):
            return f"Error: File {path} does not exist."
        
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            
        if target_text not in content:
            return f"Error: Target text not found in {path}. Please ensure exact match including whitespace."
        
        # Replace only the first occurrence to avoid accidents
        new_content = content.replace(target_text, replacement_text, 1)
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
            
        return f"Successfully edited {path}"
    except Exception as e:
        return f"Error editing file: {e}"

def ls(path="."):
    """
    Lists files in a directory.
    
    Args:
        path (str): The directory path to list (default is current directory '.').
    """
    try:
        if not path:
            path = "."
        return "\n".join(os.listdir(path))
    except Exception as e:
        return f"Error listing directory: {e}"

def grep(pattern, path="."):
    """
    SEARCH for pattern in files/directories using system grep/ripgrep.
    
    Args:
        pattern (str): The text pattern to search for. (required)
        path (str): The file or directory path to search in.
    """
    try:
        # Check if it's a file or directory
        is_dir = os.path.isdir(path)
        
        # Construct command
        # -r: recursive (if dir)
        # -n: line numbers
        # -I: ignore binary files
        cmd = ["grep", "-n", "-I", f'"{pattern}"', path]
        if is_dir:
            cmd.insert(1, "-r")
            
        command_str = " ".join(cmd)
        result = subprocess.run(command_str, shell=True, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            # Limit output length to avoid context overflow
            output = result.stdout
            if len(output) > 2000:
                return output[:2000] + "\n... (truncated)"
            return output
        elif result.returncode == 1:
            return "No matches found."
        else:
            return f"Error (code {result.returncode}): {result.stderr}"
    except Exception as e:
        return f"Error during grep: {e}"

def send_message(message):
    """
    Sends a message to the user/human.
    
    Args:
        message (str): The content of the message to send. (required)
    """
    print(f"Agent: {message}")
    return "Message sent."


# def call_agent(agent):
#     pass
# def update_ltm():
#     pass

def update_stm():
    pass


available_tools = {
    "execute_bash": execute_bash,
    "read_file": read_file,
    "write_to_file": write_to_file,
    "edit_file": edit_file,
    "ls": ls,
    "grep": grep,
    "send_message": send_message
}


