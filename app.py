#!/usr/bin/python3

import overpy
from osm_time.opening_hours import OpeningHours, ParseException
from flask import Flask, render_template, request, redirect, url_for, make_response
import datetime
app = Flask(__name__)

DAYS = ['mo', 'tu', 'we', 'th', 'fr', 'sa', 'su'] # OSM opening_hours format

def getPinned():
    current = request.cookies.get('nodeIds')
    
    if current:
        return set(map(string_as_int_or_zero, current.split(",") ) )
    else:
        return set()

@app.route("/recordar", methods=['POST']) # TODO POST with a URL param?
def remember():
    current = getPinned()
    print(f"Current: {current}")
    new = string_as_int_or_zero(request.args.get('nodeId'))
    current.add(new)
    
    resp = make_response("ok")
    
    resp.set_cookie('nodeIds', ",".join( (str(nodeId) for nodeId in current) ) )
    
    return resp

def string_as_int_or_zero(s):
    try:
        return int(s)
    except ValueError as e:
        return 0

def makeRect(center, radius):
    """
       center is a latitude, longitude string in the format "<float>,<float>"
       radius is a float
       
       returns a string containing "lat-radius, lon-radius, lat+radius, lon+radius"
    """
    lat,lon = center.split(",")
    lat,lon = float(lat),float(lon)
    
    return f"{lat-radius},{lon-radius},{lat+radius},{lon+radius}"

def getTypeFromTags(tags):
    """
    Guesses a meaningful type of OSM node/way based on the tags
    by picking one from amenity, shop, ...
    """
    keys = tags.keys()
    if   "amenity" in keys:
        return tags["amenity"]
    elif "shop" in keys:
        return tags["shop"]
        
    return "unknown"

@app.route("/")
def hours():
    center = request.args.get('center', '43.5744,7.0192').replace("%2C", ",")
    radius = 0.01
    rect = makeRect(center, radius)
    when = request.args.get('when', 'now')
    pinned = getPinned()
    
    o = overpy.Overpass()
    q = f"node[opening_hours]({rect});out;"   # TODO retrieve also ways (eg. a whole building is a shop)
    r = o.query(q)

    if when == "now":
        now = datetime.datetime.today() # TODO tz awareness
        day, hour = DAYS[now.weekday()], now.strftime("%H:%M")
    else:
        day, hour = when.split(" ")

    results = []
    
    for node in r.nodes:
        try: 
            if OpeningHours(node.tags['opening_hours']).is_open(day, hour):
                open = 'open'
            else:
                open = 'closed'
        except ParseException as e:
            open = 'unknown'

        item = { 'name': node.tags.get('name'),
                 'url':  f'https://www.openstreetmap.org/?mlat={node.lat}&mlon={node.lon}#map=19/{node.lat}/{node.lon}',
                 'hours': node.tags['opening_hours'].split(';'),
                 'open': open,
                 'type': getTypeFromTags(node.tags),
                 'id': node.id,
               }
        results.append(item)

    return render_template('tabla.html', nodes=results)
    
if __name__ == "__main__":
    app.run(host='0.0.0.0')
    