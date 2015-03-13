#!/usr/bin/python

# Name: WIN 
# File: WIN/main.py
#
# Author(s): Grant McGovern & Gaurav Sheni
# Date: Wed 11 March 2015 
#
# URL: www.github.com/g12mcgov/WIN
#
# ~ Description:
#		- A driver main() method used for debugging 
#		and testing.
#
#
#

from wfu.win import WIN

def main():
	username = "mcgoga12"
	password = ""
	
	win = WIN(username, password)

	win.login()
	student = win.internal_directory(first_name="grant", last_name="mcgovern", association="student", id="1")
	
	print student
	# schedule = win.handle_term_selection(term="Spring 2015")
	# schedule = win.current_schedule(term="Fall 2013")

	win.shutDown()


if __name__ == "__main__":
	main()
