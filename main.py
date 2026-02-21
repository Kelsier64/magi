from magi import agent, agents
import threading
import queue
import sys
import time
from config import USER_NAME

def input_listener(q):
    """
    Listens for user input from stdin in a separate thread.
    """
    while True:
        try:
            # Read line from stdin. This blocks until input is available.
            line = sys.stdin.readline()
            if not line: # EOF returns empty string
                break
            q.put(line.strip())
        except EOFError:
            break
        except Exception as e:
            print(f"[System] Input error: {e}", flush=True)
            break

import os

def main():
    print("Initializing Agent...", flush=True)
    
    workspace_dir = "agent_workspace"
    if not os.path.exists(workspace_dir):
        os.makedirs(workspace_dir)
    os.chdir(workspace_dir)
    print(f"[System] Entered workspace: {os.getcwd()}", flush=True)

    my_agent = agent(name="Magi-01", description="primary coordinator agent.")
    ltm_manager = agent(name="LTM-Manager", description="memory manager agent.")
    
    # Input Queue
    input_queue = queue.Queue()
    
    # Start Input Thread
    input_thread = threading.Thread(target=input_listener, args=(input_queue,), daemon=True)
    input_thread.start()

    print("Agent Loop Started. Type anywhere to interact with the agent.")

    while True:
        # 1. Process all pending user inputs
        while not input_queue.empty():
            user_text = input_queue.get()
            if user_text:
                print(f"\nUser: {user_text}")
                # Default to routing user input to the primary agent
                my_agent.history.append({"role": "user", "name": USER_NAME, "content": user_text})
                
                # Wake up agent if stopped
                if my_agent.status == "STOPPED":
                    my_agent.status = "RUNNING"
        
        # 2. Run Agent Step if RUNNING for all agents
        any_running = False
        for a in list(agents.values()):
            if a.status == "RUNNING":
                any_running = True
                status = a.step()
                if status == "STOPPED":
                    print(f"[System] Agent {a.name} has stopped. Waiting for new input...")
                elif status == "ERROR":
                    print(f"[System] Agent {a.name} encountered an error. Stopping.")
                    a.status = "STOPPED"
        
        if not any_running:
            # Sleep briefly to avoid CPU spinning when idle
            time.sleep(0.5)

if __name__ == "__main__":
    main()
