from urllib.parse import urljoin

from .converters import (
    UnicodeConverter, IntegerConverter, PathConverter, FloatConverter
)
from .exceptions import RequestRedirect, NotFound, BuildError


DEFAULT_CONVERTERS = {
    'default':          UnicodeConverter,
    'string':           UnicodeConverter,
    'path':             PathConverter,
    'int':              IntegerConverter,
    'float':            FloatConverter
}


class Map(object):
    """
    The base class for all the url maps.
    """

    def __init__(self, rules=None, default_subdomain='', charset='utf-8',
                 strict_slashes=True, converters=None):
        """
        `rules`
            sequence of url rules for this map.

        `default_subdomain`
            The default subdomain for rules without a subdomain defined.

        `charset`
            charset of the url. defaults to ``"utf-8"``

        `strict_slashes`
            Take care of trailing slashes.

        `converters`
            A dict of converters that adds additional converters to the
            list of converters. If you redefine one converter this will
            override the original one.
        """
        self._rules = []  # 存储规则
        self._rules_by_endpoint = {}
        self._remap = True  # 修改标志位，True表示需要重新排序

        self.default_subdomain = default_subdomain
        self.charset = charset
        self.strict_slashes = strict_slashes
        self.converters = DEFAULT_CONVERTERS.copy()
        if converters:
            self.converters.update(converters)

        # 把 rules 加入 _rules
        for rulefactory in rules or ():
            self.add(rulefactory)

    def is_endpoint_expecting(self, endpoint, *arguments):
        """
        Iterate over all rules and check if the endpoint expects
        the arguments provided.  This is for example useful if you have
        some URLs that expect a language code and others that do not and
        you want to wrap the builder a bit so that the current language
        code is automatically added if not provided but endpoints expect
        it.


        迭代所有规则，并检查它的 endpoint 是否需要提供参数。
        """
        self.update()
        arguments = set(arguments)
        for rule in self._rules_by_endpoint[endpoint]:
            if arguments.issubset(rule.arguments):
                return True
        return False

    def iter_rules(self, endpoint=None):
        """Iterate over all rules or the rules of an endpoint."""
        if endpoint is not None:
            return iter(self._rules_by_endpoint[endpoint])
        return iter(self._rules)

    def add(self, rulefactory):
        """
        Add a new rule or factory to the map and bind it.  Requires that the
        rule is not bound to another map.


        添加一个新rule或一个map工厂，并绑定它。需要这个rule没有绑定其他map。
        """
        for rule in rulefactory.get_rules(self):
            rule.bind(self)
            self._rules.append(rule)  # 加入 self._rules
            self._rules_by_endpoint.setdefault(rule.endpoint, []).append(rule)
        self._remap = True

    def bind(self, server_name, script_name=None, subdomain=None,
             url_scheme='http', default_method='GET'):
        """
        Return a new map adapter for this request.

        :param server_name: str
        :param script_name: str
        :param subdomain: str
        :param url_scheme: str, defualt is 'http'
        :param default_method: str

        :return: MapAdapter
        """
        if subdomain is None:
            subdomain = self.default_subdomain
        if script_name is None:
            script_name = '/'
        return MapAdapter(self, server_name, script_name, subdomain,
                          url_scheme, default_method)

    def update(self):
        """
        Called before matching and building to keep the compiled rules
        in the correct order after things changed.
        """
        if self._remap:
            # self._rules = sorted(self._rules, key=lambda a,
            #                      b: a.match_compare(b))
            for k, v in self._rules_by_endpoint.items():
                pass
                # self._rules = sorted(self._rules, key=lambda a,
                #                      b: a.build_compare(b))
            self._remap = False


class MapAdapter(object):
    """Map适配器"""

    def __init__(self, map, server_name, script_name, subdomain,
                 url_scheme, default_method):
        self.map = map
        self.server_name = server_name
        if not script_name.endswith('/'):
            script_name += '/'
        self.script_name = script_name
        self.subdomain = subdomain
        self.url_scheme = url_scheme
        self.default_method = default_method

    def dispatch(self, view_func, path_info, method=None):
        """
        :param view_func: callable(endpoint, args)
        :param path_info: str
        :param method: str
        """
        try:
            endpoint, args = self.match(path_info, method)
        except RequestRedirect as e:
            return e
        return view_func(endpoint, args)

    def match(self, path_info, method=None):
        """
        :param path_info: str
        :param method: str
        """
        self.map.update()
        if not isinstance(path_info, str):
            path_info = path_info.decode(self.map.charset, 'ignore')
        path = u'%s|/%s(%s)' % (
            self.subdomain,
            path_info.lstrip('/'),
            (method or self.default_method).upper()
        )

        # 每次 match 都要遍历 map._rules
        for rule in self.map._rules:
            rv = rule.match(path)
            # 返回值没有参数，继续循环
            if rv is None:
                continue
            return rule.endpoint, rv  # 返回 endpoint 和参数
        raise NotFound()  # 抛出 NotFound 异常

    def build(self, endpoint, values=None, method=None, force_external=False):
        """
        :param endpoint: str, 端点
        :param values: dict
        :param method: str
        :param force_external: bool, 是否构建全部URL
        """
        self.map.update()
        method = method or self.default_method
        if values:
            values = dict([(k, v) for k, v in values.items() if v is not None])
        else:
            values = {}

        for rule in self.map._rules_by_endpoint.get(endpoint) or ():
            if rule.suitable_for(values, method):
                rv = rule.build(values)
                if rv is not None:
                    break
        else:
            raise BuildError(endpoint, values)
        subdomain, path = rv
        if not force_external and subdomain == self.subdomain:
            return str(urljoin(self.script_name, path.lstrip('/')))
        # 拼接字符串成URL
        return str('%s://%s%s%s/%s' % (
            self.url_scheme,
            subdomain and subdomain + '.' or '',
            self.server_name,
            self.script_name[:-1],
            path.lstrip('/')
        ))
