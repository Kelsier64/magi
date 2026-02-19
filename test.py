from typing import Any,Dict
from magi import client
from pydantic import BaseModel
from typing import Optional, List
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


class AgentStep(BaseModel):
    reasoning: str  # 強制模型寫下思考過程 (Chain of Thought)
    tool_name: Optional[str] = None  # 決定要用的工具名稱
    tool_args: Optional[Dict[str, str]] = None  # 工具參數 



print(ai_request([{"role":"user","content":"hello"}],AgentStep))
