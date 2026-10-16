"""Compares HashTable lookup with sequential search (Student 2).

Run from the student2 folder:   python core/compare_lookup.py

For each size it looks up every key once and reports the average number of
comparisons and the average time per lookup.
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.searching import sequential_search
from core.structures import HashTable

SIZES = [30, 100, 1000, 5000]


def run(n):
    plates = ["P%05d" % i for i in range(n)]
    records = [{"plate": p, "slot": i} for i, p in enumerate(plates)]

    table = HashTable(size=max(53, n // 2))
    for r in records:
        table.put(r["plate"], r)

    # sequential search
    seq_comps = 0
    start = time.perf_counter()
    for p in plates:
        _, c = sequential_search(records, "plate", p)
        seq_comps += c
    seq_time = time.perf_counter() - start

    # hash table
    hash_comps = 0
    start = time.perf_counter()
    for p in plates:
        _, c = table.get_with_comparisons(p)
        hash_comps += c
    hash_time = time.perf_counter() - start

    return (n, seq_comps / n, hash_comps / n,
            seq_time / n * 1e6, hash_time / n * 1e6)


print("%-8s %-14s %-14s %-14s %-14s" %
      ("keys", "seq compares", "hash compares", "seq us/lookup", "hash us/lookup"))
for n in SIZES:
    n, sc, hc, st, ht = run(n)
    print("%-8d %-14.1f %-14.2f %-14.2f %-14.2f" % (n, sc, hc, st, ht))
