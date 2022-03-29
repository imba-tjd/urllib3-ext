'''Drop-in replacement of PoolManager'''
__all__ = ('PoolManager', 'HTTPResponse', 'request')

import urllib3
from functools import cached_property
import threading
from base64 import b64encode


class PoolManager(urllib3.PoolManager):
    default_headers = {
        'Accept-Encoding': 'gzip',
    }

    def __init__(self, **connection_pool_kw):
        connection_pool_kw.setdefault('timeout', 3)
        connection_pool_kw['headers'] = self.default_headers | connection_pool_kw.get('headers', {})
        super().__init__(**connection_pool_kw)
        self.cookies = connection_pool_kw.get('cookies') or {}

    def get(self, url: str, fields: dict[str, str] = {}, headers: dict[str, str] = {}, **kwargs):
        return self.request('GET', url, fields=fields, headers=headers, **kwargs)

    def postjson(self, url: str, obj: list | dict, headers: dict[str, str] = {}, **kwargs):
        return self.request('POST', url, json=obj, headers=headers, **kwargs)

    def head(self, url: str, fields: dict[str, str] = {}, headers: dict[str, str] = {}, **kwargs):
        return self.request('HEAD', url, fields=fields, headers=headers, redirect=False, **kwargs)

    def postform(self, url: str, form: dict[str, str], headers: dict[str, str] = {}, *, encode_multipart=True, **kwargs):
        return self.request('POST', url, fields=form, headers=headers, encode_multipart=encode_multipart, **kwargs)

    def close(self):
        self.clear()

    def request(self, *args, **kwargs):
        kwargs['headers'] |= (self.headers
                              | {'Cookie': ';'.join((f'{k}={v}' for k, v in self.cookies.items()))}
                              | {'authorization': 'Basic '+b64encode(f'{u}:{p}'.encode('latin-1')).decode() for u, p in kwargs.get('auth', {})}
                              | kwargs.get('headers', {}))
        resp = HTTPResponse._wrap(super().request(*args, **kwargs))
        with threading.Lock():
            self.cookies |= resp.cookies
        return resp


class HTTPResponse(urllib3.HTTPResponse):
    @staticmethod
    def _wrap(baseobj) -> 'HTTPResponse':  # request()返回类型是BaseHTTPResponse抽象类，且没有直接导出，干脆不声明类型
        baseobj.__class__ = HTTPResponse
        return baseobj

    @cached_property
    def cookies(self):
        return {k: v for c in self.headers.getlist('set-cookie') for k, v in c[:c.find(';')].split('=')}

    @property
    def encoding(self):
        if ct := self.headers.get('Content-Type'):
            for item in ct.split(';'):
                if item.lstrip().startswith('charset'):
                    return item.split('=')[1].strip()

    @encoding.setter
    def encoding(self, val):
        self.encoding = val

    @cached_property
    def text(self):
        return self.data.decode(self.encoding or 'u8')

    @cached_property
    def ok(self):
        return self.status >= 400

    def raise_for_status(self):
        if not self.ok:
            raise urllib3.exceptions.HTTPError('%s %s Error for url: %s' % (
                self.status, 'Server' if self.status >= 500 else 'Client', self.url))


_DEFAULT_POOL = PoolManager()


def request(*args, **kwargs):
    return _DEFAULT_POOL.request(*args, **kwargs)
