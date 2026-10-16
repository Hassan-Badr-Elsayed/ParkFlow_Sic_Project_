# ParkFlow: Data Structures and Searching (Student 2)

Files: `core/structures.py` (Stack, Queue, HashTable, UserRegistry), `core/searching.py`
Tests: `tests/test_structures.py`, `tests/test_searching.py`
Evidence script: `core/compare_lookup.py`

## 1. Stack

**What it is:** last in, first out. We use a Python list inside the class. `push` adds to the end, `pop` removes from the end.

**Where ParkFlow uses it:** the action history. Every park or queue-join is pushed. "Undo" pops the most recent one. The last action is always the one you want to undo, so a stack fits.

**Why this and not that:** a queue would give back the oldest action first, but undo needs the newest. A stack only exposes the top, so a middle action cannot be undone by mistake.

**Edge case:** `pop` or `peek` on an empty stack raises `NothingToUndoError`.

## 2. Queue

**What it is:** first in, first out. `enqueue` adds to the end, `dequeue` removes from the front.

**Where ParkFlow uses it:** the waiting list. When the lot is full, vehicles join the queue. When a space is freed, the vehicle that waited longest gets it. That is fairness, and a queue gives it for free.

**Why this and not that:** a stack would serve the newest waiting vehicle first, which is unfair to the ones who waited longer. A priority queue is not needed because ParkFlow has no priority rule, only arrival order.

**Edge case:** `dequeue` or `peek` on an empty queue raises `IndexError`. Student 3 checks `is_empty()` first.

## 3. Hash table

**What it is:** a list of 53 buckets. Each bucket is a list of `[key, value]` pairs (chaining).

**Hash function** (turns a key into a bucket number):

```
total = 0
for each character: total = total * 31 + ord(character)
bucket = total % 53
```

**Where ParkFlow uses it:**
- `ParkingLot` maps plate number to active session. Exit looks up the plate directly instead of scanning every session.
- `UserRegistry` maps username to User object (section 6).

**Why this and not that:** a list with sequential search gets slower as the data grows (see section 7). A sorted list with binary search would need re-sorting after every park and exit, while a hash table adds and removes a key cheaply. A Python dict would work, but the course requires a custom hash table.

**Collision trace (by hand).** Keys `A009` and `A020` both land in bucket 33:

| Key | Calculation | total | total % 53 |
|---|---|---|---|
| A009 | 65 -> 65*31+48 = 2063 -> 2063*31+48 = 64001 -> 64001*31+57 | 1984088 | 33 |
| A020 | 65 -> 2063 -> 2063*31+50 = 64003 -> 64003*31+48 | 1984141 | 33 |

1. `put("A009", x)`: bucket 33 is empty, so `["A009", x]` is added.
2. `put("A020", y)`: bucket 33 already holds A009, which is a collision. A020 does not match, so `["A020", y]` is added to the same bucket.
3. `get("A020")`: go to bucket 33, compare with A009 (no match), compare with A020 (match). Two comparisons.

`put` on an existing key replaces the value. `remove` returns `True` or `False`.

**Limit to be honest about:** the table size is fixed at 53, so each chain averages (keys / 53) long. That is fine for a 30-space lot. For thousands of keys, create the table bigger (`HashTable(size=...)`).

## 4. Sequential search

**What it is:** check every record from the start, one by one.

**Where ParkFlow uses it:** the Lookup tab, partial plate search (for example "ABC" finds ABC123 and ABC987). It works on unsorted data, which is what we have in the active list.

**Why this and not that:** binary search cannot be used here because the active list is not sorted. Partial matches (text anywhere inside a plate) also do not follow sorted order. A hash table only finds an exact key, so it cannot do partial search either.

**Details:** exact match uses `==`. Partial match ignores case. It scans the whole list because it collects all matches, so the comparison count equals the list length. A record missing the field is skipped.

## 5. Binary search

**What it is:** look at the middle record, then throw away the half that cannot contain the target. Repeat.

**Where ParkFlow uses it:** exact plate search in the history, after S5 sorts a copy by plate with S4's `merge_sort`.

**Why this and not that:** on a large sorted history it needs far fewer comparisons than sequential search. It is only used when the data is already sorted by the same field, because the sorting itself costs time. A hash table would only help for the one key it was built on, but the history can be sorted and searched by any field.

**Safety rule:** before searching, the function checks the list is sorted ascending by the same field. If not, it raises `NotSortedError`. This check is not counted in the comparison count, because it is a precondition and not part of the search. It does cost one pass over the list (n - 1 checks), which is more work than the search itself. We accept that cost to guarantee a correct answer (see the defense questions).

**Trace.** Sorted plates: `ABC123, DEF456, GHI789, JKL012, MNO345`. Target: `MNO345`.

| Step | low | high | mid | Record at mid | Result |
|---|---|---|---|---|---|
| 1 | 0 | 4 | 2 | GHI789 | smaller than target, low = 3 |
| 2 | 3 | 4 | 3 | JKL012 | smaller than target, low = 4 |
| 3 | 4 | 4 | 4 | MNO345 | found, index 4 |

3 comparisons. Sequential search would need 5.

## 6. User registry

**What it is:** `UserRegistry` in `structures.py`, below `HashTable`. It maps a username to its User object using our HashTable. The User class itself is written by Student 1 in `models.py`.

**Where ParkFlow uses it:** looking up a user by username. Student 5's menus call `get_user(username)` to check the user exists and read their role from the User object.

**Why this and not that:** a plain list of users would need a sequential search on every lookup, so the cost grows with the number of users. The hash table finds a username directly, the same way it finds a plate. Usernames are cleaned first (trimmed and lowercase), so `"  sARA "` and `"Sara"` are the same account.

**Edge cases:** adding a username that already exists raises `DuplicateUserError`. Looking up or removing a missing user raises `UserNotFoundError`.

## 7. Performance evidence: hash table vs sequential search

**How the numbers were produced:** `python core/compare_lookup.py`. The script looks up every key once and averages the results. Hash table size was `max(53, keys / 2)`.

**Run details:** run on 2026-10-13, Python 3.12.13, windows.

| Keys | Sequential comparisons | Hash comparisons | Sequential time per lookup | Hash time per lookup |
|---|---|---|---|---|
| 30 | 30.0 | 1.03 | 2.29 us | 0.72 us |
| 100 | 100.0 | 1.53 | 7.11 us | 0.76 us |
| 1000 | 1000.0 | 1.67 | 79.80 us | 0.79 us |
| 5000 | 5000.0 | 1.71 | 359.80 us | 0.85 us |

**What is stable and what is not:** The comparison counts are the same on every machine, so they are the stable evidence. The times change from run to run and from computer to computer, so quote them as rough sizes, not exact values.

**What it shows:** sequential search cost grows in step with the number of keys. The hash table stays at about 1 to 2 comparisons whatever the size. At 30 keys (our real lot size) both are fast, so the gain matters more as data grows.

**Binary search:** the search itself needs about log2(n) comparisons (about 12 for 5000), but the data must be sorted first, and our sorted-check adds one pass over the list on every call. So with our safety check, a single binary search is not faster than a sequential search. The benefit appears when the data is sorted once and searched many times.

## 8. Defense preparation

**Why each structure fits ParkFlow**
- Stack: undo always needs the most recent action first.
- Queue: waiting vehicles are served in arrival order.
- Hash table: exit and username lookup need to find one record by key without scanning everything.
- Sequential search: needed for partial search and for unsorted data.
- Binary search: faster exact search once the data is sorted.

**Likely questions**
- *What happens when two keys hash to the same bucket?* They share the bucket's list and are compared one by one (see the A009 and A020 trace).
- *Why does binary search check that the data is sorted first?* On unsorted data it can discard the half that holds the target and silently answer "not found" when the record exists. The check turns a silent wrong answer into a clear error.
- *Doesn't that check make binary search slower than sequential search?* Yes, for a single search. The check is one pass over the list, which is more work than the search. We keep it because correctness matters more here, and the benefit comes when sorted data is searched many times.
- *Why is the sorted check not counted in the comparison count?* It is a precondition, not part of the search algorithm. The count shows the cost of the search itself. We say clearly that the check has its own cost.
- *Why not use a Python dict?* The course requires a custom hash table.
- *What is the weakness of your hash table?* The fixed size. Chains grow if you store many more keys than buckets.
- *Your time numbers differ from mine. Which is right?* Both. Times depend on the computer and the run. The comparison counts are the stable evidence.
