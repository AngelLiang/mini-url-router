""" 测试build

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


>>> adapter.build('index')
'/'
>>> adapter.build('foo')
'/foo'
>>> adapter.build('bar')
'/bar/'

>>> adapter.build('any', {'name': 'value'})
'/any/value'


>>> adapter.build('string', {'name': 'data'})
'/string/data'


>>> adapter.build('integer', {'name': 1})
'/integer/1'


>>> adapter.build('float', {'name': 3.14})
'/float/3.14'

>>> adapter.build('index', force_external=True)
'http://example.org/'
>>> adapter.build('foo', force_external=True)
'http://example.org/foo'
"""


if __name__ == "__main__":
    import doctest
    doctest.testmod()
