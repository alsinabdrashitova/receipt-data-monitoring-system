#!/bin/bash

python3 project/data_preprocessing/dataprocessor.py
python3 project/clustering_clope/main.py --noiseLimit=0 --seed=41 --r=1.5
python3 project/clustering_dbscan/main.py --eps=2 --min_samples=10

while :; do sleep 2073600; done
