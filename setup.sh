#!/bin/bash

sudo apt-get update
sudo apt-get install -y python-virtualenv sqlite3

# Install tot.
cd /vagrant/
bash install.sh
