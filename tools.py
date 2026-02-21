import os
import json
from pty_manager import command_manager


def _resolve_path(path):
    """Resolve a path relative to cwd if not absolute."""
    if not os.path.isabs(path):
        return os.path.join(os.getcwd(), path)
    return path


def run_command(command, cwd=None, timeout="1"):
    """
    Execute a shell command. Waits up to `timeout` seconds for completion.
    If the command finishes in time, returns the full output.
    If still running, returns a command_id for use with command_status/send_command_input.

    Args:
        command (str): The shell command to execute. (required)
        cwd (str): Working directory for the command. (optional)
        timeout (str): Seconds to wait before sending to background. Default '1', max 10. (optional)
    """
    result = command_manager.run(command, cwd=cwd, timeout=float(timeout))
    return json.dumps(result, ensure_ascii=False)


def command_status(command_id, wait="0", output_lines="50"):
    """
    Check the status and read output of a background command.

    Args:
        command_id (str): The command ID returned by run_command. (required)
        wait (str): Seconds to wait for completion before returning. Default '0' (immediate). (optional)
        output_lines (str): Max number of output lines to return. Default '50'. (optional)
    """
    result = command_manager.status(
        command_id, wait=float(wait), output_lines=int(output_lines)
    )
    return json.dumps(result, ensure_ascii=False)


def send_command_input(command_id, input=None, terminate=None, wait="1"):
    """
    Send stdin input to a running command, or terminate it.
    Exactly one of `input` or `terminate` must be provided.

    Args:
        command_id (str): The command ID. (required)
        input (str): Text to send to stdin. Use '\\n' for Enter, '\\x03' for Ctrl+C. (optional)
        terminate (str): Set to 'true' to kill the process. (optional)
        wait (str): Seconds to wait for output after sending. Default '1'. (optional)
    """
    if input and terminate:
        return json.dumps({"error": "Provide either 'input' or 'terminate', not both."})
    if not input and not terminate:
        return json.dumps({"error": "Must provide either 'input' or 'terminate'."})

    terminate_bool = str(terminate).lower() in ("true", "1", "yes") if terminate else False
    result = command_manager.send_input(
        command_id, text=input, terminate=terminate_bool, wait=float(wait)
    )
    return json.dumps(result, ensure_ascii=False)

# remove
def list_commands():
    """
    Lists all tracked commands with their current status.
    """
    result = command_manager.list_commands()
    return json.dumps(result, ensure_ascii=False)


def read_file(path, start_line=None, end_line=None):
    """
    Reads the content of a file, optionally within a specific line range.

    Args:
        path (str): Path to the file (relative to working directory or absolute). (required)
        start_line (int): The starting line number (1-indexed, inclusive). (optional)
        end_line (int): The ending line number (1-indexed, inclusive). (optional)
    """
    try:
        path = _resolve_path(path)
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
        path (str): Path to the file (relative to working directory or absolute). (required)
        content (str): The content to write to the file. (required)
    """
    try:
        path = _resolve_path(path)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing to file: {e}"

def edit_file(path, target_text, replacement_text):
    """
    Replaces the first occurrence of `target_text` with `replacement_text` in the file.

    Args:
        path (str): Path to the file (relative to working directory or absolute). (required)
        target_text (str): The exact text block to replace. (required)
        replacement_text (str): The new text to insert in place of target_text. (required)
    """
    try:
        path = _resolve_path(path)
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
        path (str): Directory path (relative to working directory or absolute). Default is '.'.
    """
    try:
        if not path:
            path = "."
        path = _resolve_path(path)
        return "\n".join(os.listdir(path))
    except Exception as e:
        return f"Error listing directory: {e}"

def grep(pattern, path="."):
    """
    SEARCH for pattern in files/directories using system grep/ripgrep.

    Args:
        pattern (str): The text pattern to search for. (required)
        path (str): File or directory path (relative to working directory or absolute).
    """
    import subprocess
    try:
        path = _resolve_path(path)
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



# name

# def call_agent(agent):
#     pass
# def update_ltm():
#     pass

def update_stm():
    pass


available_tools = {
    "run_command": run_command,
    "command_status": command_status,
    "send_command_input": send_command_input,
    "list_commands": list_commands,
    "read_file": read_file,
    "write_to_file": write_to_file,
    "edit_file": edit_file,
    "ls": ls,
    "grep": grep
}
