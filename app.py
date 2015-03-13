#!/usr/bin/env python

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
import json
import redis

# Flask Includes #
from flask import Flask, jsonify

# Local Includes #
from wfu.win import WIN

# The Unofficial WFU WIN API.
app = Flask(__name__)

# Globals to keep track of API state 
authorized = False
win = None

# WIN CONFIG
password = ""
username = "mcgoga12"

# Index landing
@app.route('/', methods=['GET'])
def index():
	""" LOGS INTO THE ACTUAL APP """

	status_dict = {}

	win = WIN(username, password)

	try: 
		win.login()
		status_dict["Authorized"] = True
		authorized = True
	except:
		status_dict["Authorized"] = False

	return jsonify(status_dict)

# Internal directory route
@app.route('/winapi/directory/', methods=['GET'])
def internal_directory():
	""" SEARCHES INTERNAL DIRECTORY """

	win = WIN(username, password) 

	try:
		win.login()
		authorized = True
	except:
		authorized = False

	if not authorized:
		return "Not authorized. You must log make a login request first."

	try:
		student = win.internal_directory(first_name="grant", last_name="mcgovern", association="student", id="1")
	except:
		return "Unable to find user %s %s" % (first_name, last_name)

	return jsonify(results=student)#json.dumps(student, indent=4, separators=(',', ':'))

if __name__ == "__main__":
    app.run(debug=True)