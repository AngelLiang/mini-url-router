""" 测试match

>>> from url_router.map import Map
>>> from url_router.rule import Rule
>>> m = Map([
...     Rule('/', endpoint='index'),
...     Rule('/foo', endpoint='foo'),
...     Rule('/bar/', endpoint='bar'),
...     Rule('/any/<name>', endpoint='any'),
...     Rule('/string/<string:name>', endpoint='string'),
...     Rule('/integer/<int:name>', endpoint='integer'),
...     Rule('/float/<float:name>', endpoint='float')
... ])
>>> adapter = m.bind('example.org', '/')


>>> adapter.match('/')
('index', {})
>>> adapter.match('/foo')
('foo', {})
>>> adapter.match('/bar/')
('bar', {})


测试通用传参
>>> adapter.match('/any/data')
('any', {'name': 'data'})
>>> adapter.match('/any/1')
('any', {'name': '1'})
>>> adapter.match('/any/3.14')
('any', {'name': '3.14'})


测试字符串类型
>>> adapter.match('/string/data')
('string', {'name': 'data'})
>>> adapter.match('/string/1')
('string', {'name': '1'})
>>> adapter.match('/string/3.14')
('string', {'name': '3.14'})


测试整型
>>> adapter.match('/integer/1')
('integer', {'name': 1})
>>> adapter.match('/integer/value')
Traceback (most recent call last):
    ...
url_router.exceptions.NotFound
>>> adapter.match('/integer/3.14')
Traceback (most recent call last):
    ...
url_router.exceptions.NotFound


测试浮点
>>> adapter.match('/float/3.14')
('float', {'name': 3.14})
>>> adapter.match('/float/3')
Traceback (most recent call last):
    ...
url_router.exceptions.NotFound
>>> adapter.match('/float/value')
Traceback (most recent call last):
    ...
url_router.exceptions.NotFound


测试没匹配到的URL
>>> adapter.match('/missing')
Traceback (most recent call last):
    ...
url_router.exceptions.NotFound


测试斜杠
>>> adapter.match('/foo/')
Traceback (most recent call last):
    ...
url_router.exceptions.NotFound
>>> adapter.match('/bar')
Traceback (most recent call last):
    ...
url_router.exceptions.RequestRedirect: http://example.org/bar/
"""


if __name__ == "__main__":
    import doctest
    doctest.testmod()
