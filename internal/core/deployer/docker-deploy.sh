#!/bin/bash
sudo docker run --rm -v "${PWD}/src:/src" six8/pyinstaller-alpine-linux-amd64:alpine-3.7-pyinstaller-v3.6 --noconfirm --hidden-import flask --onefile --log-level DEBUG --clean main.py 
sudo docker build -t jdtotow/deployer -f .
sudo docker push jdtotow/deployer