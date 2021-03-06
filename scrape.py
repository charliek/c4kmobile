from lxml.html import fromstring, tostring
import multihttp
from lxml import etree
import json

host = 'http://channel4000.preview.ib-prod.com'
home_url = host + '/ibsys/servlet/page/view/ibsys-c4k/-/131288/-/l3qd6c/-/example.html'
entertainment_url = host + '/ibsys/servlet/page/view/ibsys-c4k/entertainment'

def _flatten(el):
    """Pass in an xml element and this will return all of the text between the nodes, minus the nodes"""
    result = [(el.text or "")]
    for sel in el:
        result.append(_flatten(sel))
        result.append(sel.tail or "")
    return "".join(result)


def _load_all_urls(collections):
    """Pass in a list of Fetcher objects and this will load all the urls needed and populate the objects."""
    needed = []
    for c in collections:
        needed.append(c.url)
    to_load = set(needed)
    url_content = multihttp.request_urls(to_load)
    for c in collections:
        c.content, ex = url_content[c.url]


class Fetcher(object):
    """The base object for objects fetching collection data."""

    def __init__(self):
        self.content = None
        self.url = None
        self.title = None

    @property
    def id(self):
        return self.title.strip().lower().replace(' ', '_')

    def get_doc(self):
        if self.content is None:
            self.content = multihttp.sync_url_get(self.url)
        return fromstring(self.content)

    def extract_link(self, a_elem, items):
        try:
            link = {
                'path': a_elem.get('href'),
                'teaser': a_elem.text
            }
            items.append(link)
        except Exception, e:
            print e
            pass

    def populate_articles(self, items):
        to_fetch = [host + x['path'] for x in items]
        fetched = multihttp.request_urls(to_fetch)
        articles = []
        for item in items:
            try:
                content, ex = fetched[host + item['path']]
                if ex is not None:
                    raise ex
                a = parse_article(content)
                if a is not None:
                    a['url'] = host + item['path']
                    a['teaser'] = item['teaser']
                    a['path'] = item['path']
                    articles.append(a)
            except Exception, e:
                print e
        return articles


class TopStoryFetcher(Fetcher):
    """This fetches the top stories by parsing the main page"""

    def __init__(self):
        Fetcher.__init__(self)
        self.url = home_url
        self.title = 'Top Stories'

    def get_items(self):
        doc = Fetcher.get_doc(self)
        links = []
        for elem in doc.cssselect("div#rotating131280navi li a"):
            self.extract_link(elem, links)
        return self.populate_articles(links)


class ClassBasedFetcher(Fetcher):
    """This fetches an index off the entertainment page based on the title"""

    def __init__(self, site_title):
        Fetcher.__init__(self)
        self.url = entertainment_url
        self.title = site_title

    def get_items(self):
        doc = Fetcher.get_doc(self)
        links = []
        for elem in doc.cssselect("div.dividedContainer div.containerDivision"):
            if elem.cssselect('h1')[0].text.strip() == self.title:
                for s in elem.cssselect('h3.teaserTitle a'):
                    self.extract_link(s, links)
                for s in elem.cssselect('li a.teasableLink'):
                    self.extract_link(s, links)
        return self.populate_articles(links)

COLLECTIONS = [
    TopStoryFetcher(),
    ClassBasedFetcher('Travel'),
    ClassBasedFetcher('Headlines'),
    ClassBasedFetcher('Movie Reviews'),
    ClassBasedFetcher('Celebrities'),
    ClassBasedFetcher('Interviews'),
    ]

def lookup_collections(id=None):
    if id is None:
        to_load = COLLECTIONS
    else:
        to_load = [c for c in COLLECTIONS if c.id == id]
    _load_all_urls(to_load)
    collections = []
    for c in to_load:
        col = {
            'id': c.id,
            'title': c.title,
            'articles': c.get_items()
        }
        collections.append(col)
    return collections


def parse_article(content):
    article = {}
    doc = fromstring(content)
    elems = doc.cssselect('body.content-article div.article')
    if len(elems) is 0:
        raise Exception("The url passed in does not appear to be an article")
    art_elem = elems[0]
    article['headline'] = _flatten(art_elem.cssselect('div.header h1')[0]).strip()
    try:
        article['subheadline'] = _flatten(art_elem.cssselect('div.header h2.subHeadline')[0]).strip()
    except Exception, e:
        article['subheadline'] = None

    try:
        article['author'] = _flatten(art_elem.cssselect('div.header div.author')[0]).strip()[7:].strip()
    except Exception, e:
        article['author'] = None

    article['posted_dt'] = art_elem.cssselect('div.header span.posted_at')[0].text.strip()[10:]

    try:
        article['img'] = host + art_elem.cssselect('figure img')[0].get('src')
    except Exception, e:
        article['img'] = None

    try:
        article['copyright'] = _flatten(art_elem.cssselect('div.copyright')[0])
    except Exception, e:
        article['copyright'] = None

    rt = etree.Element('div')
    for e in art_elem.xpath('span/*'):
        if e.tag != 'aside':
            rt.append(e)
    article['body'] = tostring(rt)
    return article


def lookup_article(url):
    content = multihttp.sync_url_get(url)
    article = parse_article(content)
    article['url'] = url
    return article

if __name__ == '__main__':
    #pass
    #article = lookup_article(
    #    'http://channel4000.preview.ib-prod.com/ibsys/servlet/page/view/ibsys-c4k/At-The-Movies/Felton-misses-Draco-s-magic-as-Potter-ends/-/135772/166028/-/1l4wfp/-/example.html')
    #print json.dumps(article)
    #print json.dumps(lookup_collections('top_stories'))
    print json.dumps(lookup_collections('travel'))



