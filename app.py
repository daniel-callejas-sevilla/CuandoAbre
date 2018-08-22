#!/usr/bin/python3

# Run with:
#  $ FLASK_APP=test.py flask run

import overpy
from osm_time.opening_hours import OpeningHours
from flask import Flask, render_template, request
import datetime
app = Flask(__name__)

DAYS = ['mo', 'tu', 'we', 'th', 'fr', 'sa', 'su'] # OSM opening_hours format

@app.route("/")
def hours():
    rect = request.args.get('rect', '43.572,7.014,43.578,7.026')
    when = request.args.get('when', 'now')

    o = overpy.Overpass()
    q = "node[opening_hours]({});out;".format(rect) # TODO filter rect before injecting
    r = o.query(q)

    results = []
    
    if when == "now":
        now = datetime.datetime.today() # TODO tz awareness
        day, hour = DAYS[now.weekday()], now.strftime("%H:%M")
    else:
        day, hour = when.split(" ")

    for node in r.nodes:
        item = { 'name': node.tags['name'],
                 'url': "https://www.openstreetmap.org/node/{}".format(node.id),
                 'hours': node.tags['opening_hours'].split(';'),
                 'open': OpeningHours(node.tags['opening_hours']).is_open(day, hour),
               }
        results.append(item)

    return render_template('tabla.html', nodes=results)