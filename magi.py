import os,json
from datetime import datetime
import config
from openai import AzureOpenAI,OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel
from tools import available_tools
from models import AgentStep
from ltm_loader import load_ltm_files, update_ltm_metadata
from config import SUMMARIZE_THRESHOLD,MESSAGE_LOG_PATH
load_dotenv()
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")

client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_version="2025-03-01-preview",
)

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

    def __init__(self, name,description=""):
        self.name = name
        self.description = description
        self.status = "STOPPED"
        self.agent_tools = {
            "active_ltm": self.active_ltm,
            "search_memory": self.search_memory,
            "wait": self.wait
        }


        #memory
        self.stm = []
        self.history = []
        self.ltm_content = ""
        self.load_my_ltm()

    def active_ltm(self, name):
        """
        Activates a specific Long Term Memory for the agent.
        
        Args:
            name (str): The name of the memory to activate. (required)
        """
        try:
            result = update_ltm_metadata(name, self.name, 'active_for', 'add')
            if "Successfully updated" in result:
                self.load_my_ltm()
                return f"{result}\n[System] Memory reloaded successfully."
            return result
        except Exception as e:
            return f"Error activating LTM: {e}"

    def search_memory(self, query):
        """
        Searches Long Term Memories by name, description, or content.
        
        Args:
            query (str): The search query. (required)
        """
        try:
            ltms = load_ltm_files("./ltm")
            matches = []
            query_lower = query.lower()
            for m in ltms:
                if (query_lower in m.name.lower() or 
                    query_lower in m.description.lower() or 
                    query_lower in m.content.lower()):
                    matches.append(f"- Name: {m.name}, Description: {m.description}")
                    # Auto-add visibility
                    update_ltm_metadata(m.name, self.name, 'visible_to', 'add')
            
            if not matches:
                return f"No memories found matching '{query}'."

            # Reload to reflect visibility changes
            self.load_my_ltm()
            return "Found memories (automatically added to visible):\n" + "\n".join(matches)
        except Exception as e:
            return f"Error searching memory: {e}"

    def wait(self):
        """
        Pauses agent execution indefinitely.
        """
        self.status = "STOPPED"
        if len(self.history) > SUMMARIZE_THRESHOLD:
            self.summarize()
        return "Agent paused."
    
    def get_tools_description(self):
        """Generates a text description of available tools for the system prompt."""
        description = "Available Tools:\n"
        
        # Internal tools
        for name, func in self.agent_tools.items():
            doc = func.__doc__ if func.__doc__ else "No description available."
            description += f"- {name}: {doc}\n"
            
        # External tools
        for name, func in available_tools.items():
             # Avoid duplicates if any
            if name not in self.agent_tools:
                doc = func.__doc__ if func.__doc__ else "No description available."
                description += f"- {name}: {doc}\n"
                
        return description

    def load_my_ltm(self):
        all_ltms = load_ltm_files("./ltm")
        try:
            self.active_ltms = []
            self.visible_ltms = []
            
            agent_name_lower = self.name.lower()
            
            for m in all_ltms:
                # Check visibility
                is_visible = False
                if agent_name_lower in m.visible_to:
                     is_visible = True
                
                # Check active
                is_active = False
                if agent_name_lower in m.active_for:
                    is_active = True
                
                if is_active:
                     self.active_ltms.append(m)
                elif is_visible:
                     self.visible_ltms.append(m)

            print(f"[System] Loaded {len(self.active_ltms)} active LTMs and found {len(self.visible_ltms)} visible LTMs for {self.name}")
        except Exception as e:
            print(f"[System] Failed to load LTM: {e}")
            self.active_ltms = []
            self.visible_ltms = []

        if self.active_ltms:
            self.ltm_content += "\n\nRelevant Long-Term Memories (Active):\n"
            for m in self.active_ltms:
                self.ltm_content += f"--- Memory: {m.name} ---\n{m.content}\n"
        

        if self.visible_ltms:
            self.ltm_content += "\n\nOther Available Memories (loadable via tools):\n"
            for m in self.visible_ltms:
                self.ltm_content += f"- {m.name}: {m.description}\n"


    def get_messages(self):
        # Add Active LTM to context
        system_msg_content = self.ltm_content + self.get_tools_description()
        
        # Ensure system prompt is the first message
        messages = [{"role": "system", "content": system_msg_content}] + self.stm + self.history
        return messages

    def download_messages(self):
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"messages_{timestamp}.json"
            with open(MESSAGE_LOG_PATH + filename, "w", encoding="utf-8") as f:
                json.dump(self.get_messages(), f, ensure_ascii=False, indent=4)
            print(f"  [System] Messages downloaded to {filename}")
        except Exception as e:
            print(f"  [Error] Failed to download messages: {e}")

    def summarize(self):
        try:
            self.download_messages()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            summary_prompt = [
                {"role": "system", "content": memory_cleaner_prompt},
                {"role": "user", "content": f"Current Time: {timestamp}"},
                {"role": "user", "content": json.dumps(self.get_messages(), ensure_ascii=False)}
            ]
            summary = ai_request(summary_prompt)

            self.stm.append({"role": "system", "content": f"Summary of previous conversation: {summary}"})
            self.history = []
            print(f"  [Summary] {summary}")
        except Exception as e:
            print(f"  [Error] Failed to summarize history: {e}")


    def step(self):
        
        try:
            # Call LLM with Structured Output
            if config.SHOW_THOUGHTS:
                print(f"  [Thinking] Agent is thinking...", flush=True)
            step: AgentStep = client.beta.chat.completions.parse(
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
                
                # Check internal tools first
                tool_func = self.agent_tools.get(step.tool_name)
                # Then external tools
                if not tool_func:
                    tool_func = available_tools.get(step.tool_name)

                if tool_func:
                    try:
                        
                        # Handle None args if necessary
                        args = {}
                        if step.tool_args:
                            args = step.tool_args

                        self.history.append({"role": "assistant", "content": step.model_dump_json()})
                        # Execute Tool
                        result = tool_func(**args)
                        
                        tool_feedback = f"Tool '{step.tool_name}' Output:\n{result}"
                        self.history.append({"role": "user", "content": tool_feedback})
                        
                        # Stop if status is STOPPED (set by wait tool)
                        if self.status == "STOPPED":
                            return "STOPPED"
                            
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

