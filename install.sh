#!/bin/bash

# Make sure user_allow_other is enabled for fuse.
sudo su <<EOF
grep '^user_allow_other' /etc/fuse.conf > /dev/null || (
    echo 'user_allow_other' >> /etc/fuse.conf
)
EOF


# Allow users to run tot-chroot with sudo.
sudo su -c 'cat > /etc/sudoers.d/tot' <<EOF
root        ALL=NOPASSWD: /usr/sbin/tot-chroot
EOF


# Install tot-chroot
sudo cp bin/tot-chroot /usr/sbin/
sudo chmod 755 /usr/sbin/tot-chroot
