# urllib3 extension

A wrapper prividing some convenient methods based on [urllib3 2.0](https://urllib3.readthedocs.io/en/latest/index.html). No `certifi chardet idna`.

Features:

* drop-in replacement of PoolManager
* gzip by default
* timeout=3 by default
* pm.get()/postjson()/postform()/head()
* resp.text/cookie; pm.cookie
* auth=(user,passwd)

Install:

```bash
pip install https://github.com/urllib3/urllib3/archive/refs/heads/main.zip  # 2.0 hasn't been released
pip install git+https://github.com/imba-tjd/urllib3-ext
```
