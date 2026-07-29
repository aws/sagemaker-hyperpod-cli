# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License.

import unittest
from unittest.mock import patch, Mock, MagicMock
from click.testing import CliRunner

from sagemaker.hyperpod.cli.commands.ssh import (
    space_ssh,
    _parse_ssh_connection_url,
    _start_ssm_session,
)


class TestParseSSHConnectionUrl(unittest.TestCase):
    """Test URL parsing for various connection URL formats."""

    def test_ssm_scheme_url(self):
        url = "ssm://mi-0abc123def456?documentName=AWS-StartSSHSession&portNumber=22"
        target, params = _parse_ssh_connection_url(url)
        self.assertEqual(target, "mi-0abc123def456")
        self.assertEqual(params["documentName"], "AWS-StartSSHSession")
        self.assertEqual(params["portNumber"], "22")

    def test_https_with_target_param(self):
        url = "https://ssm.us-west-2.amazonaws.com/session?target=mi-0abc123&documentName=AWS-StartSSHSession"
        target, params = _parse_ssh_connection_url(url)
        self.assertEqual(target, "mi-0abc123")
        self.assertEqual(params["documentName"], "AWS-StartSSHSession")

    def test_https_with_instance_id_param(self):
        url = "https://endpoint.example.com/connect?instanceId=mi-0abc123"
        target, params = _parse_ssh_connection_url(url)
        self.assertEqual(target, "mi-0abc123")

    def test_empty_url(self):
        target, params = _parse_ssh_connection_url("")
        self.assertIsNone(target)
        self.assertEqual(params, {})

    def test_none_url(self):
        target, params = _parse_ssh_connection_url(None)
        self.assertIsNone(target)
        self.assertEqual(params, {})


class TestSpaceSSHCommand(unittest.TestCase):
    """Test the CLI command integration."""

    @patch("sagemaker.hyperpod.cli.commands.ssh._start_ssm_session")
    @patch("sagemaker.hyperpod.cli.commands.ssh._parse_ssh_connection_url")
    @patch("sagemaker.hyperpod.cli.commands.ssh.HPSpace")
    @patch("sagemaker.hyperpod.cli.commands.ssh.resolve_region")
    def test_ssh_success(self, mock_resolve_region, mock_hp_space, mock_parse, mock_start):
        mock_resolve_region.return_value = "us-west-2"

        mock_space = Mock()
        mock_space.status = {"conditions": [{"type": "Available", "status": "True"}]}
        mock_space.create_space_access.return_value = {
            "SpaceConnectionType": "ssh-remote",
            "SpaceConnectionUrl": "ssm://mi-0abc123?documentName=AWS-StartSSHSession"
        }
        mock_hp_space.get.return_value = mock_space

        mock_parse.return_value = ("mi-0abc123", {"documentName": "AWS-StartSSHSession"})

        runner = CliRunner()
        result = runner.invoke(space_ssh, ["--name", "my-space"])

        mock_hp_space.get.assert_called_once_with(name="my-space", namespace="default")
        mock_space.create_space_access.assert_called_once_with(connection_type="ssh-remote")
        mock_start.assert_called_once_with(
            "mi-0abc123", {"documentName": "AWS-StartSSHSession"}, "us-west-2", False
        )

    @patch("sagemaker.hyperpod.cli.commands.ssh.HPSpace")
    @patch("sagemaker.hyperpod.cli.commands.ssh.resolve_region")
    def test_ssh_space_not_available(self, mock_resolve_region, mock_hp_space):
        mock_resolve_region.return_value = "us-west-2"

        mock_space = Mock()
        mock_space.status = {"conditions": [{"type": "Available", "status": "False"}]}
        mock_hp_space.get.return_value = mock_space

        runner = CliRunner()
        result = runner.invoke(space_ssh, ["--name", "my-space"])

        self.assertIn("not in Available status", result.output)


if __name__ == "__main__":
    unittest.main()
