import cgi
import re
import os
import webapp2
import jinja2
import random
import string
import hashlib


secret = "pollebolle"  #the secret is used for the hashed username that is send to the browser as cookie

def make_salt(): #the salt is used for the hashed password that is saved to the database
    return ''.join(random.choice(string.letters) for x in xrange(5))
    

def make_pw_hash(name, pw, salt=None):
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s|%s' % (h, salt)


def make_secure_val(val): # username_input passed in as param
    h = hashlib.sha256(val+secret).hexdigest()
    return '%s|%s' % (val, h)


def check_secure_val(secure_val):
    val = secure_val.split('|')[0]
    if secure_val == make_secure_val(val):
        return val


def valid_pw(name, pw, h):
    ###Your code here
    # h will look something like sghhgshgadjflafah|salt where salt is 5 random letters
    check = make_pw_hash(name, pw, h.split('|')[1]) # this will create a hash made with this exact salt

    return h == make_pw_hash(name, pw, check.split('|')[1])


def escape_html(s):
    return cgi.escape(s, quote = True)


USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
# Username: "^[a-zA-Z0-9_-]{3,20}$" Password: "^.{3,20}$" Email: "^[\S]+@[\S]+\.[\S]+$"
def valid_username(username):
    return USER_RE.match(username)


PASSWORD_RE = re.compile(r"^.{3,20}$")
def valid_password(password_entered):
    return PASSWORD_RE.match(password_entered)

EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")
def valid_email(email_entered):
    return EMAIL_RE.match(email_entered)

def password_match(password_a, password_b):
    return password_a == password_b
