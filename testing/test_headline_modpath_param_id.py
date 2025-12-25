import pytest


def test_headline_preserves_dot_bracket_in_param_id(testdir):
    testdir.makepyfile(
        **{
            "test_sample.py": (
                """
                import pytest

                @pytest.mark.parametrize("arg", [0], ids=["a..[b]"])
                def test_boo(arg):
                    assert False
                """
            )
        }
    )
    result = testdir.runpytest("-vv")
    # Ensure the failure headline contains the exact param id text without mutation
    result.stdout.fnmatch_lines([
        "*FAILURES*",
        "*test_boo[a..[b]]*",
    ])
    assert result.ret != 0
