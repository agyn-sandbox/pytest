from __future__ import annotations

import textwrap


def _run(pytester, *args):
    return pytester.runpytest("--assert=plain", *args)


def test_unittest_autouse_fixture_hidden_by_default(pytester) -> None:
    test_module = pytester.makepyfile(
        textwrap.dedent(
            """
            import unittest


            class SampleTest(unittest.TestCase):
                @classmethod
                def setUpClass(cls):
                    pass

                def test_dummy(self):
                    pass
            """
        )
    )

    default = _run(pytester, "--fixtures", str(test_module))
    default.stdout.no_fnmatch_line("*_unittest_setUpClass_fixture_*")

    verbose = _run(pytester, "-v", "--fixtures", str(test_module))
    verbose.stdout.fnmatch_lines_random(
        ["*_unittest_setUpClass_fixture_* -- */_pytest/unittest.py:*"]
    )

    per_test = _run(pytester, "--fixtures-per-test", str(test_module))
    per_test.stdout.no_fnmatch_line("*_unittest_setUpClass_fixture_*")

    per_test_verbose = _run(
        pytester, "-v", "--fixtures-per-test", str(test_module)
    )
    per_test_verbose.stdout.fnmatch_lines_random(
        ["*_unittest_setUpClass_fixture_* -- */_pytest/unittest.py:*"]
    )


def test_xunit_autouse_fixtures_hidden_by_default(pytester) -> None:
    test_module = pytester.makepyfile(
        textwrap.dedent(
            """
            values = []


            def setup_module(module):
                values.append("module")


            def teardown_module(module):
                values.append("teardown_module")


            class TestSample:
                @classmethod
                def setup_class(cls):
                    values.append("class")

                @classmethod
                def teardown_class(cls):
                    values.append("teardown_class")

                def setup_method(self, method):
                    values.append("method")

                def teardown_method(self, method):
                    values.append("teardown_method")

                def test_dummy(self):
                    pass
            """
        )
    )

    hidden_patterns = [
        "*_xunit_setup_module_fixture_*",
        "*_xunit_setup_class_fixture_*",
        "*_xunit_setup_method_fixture_*",
    ]
    visible_patterns = [
        "*_xunit_setup_module_fixture_* -- */_pytest/python.py:*",
        "*_xunit_setup_class_fixture_* -- */_pytest/python.py:*",
        "*_xunit_setup_method_fixture_* -- */_pytest/python.py:*",
    ]

    default = _run(pytester, "--fixtures", str(test_module))
    for pattern in hidden_patterns:
        default.stdout.no_fnmatch_line(pattern)

    verbose = _run(pytester, "-v", "--fixtures", str(test_module))
    verbose.stdout.fnmatch_lines_random(visible_patterns)

    per_test = _run(pytester, "--fixtures-per-test", str(test_module))
    for pattern in hidden_patterns:
        per_test.stdout.no_fnmatch_line(pattern)

    per_test_verbose = _run(pytester, "-v", "--fixtures-per-test", str(test_module))
    per_test_verbose.stdout.fnmatch_lines_random(visible_patterns)
