from magi import agent, agents
import pytest

def test_multi_agent_send_message():
    agents.clear() # clear existing
    agent1 = agent(name="Agent1", description="I am Agent 1")
    agent2 = agent(name="Agent2", description="I am Agent 2")
    
    assert "Agent1" in agents
    assert "Agent2" in agents
    assert len(agents) == 2
    
    # Send a message to agent2
    result = agent1.send_message("Agent2", "Hello Agent 2")
    assert result == "Message sent to agent 'Agent2'."
    
    # Check agent2 received it
    assert len(agent2.history) == 1
    assert agent2.history[0] == {"role": "user", "name": "Agent1", "content": "Hello Agent 2"}
    
    # Check it woke up agent2
    assert agent2.status == "RUNNING"
    
    # Send message to human
    result = agent1.send_message("human_user", "Hello human")
    assert result == "Message sent to human_user."
    
    # Sent to invalid agent
    result = agent1.send_message("Agent3", "Hello Agent 3")
    assert "Error" in result
