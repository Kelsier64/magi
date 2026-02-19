from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class AgentStep(BaseModel):
    reasoning: str  # 強制模型寫下思考過程 (Chain of Thought)
    tool_name: Optional[str] = None  # 決定要用的工具名稱
    tool_args: Optional[Dict[str, Any]] = None  # 工具參數 


class tool(BaseModel):
    name: str
    description: str
    args: Dict[str, Any]


class ltm(BaseModel):
    name: str
    description: str
    content: str
    path: str
    active_for: List[str]
    visible_to: List[str]
