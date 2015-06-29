import re

def convert_to_alnum(s, replace="_"):
    """Return s filtered to replace all non alphanumeric, hyphen, or underscore
       with the character given by replace
    """
    return re.sub(r'[^a-zA-Z0-9_-]', replace, s)

# vim: et:ai:sw=4:ts=4

