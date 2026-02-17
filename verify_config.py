import io
import sys
import unittest
from unittest.mock import MagicMock, patch

# Patch AzureOpenAI before importing magi
with patch('openai.AzureOpenAI') as MockAzureOpenAI:
    # Set up the mock client
    mock_client_instance = MagicMock()
    MockAzureOpenAI.return_value = mock_client_instance
    
    # Now import magi - it will use the mocked AzureOpenAI
    from magi import agent
    import config
    from models import AgentStep

class TestConfigVisibility(unittest.TestCase):
    def setUp(self):
        # Create a mock AgentStep
        self.mock_step = AgentStep(
            reasoning="This is a thought.",
            tool_name="test_tool",
            tool_args='{"arg": "value"}'
        )
        
        # Mock the client response structure
        # access the mocked client instance that was created during import
        # We need to find where 'client' is in magi module
        import magi
        self.mock_client = magi.client
        
        # Setup the mock response
        self.mock_response = MagicMock()
        self.mock_response.choices[0].message.parsed = self.mock_step
        
        # Configure parse method on the client
        self.mock_client.beta.chat.completions.parse.return_value = self.mock_response
        
        # Initialize agent
        self.agent = agent("TestAgent")

    def test_show_everything(self):
        # Set config to True
        config.SHOW_THOUGHTS = True
        config.SHOW_TOOL_CALLS = True
        
        # Capture stdout
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        try:
            self.agent.step()
        finally:
            sys.stdout = sys.__stdout__
            
        output = captured_output.getvalue()
        self.assertIn("[Thinking]", output)
        self.assertIn("[Reasoning]", output)
        self.assertIn("[Tool Call]", output)

    def test_hide_thoughts(self):
        # Set config
        config.SHOW_THOUGHTS = False
        config.SHOW_TOOL_CALLS = True
        
        # Capture stdout
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        try:
            self.agent.step()
        finally:
            sys.stdout = sys.__stdout__
            
        output = captured_output.getvalue()
        self.assertNotIn("[Thinking]", output)
        self.assertNotIn("[Reasoning]", output)
        self.assertIn("[Tool Call]", output)

    def test_hide_tool_calls(self):
        # Set config
        config.SHOW_THOUGHTS = True
        config.SHOW_TOOL_CALLS = False
        
        # Capture stdout
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        try:
            self.agent.step()
        finally:
            sys.stdout = sys.__stdout__
            
        output = captured_output.getvalue()
        self.assertIn("[Thinking]", output)
        self.assertIn("[Reasoning]", output)
        self.assertNotIn("[Tool Call]", output)

    def test_hide_everything(self):
        # Set config
        config.SHOW_THOUGHTS = False
        config.SHOW_TOOL_CALLS = False
        
        # Capture stdout
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        try:
            self.agent.step()
        finally:
            sys.stdout = sys.__stdout__
            
        output = captured_output.getvalue()
        self.assertNotIn("[Thinking]", output)
        self.assertNotIn("[Reasoning]", output)
        self.assertNotIn("[Tool Call]", output)

if __name__ == '__main__':
    unittest.main()
