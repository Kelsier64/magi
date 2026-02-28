import os,json
from datetime import datetime
import config
from openai import AzureOpenAI,OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel
from tools import available_tools
from models import AgentStep
from ltm_loader import load_ltm_files, update_ltm_metadata
from config import SUMMARIZE_THRESHOLD, MESSAGE_LOG_PATH, MAX_STM_LENGTH
load_dotenv()
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")

client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_version="2025-03-01-preview",
    timeout=60.0,
)

memory_cleaner_prompt = "Summarize the following conversation history into a concise paragraph using the second person 'You'. Focus on key actions taken, important discoveries, decisions made, and the current state of any ongoing tasks. Do not record trivial details or failed attempts."
# ex:remember chat if needed

def ai_request(messages,text_format=None):
    try:
        print("[DEBUG] Sending ai_request to o4-mini...", flush=True)
        if text_format is not None:
            response = client.responses.parse(
            model="o4-mini",
            input=messages,
            text_format=text_format,
            )
            print("[DEBUG] Received structured response.", flush=True)
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


 
# Global agent registry
agents = {}

class agent:

    def __init__(self, name,description=""):
        self.name = name
        self.description = description
        self.status = "STOPPED"
        self.agent_tools = {
            # "active_ltm": self.active_ltm,
            "read_ltm": self.read_ltm,
            "remember": self.remember,
            "summarize_history": self.summarize_history,
            "compress_stm": self.compress_stm,
            
            "wait": self.wait,
            "send_message": self.send_message,
            "make_new_agent": self.make_new_agent,

           
        }

        # Register self in the global agents dictionary
        agents[self.name] = self


        #memory
        self.stm = []
        self.history = []
        self.ltm_content = ""
        self.stm_content = "\n\nShort-Term Memories:\n"
        self.load_state()
        self.load_my_ltm()

    def get_state_file_path(self):
        state_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_states")
        os.makedirs(state_dir, exist_ok=True)
        return os.path.join(state_dir, f"{self.name}_state.json")

    def save_state(self):
        state = {
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "stm": self.stm,
            "history": self.history,
            "stm_content": self.stm_content
        }
        try:
            with open(self.get_state_file_path(), "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"[Error] Failed to save agent state for {self.name}: {e}")

    def load_state(self):
        state_file = self.get_state_file_path()
        if os.path.exists(state_file):
            try:
                with open(state_file, "r", encoding="utf-8") as f:
                    state = json.load(f)
                    self.description = state.get("description", self.description)
                    self.status = state.get("status", self.status)
                    self.stm = state.get("stm", self.stm)
                    self.history = state.get("history", self.history)
                    self.stm_content = state.get("stm_content", self.stm_content)
                print(f"[System] Loaded state for agent '{self.name}' from {state_file}")
            except Exception as e:
                print(f"[Error] Failed to load agent state for {self.name}: {e}")

    def read_ltm(self, name):
        """
        Reads the content of a specific Long Term Memory.
        
        Args:
            name (str): The name of the memory to read. (required)
        """
        ltm_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ltm")
        try:
            all_ltms = load_ltm_files(ltm_path)
            agent_name_lower = self.name.lower()
            
            for m in all_ltms:
                if m.name == name or f"{m.name}.md" == name or m.name == f"{name}.md":
                    if agent_name_lower in m.visible_to or "all" in m.visible_to:
                        return f"--- Memory: {m.name} ---\nDescription: {m.description}\n\nContent:\n{m.content}"

            
            return f"Error: LTM '{name}' not found."
        except Exception as e:
            return f"Error reading LTM: {e}"

    def remember(self, text):
        """
        Adds a new memory to the agent's short-term memory.
        
        Args:
            text (str): The memory content to add. (required)
            use second person perspective(you) to record the memory
        """
        # Append to stm_content for persistence
        self.stm_content += f"\n[Memory] {text}"

        print(f"[System] Remembered: {text}", flush=True)

        if len(self.stm_content) > MAX_STM_LENGTH:
            self.compress_stm()

        return "Remembered successfully."

    def summarize_history(self):
        """
        Summarizes the current conversation history to free up the context window. 
        Note: This automatically condenses past messages into Short-Term Memory and keeps the last few messages for continuity. Use 'remember' BEFORE calling this if you need to retain highly specific facts or constraints.
        """
        self.force_summarize()
        return "History summarized successfully."


# add time
    def wait(self):
        """
        Pauses agent execution indefinitely.
        """
        self.status = "STOPPED"
        if len(self.history) > SUMMARIZE_THRESHOLD:
            self.force_summarize()
        
        return "Agent paused."



    def send_message(self, recipient, message):
        """
        Sends a message to the user/human, or to another agent by name.
        
        Args:
            recipient (str): The name of the agent to send the message to, or "human_user" to send to the real user. (required)
            message (str): The content of the message to send. (required)
        """
        if recipient.lower() == "human_user":
            print(f"Agent {self.name}: {message}", flush=True)
            return "Message sent to human_user."
        
        if recipient in agents:
            target_agent = agents[recipient]
            target_agent.history.append({"role": "user", "name": self.name, "content": message})
            if target_agent.status == "STOPPED":
                target_agent.status = "RUNNING"
            target_agent.save_state()
            print(f"[System] Message routed from {self.name} to {recipient}.", flush=True)
            return f"Message sent to agent '{recipient}'."
            
        return f"Error: Agent '{recipient}' not found. Cannot send message."

    def make_new_agent(self, name, description, prompt=None):
        """
        Dynamically instantiates a new worker agent.
        
        Args:
            name (str): The name of the new agent to create.
            description (str): A description for others to know what this agent does.
            prompt (str, optional): The initial prompt/rules for this agent(in markdown format and in english).
        """
        if name in agents:
            return f"Error: Agent with name '{name}' already exists."
            
        try:
            if prompt:
                # Create a specific LTM file for this agent before instantiation so it gets loaded
                ltm_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ltm")
                os.makedirs(ltm_dir, exist_ok=True)
                ltm_filename = f"01_{name.lower().replace(' ', '_')}_rule.md"
                ltm_filepath = os.path.join(ltm_dir, ltm_filename)
                
                ltm_content = f"---\nname: {name}_rule\ndescription: Core instructions for {name}\nactive_for: \n- {name}\nvisible_to: \n- {name}\nexcept_for: []\n---\n{prompt}\n"
                with open(ltm_filepath, "w", encoding="utf-8") as f:
                    f.write(ltm_content)
                print(f"[System] Created specific LTM '{ltm_filename}' for '{name}'.", flush=True)

            # agent.__init__ automatically registers the new instance in the `agents` dict
            new_agent = agent(name=name, description=description)
            print(f"[System] Agent '{self.name}' spawned new agent '{name}'.", flush=True)
            return f"Successfully created new agent '{name}'."
        except Exception as e:
            return f"Error creating new agent: {e}"

    def edit_stm(self, new_content):
        """
        Edits the entire Short-Term Memory (STM) content of self.
        Warning: This overrides the target agent's entire STM. Use carefully.
        
        Args:
            new_content (str): The new full text content to assign to the target's STM.
        """
            
        try:
            self.stm_content = new_content
            self.save_state()
            print(f"[System] STM for agent '{self.name}' was edited by '{self.name}'.", flush=True)
            return f"Successfully updated STM for agent '{self.name}'."
        except Exception as e:
            return f"Error updating STM for agent '{self.name}': {e}"

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

    def load_my_ltm(self, verbose=True):
        self.ltm_content = "" # Reset context to load cleanly
        ltm_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ltm")
        all_ltms = load_ltm_files(ltm_path)
        try:
            self.active_ltms = []
            self.visible_ltms = []
            
            agent_name_lower = self.name.lower()
            
            for m in all_ltms:
                # First check if the agent is explicitly excluded
                if agent_name_lower in m.except_for:
                    continue
            
                # Check visibility
                is_visible = False
                if agent_name_lower in m.visible_to or "all" in m.visible_to:
                     is_visible = True
                
                # Check active
                is_active = False
                if agent_name_lower in m.active_for or "all" in m.active_for:
                    is_active = True
                
                if is_active:
                     self.active_ltms.append(m)
                elif is_visible:
                     self.visible_ltms.append(m)

            if verbose:
                print(f"[System] Loaded {len(self.active_ltms)} active LTMs and found {len(self.visible_ltms)} visible LTMs for {self.name}")
        except Exception as e:
            if verbose:
                print(f"[System] Failed to load LTM: {e}")
            self.active_ltms = []
            self.visible_ltms = []

        if self.active_ltms:
            self.ltm_content += "\n\nRelevant Long-Term Memories (Active):\n"
            for m in self.active_ltms:
                self.ltm_content += f"--- Memory: {m.name} ---\n{m.content}\n"
        

        if self.visible_ltms:
            self.ltm_content += "\n\nOther Available Memories (loadable via tools or LTM-Manager):\n"
            for m in self.visible_ltms:
                self.ltm_content += f"- {m.name}: {m.description}\n"

    def get_messages(self):
        self.load_my_ltm(verbose=False)
        # Add Active LTM to context
        system_msg_content = self.ltm_content + self.get_tools_description()
        
        # System Data
        system_data = self.get_data()


        # Ensure system prompt is the first message
        messages = [{"role": "system", "content": system_msg_content},
                    {"role": "system", "content": self.stm_content},
                    {"role": "system", "content": system_data}
                    ] + self.history
        return messages

    def get_data(self):
        agents_info = ""
        for a in agents.values():
            agents_info += f"- {a.name}: {a.description}\n"

        
        data = f"""
        System Data:
        your name: {self.name}
        your description: {self.description}
        operate system:linux
        working_directory: {os.getcwd()}
        time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        History Count: {len(self.history)}, auto clean at {config.SUMMARIZE_THRESHOLD}
        other agents: {agents_info}
        
        """
        return data

    def download_messages(self):
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"{self.name}_{timestamp}.json"
            os.makedirs(MESSAGE_LOG_PATH, exist_ok=True)
            with open(os.path.join(MESSAGE_LOG_PATH, filename), "w", encoding="utf-8") as f:
                json.dump(self.get_messages(), f, ensure_ascii=False, indent=4)
            print(f"  [System] Messages downloaded to {filename}")
        except Exception as e:
            print(f"  [Error] Failed to download messages: {e}")

    def force_summarize(self):
        try:
            self.download_messages()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            summary_prompt = [
                {"role": "system", "content": memory_cleaner_prompt},
                {"role": "user", "content": f"Current Time: {timestamp}"},
                {"role": "user", "content": json.dumps(self.history, ensure_ascii=False)}
            ]
            summary = ai_request(summary_prompt)

            self.stm_content +=f"{summary}\n"
            
            if len(self.stm_content) > MAX_STM_LENGTH:
                self.compress_stm()

            # Sliding Window: Keep the last 4 messages to preserve immediate context continuity
            self.history = self.history[-8:]
            print(f"  [Summary] {summary}")
        except Exception as e:
            print(f"  [Error] Failed to summarize history: {e}")

    def compress_stm(self):
        """
        Compresses and filters the agent's short-term memory to keep it concise.
        Automatically removes information already present in Long-Term Memory.
        Can be called manually by the agent.
        """
        try:
            print(f"[System] Compressing STM for {self.name}...", flush=True)
            prompt = [
                {"role": "system", "content": "You are a memory manager. Summarize the following short-term memory block into a highly concise format. **CRITICAL: If any information in the short-term memory is already present in the provided long-term memory or is clearly redundant, discard it completely from the summary.** Your goal is to keep only fresh, immediate context."},
                {"role": "user", "content": f"Current Active/Visible Long-Term Memories:\n{self.ltm_content}"},
                {"role": "user", "content": f"Short-Term Memory Block to Compress:\n{self.stm_content}"}
            ]
            compressed_content = ai_request(prompt)
            if compressed_content and compressed_content != "error":
                 self.stm_content = f"\n\nShort-Term Memories (Compressed):\n{compressed_content}\n"
                 return "STM successfully compressed and deduplicated."
            return "Error: Failed to generate compressed STM."
        except Exception as e:
            return f"Error during STM compression: {e}"


    def get_event(self):
        pass        
        



    def step(self):
        
        try:
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
                        
                        
                        # Stop if status is STOPPED (set by wait tool)
                        if self.status == "STOPPED":
                            self.save_state()
                            return "STOPPED"

                        self.history.append({"role": "user", "content": tool_feedback})
                            
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
            self.download_messages()
            self.save_state()
            return "ERROR"
            
        self.save_state()
        return "RUNNING"

