import sys


def test_setup_show_parametrized_fixture_bytes_no_byteswarning(testdir):
    p = testdir.makepyfile(
        """
        import pytest

        @pytest.fixture(params=[b"Hello World"])
        def data(request):
            return request.param

        def test_data(data):
            pass
        """
    )
    # Run pytest via the Python interpreter to pass -bb so BytesWarning becomes an error.
    result = testdir.run(sys.executable, "-bb", "-m", "pytest", "--setup-show", p)
    assert result.ret == 0
    # Verify that the bytes value is displayed using a repr-like format.
    result.stdout.fnmatch_lines(["*SETUP    F data?b'Hello World'?*"])
