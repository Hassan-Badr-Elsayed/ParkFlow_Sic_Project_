from core.sorting import insertion_sort, merge_sort, compare_sorts

def test_insertion_sort_ascending():
    data=[{"fee":20},{"fee":10},{"fee":15}]
    result,stats=insertion_sort(data,"fee")
    expected=sorted(data,key=lambda x:x["fee"])
    assert result == expected

def test_insertion_sort_descending():
    data = [{"fee": 20}, {"fee": 10}, {"fee": 15}, {"fee": 5}]
    result, stats = insertion_sort(data, "fee", reverse=True)
    assert result == sorted(data, key=lambda x: x["fee"], reverse=True)

def test_insertion_sort_empty():
    result,stats=insertion_sort([],"fee")
    assert result == []

def test_sorts_already_sorted_list():
    data = [{"fee": 1}, {"fee": 2}, {"fee": 3}]
    assert insertion_sort(data, "fee")[0] == data
    assert merge_sort(data, "fee")[0] == data

def test_sorts_with_duplicates():
    data = [{"fee": 3}, {"fee": 1}, {"fee": 3}, {"fee": 1}]
    expected = sorted(data, key=lambda x: x["fee"])
    assert insertion_sort(data, "fee")[0] == expected
    assert merge_sort(data, "fee")[0] == expected

def test_insertion_sort_does_not_change_original():
    data = [{"fee": 20}, {"fee": 10}]
    insertion_sort(data, "fee")
    assert data == [{"fee": 20}, {"fee": 10}]

def test_merge_sort_ascending():
    data = [{"fee": 20}, {"fee": 10}, {"fee": 15}, {"fee": 5}]
    result, stats = merge_sort(data, "fee")
    assert result == sorted(data, key=lambda x: x["fee"])

def test_merge_sort_descending():
    data = [{"fee": 20}, {"fee": 10}, {"fee": 15}, {"fee": 5}]
    result, stats = merge_sort(data, "fee", reverse=True)
    assert result == sorted(data, key=lambda x: x["fee"], reverse=True)

def test_merge_sort_empty():
    result, stats = merge_sort([], "fee")
    assert result == []

def test_merge_sort_does_not_change_original():
    data = [{"fee": 20}, {"fee": 10}]
    merge_sort(data, "fee")
    assert data == [{"fee": 20}, {"fee": 10}]

def test_sorts_agree():
    data = [{"fee": 3}, {"fee": 1}, {"fee": 3}, {"fee": 2}]
    assert compare_sorts(data, "fee")["same_result"] == True

def test_sorts_agree_descending():
    data= [{"fee": 3}, {"fee": 1}, {"fee": 4}, {"fee": 2}]

    result = compare_sorts(data, "fee", reverse=True)

    assert result["same_result"] is True
    assert insertion_sort(data, "fee", reverse=True)[0] == [
       {"fee": 4}, {"fee": 3}, {"fee": 2}, {"fee": 1}]

def test_sorts_are_stable():
    data = [{"fee": 3, "id": "a"}, {"fee": 1, "id": "b"},
            {"fee": 3, "id": "c"}, {"fee": 1, "id": "d"}]
    expected = sorted(data, key=lambda x: x["fee"])
    assert insertion_sort(data, "fee")[0] == expected
    assert merge_sort(data, "fee")[0] == expected


