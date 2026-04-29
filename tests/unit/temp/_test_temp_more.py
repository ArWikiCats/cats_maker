import json
import random
from pathlib import Path

import pytest

from src.temp import main_make_temp_no_title

test_data = {}

file = Path("D:/categories_bot/langlinks/source/new.json")

with file.open(encoding="utf-8") as f:
    data = json.load(f)

test_data = {x: "" for x in data.values() if any(char.isdigit() for char in x)}

list_data = list(test_data.items())
random.shuffle(list_data)


def get_items(limit: int) -> dict[str, str]:
    list_limit = list_data[:limit]
    return {x: v for x, v in dict(list_limit).items()}


test_data_10 = get_items(10)
test_data_10k = get_items(10000)


def test_load() -> None:
    assert len(test_data) == 100000
    assert len(test_data_10k) == 10000


@pytest.mark.parametrize("cat, expected", test_data_10.items(), ids=test_data_10.keys())
def test_10(cat: str, expected: str) -> None:
    result = main_make_temp_no_title(cat)
    assert result == expected


@pytest.mark.parametrize("cat, expected", test_data_10k.items(), ids=test_data_10k.keys())
def test_10k(cat: str, expected: str) -> None:
    result = main_make_temp_no_title(cat)
    assert result == expected
