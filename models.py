from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from typing_extensions import Literal

class AgentStep(BaseModel):
    reasoning: str  # 強制模型寫下思考過程 (Chain of Thought)
    tool_name: Optional[str] = None  # 決定要用的工具名稱
    tool_args: Optional[Dict[str, str]] = None  # tool arguments (all values as strings)

class tool(BaseModel):
    name: str
    description: str
    args: Dict[str, str]


class ltm(BaseModel):
    name: str
    description: str
    content: str
    path: str
    active_for: List[str]
    visible_to: List[str]
