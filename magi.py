import os,json
from datetime import datetime
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
memory_cleaner_prompt = "Clean the following conversation history and summarize it into a concise paragraph using the second person 'You' regarding the agent's actions. Focus only on key actions and outcomes; do not record trivial details or failed attempts."
# ex:remember chat if needed

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

    def __init__(self, name,prompt):
        self.name = name
        self.description = ""
        self.status = "STOPPED"
        self.prompt = prompt
        self.tools = []
        # self.model = "o4-mini"

        #memory
        # self.ltm = []
        self.stm = []
        self.history = []

    def get_messages(self):
        messages = [{"role": "system", "content": self.prompt}] + self.stm + self.history
        # ltm
        return messages

    def summarize(self):
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            summary_prompt = [
                {"role": "system", "content": memory_cleaner_prompt},
                {"role": "user", "content": f"Current Time: {timestamp}"},
                {"role": "user", "content": json.dumps(self.get_messages(), ensure_ascii=False)}
            ]
            summary = ai_request(summary_prompt)
            self.stm.append({"role": "system", "content": summary})
            self.history = []
            print(f"  [Summary] {summary}")
        except Exception as e:
            print(f"  [Error] Failed to summarize history: {e}")


    def step(self):
        
        try:
            # Call LLM with Structured Output
            if config.SHOW_THOUGHTS:
                print(f"  [Thinking] Agent is thinking...", flush=True)
            step = client.beta.chat.completions.parse(
                model="o4-mini",
                messages=self.get_messages(),
                response_format=AgentStep,
            ).choices[0].message.parsed
            
            # Print Reasoning
            if config.SHOW_THOUGHTS:
                print(f"  [Reasoning] {step.reasoning}", flush=True)
            
            # Check for Tool execution
            if step.tool_name:
                if config.SHOW_TOOL_CALLS:
                    print(f"  [Tool Call] {step.tool_name} args={step.tool_args}", flush=True)
                
                if step.tool_name == "wait":
                    print("  [Wait] Agent decided to wait.")
                    self.summarize()
                    result = available_tools["wait"](**json.loads(step.tool_args) if step.tool_args else {})
                    if result == "WAIT_INDEFINITE":
                        self.status = "STOPPED"
                        return "STOPPED"
                    else:
                        # Timed wait finished, resume
                        return "RUNNING"
                    
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
                        self.history.append({"role": "assistant", "content": step.model_dump_json()})
                        self.history.append({"role": "user", "content": tool_feedback})
                        # print(f"  [Result] Tool output received ({len(str(result))} chars).")
                        
                    except Exception as e:
                        error_msg = f"Error executing tool {step.tool_name}: {e}"
                        print(f"  [Error] {error_msg}")
                        self.history.append({"role": "assistant", "content": step.model_dump_json()})
                        self.history.append({"role": "user", "content": error_msg})
                else:
                    error_msg = f"Error: Tool '{step.tool_name}' not found."
                    print(f"  [Error] {error_msg}")
                    self.history.append({"role": "assistant", "content": step.model_dump_json()})
                    self.history.append({"role": "user", "content": error_msg})
            else:
                # No tool called, but maybe just reasoning?
                # Usually we force a tool call or stop.
                # print("  [Warning] No tool name provided.")
                self.history.append({"role": "assistant", "content": step.model_dump_json()})
        
        except Exception as e:
            print(f"Error during agent step: {e}")
            return "ERROR"
            
        return "RUNNING"

