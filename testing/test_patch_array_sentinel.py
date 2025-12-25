from unittest.mock import patch


class WeirdEq:
    class Amb:
        def __bool__(self):
            raise ValueError("ambiguous truth")

    def __eq__(self, other):
        return WeirdEq.Amb()


@patch("os.path.abspath", new=WeirdEq())
def test_collect_ok():
    assert True
