
import logging
from google.appengine.api import mail

def sendEmail(emailAddress, password):
    logging.debug("email address is %s" %emailAddress)
    admin_email = "noreply@freeze-it.appspotmail.com"
    msg_body = "Hi, here is your new password for 'Freeze it': %s" %password

    message = mail.EmailMessage(sender=admin_email, subject="New Password")

    message.to = emailAddress
    message.body = msg_body

    message.send()
