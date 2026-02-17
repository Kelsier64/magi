from magi import agent
import json

def main():
    print("Initializing Agent...")
    my_agent = agent("Magi-01")
    
    # Optional: Set a specific task if we modify the prompt to accept one, 
    # but for now the agent just runs with the system prompt and tools.
    # We might want to inject a user message to start.
    
    # Injecting a starting user message for testing
    my_agent.messages.append({"role": "user", "content": "Please check the current directory files and say hello."})
    
    my_agent.run()

if __name__ == "__main__":
    main()
