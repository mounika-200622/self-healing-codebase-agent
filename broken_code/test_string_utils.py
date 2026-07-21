from string_utils import is_palindrome

def test_simple_palindrome():
    assert is_palindrome("racecar") == True

def test_with_spaces_and_case():
    assert is_palindrome("Race car") == True

def test_not_palindrome():
    assert is_palindrome("hello") == False