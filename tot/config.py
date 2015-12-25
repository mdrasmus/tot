import os
import pwd
from subprocess import call
import sys
import uuid


def get_user():
    """
    Get the current user.
    """
    return pwd.getpwuid(os.getuid()).pw_name


def get_config_dir(user=None):
    """
    Get user config directory.
    """
    user = user or get_user()
    home_dir = os.environ['HOME']
    return os.path.join(home_dir, '.config', 'tot')


def get_passwd_file(user=None):
    config_dir = get_config_dir(user=user)
    return os.path.join(config_dir, 'passwd')


def setup_config(user=None):
    """
    Setup a user's config directory.
    """
    config_dir = get_config_dir(user=user)
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)

    # Setup password.
    passwd_file = get_passwd_file(user=user)

    if not os.path.exists(passwd_file):
        # Create password.
        passwd = str(uuid.uuid4())

        # Save password.
        open(passwd_file, 'w').close()
        os.chmod(passwd_file, 0600)
        with open(passwd_file, 'w') as out:
            out.write(passwd)

    # Setup mount directory.
    mount_dir = get_user_mount_dir(user=user)
    if not os.path.exists(mount_dir):
        if call(['tot-chroot', '--setup']) != 0:
            print >>sys.stderr, (
                "Could not setup user's mount directory: {}.".format(
                mount_dir))


def get_user_passwd(user=None):
    """
    Try to read a user's password. Require's reading permission.
    """
    return open(get_passwd_file(user=user)).read()


def get_run_dir():
    return '/var/run/tot/'


def get_mount_dir():
    return os.path.join(get_run_dir(), 'mnt')


def get_user_mount_dir(user=None):
    user = user or get_user()
    return os.path.join(get_mount_dir(), user)
