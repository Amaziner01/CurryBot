#!/bin/bash

if [ -e env ] 
then
    echo 'Environment Already Exists.'
else
    python3 -m venv env && . ./env/bin/activate && pip3 install -r requirements.txt
fi
