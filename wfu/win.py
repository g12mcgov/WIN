#!/usr/bin/python

# Name: WIN 
# File: WIN/win.py
#
# Author(s): Grant McGovern & Gaurav Sheni
# Date: Wed 11 March 2015 
#
# URL: www.github.com/g12mcgov/WIN
#
# ~ Description:
#		- This file defines the main WIN class to be used throughout the app. 
#		  it contains all of the necessary methods to be used as standalone or
#		  with the WIN API.
#
#
#

import re
import sys
import time
import redis
import urllib2
import logging
from PIL import Image
from bs4 import BeautifulSoup
from selenium import webdriver
from collections import OrderedDict
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC 


## Local Includes ##
from database.db import RedisConnect
from helpers.helper import cache, pairwise
from loggings.loggerConfig import configLogger


class WIN:
	def __init__(self, username, password):
		# Credentials
		self.USERNAME = username
		self.PASSWORD = password

		# Establish Redis Connection
		self.db = RedisConnect(host="localhost", port=6379, db=0)

		# Setup Logging
		self.logger = configLogger("win")

		# URL Paths
		self.LOGIN_URL = "https://win.wfu.edu/"
		self.BASE_URL = "https://win.wfu.edu/win/app/wincore.SSBGateway?"
		self.SERVICE_URL = "https://win.wfu.edu/win/app/wincore.SSBGateway?serviceID="

		# A Mappings of services to their respective URL
		self.SERVICE_PATHS = {
			"virtual_campus": "https://win.wfu.edu/win/app.wincore.WINServlet?click=1315",
			"detailed_schedule": self.SERVICE_URL + "1325",
			"change_term": self.SERVICE_URL + "1743",
			"register_with_CRN": self.SERVICE_URL + "1317",
			"internal_directory": self.LOGIN_URL + "win/app.dirx.InternalDirectory" 
		}

		# Selenium Config
		self.DRIVER_TYPE = webdriver.PhantomJS()
		self.SELENIUM_TIMEOUT = 10
		self.driver = self.setupDriver()
		self.WAIT = WebDriverWait(self.driver, self.SELENIUM_TIMEOUT)

		# XPATHS
		self.login_xpath = "/html/body/table[2]/tbody/tr/td/table[1]/tbody/tr/td[1]/form/table/tbody/tr/td/table/tbody/tr[4]/td[2]/input"
		self.student_radio_button_xpath = '//*[@id="dirform"]/table[2]/tbody/tr[2]/td/table/tbody/tr[3]/td[2]/input'
		self.faculty_radio_button_xpath = '//*[@id="dirform"]/table[2]/tbody/tr[2]/td/table/tbody/tr[4]/td[2]/input'
		self.term_change_submit_button = '/html/body/div[3]/form/input[2]'
		self.change_term_link = '/html/body/table[1]/tbody/tr[2]/td/ul[2]/li/a'
		self.student_detail_schedule_link = "/html/body/table[1]/tbody/tr[2]/td/ul[4]/li[7]/a"

		# COOKIE
		self.COOKIE = {}

	def setupDriver(self):
		""" RETURNS A WEB DRIVER OBJECT BASED ON WHAT KIND """
		return self.DRIVER_TYPE

	def login(self):
		""" LOGS INTO WIN, AND STORES COOKIE. MUST BE THE ENTRY POINT FOR APP """

		# Log request to login page
		self.logger.info("Requesting: " + self.LOGIN_URL)

		# Request login page
		self.driver.get(self.LOGIN_URL)

		# Find elements
		try:

			username_box = self.WAIT.until(EC.presence_of_element_located((By.NAME, "username")))
			password_box = self.WAIT.until(EC.presence_of_element_located((By.NAME, "password")))
			login_button = self.WAIT.until(EC.presence_of_element_located((By.XPATH, self.login_xpath)))

		except NoSuchElementException as err:
			raise err

		try:
			# Send username / password
			username_box.send_keys(self.USERNAME)
			password_box.send_keys(self.PASSWORD)

			# Click "Log in" button
			login_button.click()

		except AttributeError as err:
			raise err


		# Store the Cookie to persist through the rest of the app
		cookies = self.driver.get_cookies()

		# If there's multiple cookies, store 'em all b/c I have no idea which 
		# one is the WIN cookie.
		for cookie in cookies:
			self.driver.add_cookie(cookie)

		self.logger.info("Successfully logged in.")

	 
	def handle_term_selection(self, **kwargs):
		""" CHANGES THE CURRENT TERM IN WIN """

		if len(kwargs) > 1:
			raise Exception("\nhandler_term_selection() takes one term.\n i.e."+
				"\n\n >> handle_term_selection(term='Spring 2015')"
				)

		self.logger.info("Requesting: " + self.SERVICE_PATHS["change_term"])

		# Extract term from kwargs
		term = kwargs["term"]
		
		# This is a very hacky way of getting to the 'Change Term page.'
		# For some reason, WFU WIN won't allow you to directory go to the term 
		# page even with a static URL (even adding cookies too). As a workaround,
		# we first go to the Virtual Campus page and select the link, then go to
		# the site. 
		# TODO: Fix this. (or optimize it)
		self.driver.get(self.SERVICE_PATHS["virtual_campus"])
			
		try:
			change_term = self.WAIT.until(EC.presence_of_element_located((By.XPATH, self.change_term_link)))
			change_term.click()

		except NoSuchElementException as err:
			raise err

		try:
			dropdown_selection = self.WAIT.until(EC.presence_of_element_located((By.NAME, "term_in")))
			submit_button = self.WAIT.until(EC.presence_of_element_located((By.XPATH, self.term_change_submit_button)))
			# Use Selenium Select() method to handle dropdown option list
			select = Select(dropdown_selection)

			# In the event we encounter a selection with a '(View only)' tag, handle it.
			try: select.select_by_visible_text(term)
			except: select.select_by_visible_text(term + ' (View only)')

			submit_button.click()

			self.logger.info("Successfully changed term.")

		except NoSuchElementException as err:
			raise err

	# Actual methods
	def current_schedule(self, **kwargs):
		""" RETRIEVES CURRENT USER SCHEDULE """

		# First change the term to the current one
		if len(kwargs) > 1:
			raise Exception("\ncurrent_schedule() takes one term.\n i.e."+
				"\n\n >> current_selection(term='Spring 2015')"
				)

		# Extract term from kwargs
		term = kwargs["term"]
		
		# Switch the current term to the requested one:
		self.handle_term_selection(term=term)

		# Log our request 
		self.logger.info("Requesting: " + self.SERVICE_PATHS["detailed_schedule"])

		# This is a very hacky way of getting to the 'Change Term page.'
		# For some reason, WFU WIN won't allow you to directory go to the term 
		# page even with a static URL (even adding cookies too). As a workaround,
		# we first go to the Virtual Campus page and select the link, then go to
		# the site. 
		# TODO: Fix this. (or optimize it)
		self.driver.get(self.SERVICE_PATHS["virtual_campus"])

		try:
			detailed_schedule = self.WAIT.until(EC.presence_of_element_located((By.XPATH, self.student_detail_schedule_link)))
			detailed_schedule.click()

		except NoSuchElementException as err:
			raise err

		# Grab page HTML and send to extraScheduleData() method
		source = self.getHTML(self.driver.page_source)
		self.extractScheduleData(source)


	#@cache
	def internal_directory(self, **kwargs):
		""" SEARCHES INTERNAL DIRECTORY FOR A USER"""

		selection = ""

		if len(kwargs) > 4:
			raise Exception(
				"\nToo many arguments: method takes first_name & last_name i.e.:\n"+
				"\n>> internal_directory(first_name='bob', last_name='jones', association='student')"
				)
		elif len(kwargs) <= 1:
			raise Exception(
				"\nToo few arguments: method must have either first_name or last_name and association i.e.:\n"+
				"\n>> internal_directory(first_name='bob', association='student')"
				)

		#
		# If we have a first_name, last_name, association, and ID
		#
		if kwargs['first_name'] and kwargs['last_name'] and kwargs['association'] and kwargs['id']:
			
			first_name = kwargs['first_name'].lower()
			last_name = kwargs['last_name'].lower()
			classification = kwargs['association'].lower()
			selection = str(kwargs['id'])

			# Now we check to see if we've already made this call before.
			# If we have, we query Redis and save ourself the scraping of
			# the WIN website. If we haven't, we proceed, and store the new
			# results in Redis in the event we make this call again.
			
			# Build our query
			query = {
				"firstName": first_name,
				"lastName": last_name,
				"association": classification,
				"ID": selection
			}

			# Check if it exists in Redis
			res = self.db.checkIfExists(query)
			
			# If it does, return the res object
			if res: return res
			# Otherwise, proceed
			else:
				self.logger.info("Doesn't exist in Redis.")

		#
		# If we just have a first_name, last_name, and association:
		#
		elif kwargs['first_name'] and kwargs['last_name'] and kwargs['association']:
			first_name = kwargs['first_name'].lower()
			last_name = kwargs['last_name'].lower()
			classification = kwargs['association'].lower()

		#
		# If we have just a first_name OR last_name, id, and association
		#
		elif kwargs['first_name'] or kwargs['last_name'] and kwargs['id'] and kwargs['association']:
			first_name = kwargs['first_name'].lower()
			classification = kwargs['association'].lower()
			selection = str(kwargs['id'])
			last_name = ""

		#
		# If we just have a first_name and last_name
		#
		elif kwargs['first_name'] and kwargs['last_name']:
			first_name = kwargs['first_name'].lower()
			last_name = kwargs['last_name'].lower()
			association = ""

		#
		# If we have a first_name OR last_name AND association
		#
		elif kwargs['first_name'] or kwargs['last_name'] and kwargs['association']:
			first_name = kwargs['first_name'].lower()
			last_name = kwargs['last_name'].lower()
			classification = kwargs['association'].lower()

		#
		# If we have just have a first_name
		#
		elif kwargs['first_name']:
			raise Exception(
				"\nToo few arguments: method must have either first_name or last_name AND association i.e.:\n"+
				"\n>> internal_directory(first_name='bob', association='student')"
				)

		#
		# If we have just a last_name
		#
		elif kwargs['last_name']:
			raise Exception(
				"\nToo few arguments: method must have either first_name or last_name AND association i.e.:\n"+
				"\n>> internal_directory(last_name='smith', association='student')"
				)

		#
		# If we have just an association
		#
		elif kwargs['association']:
			raise Exception(
				"\nToo few arguments: method must have either first_name or last_name AND association i.e.:\n"+
				"\n>> internal_directory(first_name='bob', last_name='smith', association='student')"
				)

		else:
			last_name = ""
			first_name = ""
		

		# Log our request to the URL
		self.logger.info("Requesting: " + self.SERVICE_PATHS["internal_directory"])

		# Make request to web directory search page
		self.driver.get(self.SERVICE_PATHS["internal_directory"])

		try:
			# Locate elements
			first_name_box = self.WAIT.until(EC.presence_of_element_located((By.NAME, "firstName")))
			last_name_box = self.WAIT.until(EC.presence_of_element_located((By.NAME, "lastName")))
			student_radio_button = self.WAIT.until(EC.presence_of_element_located((By.XPATH, self.student_radio_button_xpath)))	
			faculty_radio_button = self.WAIT.until(EC.presence_of_element_located((By.XPATH, self.faculty_radio_button_xpath)))
			search_button = self.WAIT.until(EC.presence_of_element_located((By.NAME, "submit_button")))

			# Send search query
			first_name_box.send_keys(first_name)
			last_name_box.send_keys(last_name)

			if classification == 'student':
				student_radio_button.click()

			elif classification == 'faculty':
				faculty_radio_button.click()

			else:
				raise Exception("\nAssociation must be either 'faculty' or 'student'")

			# Execute the search query by clicking the "submit" button
			search_button.click()

		except NoSuchElementException as err:
			raise err

		# Get HTML from the page
		source = self.getHTML(self.driver.page_source)

		# Table 3 is the results table
		results = [{'ID': str(i), 'Name': res.getText() } for i, res in enumerate(source.findAll('table')[3].findAll('td'))]

		# TODO: Replace with this RESTful API parameter 'ID'
		# 		i.e.: localhost/winapi/internal_directory/?first_name=bob&last_name=smith&id=2
		if not selection:
			return results

		keys = [key['ID'] for key in results]

		if selection in keys:
			for res in results:
				if selection == res['ID']:

					try:
						current_name = self.WAIT.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), " + "'" + str(res['Name']) + "')]")))
						current_name.click()

						# Extract HTML from current page
						current_source = self.getHTML(self.driver.page_source)

						profileDict = self.extractProfileData(current_source)
						
						# Retrieve picture
						# self.getPicture(profileDict)

						# Build our query to insert into Redis
						query = {
							"firstName": first_name,
							"lastName": last_name,
							"association": classification,
							"ID": selection
						}

						# Insert into Redis
						self.db.insert(query, profileDict)

						# Return dictionary of user profile as such:
						# {
						# 	'Major': 'Finance', 
						#	'Name': 'Smith, Bob Jones (Robert)', 
						#	'Classification': 'Junior', 
						#	'Email': 'blah@wfu.edu', 
						#	'WFU Associations': 'Student', 
						#	'Home Address': '4454 Burch Dr.Chevy Chase, MD\xc2\xa020815', 
						#	'Home Phone': '(301) 694-1357'
						# }

						return profileDict

					except NoSuchElementException as err:
						raise err

					break
		else:
			raise Exception("Not a valid selection")


		# If all else fails, return an empty dict 
		return {}


	def shutDown(self):
		self.driver.quit()


	def getHTML(self, HTML):
		soup = BeautifulSoup(HTML)

		return soup


	def extractProfileData(self, HTML):
		""" EXTRACTS THE PROFILE DATA FROM A WIN DIRECTORY ENTRY """

		profileData = [res.getText().rstrip() for res in HTML.findAll('table')[3].findAll('td')]

		profileDict = {}

		# This is nasty string parsing but all I could get to work for now. Whatever.
		i = 0
		while (i != len(profileData)-1):

			if profileData[i] == "Name":
				profileDict["Name"] = str(profileData[i+1])

			elif profileData[i] == "Email":
				profileDict["Email"] = str(profileData[i+1])

			elif profileData[i] == "Classification":
				profileDict["Classification"] = str(profileData[i+1])

			elif profileData[i] == "Major":
				profileDict["Major"] = str(profileData[i+1])

			elif profileData[i] == "Home Address":
			 	profileDict["Home Address"] = profileData[i+1].encode('utf-8')

			elif profileData[i] == "Home Phone":
				profileDict["Home Phone"] = str(profileData[i+1])

			elif profileData[i] == "WFU Associations":
				profileDict["WFU Associations"] = str(profileData[i+1])

			i += 1

		return profileDict


	def extractScheduleData(self, HTML):
		""" EXTRACTS THE SCHEDULE FOR THE LOGGED IN WIN USER """
		
		#calculated_length = HTML.findAll("table", {"class": "atadisplaytable"})
		calculated_length = len(HTML.findAll("table"))

		# Remove duplicates while preserving order
		tables = OrderedDict.fromkeys(HTML.findAll("table", {"class": "datadisplaytable"})).keys()

		classes = []

		for item1, item2 in pairwise(tables):
			
			temporaryDict = {}

			temporaryDict["classInfo"] = item1.getText()
			temporaryDict["sectionInfo"] = item2.getText()

			classes.append(temporaryDict)

		
		# Overall list to store schedule
		schedule = []

		# For each class in the list, extract meta data
		for entry in classes:

			classesDict = {}

			# Generate a list by splitting on new lines
			splitted = entry['sectionInfo'].splitlines()

			i = 0
			# First check for 'sectionInfo' data.
			# Iterate through the list, word by word, parsing out desired data
			while (i != len(splitted)-1):

				if splitted[i] == 'Class':
					classesDict["Time"] = str(splitted[i+1])
					classesDict["Days"] = str(splitted[i+2])
					classesDict["Location"] = str(splitted[i+3])
					classesDict["Dates"] = str(splitted[i+4])
					classesDict["Style"] = str(splitted[i+5])

				i += 1


			# Same as above
			splitted = entry['classInfo'].splitlines()

			# Extract Course Title:
			classesDict["Title"] = str(splitted[0])
			
			# Then check classInfo dictionary
			i = 0
			while (i != len(splitted)-1):

				if splitted[i] == 'CRN:':
					classesDict["CRN"] = str(splitted[i+1])

				elif splitted[i] == 'Status:':
					classesDict["Status"] = str(splitted[i+1])

				# Note the 'i+2'
				elif splitted[i] == 'Assigned Instructor:':
					classesDict["Assigned Instructor"] = str(splitted[i+2])

				elif splitted[i] == 'Grade Mode:':
					classesDict["Grade Mode"] = str(splitted[i+1])

				elif splitted[i] == 'Credits:':
				 	classesDict["Credits"] = str(splitted[i+1]).strip()

				elif splitted[i] == 'Campus:':
					classesDict["Campus"] = str(splitted[i+1])

				i += 1

			
			schedule.append(classesDict)

		#
		# Returns a dictionary object for a schedule as such:
		# {
		#	'Status': '**Web Registered** on Nov 05, 2014', 
		#	'Style': 'Lecture', 
		#	'Title': 'Linear Algebra I - MTH 121 - C', 
		#	'Grade Mode': 'Standard Letter', 
		#	'Dates': 'Jan 13, 2015 - May 07, 2015', 
		#	'Days': 'MWF', 
		#	'Credits': '4.000', 
		#	'Location': 'Carswell Hall 101', 
		#	'Time': '12:30 pm - 1:45 pm', 
		#	'Assigned Instructor': 'Jason D. Gaddis', 
		#	'CRN': '19765', 
		#	'Campus': 'Reynolda Campus  (UG)'
		# }
		#
		return schedule

	def getPicture(self, profileDict):
		""" DOWNLOADS PICTURE ASSOCIATED WITH USER PROFILE """

		picture_FileName = profileDict['Name']+".png" 
		
		self.driver.save_screenshot(picture_FileName)
		
		im = Image.open(picture_FileName)
		
		w, h = im.size
		
		leftw = int(w*0.66)
		righw = int(w*0.747803163)
		lefth = int(h*0.462837838)
		righth = int(h*0.668918919)
		
		im.crop((leftw, lefth, righw , righth)).save(picture_FileName)


#if __name__ == "__main__":
