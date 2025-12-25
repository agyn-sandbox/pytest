import pytest


def _register_marks(pytester: pytest.Pytester) -> None:
    pytester.makeini(
        """
        [pytest]
        markers =
            alpha(value): mark used for MRO ordering checks
            beta(value): class-level mark defined on subclasses
            gamma(value): function-level mark used for ordering assertions
            shared(value): mark used to exercise deduplication
            method(value): additional function-level mark
            diamond(value): mark applied in diamond inheritance scenarios
        """
    )


def test_multiple_inheritance_merges_marks(pytester: pytest.Pytester) -> None:
    _register_marks(pytester)
    pytester.makepyfile(
        """
        import pytest

        class BaseA:
            pytestmark = pytest.mark.alpha("base-a")

        class BaseB:
            pytestmark = [pytest.mark.alpha("base-b")]

        @pytest.mark.beta("derived")
        class TestDerived(BaseA, BaseB):
            @pytest.mark.gamma("method")
            def test_method(self, request):
                seen = [(mark.name, mark.args) for mark in request.node.iter_markers()]
                assert seen == [
                    ("gamma", ("method",)),
                    ("beta", ("derived",)),
                    ("alpha", ("base-a",)),
                    ("alpha", ("base-b",)),
                ]
        """
    )

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_function_marks_precede_class_marks(pytester: pytest.Pytester) -> None:
    _register_marks(pytester)
    pytester.makepyfile(
        """
        import pytest

        @pytest.mark.alpha("base")
        class Base:
            pass

        class TestDerived(Base):
            pytestmark = [pytest.mark.beta("derived-list")]

            @pytest.mark.method("first")
            @pytest.mark.gamma("second")
            def test_method(self, request):
                names = [mark.name for mark in request.node.iter_markers()]
                assert names[:2] == ["gamma", "method"]
                assert names[2:] == ["beta", "alpha"]
        """
    )

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_diamond_inheritance_deduplicates_marks(pytester: pytest.Pytester) -> None:
    _register_marks(pytester)
    pytester.makepyfile(
        """
        import pytest

        @pytest.mark.shared("root")
        class Root:
            pass

        @pytest.mark.shared("branch")
        @pytest.mark.alpha("left")
        class Left(Root):
            pass

        @pytest.mark.shared("branch")
        @pytest.mark.alpha("right")
        class Right(Root):
            pass

        class TestLeaf(Left, Right):
            @pytest.mark.gamma("method")
            def test_leaf(self, request):
                seen = [(mark.name, mark.args) for mark in request.node.iter_markers()]
                assert seen == [
                    ("gamma", ("method",)),
                    ("alpha", ("left",)),
                    ("shared", ("branch",)),
                    ("alpha", ("right",)),
                    ("shared", ("root",)),
                ]
        """
    )

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_identical_marks_across_bases_deduped_once(
    pytester: pytest.Pytester,
) -> None:
    _register_marks(pytester)
    pytester.makepyfile(
        """
        import pytest

        class BaseA:
            pytestmark = [pytest.mark.shared("duplicate")]

        class BaseB:
            pytestmark = pytest.mark.shared("duplicate")

        class TestDerived(BaseA, BaseB):
            def test_marks(self, request):
                seen = [mark.args for mark in request.node.iter_markers(name="shared")]
                assert seen == [("duplicate",)]
        """
    )

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_parametrize_marks_merge_and_dedupe(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        import pytest

        class ParamBaseA:
            pytestmark = pytest.mark.parametrize("left", ["L1", "L2"])

        class ParamBaseB:
            pytestmark = [
                pytest.mark.parametrize("right", ["R1", "R2"]),
                pytest.mark.parametrize("left", ["L1", "L2"]),
            ]

        class TestParam(ParamBaseA, ParamBaseB):
            def test_params(self, left, right):
                pass
        """
    )

    result = pytester.runpytest()
    result.assert_outcomes(passed=4)


def test_class_pytestmark_forms_supported(pytester: pytest.Pytester) -> None:
    _register_marks(pytester)
    pytester.makepyfile(
        """
        import pytest

        class Decorated:
            pytestmark = [pytest.mark.alpha("decorated")]

        @pytest.mark.beta("derived")
        class TestDerived(Decorated):
            @pytest.mark.gamma("method")
            def test_forms(self, request):
                seen = [(mark.name, mark.args) for mark in request.node.iter_markers()]
                assert seen == [
                    ("gamma", ("method",)),
                    ("beta", ("derived",)),
                    ("alpha", ("decorated",)),
                ]
        """
    )

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)
