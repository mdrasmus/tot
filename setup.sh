#!/bin/bash

sudo apt-get update
sudo apt-get install -y python-virtualenv sqlite3 libpython-dev

# Install tot.
cd /vagrant/
bash install.sh
