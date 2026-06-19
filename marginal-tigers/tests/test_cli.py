from marginal_tigers.cli import main


def test_hello_default(capsys):
    assert main(["hello"]) == 0
    assert capsys.readouterr().out.strip() == "Hello, world!"


def test_hello_name(capsys):
    assert main(["hello", "Tigers"]) == 0
    assert capsys.readouterr().out.strip() == "Hello, Tigers!"


def test_no_command_prints_help(capsys):
    assert main([]) == 0
    assert "usage" in capsys.readouterr().out.lower()
