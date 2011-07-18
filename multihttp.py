import concurrent.futures
import urllib2
import memcache

mc = memcache.Client(['127.0.0.1:11211'], debug=0)

CACHE_PREFIX = 'multihttp:url:'
HTTP_TIMEOUT = 60
CACHE_EXPIRE = 60


def cache_key(url):
    return (CACHE_PREFIX + url).encode('ascii')


def sync_url_get(url):
    key = cache_key(url)
    content = mc.get(key)
    if content is None:
        content = urllib2.urlopen(url, timeout=HTTP_TIMEOUT).read()
        mc.set(key, content, CACHE_EXPIRE)
    return content


def request_urls(urls):
    looked_up = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = dict((executor.submit(sync_url_get, url), url) for url in urls)
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                result = future.result(), None
            except Exception, e:
                result = None, e
            looked_up[url] = result
    return looked_up

if __name__ == '__main__':
    urls = ['http://www.foxnews.com/',
            'http://www.cnn.com/',
            'http://europe.wsj.com/',
            'http://www.bbc.co.uk/',
            'http://some-made-up-domain.com/',
            'http://www.google.com/fake']

    d = request_urls(urls)
    for k, v in d.items():
        print k, v()

