import re
import operator
from .exceptions import ValidationError, RequestSlash
from .utils import url_encode

# 规则正则式
_rule_re = re.compile(r'''
    (?P<static>[^<]*)                           # static rule data
    <
    (?:
        (?P<converter>[a-zA-Z_][a-zA-Z0-9_]*)   # converter name
        (?:\((?P<args>.*?)\))?                  # converter arguments
        \:                                      # variable delimiter
    )?
    (?P<variable>[a-zA-Z][a-zA-Z0-9_]*)         # variable name
    >
''', re.VERBOSE)


def parse_rule(rule):
    """
    解析规则，判断 URL 是静态路由还是动态路由。
    解析规则并返回生成器。每一个返回迭代都是一个元组， `(converter, arguments, variable)`
    如果 converter 为 None， 则它是一个静态 URL 部分，否则是动态的。
    """
    pos = 0
    end = len(rule)
    do_match = _rule_re.match
    used_names = set()  # 已经使用的名字集合
    while pos < end:
        # 遍历rule
        m = do_match(rule, pos)  # return: re.MatchObject
        if m is None:
            break
        data = m.groupdict()
        if data['static']:
            # 返回URL静态部分
            yield None, None, data['static']
        variable = data['variable']
        converter = data['converter'] or 'default'
        if variable in used_names:
            raise ValueError('variable name %r used twice.' % variable)
        used_names.add(variable)
        # 返回URL动态部分
        yield converter, data['args'] or None, variable
        pos = m.end()  # 返回匹配结束的位置
    if pos < end:
        remaining = rule[pos:]
        if '>' in remaining or '<' in remaining:
            raise ValueError('malformed url rule: %r' % rule)
        # 返回URL剩余的部分
        yield None, None, remaining


def get_converter(map, name, args):
    """
    Create a new converter for the given arguments or raise
    exception if the converter does not exist.


    获取转换器
    创建一个新的转换器，对给定参数或抛出的异常，如果转换器不存在的话。
    """
    if not name in map.converters:
        raise LookupError('the converter %r does not exist' % name)
    if args:
        storage = type('_Storage', (), {'__getitem__': lambda s, x: x})()
        args, kwargs = eval('(lambda *a, **kw: (a, kw))(%s)' %
                            args, {}, storage)
    else:
        args = ()
        kwargs = {}
    return map.converters[name](map, *args, **kwargs)


class AbstractRule(object):

    def get_rules(self, map):
        raise NotImplementedError()


class Rule(AbstractRule):
    """
    Represents one url pattern.
    """

    def __init__(self, string, defaults=None, subdomain=None, methods=None,
                 build_only=False, endpoint=None, strict_slashes=None):
        """
        :param string: str, URL
        :param defaults: str
        :param subdomain: str
        :param methods: str
        :param build_only: str
        :param endpoint: str
        :param strict_slashes: 严格的斜杠
        """
        if not string.startswith('/'):
            raise ValueError('urls must start with a leading slash')
        self.rule = string
        self.is_leaf = not string.endswith('/')

        self.map = None
        self.strict_slashes = strict_slashes
        self.subdomain = subdomain
        self.defaults = defaults
        self.build_only = build_only
        if methods is None:
            self.methods = None
        else:
            self.methods = m = []
            for method in methods:
                m.append(method.upper())
            self.methods.sort(lambda a, b: cmp(len(b), len(a)))
        self.endpoint = endpoint
        self.greediness = 0

        self._trace = []
        self.arguments = set()
        self._converters = {}
        self._regex = None

    def get_rules(self, map):
        yield self

    def bind(self, map):
        """
        Bind the url to a map and create a regular expression based on
        the information from the rule itself and the defaults from the map.


        把url绑定到map，并创建一个正则表达式，基于来自rule自己和来自map的defaults的信息
        """
        if self.map is not None:
            raise RuntimeError('url rule %r already bound to map %r' %
                               (self, self.map))
        self.map = map

        # 严格的斜杠
        if self.strict_slashes is None:
            self.strict_slashes = map.strict_slashes

        # 子域名
        if self.subdomain is None:
            self.subdomain = map.default_subdomain

        rule = self.subdomain + '|' + (
            self.is_leaf and self.rule or self.rule.rstrip('/')
        )

        regex_parts = []
        # parse_rule: 解析规则
        for converter, arguments, variable in parse_rule(rule):
            if converter is None:
                # 静态部分
                regex_parts.append(re.escape(variable))
                self._trace.append((False, variable))
            else:
                # 动态部分
                convobj = get_converter(map, converter, arguments)
                regex_parts.append('(?P<%s>%s)' % (variable, convobj.regex))
                self._converters[variable] = convobj
                self._trace.append((True, variable))
                self.arguments.add(str(variable))  # 添加参数
                if convobj.is_greedy:
                    self.greediness += 1
        if not self.is_leaf:
            self._trace.append((False, '/'))

        if self.methods is None:
            method_re = '[^>]*'
        else:
            method_re = '|'.join([re.escape(x) for x in self.methods])

        if not self.build_only:
            regex = r'^%s%s\(%s\)$' % (
                u''.join(regex_parts),
                (not self.is_leaf or not self.strict_slashes) and
                '(?<!/)(?P<__suffix__>/?)' or '',
                method_re
            )
            self._regex = re.compile(regex, re.UNICODE)

    def match(self, path):
        """
        rule.match

        检查规则是否匹配给定的路径。路径是一个在 "subdomain|/path(method)" 的字符串，
        并且由 map 组装。

        如果rule使用转换器匹配了一个字典，一个值将被返回。否则返回None。
        """
        if not self.build_only:
            # re.search: 扫描整个字符串并返回第一个成功的匹配。
            m = self._regex.search(path)
            if m is not None:
                groups = m.groupdict()
                # we have a folder like part of the url without a trailing
                # slash and strict slashes enabled. raise an exception that
                # tells the map to redirect to the same url but with a
                # trailing slash
                if self.strict_slashes and not self.is_leaf and \
                   not groups.pop('__suffix__'):
                    raise RequestSlash()
                # if we are not in strict slashes mode we have to remove
                # a __suffix__
                elif not self.strict_slashes:
                    del groups['__suffix__']

                result = {}
                # 循环处理URL中的动态参数
                for name, value in groups.items():
                    try:
                        value = self._converters[name].to_python(value)
                    except ValidationError:
                        return
                    result[str(name)] = value
                return result

    def build(self, values):
        """
        Assembles the relative url for that rule and the subdomain.
        If building doesn't work for some reasons `None` is returned.
        """
        tmp = []
        processed = set(self.arguments)
        for is_dynamic, data in self._trace:
            if is_dynamic:
                try:
                    tmp.append(self._converters[data].to_url(values[data]))
                except ValidationError:
                    return
                processed.add(data)
            else:
                tmp.append(data)
        subdomain, url = (u''.join(tmp)).split('|', 1)

        # 拼接 query string
        query_vars = {}
        for key in set(values) - processed:
            query_vars[key] = str(values[key])
        if query_vars:
            url += '?' + url_encode(query_vars, self.map.charset)

        return subdomain, url

    def provides_defaults_for(self, rule):
        """Check if this rule has defaults for a given rule."""
        return not self.build_only and \
            self.endpoint == rule.endpoint and self != rule and \
            self.arguments == rule.arguments

    def suitable_for(self, values, method):
        """Check if the dict of values has enough data for url generation."""
        if self.methods is not None and method not in self.methods:
            return False

        valueset = set(values)

        for key in self.arguments:
            if key not in values:
                return False

        if self.arguments.issubset(valueset):
            return True

        return True

    def match_compare(self, other):
        """Compare this object with another one for matching"""
        if not other.arguments and self.arguments:
            return 1
        elif other.arguments and not self.arguments:
            return -1
        elif self.greediness > other.greediness:
            return -1
        elif self.greediness < other.greediness:
            return 1
        elif len(self.arguments) > len(other.arguments):
            return 1
        elif len(self.arguments) < len(other.arguments):
            return -1
        return 1

    def build_compare(self, other):
        """Compare this object with another one for building."""
        if not other.arguments and self.arguments:
            return -1
        elif other.arguments and not self.arguments:
            return 1
        elif self.greediness > other.greediness:
            return -1
        elif self.greediness < other.greediness:
            return 1
        elif len(self.arguments) > len(other.arguments):
            return -1
        elif len(self.arguments) < len(other.arguments):
            return 1
        return -1

    def __eq__(self, other):
        return self.__class__ is other.__class__ and \
            self._trace == other._trace

    def __ne__(self, other):
        return not self.__eq__(other)

    def __unicode__(self):
        return self.rule

    def __str__(self):
        charset = self.map is not None and self.map.charset or 'utf-8'
        return str(self).encode(charset)

    def __repr__(self):
        if self.map is None:
            return '<%s (unbound)>' % self.__class__.__name__
        charset = self.map is not None and self.map.charset or 'utf-8'
        tmp = []
        for is_dynamic, data in self._trace:
            if is_dynamic:
                tmp.append('<%s>' % data)
            else:
                tmp.append(data)
        return '<%s %r%s -> %s>' % (
            self.__class__.__name__,
            (u''.join(tmp).encode(charset)).lstrip('|'),
            self.methods is not None and ' (%s)' %
            ', '.join(self.methods) or '',
            self.endpoint
        )
