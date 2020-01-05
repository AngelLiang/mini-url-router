r""" 测试dispatch

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

>>> def view_func(endpoint, args):
...     print(f'endpoint:{endpoint}\nargs:{args}')
...     return str(endpoint)
...


>>> adapter.dispatch(view_func, '/')
endpoint:index
args:{}
'index'

>>> adapter.dispatch(view_func, '/any/value')
endpoint:any
args:{'name': 'value'}
'any'

>>> adapter.dispatch(view_func, '/missing')
Traceback (most recent call last):
    ...
url_router.exceptions.NotFound
"""


if __name__ == "__main__":
    import doctest
    doctest.testmod()
