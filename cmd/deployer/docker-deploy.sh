#!/bin/bash
sudo docker run --rm -v "${PWD}/cmd/deployer/src:/src" jdtotow/deployer_compiler --noconfirm --hidden-import flask --onefile --name deployer --log-level DEBUG --clean main.py 

