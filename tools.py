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


def read_file(path):
    """
    Reads the content of a file.
    
    Args:
        path (str): The absolute path to the file to read.(required)
    """
    try:
        if not os.path.exists(path):
            return f"Error: File {path} does not exist."
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"

def write_to_file(path, content):
    """
    Writes content to a file, overwriting it.
    
    Args:
        path (str): The absolute path to the file.(required)
        content (str): The content to write to the file.(required)
    """
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing to file: {e}"


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
    SEARCH for pattern in files/directories using a simple walk (simplified grep).
    
    Args:
        pattern (str): The text pattern to search for. (required)
        path (str): The file or directory path to search in (default is current directory '.').
    """
    results = []
    try:
        if os.path.isfile(path):
            with open(path, "r", errors='ignore') as f:
                for i, line in enumerate(f, 1):
                    if pattern in line:
                        results.append(f"{path}:{i}: {line.strip()}")
        else:
            for root, _, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Skip hidden files/dirs and obvious non-text
                    if ".git" in file_path or "__pycache__" in file_path:
                        continue
                    try:
                        with open(file_path, "r", errors='ignore') as f:
                            for i, line in enumerate(f, 1):
                                if pattern in line:
                                    results.append(f"{file_path}:{i}: {line.strip()}")
                    except:
                        continue
        return "\n".join(results) if results else "No matches found."
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
    "ls": ls,
    "grep": grep,
    "send_message": send_message
}


