import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SHOW_THOUGHTS = False
SHOW_TOOL_CALLS = False
USER_NAME = "Kelsier"
SUMMARIZE_THRESHOLD = 30
MESSAGE_LOG_PATH = os.path.join(BASE_DIR, "messages_log/")
MAX_STM_LENGTH = 1500