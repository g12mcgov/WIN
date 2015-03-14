# :tophat: WIN

A RESTful API service for [Wake Forest University](http://www.wfu.edu/)'s Internal Management System, [WIN](https://win.wfu.edu/). This is in no way affiliated with Wake Forest University, The Bridge, or the original creators of WIN.

This is designed solely as a resource for Wake Forest Students. It is no different than interacting with the web interface of WIN, it's just a little smarter :wink:.


Overview
======= 

Inspired by the many universities who have open API's for their internal systems, I felt Wake Forest deserved one. This was largely (and initially) inspired by the Python module, [cmupy](https://github.com/ScottyLabs/cmupy), designed by Carnegie Mellon students for interacting with their Student Directory. Unfortunately, unlike Carnegie Mellon, Wake Forest didn't/doesn't have any RESTful API services in place for students to use. We should have access to this data because it is <b>our</b> data. Hopefully, many of you will find this as interesting and useful as I have while building it.

<b>Why Python?</b>

I really thought about writing this API in Java because a lot of WFU undergraduates have extensive experience with Java, however, I felt as though I could get it done faster and with more knowledge in Python. Much of the web-scraping tools like [Selenium](http://www.seleniumhq.org/) and [Beautiful Soup](http://www.crummy.com/software/BeautifulSoup/) I've worked with extensively, making it an ideal choice. 

Moreover, the RESTful service is served via [Flask](http://flask.pocoo.org/), a blisteringly simple, small-footprint Python web framework. I want other students who stumble upon this to be able to fork it, contribute, and maintain it after my time at WFU. I believe writing this in Python makes the code more understandable and easier to hack at.

Design
=======

Because WFU does not provide us with an API service, this means building one from square one. I tried reverse engineering some of the WIN URLs, looking for `JSON` or `XML` responses, but to no avail. 

Part of the problem is that WIN is entirely contained within an iframe. As a result, URLs are non-existent. Furthermore, after doing some research, it seems to be an old Java application layered ontop of an Oracle Database built in 2005. It could certainly use a facelift or some updating, but it gets the job done. 

Because there are no reachable URLs, this meant scraping the data from the screen. This meant using the [Selenium](http://www.seleniumhq.org/) browser automation tool and [Beautiful Soup](http://www.crummy.com/software/BeautifulSoup/) for extracting, parsing, and working with the HTML source. However, this lends itself to a significant bottleneck of <b>speed</b>.

One of the work arounds to do is using a headless browser for web automation, and in this case, [PhantomJS](http://phantomjs.org/). Moreover, to counter speed limitations, this API makes use of [Redis](http://redis.io/). Here's How:

1) Make request with given parameters

2) Check if this identical request exists in Redis

3) If so, return that entry, otherwise, cache it for next time.

Clearly, using Redis as a caching mechanism reduces latency in duplicate calls. This alleviates some of the performance bottleneck caused by the web-scraping overhead running in the background after each `REST` request.

Installing
=======

In order to get your own instance of WIN up and running, first `cd` to a directory you wish to download it and grab the source code:

1) `$ git clone git@github.com:g12mcgov/WIN.git`

I <b>strongly</b> suggest creating a virtual environment for WIN:

2) `$ mkvirtualenv WIN`

Then, once you're in the `root` WIN directory, run the following:

3) `sudo python setup.py install`

This will install all of the `pip` dependencies for WIN. If you're curious as to what modules it uses, here you go:

	Flask==0.10.1
	Jinja2==2.7.3
	MarkupSafe==0.23
	PIL==1.1.7
	Werkzeug==0.10.1
	beautifulsoup4==4.3.2
	itsdangerous==0.24
	redis==2.10.3
	selenium==2.45.0
	wsgiref==0.1.2

Because WIN uses [PhantomJS](http://phantomjs.org/), you need to install [Node.js](https://nodejs.org/) along with [PhantomJS](http://phantomjs.org/).

To install Node.js:

<b>Mac OS X</b>:
	
	brew install node

<b>Linux</b>:
	
	sudo apt-get install npm
	sudo ln -s /usr/bin/nodejs /usr/bin/node

<b>Windows</b>:
	
[See here.](http://blueashes.com/2011/web-development/install-nodejs-on-windows/)

Now, using Node's package manager, `npm` run the following to install [PhantomJS](http://phantomjs.org/):

`npm -g install phantomjs`

(<b>NOTE:</b> If you're on a Mac, you can also install [PhantomJS](http://phantomjs.org/) by doing `brew install phantomjs`)


4) You now need to install [Redis](http://redis.io/).

<b>Mac OS X</b>:

	$ brew install redis

<b>Linux</b>:
	
	$ wget http://download.redis.io/releases/redis-2.8.19.tar.gz
	$ tar xzf redis-2.8.19.tar.gz
	$ cd redis-2.8.19
	$ make

<b>Windows</b>:

You can find the latest distribution of Redis [here](https://github.com/rgl/redis/downloads).

<br />
<br />
<br />

Before running, you must start Redis:

	$ redis-server 

And you may need to make `app.py` an executable:
	
```bash
$ chmod a+x app.py
```



Configuring
=======

You must configure your WIN instance to contain your username and password. To do that, edit the following in the bottom of the `app.py` file:

```Python
if __name__ == "__main__":

	# Globalizes a WIN object shared by the entire flask app
	global win

	# WIN CONFIG
	username = "INSERT YOUR WFU USERNAME HERE (no @wfu.edu)"
	password = "INSERT YOUR WFU PASSWORD HERE"

	win = WIN(username, password)

	# Attempt to login to WIN
	try: 
		win.login()
		authorized = True
	
	except: 
		authorized = False
		raise Exception("Error logging into WIN.")

		...
		...
		...

```


A configuration `shell` script will be added shortly.



API Documentation
=======	

Currently, the following WIN attributes are working (though not 100% stable yet):

1) <b>Student Directory</b> (Including pictures!)

2) <b>Student Schedule</b>

3) <b>Term Selection</b>

4) <b>Final/Midterm Grades</b> (In Progress)

Soon, however, additional functionality will be implemented (Class Registration, Course Evaluations, etc...) and existing API endpoints will be tested robustly.

All of the API route (Flask) implementations can be found in the `app.py` file.


---
### Login
---

Checks to see if the user is logged into WIN.

* **URL**

  `/win`

* **Method:**
  
  `GET`
  
*  **URL Params**

   **Required:**
 
     None

   **Optional:**
 
     None

* **Data Params**

  **Required:**
    
    None

  **Optional:**
    
    None

* **Success Response:**

  * **Code:** 200 <br />
  * **Content:**
      
      ```json
      {
          "Authorized": true
      }
      ``` 

* **Error Response:**

  * **Content:**
  
	  ```json
	  {
	      "Authorized": false
	  }
	  ``` 

* **Sample Call:**

  ```bash
    curl -i -H -X "Accept: application/json" http://localhost:5000/win
  ```


---
### Student Directory 
---

This returns a student's WIN bio from the internal directory based on a search query. 

This method takes 4 parameters:

1) `First Name`

2) `Last Name`

3) `Association`

4) `ID`

The `First Name` and `Last Name` are self explanatory, however, each call must require an `association`. The two options for this are:

1) `student`

2) `faculty`

Lastly, in order to handle a search query with multiple results (for example):

![example](http://i1158.photobucket.com/albums/p618/g12mcgov/Untitled.png)

We need a way to index each result. What happens is each name is mapped to a number. For example:

	{'ID': '0', 'Name': u'Search Results: '}
	{'ID': '1', 'Name': u'Backerman, Grant Madison'}
	{'ID': '2', 'Name': u'Bishop, Grant Christian'}
	{'ID': '3', 'Name': u'Dawson, Grant Harrison'}
	{'ID': '4', 'Name': u'Ferowich, Grant J.'}
	{'ID': '5', 'Name': u'Garvey, Grant Steven'}
	{'ID': '6', 'Name': u'Gieger, Joseph Grant'}
	{'ID': '7', 'Name': u'McGovern, Grant Alexandre'}
	{'ID': '8', 'Name': u"O'Brien, Grant Blandford"}
	{'ID': '9', 'Name': u'Spencer, Grant Avery'}
	{'ID': '10', 'Name': u'VanKirk, Robert Grant'}
	{'ID': '11', 'Name': u'Wissak, Grant Elias'}

Now, the next time you call the method, you can either specify your query using the last name:

	>> GET /win/wfu/directory/grant/mcgovern/student/1

Or, you can leverage the ID:
	
	>> GET /win/wfu/directory/grant/student/7

(<b>NOTE:</b> If the person you are looking for is the only person (first + last name), the ID will always be 1)

* **URL**

  `/win/directory`

* **Method:**
  
  `GET`
  
*  **URL Params**

   **Required:**
 
     None

   **Optional:**
 
 	`/win/directory/:firstname/:lastname/:association/:id` 

* **Data Params**

  **Required:**
    
    None

  **Optional:**
    
    None

* **Success Response:**

  * **Code:** 200 <br />
  * **Content:**
      
      ```json
      {
    	"response": 
		"{
			'Major': 'Computer Science', 
			'Name': 'McGovern, Grant Alexandre (Grant)', 
			'Classification': 'Junior', 
			'Email': 'mcgoga12@wfu.edu', 
			'WFU Associations': 'Student', 
			'Home Address': 'XXX2 Morrison Street NW Washington, DC 020015'
		}"
	  }
      ``` 

* **Error Response:**

  * **Content:**
  
	  ```json
	  {
    	"response": 
    	{
        	"Error": "No association type given. Please try again with either `student` or `faculty`"
    	}
	  }
	  ``` 

* **Sample Call(s):**

  ```bash
    curl -i -H -X "Accept: application/json" http://localhost:5000/win/directory/grant/mcgovern
    curl -i -H -X "Accept: application/json" http://localhost:5000/win/directory/grant/mcgovern/student
    curl -i -H -X "Accept: application/json" http://localhost:5000/win/directory/grant/mcgovern/student/1

  ```

---
### Schedule
---

Returns the schedule based on the inputted term for the user logged in.

(<b>NOTE:</b> Returns the lastest schedule by default if no term is passed in.)

* **URL**

  `/win/schedule`

* **Method:**
  
  `GET`
  
*  **URL Params**

   **Required:**
 
     None

   **Optional:**
 
     None

* **Data Params**

  **Required:**
    
    None

  **Optional:**
    
    `/win/schedule/:term`

    If you are going to pass a term, it will contain a space (i.e.: `Fall 2012`), so you must pass it using proper URL space escaping (`%20`).

    For example: `Fall 2012` => `Fall%202012`

* **Success Response:**

  * **Code:** 200 <br />
  * **Content:**
      
      ```json
      {
    	"response": 
    		"[
    			{
    				'Status': '**Registered** on Oct 29, 2014', 
    				'Style': 'Lecture', 
    				'Title': 'Computer Organization - CSC 211 - A', 
    				'Grade Mode': 'Standard Letter', 
    				'Dates': 'Jan 13, 2015 - May 07, 2015', 
    				'Days': 'MWF', 
    				'Credits': '4.000', 
    				'Location': 'Manchester Hall 241', 
    				'Time': '11:00 am - 12:15 pm', 
    				'Assigned Instructor': 'David J. John', 
    				'CRN': '20763', 
    				'Campus': 'Reynolda Campus  (UG)'
    			}, 
    			{
    				'Status': '**Registered** on Oct 29, 2014', 
    				'Style': 'Lecture', 
    				'Title': 'Data Structures & AlgorithmsII - CSC 222 - A', 
    				'Grade Mode': 'Standard Letter', 
    				'Dates': 'Jan 13, 2015 - May 07, 2015', 
    				'Days': 'TR', 
    				'Credits': '3.000', 
    				'Location': 'Manchester Hall 241', 
    				'Time': '9:30 am - 10:45 am', 
    				'Assigned Instructor': 'Victor P. Pauca', 
    				'CRN': '19508', 
    				'Campus': 'Reynolda Campus  (UG)'
    			}, 
    			{
    				'Status': '**Registered** on Oct 29, 2014', 
    				'Style': 'Lecture', 
    				'Title': 'Programming Languages - CSC 231 - A', 
    				'Grade Mode': 'Standard Letter', 
    				'Dates': 'Jan 13, 2015 - May 07, 2015', 
    				'Days': 'MWF', 
    				'Credits': '4.000', 
    				'Location': 'Manchester Hall 241', 
    				'Time': '2:00 pm - 3:15 pm', 
    				'Assigned Instructor': 
    				'William H. Turkett', 
    				'CRN': '11044', 
    				'Campus': 'Reynolda Campus  (UG)'
    			}, 
    			{
    				'Status': '**Web Registered** on Nov 05, 2014', 
    				'Style': 'Lecture', 
    				'Title': 'Linear Algebra I - MTH 121 - C', 
    				'Grade Mode': 'Standard Letter', 
    				'Dates': 'Jan 13, 2015 - May 07, 2015', 
    				'Days': 'MWF', 
    				'Credits': '4.000', 
    				'Location': 'Carswell Hall 101', 
    				'Time': '12:30 pm - 1:45 pm', 
    				'Assigned Instructor': 'Jason D. Gaddis', 
    				'CRN': '19765', 
    				'Campus': 'Reynolda Campus  (UG)'
    			}
    		]"
	  }
      ``` 

* **Error Response:**

  * **Content:**
  
	  ```json
	  {
	      "Error": "Unable to find schedule for term `Spring 2012`"
	  }
	  ``` 

* **Sample Call:**

  ```bash
    curl -i -H -X "Accept: application/json" http://localhost:5000/win/schedule/Fall%202014
  ```


Testing
=======

Testing will be integrated shortly.


Improvements
=======

On their way! (I promise)


Deployment
=======

Currently, this API has only been run locally in development. However, it will be documented how to deploy to cloud services such as Heroku, AWS, etc...


License
=======

The MIT License (MIT)

Copyright (c) 2014 Grant McGovern, Gaurav Sheni

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


