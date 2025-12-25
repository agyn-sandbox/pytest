import pytest

from _pytest._code.code import ExceptionChainRepr
from _pytest.reports import TestReport
from _pytest.reports import pytest_report_from_serializable
from _pytest.reports import pytest_report_to_serializable


CHAIN_TEST = """
def fail_with_chain():
    try:
        raise ValueError('inner')
    except ValueError:
        try:
            raise RuntimeError('middle')
        except RuntimeError as exc:
            raise KeyError('outer') from exc


def test_chain_failure():
    fail_with_chain()
"""


def _collect_failed_call_report(testdir):
    testdir.makepyfile(CHAIN_TEST)
    reprec = testdir.inline_run()
    reports = reprec.getreports("pytest_runtest_logreport")
    return next(
        rep for rep in reports if rep.when == "call" and rep.failed
    )


def test_report_json_roundtrip_preserves_chain(testdir):
    report = _collect_failed_call_report(testdir)

    serialized = report._to_json()
    reconstructed = TestReport._from_json(serialized)

    assert isinstance(reconstructed.longrepr, ExceptionChainRepr)
    text = reconstructed.longreprtext
    assert (
        "During handling of the above exception, another exception occurred:" in text
    )
    assert (
        "The above exception was the direct cause of the following exception:" in text
    )


def test_report_hook_roundtrip_preserves_chain(testdir):
    report = _collect_failed_call_report(testdir)

    payload = pytest_report_to_serializable(report)
    reconstructed = pytest_report_from_serializable(payload)

    assert isinstance(reconstructed.longrepr, ExceptionChainRepr)
    text = reconstructed.longreprtext
    assert (
        "During handling of the above exception, another exception occurred:" in text
    )
    assert (
        "The above exception was the direct cause of the following exception:" in text
    )


def test_xdist_run_preserves_chain_output(testdir):
    pytest.importorskip("xdist")

    testdir.makepyfile(CHAIN_TEST)
    result = testdir.runpytest("-n", "1")

    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(
        [
            "*During handling of the above exception, another exception occurred:*",
            "*The above exception was the direct cause of the following exception:*",
        ]
    )
