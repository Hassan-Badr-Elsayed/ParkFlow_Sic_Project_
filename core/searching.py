"""Search algorithms for ParkFlow (Student 2).

Both functions take a list of dicts (records) and a field name,
and never change the list they receive.
"""

from core.exceptions import NotSortedError


def sequential_search(records, field, target, partial=False):
    """Check every record from the start.

    partial=False: the field must equal the target.
    partial=True : the target must appear inside the field (ignores case).

    Returns (matches, comparisons).
    """
    matches = []
    comparisons = 0

    for record in records:
        comparisons += 1
        value = record.get(field)
        if value is None:
            continue
        if partial:
            if str(target).lower() in str(value).lower():
                matches.append(record)
        else:
            if value == target:
                matches.append(record)

    return matches, comparisons


def _is_sorted(records, field):
    """True if the records are in ascending order by field."""
    for i in range(1, len(records)):
        if records[i - 1].get(field) > records[i].get(field):
            return False
    return True


def binary_search(sorted_records, field, target):
    """Binary search on records sorted ascending by the same field.

    Returns (index, comparisons). The index is -1 if the target is not found.
    Raises NotSortedError if the records are not sorted by field.
    """
    if not _is_sorted(sorted_records, field):
        raise NotSortedError(
            "Binary search needs the records sorted by '%s'." % field
        )

    low = 0
    high = len(sorted_records) - 1
    comparisons = 0

    while low <= high:
        mid = (low + high) // 2
        value = sorted_records[mid].get(field)
        comparisons += 1
        if value == target:
            return mid, comparisons
        elif value < target:
            low = mid + 1
        else:
            high = mid - 1

    return -1, comparisons
