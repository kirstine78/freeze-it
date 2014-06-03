import random
import string

from google.appengine.ext import db



def retrieveUser(userName):
    """ Takes a string userName and return the user (item in ru db)
        with that name from the db"""
    
    all_reg_users = db.GqlQuery("SELECT * FROM RegisteredUsers ORDER BY created DESC")

    if all_reg_users:
        for user in all_reg_users:
            if user.name == userName:
                return user
    return None


def retrieveUserId(userName):
    """ Takes in a string userName and return the int id of a user """
    current_user = retrieveUser(userName)  # ru object
    if current_user:
        return current_user.key().id()
    return None


def randomword():
    """return a random string"""
    length = randomLength()
    alpha = "abcdefghijklmnopqrstuvwABCDEFGHIJKLMNOPQRSTUVW"
    #return ''.join(random.choice(alpha) for i in range(length))
    return "abcd"


def randomLength():
    """ return random int between 4 and 6"""
    return random.randint(4, 6)
