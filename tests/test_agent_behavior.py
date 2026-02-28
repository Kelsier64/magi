import os
import time
import pytest
import config

from magi import agent, agents

@pytest.fixture(scope="module")
def setup_dummy_ltm():
    # Setup
    test_ltm_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ltm", "test_secret_project.md")
    with open(test_ltm_path, "w", encoding="utf-8") as f:
        f.write("---\nname: test_secret_project\ndescription: Information about Project Xenix\nvisible_to:\n- all\nexcept_for:\n- none\n---\nProject Xenix involves building a quantum entanglement communicator.\n")
    
    yield test_ltm_path
    
    # Teardown
    if os.path.exists(test_ltm_path):
        os.remove(test_ltm_path)


def test_agent_autonomous_memory_search(setup_dummy_ltm):
    agents.clear()
    
    # Initialize agents like in main.py
    my_agent = agent(name="Magi-01", description="primary coordinator agent.")
    ltm_manager = agent(name="LTM-Manager", description="memory manager agent.")
    
    # Start the conversation with a natural prompt without mentioning tools
    user_prompt = "I completely forgot what Project Xenix is about. Can you check my memories and tell me?"
    
    my_agent.history.append({"role": "user", "name": config.USER_NAME, "content": user_prompt})
    my_agent.status = "RUNNING"
    
    # Run the agent loop with a maximum number of steps to avoid infinite loops
    max_steps = 15
    steps_taken = 0
    
    while steps_taken < max_steps:
        any_running = False
        for a in list(agents.values()):
            if a.status == "RUNNING":
                any_running = True
                status = a.step()
                if status == "ERROR":
                    a.status = "STOPPED"
        
        if not any_running:
            break
        
        steps_taken += 1
        time.sleep(0.1)
    
    # Verify the agent replied with the correct information
    # Check Magi-01's history for the AI's response to the user
    found_answer = False
    for msg in reversed(my_agent.history):
         # Look for the assistant's final thought or tool call that indicates success
         # The assistant might use send_message to human_user or just output the context.
         if "role" in msg and msg["role"] == "assistant":
             content = msg.get("content", "")
             if getattr(msg, "content", None):
                 content = msg.content
             if isinstance(content, str):
                  if "quantum entanglement communicator" in content.lower() or "quantum entanglement" in content.lower():
                      found_answer = True
                      break
         # Or it might have sent a message via function output/reasoning
         if isinstance(msg, dict) and "quantum entanglement" in str(msg).lower():
             found_answer = True
             break

    assert found_answer, "The agent failed to autonomously retrieve and report the memory."

