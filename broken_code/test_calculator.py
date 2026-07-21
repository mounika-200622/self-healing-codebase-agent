from calculator import calculate_average

def test_average_basic():
    assert calculate_average([1, 2, 3]) == 2

def test_average_single():
    assert calculate_average([5]) == 5