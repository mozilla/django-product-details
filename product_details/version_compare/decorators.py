import functools

from django.utils.six.moves import cPickle


def memoize(fctn):
    """
    Memoizing decorator, courtesy of:
    http://pko.ch/2008/08/22/memoization-in-python-easier-than-what-it-should-be/
    """
    memory = {}

    @functools.wraps(fctn)
    def memo(*args, **kwargs):
        haxh = cPickle.dumps((args, sorted(kwargs.items())))
        if haxh not in memory:
            memory[haxh] = fctn(*args, **kwargs)
        return memory[haxh]

    if memo.__doc__:
        memo.__doc__ = "\n".join([memo.__doc__, "This function is memoized."])
    return memo
