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
start_dt = 0
distance = 0

# for all the points in the file
for m in pattern.finditer(content):
    dt = parse(m.group(2).replace('^^xsd:dateTime', '')[1:-1])
    if start_dt != 0:
        x_prev, y_prev = x, y

    y, x = m.group(4), m.group(6)

    if start_dt == 0:
        start_dt = dt
    else:
        distance += geopy.distance.vincenty((y_prev, x_prev), (y, x)).km
    
    new_content += content[end:m.start()]
    new_content += m.group() + '\n'

    point = '<' + m.group(1) + '>'
#    scale = 50 - int(distance)
#    if scale < 0:
#        scale = 0
#    new_content += point + ' :scale ' + str(scale) + ' . '
    new_content += point + ' :mileage ' + str(distance) + ' . '

    end = m.end()
    #print elevation
new_content += content[end:] + '\n'

# new file with elevation
try:
    new_name = sys.argv[1].replace('.ttl', '_g.ttl')
    g = open(new_name, 'w')
    g.write(new_content)
    g.close()
except IOError:
    exit('Error while writing to the file ' + new_name)
