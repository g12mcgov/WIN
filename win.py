#
#
#
#
#	An API to WIN. Lol.
#
#
#
#
#

import re
import sys
import time
import redis
import urllib2
import logging
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC 

sys.path.append('loggings')
sys.path.append('helpers')

## Local Includes ##
from db import RedisConnect
from loggings.loggerConfig import configLogger
from helpers.helper import cache


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
			"detailed_schedule": self.SERVICE_URL + "1325",
			"change_term": self.SERVICE_URL + "1743",
			"register_with_CRN": self.SERVICE_URL + "1317",
			"internal_directory": self.LOGIN_URL + "win/app.dirx.InternalDirectory" 
		}

		# Selenium Config
		self.SELENIUM_TIMEOUT = 10
		self.driver = self.setupDriver()
		self.WAIT = WebDriverWait(self.driver, self.SELENIUM_TIMEOUT)

		# XPATHS
		self.login_xpath = "/html/body/table[2]/tbody/tr/td/table[1]/tbody/tr/td[1]/form/table/tbody/tr/td/table/tbody/tr[4]/td[2]/input"
		self.student_radio_button_xpath = '//*[@id="dirform"]/table[2]/tbody/tr[2]/td/table/tbody/tr[3]/td[2]/input'
		self.faculty_radio_button_xpath = '//*[@id="dirform"]/table[2]/tbody/tr[2]/td/table/tbody/tr[4]/td[2]/input'
		self.term_change_submit_button = '/html/body/div[3]/form/input'

		# COOKIE
		self.COOKIE = {}

	def setupDriver(self):
		#driver = webdriver.PhantomJS()
		driver = webdriver.Firefox()

		#driver.set_window_size(2000, 2000)

		return driver


	def login(self):
		# Make a request to the login page
		self.logger.info("Requesting: " + self.LOGIN_URL)

		# Request login page
		self.driver.get(self.LOGIN_URL)

		# Find elements
		try:
			print 

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

		for cookie in cookies:
			self.driver.add_cookie(cookie)

		self.logger.info("Successfully logged in.")

	 
	def handle_term_selection(self, **kwargs):
		print self.SERVICE_PATHS['change_term']
		""" CHANGES THE CURRENT TERM IN WIN """

		if len(kwargs) > 1:
			raise Exception("\nhandler_term_selection() takes one term.\n i.e."+
				"\n\n >> handle_term_selection(term='Spring 2015')"
				)

		self.logger.info("Requesting: " + self.SERVICE_PATHS["change_term"])

		# Extract term from kwargs
		term = kwargs["term"]
		
		# Request 'Change Term' page
		#https://ssb.win.wfu.edu/BANPROD/twbkwbis.p_WINBridge?p_proc_name_in=bwskflib.P_SelDefTerm
		#https://ssb.win.wfu.edu/BANPROD/bwskflib.P_SelDefTerm
		self.driver.get(self.SERVICE_PATHS['detailed_schedule'])

		cookie = self.driver.get_cookies()
		self.driver.add_cookie(cookie)

		try:
			print self.getHTML(self.driver.page_source)

			dropdown_selection = self.WAIT.until(EC.presence_of_element_located((By.NAME, "term_in")))
			submit_button = self.WAIT.until(EC.presence_of_element_located((By.XPATH, self.term_change_submit_button)))
			# Use Selenium Select() method to handle dropdown option list
			select = Select(dropdown_selection)

			select.select_by_visible_text(term)

			submit_button.click()

		except NoSuchElementException as err:
			raise err

		# try:
		# 	# Send username / password
		# 	username_box.send_keys(self.USERNAME)
		# 	password_box.send_keys(self.PASSWORD)

		# 	# Click "Log in" button
		# 	login_button.click()

		# except AttributeError as err:
		# 	raise err


	# Actual methods
	def current_schedule(self, term):
		""" RETRIEVES CURRENT USER SCHEDULE """

		url = self.SERVICE_PATHS["detailed_schedule"]

		try:
			page = urllib2.urlopen(url)
			soup = BeautifulSoup(page.read())
			print page

		except AttributeError as err:
			raise err

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
			if res:
				return res
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
		
		# Make request to web directory search page
		self.driver.get(self.SERVICE_PATHS['internal_directory'])

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
				raise Exception("\nType must be either 'faculty' or 'student'")

			search_button.click()

		except NoSuchElementException as err:
			raise err

		source = self.getHTML(self.driver.page_source)

		# Table 3 is the results table
		results = [{'ID': str(i), 'Name': res.getText() } for i, res in enumerate(source.findAll('table')[3].findAll('td'))]

		print "Results:\n"

		for res in results:
			print res


		if not selection:
			print "\nPlease choose a name:\n"
			selection = raw_input('> ')

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
		#time.sleep(100000)
		self.driver.quit()


	def getHTML(self, HTML):
		soup = BeautifulSoup(HTML)

		return soup


	def extractProfileData(self, HTML):
		profileData = [res.getText().rstrip() for res in HTML.findAll('table')[3].findAll('td')]

		profileDict = {}


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


if __name__ == "__main__":

	username = "mcgoga12"
	password = ""
	
	win = WIN(username, password)

	win.login()
	#win.internal_directory(first_name="christina", last_name="paragamian", association="student", id=1)
	schedule = win.handle_term_selection(term="Spring 2015")

	print student


	win.shutDown()