import sys
import os

# Add the current directory to sys.path so we can import magi
sys.path.append(os.getcwd())

from magi import agent
from ltm_loader import update_ltm_metadata

def test_ltm_functions():
    # 0. Cleanup: Ensure clean state
    print("Cleaning up LTM state...")
    update_ltm_metadata("test_mem_inactive", "Magi-Test", "active_for", "remove")
    
    print("Initializing Agent 'Magi-Test'...")
    test_agent = agent("Magi-Test")
    
    # 1. Verify inactive memory is NOT loaded initially
    print("\n--- Test 1: Verify Initial State ---")
    is_active = False
    for m in test_agent.active_ltms:
        if m.name == "test_mem_inactive":
            is_active = True
            break
    
    if not is_active:
        print("SUCCESS: 'test_mem_inactive' is correctly NOT active initially.")
    else:
        print("FAILURE: 'test_mem_inactive' should NOT be active initially.")
        return

    # 2. Test search_memory
    print("\n--- Test 2: Search Memory ---")
    query = "inactive"
    result = test_agent.search_memory(query)
    print(f"Search Result:\n{result}")
    
    if "Found memories" in result and "test_mem_inactive" in result:
        print("SUCCESS: search_memory found the correct memory.")
    else:
        print(f"FAILURE: search_memory did not find 'test_mem_inactive'. Query: {query}")

    # 3. Test active_ltm
    print("\n--- Test 3: Activate Memory ---")
    activation_result = test_agent.active_ltm("test_mem_inactive")
    print(f"Activation Result:\n{activation_result}")
    
    if "successfully" in activation_result.lower():
        print("SUCCESS: active_ltm reported success.")
    else:
        print("FAILURE: active_ltm reported failure.")

    # 4. Verify memory is NOW active
    print("\n--- Test 4: Verify Activation ---")
    is_active_now = False
    for m in test_agent.active_ltms:
        if m.name == "test_mem_inactive":
            is_active_now = True
            break
            
    if is_active_now:
        print("SUCCESS: 'test_mem_inactive' is now active.")
    else:
        print("FAILURE: 'test_mem_inactive' was not found in active_ltms after activation.")
        print("Current Active LTMs:", [m.name for m in test_agent.active_ltms])

    # 5. Cleanup
    print("\n--- Cleanup ---")
    res = update_ltm_metadata("test_mem_inactive", "Magi-Test", "active_for", "remove")
    print(f"Cleanup result: {res}")

if __name__ == "__main__":
    test_ltm_functions()
