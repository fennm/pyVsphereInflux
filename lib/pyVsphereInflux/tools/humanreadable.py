import re

SYMBOLS = ('B', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')

def human2bytes(s):
    """
    >>> human2bytes('1M')
    1048576
    >>> human2bytes('1G')
    1073741824
    """
    symbols = SYMBOLS
    letter = s[-1:].strip().upper()
    num = s[:-1]
    assert re.match(r'\d+(\.\d+)?', num) is not None and letter in symbols
    num = float(num)
    prefix = {symbols[0]:1}
    for i, s in enumerate(symbols[1:]):
        prefix[s] = 1 << (i+1)*10
    return int(num * prefix[letter])

# vim: et:ai:sw=4:ts=4
