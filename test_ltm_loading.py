import sys
import os

# Add the current directory to sys.path so we can import magi
sys.path.append(os.getcwd())

from magi import agent

def test_ltm_loading():
    print("Initializing Agent 'Magi-Test'...")
    test_agent = agent("Magi-Test")
    
    # Check if the test memory is loaded
    print("Checking active LTMs...")
    found = False
    for m in test_agent.active_ltms:
        if m.name == "test_memory":
            found = True
            print(f"Found LTM: {m.name}")
            print(f"Content Preview: {m.content[:20]}...")
            break
    
    if found:
        print("SUCCESS: Test LTM loaded correctly.")
    else:
        print("FAILURE: Test LTM not found in active memories.")
        print("Active LTMs:", [m.name for m in test_agent.active_ltms])

if __name__ == "__main__":
    test_ltm_loading()
