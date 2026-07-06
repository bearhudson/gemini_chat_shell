#!/usr/bin/env bash

python3 -m venv venv
source venv/bin/activate
pip install requests dotenv rich

echo -ne "Setup Complet!\n"
