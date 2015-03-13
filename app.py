#!/usr/bin/python

# Name: WIN 
# File: WIN/app.py
#
# Author(s): Grant McGovern & Gaurav Sheni
# Date: Wed 11 March 2015 
#
# URL: www.github.com/g12mcgov/WIN
#
# ~ Description:
#
#  **** THIS IS THE MAIN RESTFUL FLASK SERVER ****
#
# (all requests to valid endpoints are handeled here)
#
#

# Flask Includes #
from flask import Flask

# Local Includes #


# The Unofficial WFU WIN API.
app = Flask(__name__)

# Index landing
@app.route('/')
def index():
    return "Must be logged in."


if __name__ == "__main__":
    app.run(debug=True)