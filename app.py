#!/usr/bin/python3

# Run with:
#  $ FLASK_APP=test.py flask run

import overpy
from flask import Flask, render_template
app = Flask(__name__)

@app.route("/", defaults={'rect': '43.572,7.014,43.578,7.026'})
@app.route("/rect:<rect>")
def hours(rect):
    o = overpy.Overpass()
    q = "node[opening_hours]({});out;".format(rect) # TODO filter rect before injecting
    r = o.query(q)

    results = []    
    for node in r.nodes:
        item = { 'name': node.tags['name'],
                 'url': "https://www.openstreetmap.org/node/{}".format(node.id),
                 'hours': node.tags['opening_hours'].split(';'),
               }
        results.append(item)

    return render_template('tabla.html', nodes=results)