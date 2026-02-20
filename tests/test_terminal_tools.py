import json
import time
import pytest
from tools import run_command, command_status, send_command_input


class TestRunCommand:
    """Tests for the run_command tool."""

    def test_sync_completion(self):
        """Command that finishes within timeout returns done."""
        result = json.loads(run_command("echo hello", timeout="5"))
        assert result["status"] == "done"
        assert "hello" in result["output"]
        assert result["exit_code"] == 0

    def test_async_background(self):
        """Long-running command goes to background and returns command_id."""
        result = json.loads(run_command("sleep 30", timeout="1"))
        assert result["status"] == "running"
        assert result["command_id"].startswith("cmd_")
        # Clean up
        send_command_input(result["command_id"], terminate="true")

    def test_cwd(self):
        """Working directory arg works."""
        result = json.loads(run_command("pwd", cwd="/tmp", timeout="5"))
        assert result["status"] == "done"
        assert "/tmp" in result["output"]

    def test_exit_code_nonzero(self):
        """Failed command returns non-zero exit code."""
        result = json.loads(run_command("false", timeout="5"))
        assert result["status"] == "done"
        assert result["exit_code"] != 0


class TestCommandStatus:
    """Tests for the command_status tool."""

    def test_status_running(self):
        """Background command reports running status."""
        run_result = json.loads(run_command("sleep 30", timeout="1"))
        cmd_id = run_result["command_id"]

        status = json.loads(command_status(cmd_id, wait="0"))
        assert status["status"] == "running"

        # Clean up
        send_command_input(cmd_id, terminate="true")

    def test_status_wait_for_done(self):
        """Wait parameter blocks until command finishes."""
        run_result = json.loads(run_command("echo done_marker", timeout="0"))
        cmd_id = run_result["command_id"]

        status = json.loads(command_status(cmd_id, wait="5"))
        assert status["status"] == "done"
        assert "done_marker" in status["output"]

    def test_invalid_command_id(self):
        """Invalid command_id returns error."""
        result = json.loads(command_status("nonexistent_id"))
        assert "error" in result


class TestSendCommandInput:
    """Tests for the send_command_input tool."""

    def test_send_input_to_cat(self):
        """Sending text to cat echoes it back."""
        run_result = json.loads(run_command("cat", timeout="1"))
        cmd_id = run_result["command_id"]

        result = json.loads(
            send_command_input(cmd_id, input="test_message\n", wait="2")
        )
        assert "test_message" in result["output"]

        # Clean up
        send_command_input(cmd_id, terminate="true")

    def test_terminate(self):
        """Terminate kills a running process."""
        run_result = json.loads(run_command("sleep 60", timeout="1"))
        cmd_id = run_result["command_id"]

        result = json.loads(send_command_input(cmd_id, terminate="true"))
        assert result["status"] == "done"

    def test_both_input_and_terminate_error(self):
        """Providing both input and terminate returns error."""
        run_result = json.loads(run_command("sleep 60", timeout="1"))
        cmd_id = run_result["command_id"]

        result = json.loads(
            send_command_input(cmd_id, input="hello", terminate="true")
        )
        assert "error" in result

        # Clean up
        send_command_input(cmd_id, terminate="true")

    def test_neither_input_nor_terminate_error(self):
        """Providing neither input nor terminate returns error."""
        run_result = json.loads(run_command("sleep 60", timeout="1"))
        cmd_id = run_result["command_id"]

        result = json.loads(send_command_input(cmd_id))
        assert "error" in result

        # Clean up
        send_command_input(cmd_id, terminate="true")
