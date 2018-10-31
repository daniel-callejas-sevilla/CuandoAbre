#!/usr/bin/python3

import overpy
import osmapi
from osm_time.opening_hours import OpeningHours, ParseException
from flask import Flask, render_template, request, redirect, url_for, make_response
import datetime
from geopy.distance import VincentyDistance
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

@app.route("/olvidar", methods=['POST']) # TODO same remark as remember()
def olvidar():
    current = getPinned()
    forget = string_as_int_or_zero(request.args.get('nodeId'))
    try:
        current.remove(forget)
    except KeyError:
        pass
    
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
    elif "healthcare" in keys:
        return tags["healthcare"]
        
    return "unknown"

def makeNode(name, lat, lon, id, type, hours, day, hour, center):
    try: 
        if OpeningHours(hours).is_open(day, hour):
            open = 'open'
        else:
            open = 'closed'
    except ParseException as e:
        open = 'unknown'

    return { 
        'name': name,
        'url': f'https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=19/{lat}/{lon}',
        'hours': hours.split(';'),
        'open': open,
        'id': id,
        'type': type,
        'distance': VincentyDistance( (lat, lon), map(float, center.split(",")) ).m
    }


@app.route("/")
def hours():
    center = request.args.get('center', '43.5744,7.0192').replace("%2C", ",")
    radius = 0.01
    rect = makeRect(center, radius)
    when = request.args.get('when', 'now')
    pinned = getPinned()
    
    if when == "now":
        now = datetime.datetime.today() # TODO tz awareness
        day, hour = DAYS[now.weekday()], now.strftime("%H:%M")
    else:
        day, hour = when.split(" ")

    osm = osmapi.OsmApi()    
    pinnedResults = []
    for p in pinned:
        node = osm.NodeGet(p)
        pinnedResults.append( makeNode(node['tag']['name'],
                                       node['lat'], node['lon'],
                                       node['id'],
                                       getTypeFromTags(node['tag']),
                                       node['tag']['opening_hours'],
                                       day, hour,
                                       center )
                            )
                                       
    o = overpy.Overpass()
    q = f"node[opening_hours]({rect});out;"   # TODO retrieve also ways (eg. a whole building is a shop)
    r = o.query(q)
    results = []
    for node in r.nodes:
        results.append( makeNode(node.tags.get('name'), 
                                 node.lat, node.lon, 
                                 node.id, 
                                 getTypeFromTags(node.tags), 
                                 node.tags['opening_hours'],
                                 day, hour,
                                 center )
                      )

    return render_template('tabla.html', nodes=results, pinned=pinnedResults)
    
if __name__ == "__main__":
    app.run(host='0.0.0.0')
    