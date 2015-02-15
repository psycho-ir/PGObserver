__author__ = 'soroosh'


def makeTimeIntervalReadable(micro):
    s = int(micro / 1000)
    micro %= 1000
    m = int(s / 60)
    s %= 60
    h = int(m / 60)
    m %= 60

    if h > 0:
        return str(h) + "h " + str(m) + "m " + str(s) + "s"

    if m > 0:
        return str(m) + "m " + str(s) + "." + '{0:03}'.format(micro) + "s"

    return str(s) + "." + '{0:03}'.format(micro) + "s"
