#!/bin/sh

FOLDER_NAME=$1

for dir in $FOLDER_NAME/*/
do
    ./gpx_p1.sh $dir &
done

wait



