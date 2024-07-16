import pytest
from memotica.sm2 import sm2


@pytest.mark.parametrize(
    "test_name, test_data",
    [
        (
            "first recall wrong",
            {
                "parameters": {"n": 0, "ef": 2.5, "i": 0, "q": 0},
                "expected": (0, pytest.approx(2.15), 1),
            },
        ),
        (
            "first recall correct",
            {
                "parameters": {"n": 0, "ef": 2.5, "i": 0, "q": 3},
                "expected": (1, pytest.approx(2.43), 1),
            },
        ),
        (
            "second recall correct",
            {
                "parameters": {"n": 1, "ef": 2.5, "i": 1, "q": 3},
                "expected": (2, pytest.approx(2.43), 6),
            },
        ),
        (
            "first recall easy",
            {
                "parameters": {"n": 0, "ef": 2.5, "i": 0, "q": 5},
                "expected": (1, pytest.approx(2.6), 1),
            },
        ),
        (
            "fourth recall easy",
            {
                "parameters": {"n": 3, "ef": 2.5, "i": 12, "q": 5},
                "expected": (4, pytest.approx(2.6), 30),
            },
        ),
        (
            "fifth recall wrong",
            {
                "parameters": {"n": 5, "ef": 2.5, "i": 0, "q": 0},
                "expected": (0, pytest.approx(2.15), 1),
            },
        ),
    ],
)
def test_sm2(test_name, test_data):
    results = sm2(**test_data["parameters"])
    assert results == test_data["expected"]
