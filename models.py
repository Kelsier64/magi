from pydantic import BaseModel
from typing import Optional, Dict, Any

class AgentStep(BaseModel):
    reasoning: str  # 強制模型寫下思考過程 (Chain of Thought)
    tool_name: Optional[str] = None  # 決定要用的工具名稱
    tool_args: Optional[str] = None  # 工具參數 (JSON String)


class tool(BaseModel):
    name: str
    description: str
    args: Dict[str, Any]