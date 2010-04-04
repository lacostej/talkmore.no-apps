from talkmore import Talkmore

import urlparse
import httplib2
import os
from email import message_from_string, message_from_file

HTTP_SRC_DIR = "./test/data/"

class MyHttpReplacement:
  """Build a stand-in for httplib2.Http that takes its response headers and bodies from files on disk"""

  def __init__(self, cache=None, timeout=None):
    self.hit_counter = {}

  def request(self, uri, method="GET", body=None, headers=None, redirections=5):
    path = urlparse.urlparse(uri)[2]
    fname = os.path.join(HTTP_SRC_DIR, path[1:])
    if not os.path.exists(fname):
      index = self.hit_counter.get(fname, 1)
      if os.path.exists(fname + "." + str(index)):
        self.hit_counter[fname] = index + 1
        fname = fname + "." + str(index)
    if os.path.exists(fname):
      f = file(fname, "r")
      response = message_from_file(f)
      f.close()
      body = response.get_payload()
      headers = httplib2.Response(response)
      return (headers, body)
    else:
      return (httplib2.Response({"status": "404"}), "")

  def add_credentials(self, name, password):
    pass


def setUp(self):
  self.old_httplib2 = httplib2.Http
  httplib2.Http = MyHttpReplacement

def tearDown(self):
  httplib2.Http = self.old_httplib2

def testParseBalance():
  testdata = "http://example.org/talkmore_balance"
  t = Talkmore()
  result = t.parse_balance_page(testdata)
  assert result == '130,23'
