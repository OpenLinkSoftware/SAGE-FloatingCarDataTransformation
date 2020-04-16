#!/usr/bin/python

# importing libraries
import sys
import re
import os
import os.path
import geopy.distance
from dateutil.parser import parse
from datetime import timedelta

def p(s):
    return (s[1], s[2])

def dot(a, b):
    return a[0]*b[0] + a[1]*b[1]

def minimum_distance(v, w, point, pp = None):
    p1 = p(point)
    l2 = pow(w[0]-v[0],2)+pow(w[1]-v[1],2)
    if l2 == 0:
        if pp != None:
            pp.append((point[0], v[0], v[1], point[3], point[4], point[5]))
        return geopy.distance.distance(p1, v).m
    t = max(0, min(1, dot((p1[0]-v[0], p1[1]-v[1]), (w[0]-v[0], w[1]-v[1])) / l2))
    projection = (v[0] + t * (w[0] - v[0]), v[1] + t * (w[1] - v[1]))
    if pp != None:
        pp.append((point[0], round(projection[0], 6), round(projection[1], 6), point[3], point[4], point[5]))
    return geopy.distance.distance(p1, projection).m

def min_dist(i, j, pp = None):
    return minimum_distance(segments[j][0], segments[j][1], points[i], pp)

def print_link(i, j, s = 'yes'):
    print i, '\t', j, '\t', s, '\t',
    if s != 'miss':
        print min_dist(i, j)
    else:
        print '-'
    #print p(points[i]), ' - ', segments[j]
    return

def make_a_link(i, j):
    links.append((i, j))
    return

# correct usage
if (len(sys.argv) != 2 or not sys.argv[1].endswith('.ttl.gz')):
    exit('usage: ' + sys.argv[0] + ' ttl.gz_file instread of ' + sys.argv[0] + ' ' + sys.argv[1])

try:
    os.system('gunzip -f ' + sys.argv[1])
    f = open(sys.argv[1][:-3], 'r')
    content = f.read()
    f.close()
except IOError:
    exit('Error while reading ' + sys.argv[1][:-3])


reg_exp = r'<(.*)> :hasTimestamp ([^ ]+) ;\n([ \t]*):lat (\d*(\.\d*)?) ;\n[ \t]*:lon (\d*(\.\d*)?) ;\n[ \t]*:elv (\d*(\.\d*)?) ;\n[ \t]*:hasSpeed ([^ ]+) \.'
pattern = re.compile(reg_exp)
points = []
point = 0
for m in pattern.finditer(content):
    speed_reg_exp = m.group(10) + r' :velocityValue (\d+(\.\d*))'
    m1 = re.search(speed_reg_exp, content[m.end():])
    if m1 == None:
        exit('Error: There is no speed data')
    scale_reg_exp = '<' + m.group(1) + r'> :scale (\d+)'
    m2 = re.search(scale_reg_exp, content[m.end():])
    if m2 == None:
        exit('Error: There is no scale data')
    time, y, x, elv, speed, scale = m.group(2), float(m.group(4)), float(m.group(6)), int(m.group(8)), float(m1.group(1)), int(m2.group(1))
    points.append((time, y, x, elv, speed, scale))
    if m.group(1) != '#point' + str(point):
        exit('Error: Points order')
    point += 1

try:
    f = open(sys.argv[1] + '.gpx.res.gpx', 'r')
    content = f.read()
    f.close()
except IOError:
    exit('Error while reading ' + sys.argv[1] + '.gpx.res.gpx')
reg_exp = r'<trkpt\s+lat="(\d+\.\d*)"\s+lon="(\d+\.\d*)">'
pattern = re.compile(reg_exp)
segments = []
point = 0
for m in pattern.finditer(content):
    if point != 0:
        old_y, old_x = y, x
    y, x = float(m.group(1)), float(m.group(2))
    if point != 0:
        segment = ((old_y, old_x), (y, x))
        segment_distance = geopy.distance.distance((old_y, old_x), (y, x)).m
        if segment_distance > 5000:
            break
        if segment_distance > 0.01:
            segments.append(segment)
    point += 1

#print len(points), len(segments)

links = []
proj = []
min_dist(0, 0, proj)
make_a_link(0, 0)
projections = []
projections.append(proj[0])

i = 1
j = 0
while i < len(points) and j < len(segments):
    dist = min_dist(i, j)
    j1 = j
    while True:
        if j1 >= len(segments):
            break
        #print_link(i, j1, '')
        new_dist = min_dist(i, j1)
        if new_dist > dist:
            break
        dist = new_dist
        j1 += 1

    if dist > 40:
        dist = min_dist(i, j1-1)
        min_j = j1-1
        while True:
            if j1 >= len(segments) or j1 - j > 20:
                break
            #print_link(i, j1, '')
            new_dist = min_dist(i, j1)
            if new_dist < dist:
                dist = new_dist
                min_j = j1
            j1 += 1
        j = min_j
    else:
        j = j1 - 1
    proj = []
    if min_dist(i, j, proj) > 40:
        sys.stderr.write("End at " + str(i * 100 / len(points)) + "% (" + str(i) + "/"+ str(len(points)) + ")\n")
        break
    make_a_link(i, j)
    projections.append(proj[0])
    i += 1
else:
    sys.stderr.write("Success\n")
points = points[:len(projections)]

    
links_tmp = []
counter = 0
while counter < len(links):
    links_tmp.append((links[counter], 'real'))
    counter += 1
    while counter < len(links) and links[counter-1][1] == links[counter][1]:
        links_tmp.append((links[counter], 'rptd'))
        counter += 1
links = links_tmp


links_tmp = []
counter = 0
while True:
    links_tmp.append(links[counter])
    counter += 1
    if counter == len(links):
        break
    for mis in range(links[counter-1][0][1]+1, links[counter][0][1]):
        links_tmp.append(((-1, mis), 'miss'))
links = links_tmp


new_track = []
new_track.append(points[0][1:3] + (points[0][0],) + points[0][3:])
new_track.append(projections[0][1:3])
new_indices = {}
new_indices[0] = 0
for x, f in links:
    i, j = x
    #print_link(i, j, f)
    if i == 0:
        continue
    if f != 'rptd':
        new_track.append(segments[j][0])
    if f != 'miss':
        new_track.append(projections[i][1:3] + (projections[i][0],) + projections[i][3:])
        new_indices[i] = len(new_track) - 1
new_track.append(projections[-1][1:3])
new_track.append(points[-1][1:3] + (points[-1][0],) + points[-1][3:])
new_indices[links[-1][0][0] + 1] = len(new_track) - 1
links.append(((links[-1][0][0] + 1, links[-1][0][1]), 'real'))

gpx_content = '\n'
gpx_content += '<gpx>\n'
gpx_content += '<trk>\n'
gpx_content += '<name>Test</name>\n'
gpx_content += '<trkseg>\n'
for t in new_track:
    gpx_content += '<trkpt lat="' + str(t[0]) + '" lon="' + str(t[1]) + '"></trkpt>\n'
gpx_content += '</trkseg>\n'
gpx_content += '</trk>\n'
gpx_content += '</gpx>\n'


# new gpx file
try:
    new_name = sys.argv[1][:-3].replace('.ttl', '.gpx')
    g = open(new_name, 'w')
    g.write(gpx_content)
    g.close()
except IOError:
    exit('Error while writing to the file ' + new_name)


new_content  = '@base          <http://www.tomtom.com/trace-data/' + os.path.basename(sys.argv[1][:-3]) + '> .\n'
new_content += '@prefix :      <http://www.tomtom.com/ontologies/traces#> .\n'
new_content += '@prefix geo:   <http://www.opengis.net/ont/geosparql#> .\n'
new_content += '@prefix sf:    <http://www.opengis.net/ont/sf#> .\n'
new_content += '@prefix xsd:   <http://www.w3.org/2001/XMLSchema#> .\n'
new_content += '@prefix rdfs:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\n'
new_content += '<#trace> a :Trace .\n'
new_content += '\n'

geom_line_text = ""
for i in range(0, len(new_track)):
    if len(new_track[i]) == 6:
        old_point = (new_track[i][1], new_track[i][0], 'real')
    new_content += '<#trace> :hasPoint <#point' + str(i) + '> .\n'
    if len(new_track[i]) == 6:
        new_content += '<#point' + str(i) + '> :hasTimestamp ' + new_track[i][2] + ' ;\n'
        old_dt = parse(new_track[i][2].replace('^^xsd:dateTime', '')[1:-1])
    else:
        new_point = (new_track[i][1], new_track[i][0])
        if old_point[2] == 'real':
            orig_dist = geopy.distance.distance(new_point, old_point[:-1]).m
            for ii in range(i + 1, len(new_track)):
                orig_dist += geopy.distance.distance((new_track[ii-1][1], new_track[ii-1][0]), (new_track[ii][1], new_track[ii][0])).m
                if len(new_track[ii]) == 6:
                    new_dt = parse(new_track[ii][2].replace('^^xsd:dateTime', '')[1:-1])
                    dur = (new_dt - old_dt).seconds
                    break
        curr_dist = geopy.distance.distance(new_point, old_point[:-1]).m
        if orig_dist != 0:
            old_dt = old_dt + timedelta(seconds = curr_dist / orig_dist * dur)
        old1_dt = old_dt.replace(microsecond = 0)
        old_point = new_point + ('helper',)
        tmstp = old1_dt.strftime('"%Y-%m-%dT%H:%M:%SZ"^^xsd:dateTime')
        new_content += '<#point' + str(i) + '> :hasTimestamp ' + tmstp + ' ;\n'
    new_content += '	:lat ' + str(new_track[i][0]) + ' ;\n'
    new_content += '	:lon ' + str(new_track[i][1]) + ' ;\n'
    if len(new_track[i]) == 6:
        old_elevation  = str(new_track[i][3])
        new_content += '	:elv ' + old_elevation + ' ;\n'
    else:
        new_content += '	:elv ' + old_elevation + ' ;\n'
    new_content += '	:hasSpeed <#speed' + str(i) + '> .\n'
    if len(new_track[i]) == 6:
        old_scale = str(new_track[i][5])
        new_content += '<#point' + str(i) + '> :scale ' + old_scale + ' . \n'
    else:
        new_content += '<#point' + str(i) + '> :scale ' + old_scale + ' . \n'
    new_content += '<#point' + str(i) + '> a geo:Feature . \n'
    new_content += '<#point' + str(i) + '> a :TracePoint . \n'
    new_content += '<#point' + str(i) + '> geo:hasGeometry <#point' + str(i) + '_geom> . \n'
    new_content += '<#point' + str(i) + '_geom> a sf:Point . \n'
    geom_point_text = str(new_track[i][1]) + ' ' + str(new_track[i][0]) + ' ' + old_elevation
    geom_line_text += geom_point_text + ', '
    new_content += '<#point' + str(i) + '_geom> geo:asWKT "POINT Z(' + geom_point_text + ')"^^geo:wktLiteral . \n'
    if len(new_track[i]) == 6:
        old_speed = new_track[i][4]
        new_content += '<#speed' + str(i) + '> :velocityValue ' + ('%.2f' % old_speed) + ' ;\n'
        nth = 0
    else:
        if nth == 0:
            gap = 1
        for np in new_track[i+1:]:
            if len(np) == 6:
                next_speed = np[4]
                break
            if nth == 0:
                gap = gap + 1
        nth = nth + 1
        new_content += '<#speed' + str(i) + '> :velocityValue ' + ('%.2f' % (old_speed + (next_speed - old_speed)*nth/(gap+1))) + ' ;\n'
        #new_content += '<#speed' + str(i) + '> :velocityValue ' + ('%.2f' % old_speed) + ' ;\n'
    new_content += '	:velocityMetric :kilometers_perHour .\n'
    if len(new_track[i]) == 6:
        new_content += '<#point' + str(i) + '> :isHelperPoint "false"^^xsd:boolean. \n'
    else:
        new_content += '<#point' + str(i) + '> :isHelperPoint "true"^^xsd:boolean. \n'

new_content += '<#trace> :numID "' + os.path.basename(sys.argv[1])[:-7] + '"^^xsd:integer .\n'
new_content += '<#trace> :hasStartPoint <#point0> .\n'
new_content += '<#trace> :hasEndPoint <#point' + str(len(new_track)-1) + '> .\n'
new_content += '<#trace> :hasDuration "'+ str((parse(new_track[-1][2].replace('^^xsd:dateTime', '')[1:-1]) - parse(new_track[0][2].replace('^^xsd:dateTime', '')[1:-1])).seconds) + '"^^xsd:integer .\n'
new_content += '<#trace> a geo:Feature .\n'
new_content += '<#trace> geo:hasGeometry <#trace_geom> .\n'
new_content += '<#trace_geom> a sf:LineString .\n'
new_content += '<#trace_geom> geo:asWKT "LINESTRING Z(' + geom_line_text[:-2] + ')"^^geo:wktLiteral .\n'
new_content += '\n'

def seg_to_iri(s):
    return '<segment_' + str(s).replace('(', '').replace(')', '').replace(', ', '_') + '>'

segment_content  = '@base          <http://www.tomtom.com/trace-data/> .\n'
segment_content += '@prefix :      <http://www.tomtom.com/ontologies/traces#> .\n'
segment_content += '@prefix geo:   <http://www.opengis.net/ont/geosparql#> .\n'
segment_content += '@prefix sf:    <http://www.opengis.net/ont/sf#> .\n'
segment_content += '\n'

seg_id = -1
for i in range(0, len(links)):
    z, f = links[i]
    y, x = z
    if seg_id != x:
        seg_iri = seg_to_iri(segments[x])
        seg_iri_geom = seg_iri.replace('>', '_geom>')
        seg_id = x
    if y != -1:# and len(new_track[y]) == 6:
        new_content += '<#point' + str(new_indices[y]) + '> :isLinked ' + seg_iri + ' .\n'
    if i == len(links) - 1 or seg_id != links[i+1][0][1]:
        segment_content += seg_iri + ' a :RoadSegment .\n'
        segment_content += seg_iri + ' geo:hasGeometry ' + seg_iri_geom + ' .\n'
        segment_content += seg_iri_geom + ' a sf:LineString .\n'
        segment_content += seg_iri_geom + ' geo:asWKT "LINESTRING (' + str(segments[x][0][1]) + ' ' + str(segments[x][0][0]) + ', ' + str(segments[x][1][1]) + ' ' + str(segments[x][1][0]) + ')"^^geo:wktLiteral .\n'

    
# new ttl file
try:
    new_name = sys.argv[1][:-3].replace('.ttl', '.l.ttl')
    g = open(new_name, 'w')
    g.write(new_content)
    g.close()
    os.system('gzip -f ' + new_name)
    os.system('gzip -f ' + sys.argv[1][:-3])
except IOError:
    exit('Error while writing to the file ' + new_name)

# segment file
try:
    new_name = sys.argv[1][:-3].replace('.ttl', '.segment.ttl')
    g = open(new_name, 'w')
    g.write(segment_content)
    g.close()
    #os.system('gzip -f ' + new_name)
except IOError:
    exit('Error while writing to the file ' + new_name)

#def mmm(zzz):
#    return new_track[zzz][4]
#
#for x, y in segments_to_points.iteritems():
#    print x, map(mmm, y)

#for x, y in new_indices.iteritems():
#    print x, y
#print len(new_indices)
