import hashlib


def unique(items, key=lambda x: x):
    """
    Iterate through unique items in an iterable.

    Order is preserved.
    """
    seen = set()
    for item in items:
        if item not in seen:
            yield item
            seen.add(item)


def hash_file(path):
    """
    Return the sha1 hash of a file.
    """
    blocklen = 1024 * 4

    with open(path) as infile:
        m = hashlib.sha1()
        while True:
            block = infile.read(blocklen)
            if len(block) == 0:
                break
            m.update(block)
    file_hash = m.digest().encode("hex")
    return file_hash


def format_timestamp(timestamp):
    """
    Format a timestamp to a string.
    """
    return timestamp.strftime('%Y-%M-%d %H:%M:%S')
