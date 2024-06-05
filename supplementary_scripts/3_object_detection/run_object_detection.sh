#!/bin/bash

source ~/python/venv/bin/activate

mkdir -p $2
mkdir -p $3

touch $3/log.txt
touch $3/results.tsv

echo -n "" > $3/results.tsv
echo -n "" > $3/log.txt

for FILE in $(ls $1/DSC*);
do
	FILE=$(basename $FILE)
	echo $FILE
	python3 object_detection.py $1/$FILE $2/$FILE >> $3/results.tsv 2>> $3/log.txt 
done
