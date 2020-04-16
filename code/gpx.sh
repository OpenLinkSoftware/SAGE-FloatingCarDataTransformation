#!/bin/bash

FILE_NAME=$1

(echo '<gpx><trk><name>Test</name><trkseg>' ; zcat $1 | egrep -o 'POINT[^)]+\)' | sed 's/POINT Z(//g' | sed -E 's/[0-9]+[)]//' | sed 's/ /" lat="/' | sed -E 's/^/<trkpt lon="/' | sed -E 's/ $/"><\/trkpt>/'; echo '</trkseg></trk></gpx>') > $1.gpx

java -jar graphhopper-map-matching-web-1.0-SNAPSHOT.jar match --gps_accuracy 20 $1.gpx > $1.out 2> $1.err

[ -s $1.err ] || rm $1.err

