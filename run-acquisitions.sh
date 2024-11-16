#! /bin/bash

python3 main.py 170 -p /dev/ttyUSB1 -s 400 \
    && echo "\nAcquisizione finita, andate in pace"
