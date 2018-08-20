#!/usr/bin/python3

# Run with:
#  $ FLASK_APP=test.py flask run

import overpy
from flask import Flask
app = Flask(__name__)

@app.route("/", defaults={'rect': '43.572,7.014,43.578,7.026'})
@app.route("/rect:<rect>")
def hours(rect):
    o = overpy.Overpass()
    q = "node[opening_hours]({});out;".format(rect) # TODO filter rect before injecting
    r = o.query(q)
    
    output = ""
    
    output += "<table border='1'>"
    for node in r.nodes:
        output += "<tr>"
        node_url = "https://www.openstreetmap.org/node/{}".format(node.id)
        
        output += "<td><a href='{}'>{}</a></td>".format(node_url, node.tags['name'])
        
        output += "<td>"
        for b in node.tags['opening_hours'].split(';'):
            output += b + "<br />"
        output += "</td>"
        output += "<td>?</td>"
        output += "</tr>"
    output += "</table>"

    return output
