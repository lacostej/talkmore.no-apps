#!/usr/bin/python

# for some reason, some users have issues with from xx import yy style
import wx
import wx.lib.delayedresult
print "Usign wx " + wx.VERSION_STRING

from talkmoreapi import *

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
		
		label4 = wx.StaticText(panel, -1, "Recipient(s):")
		label5 = wx.StaticText(panel, -1, "Message:")
		label6 = wx.StaticText(panel, -1, "Nb chararacters:")
		self.loginCtrl = wx.TextCtrl(panel, -1, creds[0])
		self.passwordCtrl = wx.TextCtrl(panel, -1, creds[1], style=wx.TE_PASSWORD)

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
		
		self.CreateStatusBar(3)
		self.SetStatusWidths([-1, 70, 100])
		self.SetStatusText("Balance:", 1)

		self.panel = panel
		
		sizer = wx.FlexGridSizer(6, 2, 6, 6)
		sizer.Add(label1)
		sizer.Add(self.loginCtrl)
		sizer.Add(label2)
		sizer.Add(self.passwordCtrl)

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

	def _updateStatus(self, status):
		print status
		self.SetStatusText(status, 0)

	def _updateBalanceConsumer(self, delayedResult):
		if wx.IsBusy():
			wx.EndBusyCursor()
		self.updateInfo.Enable(True)
		try:
			result = delayedResult.get()
		except Exception, exc:
			self._updateStatus("Result for %s raised exception: %s" % ("Update Balance", exc))
			return

		self.UpdateBalance()

	def _updateBalanceProducer(self):
		self.tm.update_balance()
	
	def UpdateBalance(self):
		print "Balance: " + str(self.tm.balance) + " NOK"
		self.SetStatusText(str(self.tm.balance) + " NOK", 2)
		
	def LoginIfNecessary(self):
		if not self.tm.is_logged_in():
			self.login.Enable(False)
			wx.BeginBusyCursor()
			wx.lib.delayedresult.startWorker(self._loginConsumer, self._loginProducer)

	def _loginProducer(self):
		self._updateStatus("Logging in...")
		login = self.loginCtrl.GetValue()
		password = self.passwordCtrl.GetValue()
		self.tm.login(login, password)
		if self.tm.is_logged_in():
			save_credentials(login, password)

	def _loginConsumer(self, delayedResult):
		if wx.IsBusy():
			wx.EndBusyCursor()
		try:
			result = delayedResult.get()
		except Exception, exc:
			self._updateStatus("Result for %s raised exception: %s" % ("Login", exc))
			self.login.Enable(True)
			return

		self._updateStatus("Logged in with user: " + str(self.tm.user))

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
			self._updateStatus("Logged out")

	def _logoutConsumer(self, delayedResult):
		if wx.IsBusy():
			wx.EndBusyCursor()
		try:
			result = delayedResult.get()
		except Exception, exc:
			self._updateStatus("Result for %s raised exception: %s" % ("Logout", exc))
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
			self._updateStatus("Result for %s raised exception: %s" % ("Send", exc))
			return

	def OnMessageUpdated(self, event):
		self.counterCtrl.SetValue(str(len(self.messageCtrl.GetValue())) + " char(s)")
		event.Skip()

class TalkmoreApp(wx.App):
    def OnInit(self):
		frame = MyFrame(None, -1, "Talkmore Client")
		frame.Show(True)
		self.SetTopWindow(frame)
		return True	

def main():
	app = TalkmoreApp(0)
	app.MainLoop()

if __name__ == "__main__":
	main()
