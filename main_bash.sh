#!/bin/sh


counter=1
while [ $counter -le 1 ]
do
    python digitizer.py
    ((counter++))
done
