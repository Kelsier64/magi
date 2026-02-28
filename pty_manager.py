import os
import pty
import select
import signal
import time
import threading


class CommandSession:
    """Represents a single PTY command session."""

    def __init__(self, command_id, pid, fd):
        self.command_id = command_id
        self.pid = pid
        self.fd = fd
        self.output_lines = []
        self.status = "running"
        self.exit_code = None
        self._lock = threading.Lock()

    def _collect_output(self, timeout=0.1):
        """Read any available output from the PTY fd."""
        try:
            while True:
                ready, _, _ = select.select([self.fd], [], [], timeout)
                if not ready:
                    break
                data = os.read(self.fd, 4096)
                if not data:
                    break
                text = data.decode("utf-8", errors="replace")
                with self._lock:
                    # Split by newline, merge with last partial line
                    parts = text.split("\n")
                    if self.output_lines and not self.output_lines[-1].endswith("\n"):
                        self.output_lines[-1] += parts[0]
                        parts = parts[1:]
                    for part in parts:
                        if part:
                            self.output_lines.append(part)
        except OSError:
            # fd closed or process exited
            pass

    def _check_exit(self):
        """Check if the process has exited."""
        if self.status != "running":
            return
        try:
            pid, wait_status = os.waitpid(self.pid, os.WNOHANG)
            if pid != 0:
                self.status = "done"
                if os.WIFEXITED(wait_status):
                    self.exit_code = os.WEXITSTATUS(wait_status)
                elif os.WIFSIGNALED(wait_status):
                    self.exit_code = -os.WTERMSIG(wait_status)
                else:
                    self.exit_code = -1
        except ChildProcessError:
            self.status = "done"
            self.exit_code = -1

    def get_output(self, max_lines=50):
        """Get recent output lines."""
        self._collect_output(timeout=0.05)
        self._check_exit()
        with self._lock:
            if max_lines and len(self.output_lines) > max_lines:
                return self.output_lines[-max_lines:]
            return list(self.output_lines)

    def write(self, text):
        """Write text to the PTY stdin."""
        try:
            os.write(self.fd, text.encode("utf-8"))
        except OSError as e:
            return f"Error writing to process: {e}"
        return None

    def terminate(self):
        """Kill the process and clean up."""
        try:
            os.kill(self.pid, signal.SIGTERM)
            time.sleep(0.2)
            try:
                os.kill(self.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        except ProcessLookupError:
            pass
        self._collect_output(timeout=0.1)
        self._check_exit()
        if self.status != "done":
            self.status = "done"
            self.exit_code = -1
        try:
            os.close(self.fd)
        except OSError:
            pass


class CommandManager:
    """Manages multiple PTY command sessions."""

    MAX_DONE_SESSIONS = 5

    def __init__(self):
        self._sessions = {}
        self._counter = 0

    def _next_id(self):
        self._counter += 1
        return f"cmd_{self._counter}"

    def _cleanup(self):
        """Remove old completed sessions, keeping at most MAX_DONE_SESSIONS."""
        done = [cid for cid, s in self._sessions.items() if s.status == "done"]
        if len(done) > self.MAX_DONE_SESSIONS:
            # Remove oldest done sessions (lower cmd_ numbers first)
            to_remove = sorted(done)[: len(done) - self.MAX_DONE_SESSIONS]
            for cid in to_remove:
                del self._sessions[cid]

    def run(self, command, cwd=None, timeout=1):
        """
        Spawn a command in a new PTY.
        Wait up to `timeout` seconds for it to finish.
        Returns a dict with status, output, and command_id.
        """
        timeout = min(max(float(timeout), 0), 10)
        self._cleanup()

        env = os.environ.copy()
        env["TERM"] = "dumb"
        env["PAGER"] = "cat"

        if cwd:
            cwd = os.path.expanduser(cwd)
            if not os.path.isabs(cwd):
                cwd = os.path.join(os.getcwd(), cwd)

        pid, fd = pty.openpty()
        child_pid = os.fork()

        if child_pid == 0:
            # Child process
            os.close(pid)
            os.setsid()
            import fcntl
            import termios
            fcntl.ioctl(fd, termios.TIOCSCTTY, 0)
            os.dup2(fd, 0)
            os.dup2(fd, 1)
            os.dup2(fd, 2)
            if fd > 2:
                os.close(fd)
            if cwd:
                os.chdir(cwd)
            os.execvpe("/bin/bash", ["/bin/bash", "-c", command], env)
        else:
            # Parent process
            os.close(fd)
            command_id = self._next_id()
            session = CommandSession(command_id, child_pid, pid)
            self._sessions[command_id] = session

            # Wait for completion or timeout
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                session._collect_output(timeout=0.1)
                session._check_exit()
                if session.status == "done":
                    break

            # Final collect
            session._collect_output(timeout=0.05)
            session._check_exit()

            output = "\n".join(session.get_output(max_lines=100))
            result = {
                "status": session.status,
                "command_id": command_id,
                "output": output,
            }
            if session.status == "done":
                result["exit_code"] = session.exit_code
                # Clean up finished sessions
                try:
                    os.close(pid)
                except OSError:
                    pass

            return result

    def status(self, command_id, wait=0, output_lines=50):
        """Check status and get output of a command."""
        session = self._sessions.get(command_id)
        if not session:
            return {"error": f"Command '{command_id}' not found."}

        wait = min(max(float(wait), 0), 10)
        output_lines = int(output_lines)

        if wait > 0 and session.status == "running":
            deadline = time.monotonic() + wait
            while time.monotonic() < deadline:
                session._collect_output(timeout=0.1)
                session._check_exit()
                if session.status == "done":
                    break

        lines = session.get_output(max_lines=output_lines)
        output = "\n".join(lines)

        result = {"status": session.status, "output": output}
        if session.status == "done":
            result["exit_code"] = session.exit_code
        return result

    def send_input(self, command_id, text=None, terminate=False, wait=1):
        """Send input to a command or terminate it."""
        session = self._sessions.get(command_id)
        if not session:
            return {"error": f"Command '{command_id}' not found."}

        wait = min(max(float(wait), 0), 10)

        if terminate:
            session.terminate()
            lines = session.get_output(max_lines=50)
            return {
                "status": session.status,
                "exit_code": session.exit_code,
                "output": "\n".join(lines),
            }

        if text is not None:
            err = session.write(text)
            if err:
                return {"error": err}

            # Wait for output
            time.sleep(min(wait, 0.5))
            session._collect_output(timeout=wait)
            session._check_exit()

            lines = session.get_output(max_lines=50)
            result = {"status": session.status, "output": "\n".join(lines)}
            if session.status == "done":
                result["exit_code"] = session.exit_code
            return result

        return {"error": "Either 'text' or 'terminate' must be provided."}

    def list_commands(self):
        """Return status summary of all tracked commands."""
        results = []
        for cmd_id, session in self._sessions.items():
            session._collect_output(timeout=0.02)
            session._check_exit()
            entry = {
                "command_id": cmd_id,
                "status": session.status,
                "output_lines": len(session.output_lines),
            }
            if session.status == "done":
                entry["exit_code"] = session.exit_code
            results.append(entry)
        return results


# Module-level singleton
command_manager = CommandManager()
