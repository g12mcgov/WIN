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
import time
import urllib2
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC 
from PIL import Image

class WIN:
	def __init__(self, username, password):
		# Credentials
		self.USERNAME = username
		self.PASSWORD = password

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

		# COOKIE
		self.COOKIE = {}

	def setupDriver(self):
		#driver = webdriver.PhantomJS()
		driver = webdriver.Firefox()

		#driver.set_window_size(2000, 2000)

		return driver


	def login(self):
		# Make a request to the login page
		print "Hitting login url..."
		print self.LOGIN_URL

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
		cookie = self.driver.get_cookies()[0]

		# self.driver.add_cookie({
		# 	"domain": cookie["domain"],
		# 	"name": cookie["name"],
		# 	"value": cookie["value"],
		# 	"path": cookie["path"],
		# 	"httponly": cookie["httponly"],
		# 	"secure": cookie["secure"]
		# 	})		
		
		self.driver.add_cookie(cookie)

	# Helper Methods 
	def handle_term_selection(self):
		pass

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

	def internal_directory(self, **kwargs):
		""" SEARCHES INTERNAL DIRECTORY """

		if len(kwargs) > 3:
			raise Exception(
				"\nToo many arguments: method takes first_name & last_name i.e.:\n"+
				"\n>> internal_directory(first_name='bob', last_name='jones', type='student')"
				)
		elif len(kwargs) <= 1:
			raise Exception(
				"\nToo few arguments: method must have either first_name or last_name and associationi.e.:\n"+
				"\n>> internal_directory(first_name='bob', association='student')"
				)

		# Normalize inputs by making them all lowercase
		if len(kwargs) == 3:
			first_name = kwargs['first_name'].lower()
			last_name = kwargs['last_name'].lower()
			classification = kwargs['association'].lower()

		if len(kwargs) == 2:
			first_name = kwargs['first_name'].lower()
			last_name = kwargs['last_name'].lower()

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

		print "\nPlease choose a name:\n"
		selection = raw_input('> ')

		keys = [key['ID'] for key in results]
		values = [value['Name'] for value in results]

		if selection in keys:
			# Click on the appropriate name, and begin digest
			for res in results:
				if selection == res['ID']:

					try:
						current_name = self.WAIT.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), " + "'" + str(res['Name']) + "')]")))
						current_name.click()

						# Extract HTML from current page
						current_source = self.getHTML(self.driver.page_source)

						profileDict = self.extractProfileData(current_source)
						
						#Picture
						picture_FileName = profileDict['Name']+".png" 
						self.driver.save_screenshot(picture_FileName) 
						im = Image.open(picture_FileName)
						w, h = im.size
						leftw = int(w*0.66)
						righw = int(w*0.747803163)
						lefth = int(h*0.462837838)
						righth = int(h*0.668918919)
						im.crop((leftw, lefth, righw , righth)).save(picture_FileName)

						return profileDict

					except NoSuchElementException as err:
						raise err

					break

				else:
					pass

		else:
			raise Exception("Not a valid selection")


		# If all else fails, return an empty dict 
		return {}


	def shutDown(self):
		time.sleep(100000)
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
	password = "blah"
	
	win = WIN(username, password)

	win.login()
	student = win.internal_directory(first_name="christina", last_name="", association="student")

	print student


	win.shutDown()
