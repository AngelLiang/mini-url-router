"""
类型转换器
"""

from .exceptions import ValidationError
from urllib.parse import quote


class BaseConverter(object):
    """
    Base class for all converters.
    """
    regex = '[^/]+'
    is_greedy = False

    def __init__(self, map):
        self.map = map

    def to_python(self, value):
        return value

    def to_url(self, value):
        return quote(value.encode(self.map.charset))


class UnicodeConverter(BaseConverter):
    """
    The default converter for all URL parts. Matches one string without a
    slash in the part. Can also check for the length of that string.
    """

    def __init__(self, map, minlength=1, maxlength=None, length=None):
        BaseConverter.__init__(self, map)
        if length is not None:
            length = '{%d}' % int(length)
        else:
            if maxlength is None:
                maxlength = ''
            else:
                maxlength = int(maxlength)
            length = '{%s,%s}' % (
                int(minlength),
                maxlength
            )
        self.regex = '[^/]' + length


class PathConverter(BaseConverter):
    """
    Matches a whole path (including slashes)
    """
    regex = '[^/].*'  # 匹配路径
    is_greedy = True  # 贪婪的


class NumberConverter(BaseConverter):
    """
    Baseclass for `IntegerConverter` and `FloatConverter`.
    """

    def __init__(self, map, fixed_digits=0, min=None, max=None):
        BaseConverter.__init__(self, map)
        self.fixed_digits = fixed_digits
        self.min = min
        self.max = max

    def to_python(self, value):
        """转换为Python类型"""
        if (self.fixed_digits and len(value) != self.fixed_digits):
            raise ValidationError()
        value = self.num_convert(value)
        if (self.min is not None and value < self.min) or \
           (self.max is not None and value > self.max):
            raise ValidationError()
        return value

    def to_url(self, value):
        """转换为URL类型，用于构建URL"""
        value = self.num_convert(value)
        if self.fixed_digits:
            value = ('%%0%sd' % self.fixed_digits) % value
        return str(value)


class IntegerConverter(NumberConverter):
    """
    Only accepts integers.
    """
    regex = r'\d+'  # 匹配整型
    num_convert = int


class FloatConverter(NumberConverter):
    """
    Only accepts floats and integers.
    """
    regex = r'\d+\.\d+'  # 匹配浮点数
    num_convert = float

    def __init__(self, map, min=None, max=None):
        NumberConverter.__init__(self, map, 0, min, max)
