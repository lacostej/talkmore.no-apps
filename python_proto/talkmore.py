#!/usr/bin/python

import httplib2
from urllib import urlencode

#from elementtidy.TidyHTMLTreeBuilder import TidyHTMLTreeBuilder as TB
#import xml.etree.ElementTree as ET

from wx import *
print "Usign wx " + wx.VERSION_STRING

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



class MyFrame(wx.Frame):		
	tm = Talkmore()

	def __init__(self, parent, id, title):
		wx.Frame.__init__(self, parent, id, title)

		panel = wx.Panel(self, -1)
		label1 = wx.StaticText(panel, -1, "Mobile:")
		label2 = wx.StaticText(panel, -1, "Password:")
		label3 = wx.StaticText(panel, -1, "Balance:")
		
		label4 = wx.StaticText(panel, -1, "Recipient(s):")
		label5 = wx.StaticText(panel, -1, "Message:")
		label6 = wx.StaticText(panel, -1, "Nb chararacters:")
		self.loginCtrl = wx.TextCtrl(panel, -1, "40867729")
		self.passwordCtrl = wx.TextCtrl(panel, -1, "") # FIXME hide
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
		# FIXME async + status notification (sending... done)
		self.LoginIfNecessary()
	
	def OnLogoutPressed(self, event):
		# FIXME async + status notification (sending... done)
		self.LogoutIfNecessary()
		
	def OnUpdateInfoPressed(self, event):
		self.tm.update_balance()
		self.UpdateBalance()
	
	def UpdateBalance(self):
		print "Balance: " + str(self.tm.balance) + " NOK"
		self.balanceCtrl.SetValue(str(self.tm.balance) + " NOK")
		
	def LoginIfNecessary(self):
		if not self.tm.is_logged_in():
			self.tm.login(self.loginCtrl.GetValue(), self.passwordCtrl.GetValue())

			if self.tm.is_logged_in():
				print "Logged in with user: " + str(self.tm.user)

			self.loginCtrl.Enable(False)
			self.passwordCtrl.Enable(False)

			self.login.Enable(False)
			self.updateInfo.Enable(True)
			self.logout.Enable(True)
			self.send.Enable(True)

			self.UpdateBalance()

	def LogoutIfNecessary(self):
		if self.tm.is_logged_in():
			self.tm.logout()

			if not self.tm.is_logged_in():
				print "Logged out"

			self.loginCtrl.Enable(True)
			self.passwordCtrl.Enable(True)

			self.login.Enable(True)
			self.updateInfo.Enable(False)
			self.logout.Enable(False)
			self.send.Enable(False)

	def OnSendPressed(self, event):
		# FIXME async + status notification (sending... done)
	
		# FIXME support multiple recipients
		self.tm.send_sms([self.recipientsCtrl.GetValue()], self.messageCtrl.GetValue())
#		print "Fake sending..."

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
