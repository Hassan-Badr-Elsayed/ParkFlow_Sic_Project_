import pytest
from core.structures import Stack, Queue, HashTable, UserRegistry
from core.exceptions import DuplicateUserError, UserNotFoundError, NothingToUndoError



def test_stack_is_last_in_first_out():
    s = Stack()
    s.push("a")
    s.push("b")
    s.push("c")
    assert s.pop() == "c"
    assert s.pop() == "b"
    assert s.peek() == "a"
    assert s.size() == 1


def test_stack_empty_pop_and_peek_raise():
    s = Stack()
    assert s.is_empty()
    with pytest.raises(NothingToUndoError):
        s.pop()
    with pytest.raises(NothingToUndoError):
        s.peek()


def test_stack_to_list_is_a_copy():
    s = Stack()
    s.push(1)
    s.push(2)
    items = s.to_list()
    assert items == [1, 2]
    items.append(99)
    assert s.size() == 2


def test_queue_is_first_in_first_out():
    q = Queue()
    q.enqueue("a")
    q.enqueue("b")
    q.enqueue("c")
    assert q.peek() == "a"
    assert q.dequeue() == "a"
    assert q.dequeue() == "b"
    assert q.to_list() == ["c"]
    assert q.size() == 1


def test_queue_empty_dequeue_and_peek_raise():
    q = Queue()
    assert q.is_empty()
    with pytest.raises(IndexError):
        q.dequeue()
    with pytest.raises(IndexError):
        q.peek()


def test_hash_put_get_and_default():
    h = HashTable()
    h.put("ABC123", {"space": "A-01"})
    assert h.get("ABC123") == {"space": "A-01"}
    assert h.get("NOPE") is None
    assert h.get("NOPE", "none") == "none"
    assert h.contains("ABC123")
    assert not h.contains("NOPE")


def test_hash_put_same_key_replaces_value():
    h = HashTable()
    h.put("ABC123", 1)
    h.put("ABC123", 2)
    assert h.get("ABC123") == 2
    assert len(h) == 1


def test_hash_collisions_share_a_bucket_and_both_work():
    h = HashTable(size=1)          # size 1 forces every key into one bucket
    h.put("AAA111", 1)
    h.put("BBB222", 2)
    h.put("CCC333", 3)
    assert h.get("AAA111") == 1
    assert h.get("BBB222") == 2
    assert h.get("CCC333") == 3
    assert len(h) == 3


def test_hash_remove_then_get():
    h = HashTable(size=1)
    h.put("AAA111", 1)
    h.put("BBB222", 2)
    assert h.remove("AAA111") is True
    assert h.get("AAA111") is None
    assert h.get("BBB222") == 2          # the other key in the bucket survives
    assert h.remove("AAA111") is False   # already gone
    assert len(h) == 1


def test_hash_keys_and_values():
    h = HashTable()
    h.put("A", 1)
    h.put("B", 2)
    assert sorted(h.keys()) == ["A", "B"]
    assert sorted(h.values()) == [1, 2]


def test_hash_empty():
    h = HashTable()
    assert len(h) == 0
    assert h.keys() == []
    assert h.values() == []


class FakeUser:
    """Stand-in for Student 1's User class."""
    def __init__(self, username, role="driver"):
        self.username = username
        self.role = role
 
 
def test_add_and_get_user():
    reg = UserRegistry()
    sara = FakeUser("sara", "admin")
    reg.add_user(sara)
    assert reg.get_user("sara") is sara
    assert reg.has_user("sara")
    assert reg.count() == 1
 
 
def test_username_is_not_case_sensitive_and_ignores_spaces():
    reg = UserRegistry()
    sara = FakeUser("Sara")
    reg.add_user(sara)
    assert reg.get_user("  sARA ") is sara
 
 
def test_duplicate_username_raises():
    reg = UserRegistry()
    reg.add_user(FakeUser("sara"))
    with pytest.raises(DuplicateUserError):
        reg.add_user(FakeUser("SARA"))
 
 
def test_get_missing_user_raises():
    reg = UserRegistry()
    assert not reg.has_user("ghost")
    with pytest.raises(UserNotFoundError):
        reg.get_user("ghost")
 
 
def test_remove_user():
    reg = UserRegistry()
    reg.add_user(FakeUser("sara"))
    reg.remove_user("sara")
    assert not reg.has_user("sara")
    assert reg.count() == 0
    with pytest.raises(UserNotFoundError):
        reg.remove_user("sara")
 
 
def test_all_users_and_empty_registry():
    reg = UserRegistry()
    assert reg.all_users() == []
    a, b = FakeUser("a"), FakeUser("b")
    reg.add_user(a)
    reg.add_user(b)
    assert len(reg.all_users()) == 2


def test_hash_get_with_comparisons():
    h = HashTable(size=1)                 # one bucket, so keys are checked in order
    h.put("AAA111", 1)
    h.put("BBB222", 2)
    assert h.get_with_comparisons("AAA111") == (1, 1)
    assert h.get_with_comparisons("BBB222") == (2, 2)
    assert h.get_with_comparisons("NOPE", "x") == ("x", 2)