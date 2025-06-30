"""
简单测试验证测试框架
"""

import pytest


def test_simple_math():
    """测试简单数学运算"""
    assert 1 + 1 == 2
    assert 2 * 3 == 6
    assert 10 / 2 == 5


def test_string_operations():
    """测试字符串操作"""
    text = "Hello World"
    assert text.lower() == "hello world"
    assert text.replace("World", "Python") == "Hello Python"
    assert len(text) == 11


def test_list_operations():
    """测试列表操作"""
    numbers = [1, 2, 3, 4, 5]
    assert len(numbers) == 5
    assert sum(numbers) == 15
    assert max(numbers) == 5
    assert min(numbers) == 1


@pytest.mark.parametrize("input,expected", [
    (2, 4),
    (3, 9),
    (4, 16),
    (5, 25),
])
def test_square_function(input, expected):
    """测试平方函数"""
    def square(x):
        return x * x
    
    assert square(input) == expected


class TestClass:
    """测试类示例"""
    
    def test_class_method(self):
        """测试类方法"""
        assert True
    
    def test_fixture_usage(self, test_config):
        """测试fixture使用"""
        assert 'platforms' in test_config
        assert isinstance(test_config['platforms'], list)
        assert len(test_config['platforms']) > 0
