#!/bin/sh

FOLDER_NAME=$1

for dir in $FOLDER_NAME/*/
do
    FILES=$dir/*.ttl.gz
    for file in $FILES
    do
	./link.py "$file" 2> "${file/.ttl.gz/.err}"
	#gzip "${file/.ttl/.l.ttl}"
	#gzip "$file"
    done
done


