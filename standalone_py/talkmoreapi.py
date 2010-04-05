#!/usr/bin/python

# requires python-wxgtk2.8 on Debian/Ubuntu
import httplib2
from urllib import urlencode

import os
import base64
import re

class MyException(Exception):
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)

class Talkmore:
	user=None
	cookie=None
	balance=None

	def login(self, login, pwd):
		data = {'username':login, 'password':pwd}
		headers = {'Content-type': 'application/x-www-form-urlencoded'}
		h = httplib2.Http(".cache")
		response, content = h.request('https://www.talkmore.no/talkmore3/servlet/Login', 'POST', headers=headers, body=urlencode(data))
		self.cookie = response['set-cookie']

		self.update_balance()
		self.user=login
		# FIXME check logged in (e.g. find phone number on page + response code)
		# check response - location +uid
		# parse ringesaldo

	def update_balance(self):
		if not self.is_logged_in():
			raise MyException("Must be logged int to parse balance")
		self.balance = self.parse_balance_page('https://www.talkmore.no/talkmore3/servlet/SubscriptionUsage')

	def parse_balance_page(self, url):
		h = httplib2.Http(".cache")
		headers = {'Cookie' : self.cookie }
		response, content = h.request(url, 'GET', headers=headers)
		m = re.search('.*Ringesaldo:.* &nbsp;(.*)  kroner.*', content)
		if response.status !=  200:
			raise MyException("couldn't open " + url + " status " + str(response.status))
		return m.group(1)

	def is_logged_in(self):
		return self.cookie is not None

	def get_balance(self):
		self.update_balance()
		return self.balance

	def send_sms(self, to_numbers, message):
		'''We support sending messages to multiple numbers. The first parameter is an array of Strings representing norwegian numbers.
		   The second parameter should be the message, max 1600 characters (dixit talkmore web interface, I haven't tried it'''
		if not self.is_logged_in():
			raise MyException("Must be logged int to send SMS")

	    # FIXME check numbers (must be norwegian)
		number_list = ';'.join(to_numbers)
		data = {'list':number_list, 'message1':message}
		headers = {'Content-type': 'application/x-www-form-urlencoded', 'Cookie' : self.cookie}
		h = httplib2.Http(".cache")
		response, content = h.request('https://www.talkmore.no/talkmore3/servlet/SendSmsFromSelfcare', 'POST', headers=headers, body=urlencode(data))
		if response.status !=  200:
			raise MyException("couldn't send SMS to " + number_list + ". status " + str(response.status))
		m = re.search('.*Du har sendt +(.*) +SMS hittil i dag.*', content)
#		print content
		print "Sent SMS(es): " + m.group(1)

	def logout(self):
		headers = {'Cookie' : self.cookie }
		h = httplib2.Http(".cache")
		response, content = h.request('https://www.talkmore.no/talkmore3/servlet/Logout', 'GET', headers=headers)
		self.cookie = None
		self.user = None

def get_profile_dir():
	profile_dir = os.path.expanduser("~/.talkmore/")
	if not os.path.exists(profile_dir):
		os.mkdir(profile_dir)
		# FIXME error check
	if not os.path.exists(profile_dir):
		raise MyException("couldn't find/create " + str(profile_dir))
	return profile_dir

def get_credentials():
	'Return a tuple login,password or None if no credentials saved'
	profile_dir = get_profile_dir()
	credentials_file = os.path.join(profile_dir, "credentials")
	if not os.path.exists(credentials_file):
		return None
	with open(credentials_file, "r") as f:
		login = f.readline().rstrip('\n')
		password = base64.b64decode(f.readline().rstrip('\n'))
		return login, password

def save_credentials(login, password):
	'Save credentials into home file'
	profile_dir = get_profile_dir()
	with open(os.path.join(profile_dir, "credentials"), "w") as f:
		f.write(login + "\n")
		f.write(base64.b64encode(password) + "\n")
