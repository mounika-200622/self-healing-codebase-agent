def is_palindrome(s):
    """Returns True if s is a palindrome (reads the same forwards and backwards), ignoring case and spaces."""
    s = ''.join(e for e in s if e.isalnum()).lower()
    return s == s[::-1]