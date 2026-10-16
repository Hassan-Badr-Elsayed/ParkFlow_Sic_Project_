import pytest
from core.searching import sequential_search, binary_search
from core.exceptions import NotSortedError

RECORDS = [
    {"plate": "ABC123", "fee": 10},
    {"plate": "DEF456", "fee": 20},
    {"plate": "GHI789", "fee": 30},
    {"plate": "JKL012", "fee": 40},
    {"plate": "MNO345", "fee": 50},
]


def test_sequential_exact_match():
    matches, comps = sequential_search(RECORDS, "plate", "GHI789")
    assert matches == [RECORDS[2]]
    assert comps == 5          # checks every record


def test_sequential_partial_match_ignores_case():
    matches, _ = sequential_search(RECORDS, "plate", "ef4", partial=True)
    assert matches == [RECORDS[1]]


def test_sequential_partial_can_return_several():
    matches, _ = sequential_search(RECORDS, "plate", "1", partial=True)
    assert [m["plate"] for m in matches] == ["ABC123", "JKL012"]


def test_sequential_no_results():
    matches, comps = sequential_search(RECORDS, "plate", "ZZZ999")
    assert matches == []
    assert comps == 5


def test_sequential_empty_list():
    assert sequential_search([], "plate", "ABC123") == ([], 0)


def test_sequential_works_on_unsorted_data():
    unsorted = [RECORDS[3], RECORDS[0], RECORDS[4]]
    matches, _ = sequential_search(unsorted, "plate", "ABC123")
    assert matches == [RECORDS[0]]


def test_sequential_skips_records_missing_the_field():
    data = [{"plate": "ABC123"}, {"fee": 5}]
    matches, comps = sequential_search(data, "plate", "ABC123")
    assert len(matches) == 1
    assert comps == 2


def test_binary_finds_first_middle_and_last():
    assert binary_search(RECORDS, "plate", "ABC123")[0] == 0
    assert binary_search(RECORDS, "plate", "GHI789")[0] == 2
    assert binary_search(RECORDS, "plate", "MNO345")[0] == 4


def test_binary_not_found_returns_minus_one():
    index, comps = binary_search(RECORDS, "plate", "ZZZ999")
    assert index == -1
    assert comps > 0


def test_binary_counts_comparisons_in_the_middle():
    index, comps = binary_search(RECORDS, "plate", "GHI789")
    assert index == 2
    assert comps == 1          # the middle item is found on the first check


def test_binary_empty_list():
    assert binary_search([], "plate", "ABC123") == (-1, 0)


def test_binary_works_on_numbers():
    assert binary_search(RECORDS, "fee", 40)[0] == 3


def test_binary_unsorted_data_raises():
    unsorted = [RECORDS[2], RECORDS[0], RECORDS[1]]
    with pytest.raises(NotSortedError):
        binary_search(unsorted, "plate", "ABC123")


def test_binary_sorted_by_a_different_field_raises():
    # sorted by fee, but we search by plate descending order
    data = [{"plate": "ZZZ111", "fee": 1}, {"plate": "AAA111", "fee": 2}]
    with pytest.raises(NotSortedError):
        binary_search(data, "plate", "AAA111")


def test_searches_do_not_change_the_list():
    copy = list(RECORDS)
    sequential_search(RECORDS, "plate", "GHI789")
    binary_search(RECORDS, "plate", "GHI789")
    assert RECORDS == copy
