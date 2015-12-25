import os
import pwd
import random


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
        passwd = str(random.randint(0, 1e9))

        # Save password.
        open(passwd_file, 'w').close()
        os.chmod(passwd_file, 0600)
        with open(passwd_file, 'w') as out:
            out.write(passwd)


def get_user_passwd(user=None):
    """
    Try to read a user's password. Require's reading permission.
    """
    return open(get_passwd_file(user=user)).read()
