#!/bin/bash

( cd /home/dani/CuandoAbre/ ; pipenv run ~/.local/share/virtualenvs/CuandoAbre-zqUoyEyW/bin/gunicorn -c /home/dani/CuandoAbre/gunicorn-conf.py.txt app:app  & ) &

