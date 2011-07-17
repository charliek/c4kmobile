import concurrent.futures
import urllib2
import memcache

mc = memcache.Client(['127.0.0.1:11211'], debug=0)

CACHE_PREFIX = 'multihttp:url:'

def cache_key(url):
    return (CACHE_PREFIX+url).encode('ascii')

def sync_url_get(url, http_timeout=60, cache_expire=300):
    key = cache_key(url)
    content = mc.get(key)
    if content is None:
        content = urllib2.urlopen(url, timeout=http_timeout).read()
        mc.set(key, content, cache_expire)
    return content

def request_urls(urls, http_timeout=60, cache_expire=300):
    looked_up = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = dict((executor.submit(sync_url_get, url, http_timeout, cache_expire), url) for url in urls)
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            def run():
                if future.exception() is not None:
                    raise future.exception()
                else:
                    return future.result()
            looked_up[url] = run
    return looked_up

if __name__ == '__main__':
    urls = ['http://www.foxnews.com/',
            'http://www.cnn.com/',
            'http://europe.wsj.com/',
            'http://www.bbc.co.uk/',
            'http://some-made-up-domain.com/',
            'http://www.google.com/fake']

    d = request_urls(urls, http_timeout=60, cache_expire=0)
    for k, v in d.items():
        print k, v()

