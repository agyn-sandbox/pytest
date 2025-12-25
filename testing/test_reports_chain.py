import re
import pytest


def _make_chained_test(testdir):
    return testdir.makepyfile(
        
        """
        def inner():
            raise ValueError("inner value error")

        def outer():
            try:
                inner()
            except ValueError as e:
                raise RuntimeError("outer runtime error") from e

        def test_chained_exception():
            outer()
        """
    )


def test_chained_exception_serialization_roundtrip(testdir):
    _make_chained_test(testdir)
    reprec = testdir.inline_run()
    reports = reprec.getreports("pytest_runtest_logreport")
    # setup, call, teardown
    assert len(reports) == 3
    rep = reports[1]
    assert rep.when == "call" and rep.failed
    # ensure chain marker is present in the worker-side representation
    longtext = rep.longreprtext
    assert (
        "The above exception was the direct cause of the following exception:" in longtext
    ), longtext

    # round-trip through pytest's JSON-serializable report format
    data = rep._to_json()
    newrep = type(rep)._from_json(data)

    assert newrep.longreprtext == rep.longreprtext


def test_chained_exception_hooks_roundtrip(testdir, pytestconfig):
    _make_chained_test(testdir)
    reprec = testdir.inline_run()
    rep = reprec.getreports("pytest_runtest_logreport")[1]

    data = pytestconfig.hook.pytest_report_to_serializable(
        config=pytestconfig, report=rep
    )
    assert data["_report_type"] == "TestReport"
    newrep = pytestconfig.hook.pytest_report_from_serializable(
        config=pytestconfig, data=data
    )
    assert newrep.longreprtext == rep.longreprtext


def test_chained_exception_visible_with_xdist(testdir):
    xdist = pytest.importorskip("xdist")
    p = _make_chained_test(testdir)
    # require at least one worker
    result = testdir.runpytest("-n", "1", str(p))
    result.stdout.fnmatch_lines([
        "*The above exception was the direct cause of the following exception:*",
    ])
