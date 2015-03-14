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
from flask import Flask, jsonify, abort

# Local Includes #
from wfu.win import WIN

# The Unofficial WFU WIN API.
app = Flask(__name__)


# Index landing
@app.route('/', methods=['GET'])
@app.route('/win', methods=['GET'])
def index():
	""" LOGS INTO THE ACTUAL APP """

	status_dict = {}

	if authorized:
		status_dict["Authorized"] = True
	else:
		status_dict["Authorized"] = False

	return jsonify(status_dict)

# Internal directory routes
@app.route('/win/directory/<first_name>', methods=['GET'], defaults={'last_name': None, 'association': None, 'ID': None})
@app.route('/win/directory/<first_name>/<last_name>', methods=['GET'], defaults={'association': None, 'ID': None})
@app.route('/win/directory/<first_name>/<last_name>/<association>', methods=['GET'], defaults={'ID': None})
@app.route('/win/directory/<first_name>/<last_name>/<association>/<ID>', methods=['GET'])
def internal_directory(first_name, last_name, association, ID):
	""" SEARCHES INTERNAL DIRECTORY """

	# Check if we're first authorized
	if not authorized: return jsonify({"Authorized": False})

	# If we are, proceed and check parameters.
	if first_name and last_name and association and ID:
		pass
	elif first_name and last_name and association and (ID == None):
		ID = ""
	elif first_name and last_name and (association == None) and (ID == None):
		association = None
		ID = None
	elif first_name and (last_name == None) and (association == None) and (ID == None):
		last_name = ""
		association = ""
		ID = ""


	# Attempt to find in directory
	try:
		student = win.internal_directory(first_name=first_name, last_name=last_name, association=association, id=ID)
		print student

		# Otherwise, we've found what we're looking for, and return it
		return jsonify(response=student)

	# First check if Redis is up and running and report if it's not
	except redis.exceptions.ConnectionError:
		# If you want to throw a 404 error instead, go ahead (uncomment line below), but I like to know what's going on
		# abort(404)
		return jsonify({"Error": "Could not resolve Redis connection"})

	except :
		return jsonify({"Error": "Unable to find user " + first_name + " " + last_name})


# Student Schedule Routes
@app.route('/win/schedule', methods=['GET'], defaults={'term': 'Spring 2015'}) # This will need to be updated every semester... :/ 
@app.route('/win/schedule/<term>', methods=['GET'])
def student_schedule(term):
	""" RETRIEVES THE SCHEDULE FOR A GIVEN TERM OF THE USER LOGGED IN """

	# Check if we're first authorized
	if not authorized: return jsonify({"Authorized": False})

	# Attempt to find in directory
	try:
		schedule = win.current_schedule(term=term)

		# Otherwise, we've found what we're looking for, and return it
		return jsonify(response=schedule)

	except redis.exceptions.ConnectionError:
		# If you want to throw a 404 error instead, go ahead (uncomment line below), but I like to know what's going on
		# abort(404)
		return jsonify({"Error": "Could not resolve Redis connection"})

	except :
		return jsonify({"Error": "Unable to find schedule for term " + term})


if __name__ == "__main__":

	# Creates a WIN object shared by the entire flask app (assuming you call it win too)
	global win

	# WIN CONFIG
	username = "mcgoga12"
	password = ""

	win = WIN(username, password)

	# Attempt to login to WIN
	try: 
		win.login()
		authorized = True
	
	except: 
		authorized = False
		raise Exception("Error logging into WIN.")


	# Method to test if we're authorized
	# isAuthorized = lambda authorized: True if authorized else False

	# NOTE: The Werkzeug reloader spawns a child process so that it can
	# restart that process each time your code changes. Werkzeug is the 
	# library that supplies Flask with the development server when you 
	# call app.run().
	#
	# As a result, the `use_reloader` argument is passed in and set to 
	# false as a way to prevent the win.login() method from being called
	# twice.
	#
	# To re-enable reloading, simply remove the argument and call like so:
	# app.run(debug=True)
	app.run(debug=True, use_reloader=False)


