from inventory import apply_discount, total_cost

def test_discount_20_percent():
    assert apply_discount(100, 20) == 80

def test_discount_50_percent():
    assert apply_discount(200, 50) == 100

def test_total_cost_single_item():
    assert total_cost([(10, 2)]) == 20

def test_total_cost_multiple_items():
    assert total_cost([(10, 2), (5, 3)]) == 35