from scrape import host, lookup_article, lookup_collections
from flask import Flask, render_template, jsonify, make_response, request, abort, redirect, url_for
import json

app = Flask(__name__)

@app.route('/')
def index():
    #collections = lookup_collections('top_stories')
    #if len(collections) > 0:
    #    return render_template('index.html', collection=collections[0], story=collections[0]['articles'][0])
    #else:
    #    abort(500)
    return display_collection_html('top_stories')


@app.route('/collection/<id>')
def display_collection_html(id):
    collections = lookup_collections(id)
    if len(collections) > 0:
        return render_template('collection.html', collection=collections[0])
    else:
        abort(404)


@app.route('/article/<path:server_path>')
def display_article_html(server_path):
    path = host + '/' + server_path
    article = lookup_article(path)
    return render_template('article.html', article=article)


@app.route('/api/collection/<id>')
def display_collection_json(id=None):
    collections = lookup_collections(id)
    indent = 5 if request.args.get('format') == 'true' else None
    txt = json.dumps(collections, indent=indent)

    # we want to return a json array as opposed to a dict so we don't use jsonify here
    resp = make_response()
    resp.data = txt
    resp.mimetype = 'application/json'
    return resp


@app.route('/api/article/<path:server_path>')
def display_article_json(server_path):
    path = host + '/' + server_path
    article = lookup_article(path)
    return jsonify(article)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
