from urllib.parse import quote, quote_plus


def url_encode(obj, charset='utf-8'):
    """Urlencode a dict.

    把字典转换成 URL 字符串

    Usage::

        >>> url_encode({'key1': 'value1', 'key2': 123, 'key3': 3.14})
        'key1=value1&key2=123&key3=3.14'

    :param obj: dict
    :param charset: str
    """
    if obj is None:
        items = []
    elif isinstance(obj, dict):
        items = [(key, [value]) for key, value in obj.items()]
    else:
        items = obj
    tmp = []
    for key, values in items:
        for value in values:
            if value is None:
                continue
            elif isinstance(value, str):
                value = value.encode(charset)
            else:
                value = str(value)
            tmp.append('%s=%s' % (quote(key), quote_plus(value)))
    return '&'.join(tmp)
