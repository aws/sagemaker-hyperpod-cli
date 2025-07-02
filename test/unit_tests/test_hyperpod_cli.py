# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
from click.testing import CliRunner

from sagemaker.hyperpod.cli.hyp_cli import cli


def test_hyperpod_cli_importable():
    import sagemaker.hyperpod.cli  # noqa: F401


def test_cli_init():
    runner = CliRunner()
    result = runner.invoke(cli)
    assert result.exit_code == 0
    assert not result.exception


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Basic Commands:" in result.output
