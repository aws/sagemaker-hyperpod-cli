import unittest
from unittest.mock import patch, MagicMock
import click
from click.testing import CliRunner
from sagemaker.hyperpod.cli.hyp_cli import cli, create, list, describe
from sagemaker.hyperpod.cli.commands.training import (
    pytorch_create,
    list_jobs,
    pytorch_describe,
)


class TestCLI(unittest.TestCase):
    """Test cases for the main CLI module"""

    def setUp(self):
        self.runner = CliRunner()

    def test_cli_help(self):
        """Test that the CLI help command works"""
        result = self.runner.invoke(cli, ["--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Usage:", result.output)
        self.assertIn("create", result.output)

    def test_cli_create_help(self):
        """Test that the create help command works"""
        result = self.runner.invoke(cli, ["create", "--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("hp-pytorch-job", result.output)

    @patch("sagemaker.hyperpod.cli.commands.training.list_jobs")
    def test_cli_list_jobs_help(self, mock_list_jobs):
        """Test that the list jobs help command works"""
        result = self.runner.invoke(cli, ["list", "hp-pytorch-job", "--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("List all HyperPod PyTorch jobs", result.output)

    @patch("sagemaker.hyperpod.cli.commands.training.pytorch_describe")
    def test_cli_describe_job_help(self, mock_pytorch_describe):
        """Test that the describe job help command works"""
        result = self.runner.invoke(cli, ["describe", "hp-pytorch-job", "--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Describe a HyperPod PyTorch job", result.output)

    def test_cli_commands_registered(self):
        """Test that all commands are registered with the CLI"""
        # Get all commands registered with the CLI
        commands = cli.commands

        # Check that the expected commands are registered
        self.assertIn("create", commands)
        self.assertIn("list", commands)
        self.assertIn("describe", commands)

    def test_subcommands_registered(self):
        """Test that all subcommands are registered with their parent commands"""
        # Check that the expected subcommands are registered
        create_commands = create.commands
        list_commands = list.commands
        describe_commands = describe.commands

        self.assertIn("hp-pytorch-job", create_commands)
        self.assertIn("hp-pytorch-job", list_commands)
        self.assertIn("hp-pytorch-job", describe_commands)

    def test_cli_command_help_format(self):
        """Test that the custom help format is used"""
        # Test create command help format
        result = self.runner.invoke(create, ["--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Usage: create [OPTIONS] COMMAND [ARGS]", result.output)

        # Test list command help format
        result = self.runner.invoke(list, ["--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Usage: list [OPTIONS] COMMAND [ARGS]", result.output)

        # Test describe command help format
        result = self.runner.invoke(describe, ["--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Usage: describe [OPTIONS] COMMAND [ARGS]", result.output)


