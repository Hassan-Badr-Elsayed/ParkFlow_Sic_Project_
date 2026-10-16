"""Custom data structures for ParkFlow (Student 2).

Stack      - action history, used for undo
Queue      - waiting list of vehicles (first come, first served)
HashTable  - fast lookup of an active session by plate number
"""

from core.exceptions import NothingToUndoError, DuplicateUserError, UserNotFoundError


class Stack:
    """Last in, first out. The top of the stack is the end of the list."""

    def __init__(self):
        self._items = []

    def push(self, item):
        self._items.append(item)

    def pop(self):
        if self.is_empty():
            raise NothingToUndoError("There is nothing to undo.")
        return self._items.pop()

    def peek(self):
        if self.is_empty():
            raise NothingToUndoError("There is nothing to undo.")
        return self._items[-1]

    def is_empty(self):
        return len(self._items) == 0

    def size(self):
        return len(self._items)

    def to_list(self):
        """Return a copy, bottom of the stack first."""
        return list(self._items)


class Queue:
    """First in, first out. The front of the queue is the start of the list."""

    def __init__(self):
        self._items = []

    def enqueue(self, item):
        self._items.append(item)

    def dequeue(self):
        if self.is_empty():
            raise IndexError("The queue is empty.")
        return self._items.pop(0)

    def peek(self):
        if self.is_empty():
            raise IndexError("The queue is empty.")
        return self._items[0]

    def is_empty(self):
        return len(self._items) == 0

    def size(self):
        return len(self._items)

    def to_list(self):
        """Return a copy, front of the queue first."""
        return list(self._items)


class HashTable:
    """Hash table with chaining.

    The table is a list of buckets. Each bucket is a list of [key, value]
    pairs. Keys that land in the same bucket (a collision) sit together
    in that bucket's list.
    """

    def __init__(self, size=53):
        self._size = size
        self._buckets = [[] for _ in range(size)]
        self._count = 0

    def _hash(self, key):
        """Turn a key into a bucket index."""
        total = 0
        for ch in str(key):
            total = total * 31 + ord(ch)
        return total % self._size

    def put(self, key, value):
        """Add a key, or replace its value if the key already exists."""
        bucket = self._buckets[self._hash(key)]
        for pair in bucket:
            if pair[0] == key:
                pair[1] = value
                return
        bucket.append([key, value])
        self._count += 1

    def get(self, key, default=None):
        bucket = self._buckets[self._hash(key)]
        for pair in bucket:
            if pair[0] == key:
                return pair[1]
        return default

    def get_with_comparisons(self, key, default=None):
        """Same as get, but also returns how many keys were compared.
 
        Returns (value, comparisons). Used for the performance evidence.
        """
        bucket = self._buckets[self._hash(key)]
        comparisons = 0
        for pair in bucket:
            comparisons += 1
            if pair[0] == key:
                return pair[1], comparisons
        return default, comparisons

    def remove(self, key):
        """Remove a key. Returns True if it was there, False if not."""
        bucket = self._buckets[self._hash(key)]
        for i in range(len(bucket)):
            if bucket[i][0] == key:
                bucket.pop(i)
                self._count -= 1
                return True
        return False

    def contains(self, key):
        bucket = self._buckets[self._hash(key)]
        for pair in bucket:
            if pair[0] == key:
                return True
        return False

    def keys(self):
        result = []
        for bucket in self._buckets:
            for pair in bucket:
                result.append(pair[0])
        return result

    def values(self):
        result = []
        for bucket in self._buckets:
            for pair in bucket:
                result.append(pair[1])
        return result

    def __len__(self):
        return self._count


class UserRegistry:
 
    def __init__(self):
        self._users = HashTable()
 
    def _clean(self, username):
        """Usernames are not case sensitive: 'Sara ' and 'sara' are the same."""
        return str(username).strip().lower()
 
    def add_user(self, user):
        key = self._clean(user.username)
        if self._users.contains(key):
            raise DuplicateUserError("Username '%s' is already taken." % user.username)
        self._users.put(key, user)
 
    def get_user(self, username):
        user = self._users.get(self._clean(username))
        if user is None:
            raise UserNotFoundError("No user named '%s'." % username)
        return user
 
    def has_user(self, username):
        return self._users.contains(self._clean(username))
 
    def remove_user(self, username):
        if not self._users.remove(self._clean(username)):
            raise UserNotFoundError("No user named '%s'." % username)
 
    def all_users(self):
        return self._users.values()
 
    def count(self):
        return len(self._users)