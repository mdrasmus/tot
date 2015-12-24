#!/bin/bash

sudo apt-get update

sudo apt-get install -y python-virtualenv

sudo su <<EOF
grep '^user_allow_other' /etc/fuse.conf > /dev/null || (
    echo 'user_allow_other' >> /etc/fuse.conf
)
EOF


sudo su -c 'cat > /bin/tot-chroot' <<EOF
#!/usr/bin/env python
import sys
from subprocess import call
print '>>', sys.argv[1:]
sys.exit(call([
    'chroot', '/vagrant/chroot/mnt', '/vagrant/bin/tot', '--chroot'] + sys.argv[1:]))
EOF


sudo su -c 'cat > /etc/sudoers.d/tot' <<EOF
root        ALL=NOPASSWD: /bin/tot-chroot
EOF
