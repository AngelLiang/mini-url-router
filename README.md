# 迷你URL路由

模仿 Werkzeug 中的 routing 路由代码

## 目录结构

- `converters`: 类型转换器
- `exceptions`: 异常类
- `map`: Map类和MapAdapter类
- `rule`: Rule类
- `utils`: 辅助代码

## 测试代码


### 测试 match 功能

```python
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
```


### 测试 build 功能

```python
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
```


### 测试 dispatch 功能

```python

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
```
