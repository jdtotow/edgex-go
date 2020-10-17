#!/bin/bash
FOLDER = $PWD
cd ./monitoring/prometheus/node-exporter
./install.sh
cd $FOLDER 
sudo docker-compose up -d 