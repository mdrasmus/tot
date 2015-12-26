#!/bin/bash

sudo apt-get update
sudo apt-get install -y python-virtualenv

# Install tot.
cd /vagrant/
bash install.sh
