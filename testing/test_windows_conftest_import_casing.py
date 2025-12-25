import sys

import pytest


pytestmark = pytest.mark.skipif(
    sys.platform != "win32",
    reason="requires Windows path casing behavior",
)


def test_conftest_import_preserves_package_casing(pytester):
    pytester.makepyfile(
        **{
            "imageProcessing/__init__.py": "",
            "imageProcessing/subpkg/__init__.py": "",
            "imageProcessing/subpkg/helper.py": "FOO = 1\n",
            "conftest.py": (
                "from imageProcessing.subpkg import helper\n\n"
                "def pytest_configure(config):\n"
                "    config._helper_value = helper.FOO\n"
            ),
            "test_sample.py": (
                "def test_conftest_import(pytestconfig):\n"
                "    assert pytestconfig._helper_value == 1\n"
            ),
        }
    )

    result = pytester.runpytest("-q")
    result.assert_outcomes(passed=1)
