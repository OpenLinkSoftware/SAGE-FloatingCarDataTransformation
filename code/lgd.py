#!/usr/bin/python2.7

import sys
import re
import os
import requests
import codecs
import os.path

if len(sys.argv) < 2:
    exit('usage: ' + sys.argv[0] + ' file_with_segments [--skip number]')

if len(sys.argv) == 4 and sys.argv[2] == '--skip':
    skip = int(sys.argv[3])
else:
    skip = 0

try:
    f = open(sys.argv[1], 'r')
    content = f.read()
    f.close()
except IOError:
    exit('Error while reading')
    
reg_exp =  r'(<[^>]+>)\s+a\s+:RoadSegment.*\n'
reg_exp += r'\1\s+geo:hasGeometry\s+(<[^>]+>).*\n'
reg_exp += r'\2\s+a\s+sf:LineString.*\n'
reg_exp += r'\2\s+geo:asWKT\s+("[^"]+")\^\^geo:wktLiteral.*\n'

pattern = re.compile(reg_exp)

query = '  \
PREFIX geof: <http://www.opengis.net/def/function/geosparql/>  \
CONSTRUCT {  \
  ?segment a <http://linkedgeodata.org/ontology/HighwayThing> .  \
  ?segment a ?type .  \
  ?segment <http://www.w3.org/2000/01/rdf-schema#label> ?label .  \
  ?segment <http://linkedgeodata.org/ontology/localName> ?localName .  \
  ?segment <http://linkedgeodata.org/ontology/internationalName> ?interName .  \
  ?segment <http://linkedgeodata.org/ontology/nationalName> ?nationName .  \
  ?segment <http://linkedgeodata.org/ontology/short_name> ?shortName .  \
  ?segment <http://geovocab.org/geometry#geometry> ?geom .  \
  ?geom <http://www.opengis.net/ont/geosparql#asWKT> ?wkt .  \
  %%%%% <http://www.tomtom.com/ontologies/traces#connected> ?segment .  \
}  \
WHERE {  \
  ?segment a ?type .  \
  ?type rdfs:subClassOf* <http://linkedgeodata.org/ontology/HighwayThing> .  \
  ?segment <http://geovocab.org/geometry#geometry> ?geom .  \
  ?geom <http://www.opengis.net/ont/geosparql#asWKT> ?wkt .  \
  FILTER (bif:GeometryType(?wkt) = "LINESTRING") .  \
  FILTER (bif:st_may_intersect (?wkt, bif:st_geomfromtext(#####))) .  \
  FILTER (geof:ehContains (geof:buffer(?wkt, $$$$$), bif:st_geomfromtext(@@@@@))) .  \
  OPTIONAL { ?segment <http://www.w3.org/2000/01/rdf-schema#label> ?label }  \
  OPTIONAL { ?segment <http://linkedgeodata.org/ontology/localName> ?localName }  \
  OPTIONAL { ?segment <http://linkedgeodata.org/ontology/internationalName> ?interName }  \
  OPTIONAL { ?segment <http://linkedgeodata.org/ontology/nationalName> ?nationName }  \
  OPTIONAL { ?segment <http://linkedgeodata.org/ontology/short_name> ?shortName }  \
}'

ls_regex = r'LINESTRING\s*\(\s*(\d+(\.\d*)?)\s+(\d+(\.\d*)?)\s*,\s*(\d+(\.\d*)?)\s+(\d+(\.\d*)?)\)'
ls_patt = re.compile(ls_regex)

def box(s):
    m1 = ls_patt.search(s)
    x1, y1, x2, y2 = float(m1.group(1)), float(m1.group(3)), float(m1.group(5)), float(m1.group(7))
    x_min, x_max = min(x1, x2), max(x1, x2)
    y_min, y_max = min(y1, y2), max(y1, y2)
    return '"BOX (' + str(x_min-0.000005) + ' ' + str(y_min-0.000005) + ', '  + str(x_max+0.000005) + ' ' + str(y_max+0.000005) + ')"'

url = 'http://sparql.cs.upb.de:8890/sparql/?'
counter = 0

def search(start, end):
    print str(counter).ljust(6), '-', '(',
    filename = './segment' + str(counter).rjust(6, '0') + '.ttl'
    if os.path.exists(filename + '.gz'):
        print 'OK )'
        return True
    while True:
        tolerance = (start + end) / 2;
        myobj = {'query': query.replace('@@@@@', m.group(3)).replace('#####', box(m.group(3))).replace('$$$$$', str(tolerance)).replace('%%%%%', m.group(1))}
        x = requests.post(url, data = myobj)

        #os.system("curl --request POST 'http://sparql.cs.upb.de:8890/sparql/?' --header 'Accept-Encoding: gzip' --data 'format=ntriple' --data-urlencode 'query=" + query.replace('@@@@@', m.group(3)) + "' --output 'segment" + str(counter) + ".gz'")
    
        if x.ok == False:
            print str(counter).ljust(6), '-', 'Problem:' + m.group(1) + '( query )'
            return False
    
        number_of_responeses = x.text.count('asWKT')
        if number_of_responeses == 1:
            try:
                f = codecs.open(filename, 'w', encoding='utf8')
                f.write(x.text)
                f.close()
                os.system('gzip -f ' + filename)
            except IOError:
                exit('Error while write ' + filename + ' ' + m.group(1))

    
        print number_of_responeses,
        if number_of_responeses == 1:
            break
        if tolerance-start < 0.00000001 or end-tolerance < 0.00000001:
            print 'Problem:' + m.group(1),
            break
        if number_of_responeses > 1:
            end = tolerance
        else:
            start = tolerance
            
    print ')', tolerance
    if number_of_responeses == 1:
        return True
    else:
        return False

for m in pattern.finditer(content):
    if m.group(1) != m.group(2).replace('_geom', ''):
        exit("Error in " + m.group(1))
    counter += 1

    if skip >= counter:
        continue

    search(0.0000001, 0.0005)
    #search(0.0005, 0.01)
    
    #if counter > 10:
    #    break
 

    

