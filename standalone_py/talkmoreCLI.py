#!/usr/bin/python

from talkmoreapi import *

import getpass

def login(tm):
    creds = get_credentials()
    while not tm.is_logged_in():
        if creds is None:
            print "You need to enter your login and password"
            login = raw_input("Enter your login: ")
            pwd = getpass.getpass("Enter your password: ")
            save_credentials(login,pwd)
            creds = login, pwd
        try:
            print "Logging in..."
            tm.login(creds[0], creds[1])
            if tm.is_logged_in():
                print "Logged in with user: " + str(tm.user)
                break
        except Exception, exc:
            print exc

        # force overriding. Note we shouldn't do that when the error isn't invalid credentials. FIXME detect invalid credentials from network issues
        creds = None
        print "Couldn't log in user " + login + ". Try again." + str(tm.is_logged_in())

def send_sms(tm):
    theNumbers = raw_input("Please enter the numbers. comma separated: ")
    theMsg = raw_input("Please write your message: ")
    telNbs = theNumbers.split(",") # splits the list of CSV into an array
    print "You are going to send an SMS to", telNbs, "with the message :\n", theMsg
    nb_messages = len(theMsg)/160+1
    if (nb_messages > 1):
        print "Your message is",len(theMsg),"chars long which is more than one SMS (",nb_messages,"SMSs to be precise)"
        if (raw_input("Do you really want to send it (y/n)? ")) != "y":
            print "Not sending the SMS..."
            continue
    print "Sending the SMS(s)..."
    tm.send_sms(telNbs, theMsg)
    print "SMS(s) sent!"

def logout(tm):
    print "Logging out"
    tm.logout()
    if not tm.is_logged_in():
        print "Logged out"
    else:
        print "Bye now :)"

def main():
    tm = Talkmore()

    login(tm)
    print "Balance: " + str(tm.balance) + " NOK"

    while raw_input("Do you want to send an SMS (y/n)? ") == "y":
        send_sms(tm)

    logout(tm)


if __name__ == "__main__":
    main()
