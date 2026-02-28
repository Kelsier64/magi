import os
import tempfile
import pytest

import config

from magi import agent, agents
from tools import grep

@pytest.fixture(autouse=True)
def setup_teardown():
    agents.clear()
    yield


def test_stm_remember(tmp_path):

    (tmp_path / "ltm").mkdir()
    
    my_agent = agent(name="TestAgent", description="A test agent.")
    
    # Test remember
    result = my_agent.remember("Secret code is 12345")
    assert "successfully" in result
    assert "Secret code is 12345" in my_agent.stm_content

def test_ltm_search_via_grep(tmp_path):
    # Setup dummy LTM file
    ltm_dir = tmp_path / "ltm"
    ltm_dir.mkdir()
    dummy_ltm = ltm_dir / "test_memory.md"
    dummy_ltm.write_text("---\nname: test_memory\ndescription: A test memory\nvisible_to:\n- all\n---\nMy secret password is 'supersecret99'.\n")
    
    # Act: Search using grep tool
    search_result = grep("supersecret99", str(ltm_dir))
    
    # Assert
    assert "supersecret99" in search_result
    assert "test_memory.md" in search_result
    
    search_result_not_found = grep("not_exist_word", str(ltm_dir))
    assert "No matches found" in search_result_not_found or search_result_not_found == ""

def test_read_ltm():
    ltm_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ltm")
    os.makedirs(ltm_dir, exist_ok=True)
    test_file_path = os.path.join(ltm_dir, "test_ltm_mock.md")
    
    with open(test_file_path, "w", encoding="utf-8") as f:
        f.write("---\nname: test_ltm_mock\ndescription: Test LTM content\nvisible_to:\n- all\nexcept_for:\n- none\n---\nThis is the content of the LTM.")
    
    try:
        my_agent = agent(name="TestAgent", description="A test agent.")
        result = my_agent.read_ltm("test_ltm_mock")
        assert "This is the content of the LTM." in result
    finally:
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
