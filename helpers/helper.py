#!/usr/bin/python

# Name: WIN 
# File: WIN/helpers/helper.py
#
# Author(s): Grant McGovern & Gaurav Sheni
# Date: Wed 11 March 2015 
#
# URL: www.github.com/g12mcgov/WIN
#
# ~ Description:
#       - An assortment of methods use in conjunction with the
#         rest of the app.
#
#
#
from itertools import izip

def cache(fn):
    """ Cache function calls to insert into Redis """

    holder = {}

    def wrapped(*args):
        # Key -> Val
        # arg1=1 arg2=2 -> 3
        if args in holder:
            return holder[args]
       
        result = fn(*args)
        holder[args] = result
        
        return result

    return wrapped

def pairwise(iterable):
    "s -> (s0,s1), (s2,s3), (s4, s5), ..."
    a = iter(iterable)
    
    return izip(a, a)