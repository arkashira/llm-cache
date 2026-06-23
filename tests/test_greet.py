import pytest
from axentx_product import greet

def test_greet_basic():
    assert greet("World") == "Hello, World!"

def test_greet_whitespace_and_case():
    assert greet("  alice  ") == "Hello, Alice!"
    assert greet("bOb") == "Hello, Bob!"

def test_greet_empty_string():
    assert greet("") == "Hello!"
    assert greet("   ") == "Hello!"

def test_greet_non_string():
    with pytest.raises(TypeError):
        greet(123)
