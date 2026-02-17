import os,json
import config
from openai import AzureOpenAI,OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel
from tools import available_tools, get_tools_description
from models import AgentStep

load_dotenv()
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")

client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_version="2025-03-01-preview",
)
system_prompt = ""

main_prompt = """
You are an AI agent in a multi-agent system.
You have access to tools and skills to perform tasks. 
Your output and actions will be recorded in your memory from a first-person perspective, so do not address the user directly in your output; instead, use the 'send_message' tool to communicate with them.
"""

def ai_request(messages,text_format=None):
    try:
        if text_format is not None:
            response = client.responses.parse(
            model="o4-mini",
            input=messages,
            text_format=text_format,
            )
            return response.output_parsed
        else:
            response = client.responses.parse(
            model="o4-mini",
            input=messages,
            )
            return response.output_text
    except Exception as e:
        print(f"Error in ai request: {e}")
        return "error"


def ai_tool_request(messages,tools_schema):
    try:
        response = client.chat.completions.create(
            model="o4-mini",
            messages=messages,
            tools=tools_schema,
            tool_choice="auto"
        )
        return response
    except Exception as e:
        print(f"Error in ai tool request: {e}")
        return "error"



class agent:
    def __init__(self, name):
        self.name = name
        self.description = ""
        self.status = "STOPPED"
        self.prompt = ""
        # self.model = "o4-mini"
        self.history = []

        self.memory = [main_prompt]
        self.stm = ""
        self.ltm = []

        self.skills = []

        # Tools description for System Prompt
        tools_desc = get_tools_description()
        
        # Initialize Prompt
        system_instruction = f"""
{main_prompt}

You are a helpful AI assistant.
You have access to the following tools:
{tools_desc}

To use a tool, you MUST output a valid JSON object matching the `AgentStep` schema.
1. `reasoning`: Explain YOUR THINKING PROCESS. Why are you taking this step? What do you expect to see?
2. `tool_name`: The exact name of the tool to call.
3. `tool_args`: The parameters for the tool as a valid JSON string (e.g. '{{"path": "./file.txt"}}'). Ensure all quotes and newlines within the string are properly escaped.

If you have completed the task or cannot proceed, use the `stop` tool.
"""
        self.messages = [
            {"role": "system", "content": system_instruction}
        ]

    def update(self):
        pass


    def step(self):
        print(f"Agent {self.name} stepping...", flush=True)
        
        try:
            # Call LLM with Structured Output
            if config.SHOW_THOUGHTS:
                print(f"  [Thinking] Agent is thinking...", flush=True)
            step = client.beta.chat.completions.parse(
                model="o4-mini", # Or your deployment name
                messages=self.messages,
                response_format=AgentStep,
            ).choices[0].message.parsed
            
            # Print Reasoning
            if config.SHOW_THOUGHTS:
                print(f"  [Reasoning] {step.reasoning}", flush=True)
            
            # Check for Tool execution
            if step.tool_name:
                if config.SHOW_TOOL_CALLS:
                    print(f"  [Tool Call] {step.tool_name} args={step.tool_args}", flush=True)
                
                if step.tool_name == "stop":
                    print("  [Stop] Agent decided to stop.")
                    self.status = "STOPPED"
                    return "STOPPED"
                    
                tool_func = available_tools.get(step.tool_name)
                if tool_func:
                    try:
                        # Execute Tool
                        # Handle None args if necessary
                        # Robust JSON parsing for args
                        args = {}
                        if step.tool_args:
                            try:
                                args = json.loads(step.tool_args)
                            except json.JSONDecodeError as e:
                                # Try to fix common issues like unescaped newlines in the string
                                print(f"  [Warning] JSON decode failed for args: {step.tool_args}. Error: {e}")
                                # Fallback: Empty args or raise
                                raise e
                        
                        result = tool_func(**args)
                        
                        # Add Tool Output to History (User role usually used for tool outputs in this pattern if not using native tool calls)
                        # Or we can use 'function' role if we were using native tools.
                        # Since we are essentially "simulating" tools, we can feed the result back as a User message or System message representing the environment.
                        # Let's use 'user' role to represent Environment feedback for simplicity in this pattern.
                        tool_feedback = f"Tool '{step.tool_name}' Output:\n{result}"
                        self.messages.append({"role": "assistant", "content": step.model_dump_json()}) # Store Agent's decision
                        self.messages.append({"role": "user", "content": tool_feedback})
                        print(f"  [Result] Tool output received ({len(str(result))} chars).")
                        
                    except Exception as e:
                        error_msg = f"Error executing tool {step.tool_name}: {e}"
                        print(f"  [Error] {error_msg}")
                        self.messages.append({"role": "assistant", "content": step.model_dump_json()})
                        self.messages.append({"role": "user", "content": error_msg})
                else:
                    error_msg = f"Error: Tool '{step.tool_name}' not found."
                    print(f"  [Error] {error_msg}")
                    self.messages.append({"role": "assistant", "content": step.model_dump_json()})
                    self.messages.append({"role": "user", "content": error_msg})
            else:
                # No tool called, but maybe just reasoning? 
                # Usually we force a tool call or stop.
                print("  [Warning] No tool name provided.")
                self.messages.append({"role": "assistant", "content": step.model_dump_json()})
        
        except Exception as e:
            print(f"Error during agent step: {e}")
            return "ERROR"
            
        return "RUNNING"