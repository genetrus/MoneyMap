from money_map.app import cli


def test_cli_help() -> None:
    exit_code = cli.main(["--help"])
    assert exit_code == 0
