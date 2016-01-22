# coding: utf-8
import datetime


def new_list(l=[], element=None):
    nl = [e for e in l]
    nl.append(element)
    return nl

def str_list_strip(l):
    vals = []
    for x in l:
        x = x.strip()
        if x:
            vals.append(x)
    return vals

def str_list_strip_replace(l, replaces=[]):
    l = str_list_strip(l)
    for r in replaces:
        l = [x.replace(r, '') for x in l]
    return l

def add_one_month(t):
    """Return a `datetime.date` or `datetime.datetime` (as given) that is
    one month earlier.

    Note that the resultant day of the month might change if the following
    month has fewer days:

        >>> add_one_month(datetime.date(2010, 1, 31))
        datetime.date(2010, 2, 28)
    """
    one_day = datetime.timedelta(days=1)
    one_month_later = t + one_day
    while one_month_later.month == t.month:  # advance to start of next month
        one_month_later += one_day
    target_month = one_month_later.month
    while one_month_later.day < t.day:  # advance to appropriate day
        one_month_later += one_day
        if one_month_later.month != target_month:  # gone too far
            one_month_later -= one_day
            break
    return one_month_later

def add_months(t, mons, pattern=None):
    for _ in xrange(0, mons):
        t = add_one_month(t)
    if pattern:
        return t.strftime(pattern)
    return t

def subtract_one_month(t):
    """Return a `datetime.date` or `datetime.datetime` (as given) that is
    one month later.

    Note that the resultant day of the month might change if the following
    month has fewer days:

        >>> subtract_one_month(datetime.date(2010, 3, 31))
        datetime.date(2010, 2, 28)
    """
    one_day = datetime.timedelta(days=1)
    one_month_earlier = t - one_day
    while one_month_earlier.month == t.month or one_month_earlier.day > t.day:
        one_month_earlier -= one_day
    return one_month_earlier

def subtract_months(t, mons, pattern=None):
    for _ in xrange(0, mons):
        t = subtract_one_month(t)
    if pattern:
        return t.strftime(pattern)
    return t

