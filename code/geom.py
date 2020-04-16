#!/usr/bin/python

# importing libraries
import requests 
import sys
import re
import os
from dateutil.parser import parse
import geopy.distance

def name2num(s):
    return re.match(r'\d+', os.path.basename(s)).group()

# correct usage
if (len(sys.argv) != 2 or not sys.argv[1].endswith('.ttl')):
    exit('usage: ' + sys.argv[0] + ' ttl_file instread of ' + sys.argv[0] + ' ' + sys.argv[1])

# file with traces
try:
    f = open(sys.argv[1], 'r')
    content = f.read()
    f.close()
except IOError:
    exit('Error while reading ' + sys.argv[1])

# regular expression pattern
reg_exp = r'<(.*)> :hasTimestamp ([^ ]+) ;\n([ \t]*):lat (\d*(\.\d*)?) ;\n[ \t]*:lon (\d*(\.\d*)?) ;\n[ \t]*:elv (\d*(\.\d*)?) ;[^.]*\.'
pattern = re.compile(reg_exp)

end = 0
new_content = ''
line_wkt = '"LINESTRING ZM('
start_dt = 0
distance = 0

# for all the points in the file
for m in pattern.finditer(content):
    dt = parse(m.group(2).replace('^^xsd:dateTime', '')[1:-1])
    if start_dt != 0:
        x_prev, y_prev = x, y

    y, x, z = m.group(4), m.group(6), m.group(8)

    if start_dt == 0:
        start_dt = dt
    else:
        distance += geopy.distance.vincenty((y_prev, x_prev), (y, x)).km
    
    new_content += content[end:m.start()]
    new_content += m.group() + '\n'

    point = '<' + m.group(1) + '>'
    pointGeomID = '<' + m.group(1) + '_geom>' 
    wkt = '"POINT ZM(' + x + ' ' + y + ' ' + z + ' ' + str(distance) + ')"^^geo:wktLiteral'
    new_content += point + ' :mileage ' + str(distance) + ' . \n'
    new_content += point + ' a geo:Feature . \n'
    new_content += point + ' a :TracePoint . \n'
    new_content += point + ' geo:hasGeometry ' + pointGeomID + ' . \n'
    new_content += pointGeomID + ' a sf:Point . \n'
    new_content += pointGeomID + ' geo:asWKT ' + wkt + ' . '

    line_wkt += x + ' ' + y + ' ' + z + ' ' + str(distance) + ', '
    
    end = m.end()
    #print elevation
new_content += content[end:] + '\n'
line_wkt = line_wkt[:-2] + ')"'

new_prefixes = ''
new_prefixes += '@prefix :      <http://www.tomtom.com/ontologies/traces#> .\n'
new_prefixes += '@prefix geo:   <http://www.opengis.net/ont/geosparql#> .\n'
new_prefixes += '@prefix sf:    <http://www.opengis.net/ont/sf#> .\n'

new_content = new_content.replace('@prefix :      <http://www.tomtom.com/ontologies/traces#> .\n', new_prefixes, 1)

# addtional enhancements
duration =  dt - start_dt
new_content += '<#trace> :numID "' + name2num(sys.argv[1]) + '"^^xsd:integer .\n'
new_content += '<#trace> :hasStartPoint <#point0> .\n'
new_content += '<#trace> :hasEndPoint ' + point + ' .\n'
new_content += '<#trace> :hasDuration "' + str(duration.days * 24 * 60 * 60 + duration.seconds) + '"^^xsd:integer .\n'


# trace enhancements
new_content += '<#trace> a geo:Feature .\n'
new_content += '<#trace> geo:hasGeometry <#trace_geom> .\n'
new_content += '<#trace_geom> a sf:LineString .\n'
new_content += '<#trace_geom> geo:asWKT ' + line_wkt + ' .\n'

# new file with elevation
try:
    new_name = sys.argv[1].replace('.ttl', '_g.ttl')
    g = open(new_name, 'w')
    g.write(new_content)
    g.close()
except IOError:
    exit('Error while writing to the file ' + new_name)
