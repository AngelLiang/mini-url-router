import time
import timeit
from url_router.map import Map
from url_router.rule import Rule

m = Map([
    Rule('/', endpoint='index'),
    Rule('/foo', endpoint='foo'),
    Rule('/bar/', endpoint='bar'),
    Rule('/any/<name>', endpoint='any'),
    Rule('/string/<string:name>', endpoint='string'),
    Rule('/integer/<int:name>', endpoint='integer'),
    Rule('/float/<float:name>', endpoint='float'),
])

adapter = m.bind('example.org', '/')


if __name__ == "__main__":
    # start = time.time()
    # adapter.match('/')
    # used = time.time() - start
    # print(used)

    # start = time.time()
    # adapter.match('/float/3.14')
    # used = time.time() - start
    # print(used)

    print(timeit.timeit("adapter.match('/')", 'from __main__ import adapter'))
    print(timeit.timeit("adapter.match('/float/3.14')",
                        'from __main__ import adapter'))
