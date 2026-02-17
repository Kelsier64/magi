from magi import agent
import json

# Mock available_tools to avoid side effects or input() calls if any
from magi import available_tools
def mock_send_message(message):
    print(f"DTOOL: {message}")
    return "Message sent."
available_tools["send_message"] = mock_send_message

print("Initializing Agent...")
a = agent("TestAgent")
a.messages.append({"role": "user", "content": "Write a Python script that prints 'Hello World' and explain how to run it."})

print("Running Step...")
try:
    status = a.step()
    print(f"Step Status: {status}")
except Exception as e:
    print(f"Step Error: {e}")
