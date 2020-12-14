#!/bin/bash
sudo docker run --rm -v "${PWD}/cmd/deployer/src:/src" six8/pyinstaller-alpine-linux-amd64:alpine-3.7-pyinstaller-v3.6 --noconfirm --hidden-import flask --onefile --log-level DEBUG --clean main.py 
sudo mv cmd/deployer/src/dist/main cmd/deployer/deployer 
sudo chmod +x cmd/deployer/deployer
