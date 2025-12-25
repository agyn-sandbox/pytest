import sys


def test_capfd_includes_carriage_return(capfd):
    print("Greetings from DOS", end="\r")
    out, err = capfd.readouterr()
    assert out.endswith("\r")


def test_capfd_preserves_crlf(capfd):
    print("X\r\nY", end="", flush=True)
    out, err = capfd.readouterr()
    assert "\r\n" in out


def test_capfd_stderr_includes_carriage_return(capfd):
    print("Greetings from stderr", end="\r", file=sys.stderr)
    out, err = capfd.readouterr()
    assert err.endswith("\r")
