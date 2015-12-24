#!/bin/bash

sudo apt-get update

sudo apt-get install -y python-virtualenv

sudo su <<EOF
grep '^user_allow_other' /etc/fuse.conf > /dev/null || (
    echo 'user_allow_other' >> /etc/fuse.conf
)
EOF
