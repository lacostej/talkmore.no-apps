#!/usr/bin/python

# https://bugs.launchpad.net/ubuntu/+source/wxwidgets2.8/+bug/555592

import wx
import wx.lib.delayedresult
print "Usign wx " + wx.VERSION_STRING

class MyFrame(wx.Frame):		
	def __init__(self, parent, id, title):
		wx.Frame.__init__(self, parent, id, title)

		panel = wx.Panel(self, -1)

		self.login = wx.Button(panel, label="Login")
		self.login.Bind(wx.EVT_BUTTON, self.OnLoginPressed)
		
		self.CreateStatusBar(1)

		self.panel = panel
		
		sizer = wx.FlexGridSizer(6, 2, 6, 6)

		sizer.Add(self.login)

		border = wx.BoxSizer()
		border.Add(sizer, 0, wx.ALL, 15)
		panel.SetSizerAndFit(border)
		self.Fit()
	
	def OnLoginPressed(self, event):
		# comment the next line and uncomment the next one removes the use of threading and apparently fixes the issue
		wx.lib.delayedresult.startWorker(self._loginConsumer, self._loginProducer)
#		self._updateStatus("Logging in...")

	def _updateStatus(self, status):
		self.SetStatusText(status, 0)

	def _loginProducer(self):
		self._updateStatus("Logging in...")

	def _loginConsumer(self, delayedResult):
		try:
			result = delayedResult.get()
		except Exception, exc:
			self._updateStatus("Result for %s raised exception: %s" % ("Login", exc))
			return

		self._updateStatus("Logged in...")

class TalkmoreApp(wx.App):
    def OnInit(self):
		frame = MyFrame(None, -1, "GUI")
		frame.Show(True)
		self.SetTopWindow(frame)
		return True	

if __name__ == "__main__":
	app = TalkmoreApp(0)
	app.MainLoop()
