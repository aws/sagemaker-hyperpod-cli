import unittest
from sagemaker.hyperpod.cli.constants.hp_pytorch_command_constants import HELP_TEXT


class TestConstants(unittest.TestCase):
    """Test cases for the constants module"""

    def test_help_text_content(self):
        """Test that the help text contains expected content"""
        self.assertIsInstance(HELP_TEXT, str)
        self.assertIn("HyperPod PyTorch Job CLI", HELP_TEXT)
        self.assertIn("Commands:", HELP_TEXT)
        self.assertIn("Examples:", HELP_TEXT)
        self.assertIn("Usage:", HELP_TEXT)


if __name__ == "__main__":
    unittest.main()
