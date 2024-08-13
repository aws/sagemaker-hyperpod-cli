from click.testing import CliRunner

from hyperpod_cli.cli import cli


def test_hyperpod_cli_importable():
    import hyperpod_cli  # noqa: F401


def test_cli_init():
    runner = CliRunner()
    result = runner.invoke(cli)
    assert result.exit_code == 0
    assert not result.exception


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.output
