import pytest


pytest_plugins = "pytester"


@pytest.fixture
def pytester(testdir):
    return testdir


def _disable_plugin_autoload(pytester):
    pytester.monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")


def test_dynamic_xfail_during_call(pytester):
    _disable_plugin_autoload(pytester)
    pytester.makepyfile(
        """
        import pytest


        def test_dynamic_xfail(request):
            request.node.add_marker(pytest.mark.xfail(reason="late xfail"))
            assert 0
        """
    )

    result = pytester.runpytest("-rx")
    result.assert_outcomes(xfailed=1)
    result.stdout.fnmatch_lines(
        ["*XFAIL*test_dynamic_xfail*", "*late xfail*"]
    )


def test_xfail_run_false_prevents_call(pytester):
    _disable_plugin_autoload(pytester)
    pytester.makepyfile(
        """
        import pytest


        @pytest.mark.xfail(run=False, reason="dismiss")
        def test_not_run():
            raise AssertionError("should not run")
        """
    )

    result = pytester.runpytest("-rx")
    result.assert_outcomes(xfailed=1)
    result.stdout.fnmatch_lines(
        ["*XFAIL*test_not_run*", "  reason: [NOTRUN] dismiss"]
    )
