# see also goobook

import atom
import gdata.contacts
import gdata.contacts.service

class GoogleAddressBook():
	def __init__(self):
		self.gd_client = gdata.contacts.service.ContactsService()

	def login(self, email, password):
		self.gd_client.email = email
		self.gd_client.password = password
		self.gd_client.source = 'coffeebreaks-talkmore.no-py'
		self.gd_client.ProgrammaticLogin()

	def PrintFeed(self, feed):
		for i, entry in enumerate(feed.entry):
			print '\n%s %s' % (i+1, entry.title.text)
			if entry.content:
				print '    %s' % (entry.content.text)
			# Display the primary email address for the contact.
			for email in entry.email:
				if email.primary and email.primary == 'true':
					print '    %s' % (email.address)
			# Display the phone numbers
			if entry.phone_number:
				for phone in entry.phone_number:
					if phone:
						print '    %s' % (phone.text)
			# Show the contact groups that this contact is a member of.
			for group in entry.group_membership_info:
				print '    Member of group: %s' % (group.href)
			# Display extended properties.
			for extended_property in entry.extended_property:
				if extended_property.value:
					value = extended_property.value
				else:
					value = extended_property.GetXmlBlobString()
				print '    Extended Property - %s: %s' % (extended_property.name, value)

	def printContacts(self):
		query = gdata.contacts.service.ContactsQuery()
		query.max_results = 400
		feed = self.gd_client.GetContactsFeed(query.ToUri())
		self.PrintFeed(feed)


def main():
	ab = GoogleAddressBook()
	ab.login('jerome.lacoste@gmail.com', '.....')
	ab.printContacts()

if __name__ == "__main__":
	main()
