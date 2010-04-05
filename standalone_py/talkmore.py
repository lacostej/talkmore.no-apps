#!/usr/bin/python

# requires python-wxgtk2.8 on Debian/Ubuntu
import httplib2
from urllib import urlencode

# for some reason, some users have issues with from xx import yy style
import wx
import wx.lib.delayedresult
print "Usign wx " + wx.VERSION_STRING

import os
import base64
import re
#import pickle

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
	return profile_dir

def get_credentials():
	'Return a tuple login,password or None if no credentials saved'
	profile_dir = get_profile_dir()
	f = open(os.path.join(profile_dir, "credentials"), "r")
	login = f.readline().rstrip('\n')
	password = base64.b64decode(f.readline().rstrip('\n'))
	return login, password
#	res = pickle.load(f)
#	f.close()
#	return res[0], base64.b64decode(res[1])

def save_credentials(login, password):
	'Save credentials into home file'
	profile_dir = get_profile_dir()
	f = open(os.path.join(profile_dir, "credentials"), "w")
	#pickle.dump([login, base64.b64encode(password)], f)
	f.write(login + "\n")
	f.write(base64.b64encode(password) + "\n")
	f.close()

class MyFrame(wx.Frame):		
	tm = Talkmore()

	def __init__(self, parent, id, title):
		wx.Frame.__init__(self, parent, id, title)

		creds = get_credentials()
		if creds is None:
			creds = ["", ""]

		panel = wx.Panel(self, -1)
		label1 = wx.StaticText(panel, -1, "Mobile:")
		label2 = wx.StaticText(panel, -1, "Password:")
		label3 = wx.StaticText(panel, -1, "Balance:")
		
		label4 = wx.StaticText(panel, -1, "Recipient(s):")
		label5 = wx.StaticText(panel, -1, "Message:")
		label6 = wx.StaticText(panel, -1, "Nb chararacters:")
		self.loginCtrl = wx.TextCtrl(panel, -1, creds[0])
		self.passwordCtrl = wx.TextCtrl(panel, -1, creds[1], style=wx.TE_PASSWORD)
		self.balanceCtrl = wx.TextCtrl(panel, -1, "", style=wx.TE_READONLY)

		self.login = wx.Button(panel, label="Login")
		self.login.Bind(wx.EVT_BUTTON, self.OnLoginPressed)
		self.updateInfo = wx.Button(panel, label="Update Info")
		self.updateInfo.Bind(wx.EVT_BUTTON, self.OnUpdateInfoPressed)
		
		self.recipientsCtrl = wx.TextCtrl(panel, -1, "", size=[400, 25])
		self.messageCtrl = wx.TextCtrl(panel, -1, "", size=[400, 100], style = wx.TE_MULTILINE | wx.TE_RICH)
		self.messageCtrl.Bind(wx.EVT_KEY_DOWN, self.OnMessageUpdated)
		self.counterCtrl = wx.TextCtrl(panel, -1, "", style=wx.TE_READONLY)

		self.send = wx.Button(panel, label="Send")
		self.send.Bind(wx.EVT_BUTTON, self.OnSendPressed)
		self.logout = wx.Button(panel, label="Logout")
		self.logout.Bind(wx.EVT_BUTTON, self.OnLogoutPressed)

		self.updateInfo.Enable(False)
		self.send.Enable(False)
		self.logout.Enable(False)
		
		self.panel = panel
		
		sizer = wx.FlexGridSizer(6, 2, 6, 6)
		sizer.Add(label1)
		sizer.Add(self.loginCtrl)
		sizer.Add(label2)
		sizer.Add(self.passwordCtrl)
		sizer.Add(label3)
		sizer.Add(self.balanceCtrl)

		sizer.Add(self.login)
		sizer.Add(self.updateInfo)

		sizer.Add(label4)
		sizer.Add(self.recipientsCtrl)
		sizer.Add(label5)
		sizer.Add(self.messageCtrl)
		sizer.Add(label6)
		sizer.Add(self.counterCtrl)
		sizer.Add(self.send)
		sizer.Add(self.logout)
		
		border = wx.BoxSizer()
		border.Add(sizer, 0, wx.ALL, 15)
		panel.SetSizerAndFit(border)
		self.Fit()
	
	def OnLoginPressed(self, event):
		self.LoginIfNecessary()
	
	def OnLogoutPressed(self, event):
		self.LogoutIfNecessary()
		
	def OnUpdateInfoPressed(self, event):
		self.updateInfo.Enable(False)
		wx.BeginBusyCursor()
		wx.lib.delayedresult.startWorker(self._updateBalanceConsumer, self._updateBalanceProducer)

	def _updateBalanceConsumer(self, delayedResult):
		if wx.IsBusy():
			wx.EndBusyCursor()
		self.updateInfo.Enable(True)
		try:
			result = delayedResult.get()
		except Exception, exc:
			print "Result for %s raised exception: %s" % ("Update Balance", exc)
			return

		self.UpdateBalance()

	def _updateBalanceProducer(self):
		self.tm.update_balance()
	
	def UpdateBalance(self):
		print "Balance: " + str(self.tm.balance) + " NOK"
		self.balanceCtrl.SetValue(str(self.tm.balance) + " NOK")
		
	def LoginIfNecessary(self):
		if not self.tm.is_logged_in():
			self.login.Enable(False)
			wx.BeginBusyCursor()
			wx.lib.delayedresult.startWorker(self._loginConsumer, self._loginProducer)

	def _loginProducer(self):
		print "Logging in..."
		login = self.loginCtrl.GetValue()
		password = self.passwordCtrl.GetValue()
		self.tm.login(login, password)
		if self.tm.is_logged_in():
			print "Logged in with user: " + str(self.tm.user)
			save_credentials(login, password)

	def _loginConsumer(self, delayedResult):
		if wx.IsBusy():
			wx.EndBusyCursor()
		try:
			result = delayedResult.get()
		except Exception, exc:
			print "Result for %s raised exception: %s" % ("Login", exc)
			self.login.Enable(True)
			return

		self.loginCtrl.Enable(False)
		self.passwordCtrl.Enable(False)

		self.updateInfo.Enable(True)
		self.logout.Enable(True)
		self.send.Enable(True)

		self.UpdateBalance()

	def LogoutIfNecessary(self):
		if self.tm.is_logged_in():
			self.logout.Enable(False)
			wx.BeginBusyCursor()
			wx.lib.delayedresult.startWorker(self._logoutConsumer, self._logoutProducer)

	def _logoutProducer(self):
		self.tm.logout()
		if not self.tm.is_logged_in():
			print "Logged out"

	def _logoutConsumer(self, delayedResult):
		if wx.IsBusy():
			wx.EndBusyCursor()
		try:
			result = delayedResult.get()
		except Exception, exc:
			print "Result for %s raised exception: %s" % ("Logout", exc)
			self.logout.Enable(True)
			return

		self.loginCtrl.Enable(True)
		self.passwordCtrl.Enable(True)

		self.login.Enable(True)
		self.updateInfo.Enable(False)
		self.send.Enable(False)

	def OnSendPressed(self, event):
		wx.lib.delayedresult.startWorker(self._sendConsumer, self._sendProducer)

	def _sendProducer(self):
		self.send.Enable(False)
		wx.BeginBusyCursor()
		to_numbers = re.findall(r'\w+', self.recipientsCtrl.GetValue())
		self.tm.send_sms(to_numbers, self.messageCtrl.GetValue())
#		print "Fake sending..."

	def _sendConsumer(self, delayedResult):
		if wx.IsBusy():
			wx.EndBusyCursor()
		self.send.Enable(True)
		try:
			result = delayedResult.get()
		except Exception, exc:
			print "Result for %s raised exception: %s" % ("Send", exc)
			return

	def OnMessageUpdated(self, event):
		self.counterCtrl.SetValue(str(len(self.messageCtrl.GetValue())) + " char(s)")
		event.Skip()

class TalkmoreApp(wx.App):
    def OnInit(self):
		frame = MyFrame(None, -1, "Talkmore Client")
        
		frame.Show(True)

		self.SetTopWindow(frame)

		# Return a success flag
		return True	

def main():
	app = TalkmoreApp(0)
	app.MainLoop()

if __name__ == "__main__":
	main()
