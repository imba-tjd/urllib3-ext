__all__ = ('PoolManager', 'HTTPResponse', 'request')

from functools import cached_property
import threading
from base64 import b64encode
import os

try:
    import urllib3
    if urllib3.__version__[0] != '2':  # type: ignore
        raise ImportError
except ImportError:
    import sys
    if 'urllib3' in sys.modules:
        del sys.modules['urllib3']
    sys.path.insert(0, os.path.dirname(__file__) + '/urllib3_ext_vendor.py')
    import urllib3
    sys.path[:] = sys.path[1:]
    del sys.modules['urllib3']


class PoolManagerExt(urllib3.PoolManager):
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
        kwargs['headers'] = (self.headers
                             | {'Cookie': ';'.join((f'{k}={v}' for k, v in self.cookies.items()))}
                             | {'authorization': 'Basic '+b64encode(f'{u}:{p}'.encode('latin-1')).decode() for u, p in kwargs.get('auth', {})}
                             | kwargs.get('headers', {}))
        resp = HTTPResponse._wrap(super().request(*args, **kwargs))
        with threading.Lock():
            self.cookies |= resp.cookies
        return resp


class ProxyManagerExt(PoolManagerExt, urllib3.ProxyManager):
    pass


def PoolManager(**connection_pool_kw):
    if hp := os.getenv('HTTP_PROXY'):
        connection_pool_kw['proxy_url'] = hp
    if 'proxy_url' in connection_pool_kw:
        return ProxyManagerExt(**connection_pool_kw)
    else:
        return PoolManagerExt(**connection_pool_kw)


class HTTPResponse(urllib3.HTTPResponse):
    @staticmethod
    def _wrap(baseobj) -> 'HTTPResponse':  # request()返回类型是BaseHTTPResponse抽象类，且没有直接导出，干脆不声明类型
        baseobj.__class__ = HTTPResponse
        return baseobj

    @cached_property
    def cookies(self):
        return dict(c[:c.find(';')].split('=') for c in self.headers.getlist('set-cookie'))

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


_DEFAULT_POOL: PoolManagerExt | None = None


def request(*args, **kwargs):
    global _DEFAULT_POOL
    if not _DEFAULT_POOL:
        _DEFAULT_POOL = PoolManager()
    return _DEFAULT_POOL.request(*args, **kwargs)
