from magi import agent
import threading
import queue
import sys
import time
from tools import get_tools_description
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

def main():
    print("Initializing Agent...", flush=True)

    my_agent = agent(name="Magi-01")
    
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
                my_agent.history.append({"role": "user", "name":USER_NAME, "content": user_text})
                
                # Wake up agent if stopped
                if my_agent.status == "STOPPED":
                    # print("[System] Waking up agent due to new input...")
                    my_agent.status = "RUNNING"
        
        # 2. Run Agent Step if RUNNING
        if my_agent.status == "RUNNING":
            status = my_agent.step()
            if status == "STOPPED":
                print("[System] Agent has stopped. Waiting for new input...")
            elif status == "ERROR":
                print("[System] Agent encountered an error. Stopping.")
                my_agent.status = "STOPPED"
        else:
            # Sleep briefly to avoid CPU spinning when idle
            time.sleep(0.5)

if __name__ == "__main__":
    main()
