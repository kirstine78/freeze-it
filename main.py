#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#########################
#                       #
#   Freeze it           #
#                       #
#########################

import validation
import passwordValid
import dataFunctions
import cgi
import re
import os
import webapp2
import jinja2
import random
import string
import hashlib
import time
import logging
from datetime import datetime
from datetime import date
from google.appengine.ext import db


template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=True)

list_of_units = ["", "gram", "kilo", "liter", "piece"]

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)
    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)
    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))
        

class FoodItem(db.Model): # abbreviated 'FI'
    description = db.StringProperty(required = True)  # food description   
    note = db.StringProperty(required = False)  # a string with notes, fx "30 gram"
    expiry = db.DateProperty(required = False)  # expiry date for food yyyy-mm-dd. Not a string.
    exp_with_month_letters = db.StringProperty(required = False)  # "27-Apr-2014" format

    days_in_freezer = db.IntegerProperty(required = False)  # counting days from being added to freezer

    is_expired = db.BooleanProperty(required=False)  # is True if exp. date has been exceeded
    is_soon_to_expire = db.BooleanProperty(required=False)  # is True if exp. date is within 5 days
    days_before_exp =  db.IntegerProperty(required = False)  # counting days before expiry
    
    created = db.DateTimeProperty(auto_now_add = True)  # more precise than added_date, when sorting
    added_date = db.DateProperty(auto_now_add = True)  # date the food is added to freezer yyyy-mm-dd. Not a string.

    fk_registered_user_id = db.IntegerProperty(required=True)  # the id of user
    #last_modified = db.DateTimeProperty(auto_now = True)


class RegisteredUsers(db.Model):  #  --> ru
    name = db.StringProperty(required = True)
    password_hashed = db.StringProperty(required = True)  # (name + pw + salt) hexdigested and then pipe salt with format "hexdigestedValue|salt"
    email = db.StringProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)




# '/signup', SignupHandler
class SignupHandler(Handler):
        
    def write_form(self, a_signup_name="", a_username_error="", a_password_error="", a_verify_error="",
                   a_email="", a_email_error="", a_verify_email="", a_verify_email_error=""):
        
        self.render("signupForFreezeIt.html", signup_username=a_signup_name, username_error=a_username_error,
                    password_error=a_password_error, verify_error=a_verify_error,
                    email=a_email, email_error=a_email_error, email_verify=a_verify_email, verify_email_error=a_verify_email_error)

        
    def get(self):
        self.write_form()


    def post(self):
        #secure_value # this is the (name + pw + salt) hexdigested and then pipe salt with format "hexdigestedValue|salt"
        
        username_input = self.request.get('username')
        password_input = self.request.get('password')
        verify_input = self.request.get('verify')
        email_input = self.request.get('email')
        verify_email_input = self.request.get('verify_email')

        escaped_username_input = passwordValid.escape_html(username_input)
        escaped_email_input = passwordValid.escape_html(email_input)
        
        escaped_verify_email_input = passwordValid.escape_html(verify_email_input)

        is_valid_username = passwordValid.valid_username(username_input)
        is_valid_password = passwordValid.valid_password(password_input)        
        
        if len(email_input) > 0:
            is_valid_email = passwordValid.valid_email(email_input)
        else:
            is_valid_email = False
            

        does_password_match = passwordValid.password_match(password_input, verify_input)
        does_email_match = passwordValid.email_match(email_input, verify_email_input)
        
        final_username_error=""
        final_password_error=""
        final_verify_error=""
        final_email_error=""
        final_verify_email_error=""

        if not (is_valid_username):
            final_username_error="Invalid username"
        if not (is_valid_password):
            final_password_error="Invalid password"
        if not (does_password_match):
            final_verify_error="Password doesn't match"
        if not (is_valid_email):
            final_email_error="Invalid e-mail"
        if not (does_email_match):
            final_verify_email_error="E-mail doesn't match"

        if is_valid_username and is_valid_password and does_password_match and is_valid_email and does_email_match:
            
            # check if user already exist
            user_already_exists = False
           
            existing_user = dataFunctions.retrieveUser(username_input)
            
            if existing_user:
                user_already_exists = True
                
            if user_already_exists:
                #write error message out
                final_username_error="User already exist"
                self.write_form(escaped_username_input, final_username_error,
                                final_password_error, final_verify_error,
                                escaped_email_input, final_email_error,
                                escaped_verify_email_input, final_verify_email_error)
                    
            else:  # ok to register new user

                # username_and_password = username_input + password_input
                secure_password = passwordValid.make_pw_hash(username_input, password_input)  # the function returns hash|salt
                secure_username = passwordValid.make_secure_val(username_input) # the function returns username_input|hash

               
                ru = RegisteredUsers(name = username_input, password_hashed = secure_password, email = email_input) # save the hashed password in database
                ru.put()
                time.sleep(0.1)  # to delay so db table gets displayed correct
                self.response.headers.add_header('Set-Cookie', 'user_id=%s; Path=/' %str(secure_username))#sending secure_username back to browser
                self.redirect("/frontpage")
        else:
            # check if user already exist
            user_already_exists = False
           
            all_reg_users = db.GqlQuery("SELECT * FROM RegisteredUsers ORDER BY created DESC")

            if all_reg_users:
                for users in all_reg_users:
                    if users.name == username_input:
                        user_already_exists = True
                        break
                
            if user_already_exists:
                #write error message out
                final_username_error="User already exist"
                final_password_error=""
                final_email_error=""
                
            self.write_form(escaped_username_input, final_username_error,
                            final_password_error, final_verify_error,
                            escaped_email_input, final_email_error,
                            escaped_verify_email_input, final_verify_email_error)

# '/', LoginHandler
class LoginHandler(Handler):
    def write_form(self, a_username="", an_invalid_error=""):
        self.render("loginToFreezeIt.html", the_login_username=a_username, error_login=an_invalid_error)

        
    def get(self):
        self.write_form()


    def post(self):
        login_username_input = self.request.get('login_username')
        login_password_input = self.request.get('login_password')
        checkbox_stay_loggedIn = self.request.get('stay_logged_in_clicked')

        #check if username exists
        user_already_exists = False
        all_reg_users = db.GqlQuery("SELECT * FROM RegisteredUsers ORDER BY created DESC")

        if all_reg_users:
            for users in all_reg_users:
                if users.name == login_username_input:
                    user_already_exists = True
                    the_user_hash = users.password_hashed
                    break
            if user_already_exists:
                #check if password is correct
                if passwordValid.valid_pw(login_username_input, login_password_input, the_user_hash):
                    secure_username = passwordValid.make_secure_val(login_username_input) # return login_username_input|hash
                    self.response.headers.add_header('Set-Cookie', 'user_id=%s; Path=/' %str(secure_username))

                    # if checkbox_stay_loggedIn:
                        # make sure to set cookie expire to never
                    # else:
                        # cookie expire when???


                    
                    self.redirect("/frontpage")
                else:
                    self.loginError()
            else:
                self.loginError()
        else:
            self.loginError()

    def loginError(self):
        error_log_in = "Invalid login"
        self.write_form("", error_log_in)

        
# '/logout', LogoutHandler 
class LogoutHandler(Handler):
    def get(self):
        #set cookie value to 'empty'
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')
        self.response.headers.add_header('Set-Cookie', 'sort_code=; Path=/')

        #then redirect to '/' Login
        self.redirect("/")



# '/forgotten', ForgottenHandler
class ForgottenHandler(Handler):
    def render_forgotten(self, name_error=""):
        self.render("forgotPassword.html", user_name_error=name_error)
        
    def get(self):
        self.render_forgotten()

    def post(self):
        # check if valid username
        # if valid:
            # change password in db
            # send new password to email
            # then redirect to sentpassword.
            #self.redirect("/sentpassword")
        # else:
            # give user_name_error and re render page
            # error = "invalid username"
            # self.render_forgotten(name_error=error):

        
        self.redirect("/sentpassword")
        



# '/sentpassword', SentPasswordHandler
class SentPasswordHandler(Handler):
    def get(self):
        self.render("sendPassword.html")

# ('/profile', ProfileHandler)
class ProfileHandler(Handler):
    def get(self):
        user_id_cookie_value = self.request.cookies.get('user_id')# username_input|hash (cookie)

        if user_id_cookie_value:

            username = passwordValid.check_secure_val(user_id_cookie_value)
            
            # if valid cookie:
            if username:
                the_RU = dataFunctions.retrieveUser(username)
                
                if the_RU:
                    email_RU = the_RU.email
                    self.render("profile.html", a_name=username, an_email=email_RU)
                else:
                    self.redirect("/")

            else:  # invalid
                self.redirect("/")
        else:  # None
                self.redirect("/")
        
    
# '/editemail', EditEmailHandler
class EditEmailHandler(Handler):
    def get(self):
        self.render("editEmail.html")

    def post(self):
        new_email = self.request.get("email")
        new_verify_email = self.request.get("verify_email")
        a_password = self.request.get("password")

        user_id_cookie_value = self.request.cookies.get('user_id')  # username_input|hash (cookie)

        if user_id_cookie_value:

            username = passwordValid.check_secure_val(user_id_cookie_value)
            
            if username:
                the_RU = dataFunctions.retrieveUser(username)

                if the_RU:
                    escaped_email_input = passwordValid.escape_html(new_email)
                    escaped_verify_email_input = passwordValid.escape_html(new_verify_email)
                    
                    if len(new_email) > 0:
                        is_valid_email = passwordValid.valid_email(new_email)
                    else:
                        is_valid_email = False

                    does_email_match = passwordValid.email_match(new_email, new_verify_email)

                    is_password_correct = passwordValid.valid_pw(the_RU.name, a_password, the_RU.password_hashed)
                    
                    final_password_error=""
                    final_email_error=""
                    final_verify_email_error=""

                    if not (is_valid_email):
                        final_email_error="Invalid e-mail"
                    if not (does_email_match):
                        final_verify_email_error="E-mail doesn't match"
                    if not (is_password_correct):
                        final_password_error="Invalid password"

                    if is_valid_email and does_email_match and is_password_correct:
                        the_RU.email = new_email
                        the_RU.put()
                        time.sleep(0.1)  # to delay so db table gets displayed correct
                        self.render("profile.html", a_name=username, an_email=new_email,
                                    changed_message="Your e-mail has been changed")

                    else:
                        self.render("editEmail.html", email=escaped_email_input, email_error=final_email_error,
                                    email_verify=escaped_verify_email_input, verify_email_error=final_verify_email_error,
                                    password_error=final_password_error)
                    
                else: # the_RU is None
                    self.redirect("/logout")

            else: # username is None
                self.redirect("/logout")
                
        else:  # user_id_cookie_value is None
                self.redirect("/logout")
        

# '/editpassword', EditPasswordHandler
class EditPasswordHandler(Handler):
    def get(self):
        self.render("editPassword.html")

    def post(self):
        new_password = self.request.get("new_password")
        new_verify_password = self.request.get("verify_new_password")
        a_password = self.request.get("old_password")

        user_id_cookie_value = self.request.cookies.get('user_id')  # username_input|hash (cookie)

        if user_id_cookie_value:

            username = passwordValid.check_secure_val(user_id_cookie_value)
            
            if username:
                the_RU = dataFunctions.retrieveUser(username)

                if the_RU:
                    is_valid_new_password = passwordValid.valid_password(new_password)
                    does_new_passwords_match = passwordValid.password_match(new_password, new_verify_password)

                    is_password_correct = passwordValid.valid_pw(the_RU.name, a_password, the_RU.password_hashed)
                    
                    final_new_password_error=""
                    final_new_verify_password_error=""
                    final_old_password_error=""

                    if not (is_valid_new_password):
                        final_new_password_error="Invalid password"
                    if not (does_new_passwords_match):
                        final_new_verify_password_error="Password doesn't match"
                    if not (is_password_correct):
                        final_old_password_error="Invalid password"

                    if is_valid_new_password and does_new_passwords_match and is_password_correct:
                        the_RU.password_hashed = passwordValid.make_pw_hash(username, new_password)  # the function returns hash|salt
                        the_RU.put()
                        time.sleep(0.1)  # to delay so db table gets displayed correct
                        self.render("profile.html", a_name=username, an_email=the_RU.email,
                                    changed_message="Your password has been changed")

                    else:
                        self.render("editPassword.html", new_password_error=final_new_password_error,
                                    verify_error=final_new_verify_password_error,
                                    password_error=final_old_password_error)
                    
                else: # the_RU is None
                    self.redirect("/logout")

            else: # username is None
                self.redirect("/logout")
                
        else:  # user_id_cookie_value is None
                self.redirect("/logout")
                
            

# handler for '/frontpage', FrontPage
class FrontPage(Handler):
    def render_front(self, a_username, parameter="" ):  # 'youngest' created date shown first by default
        current_user_id = dataFunctions.retrieveUserId(a_username)  # an int
        all_food_items = db.GqlQuery("SELECT * FROM FoodItem WHERE fk_registered_user_id=%s ORDER BY %s" %(current_user_id, parameter))

        counter = 0  # keep track of amount of iteration in for loop
        
        # loop through all items and set is_expired
        for item in all_food_items:
            counter = counter + 1
            if item.expiry:
                if date.today() >= item.expiry:
                    item.is_expired = True
                # check if expiry soon happens and update days_before_exp
                item.is_soon_to_expire, item.days_before_exp = validation.expires_soon(item.expiry)
                item.exp_with_month_letters = validation.convert_to_letter_month(item.expiry)
            else: # no exp date
                item.is_expired = False
                item.is_soon_to_expire = False
                item.days_before_exp = None

            item.days_in_freezer = validation.days_in_freezer(item.added_date)
            
            item.put() 

        time.sleep(0.1)  # to delay so db table gets displayed correct

        if counter == 0:  # checks if there is any items in database
            all_food_items = None

        logging.debug("all_food_items = " + str(type(all_food_items)))

        # toggle function

        # toggle variables
        descrip_a_d="ASC"
        days_left_a_d="ASC"
        #exp_a_d="ASC"
        days_frozen_a_d="DESC"

        # decide which sorted code (1-7) you pass into html and also update variables.

        code = validation.get_number_code(parameter)  #return an int (1-7) based on which parameter passed in

        # check if any toggle variables must be updated
        if code == 2:  # parameter=="description ASC"
            descrip_a_d="DESC"
        elif code == 5:  # parameter=="days_in_freezer DESC"
            days_frozen_a_d="ASC"
        elif code == 6:  # parameter=="days_before_exp ASC"
            days_left_a_d="DESC"

        self.response.headers.add_header('Set-Cookie', 'sort_code=%s; Path=/' %str(code))
            
        self.render("frontpage.html", username=a_username,
                    food_items = all_food_items,
                    descr_asc_desc=descrip_a_d,
                    days_left_asc_desc=days_left_a_d,
                    days_frozen_asc_desc=days_frozen_a_d,
                    look_number=code) # passing contents into the html file
     
        
    def get(self):

        user_id_cookie_value = self.request.cookies.get('user_id')# username_input|hash (cookie)

        if user_id_cookie_value:

            username = passwordValid.check_secure_val(user_id_cookie_value)
            
            
            # if valid cookie:
            if username:

                id_descript = self.request.get("id_description")  # if header link 'Description' is clicked 'ASC' or 'DESC' will be assigned
                id_days_left = self.request.get("id_days_to_exp")  # if header link 'Days to exp' is clicked 'ASC' or 'DESC' will be assigned
                id_days_in_freezer = self.request.get("id_days_frozen")  # if header link 'Days in freezer' is clicked 'ASC' or 'DESC' will be assigned

                if id_descript: # 'Description' was clicked
                    self.render_front(username, parameter="description %s" %id_descript)
                elif id_days_left:  # 'Days to exp' was clicked
                    self.render_front(username, parameter="days_before_exp %s" %id_days_left)  # the 'oldest' shown first
                elif id_days_in_freezer:  # 'Days in freezer' was clicked
                    self.render_front(username, parameter="days_in_freezer %s" %id_days_in_freezer)
                else:
                    sort_code = self.request.cookies.get('sort_code')# look_number (cookie)
                    if sort_code:
                        sort_criteria = validation.get_param(sort_code)
                    else:
                        sort_criteria = "created DESC"
                    self.render_front(username, parameter=sort_criteria)

            else:  # invalid
                self.redirect("/")
        else:  # None
                self.redirect("/")
        
        

    def post(self):
        user_id_cookie_value = self.request.cookies.get('user_id')# username_input|hash (cookie)

        if user_id_cookie_value:

            user_id_cookie_valid = passwordValid.check_secure_val(user_id_cookie_value)
            
            # get request data
          
            # id data (which check boxes has user checked) put in a variable
            list_of_id_checked = self.request.get_all("delete")  # returns a list of id strings

            # delete button data (if delete button clicked, list will have 1 item else no item in list)
            one_item_delete_button_list = self.request.get_all("delete_button")  # there is only 1 delete_button

            if len(one_item_delete_button_list) == 1:  # delete button is clicked
                # loop through list_of_id_checked and remove matches from db
                for an_id in list_of_id_checked:
                    # find the item with the specific id in db
                    match = FoodItem.get_by_id(int(an_id))
                    # remove the item
                    if match:
                        FoodItem.delete(match)
                time.sleep(0.1)  # to delay so db table gets displayed correct

            sort_code = self.request.cookies.get('sort_code')# look_number (cookie)
            if sort_code:
                sort_criteria = validation.get_param(sort_code)
            else:
                sort_criteria = "created DESC"
            self.render_front(user_id_cookie_valid, parameter=sort_criteria)
                    
        else:
            self.redirect("/signup")
      


# handler for '/food'
class FoodPage(Handler):
    def render_foodPage(self, f_d_content, f_d_error, note, date_error,
                        exp, headline, change_butt, passive_butt, item_ID,
                        create_date, add_message, the_user_name):
        
        self.render("food.html", food_description_content=f_d_content, food_description_error=f_d_error,
                    note_content=note,
                    date_error=date_error,
                    exp_content = exp,
                    headline=headline,
                    change_button=change_butt, passive_button=passive_butt,
                    item_id=item_ID,
                    created_date=create_date,
                    add_message=add_message,
                    username=the_user_name) # sorted_mode_code=sorting_mode_code

        
    def get(self):
        user_id_cookie_value = self.request.cookies.get('user_id')# username_input|hash (cookie)

        if user_id_cookie_value:

            username = passwordValid.check_secure_val(user_id_cookie_value)
            
            # if valid cookie:
            if username:
                an_id = self.request.get("id")  # if any foodItem description is clicked, there is an_id
        
                if an_id:  # means there is an item to edit
                    specific_item = FoodItem.get_by_id(int(an_id))  # get the item with the specific id (an_id)

                    # check if there is a DateProperty (expiry) yyyy-mm-dd. It is NOT a string
                    if specific_item.expiry:
                        # create a string in format "dd-mm-yyyy" of the DateProperty yyyy-mm-dd 
                        date_html_format = validation.convert_DateProperty_to_str_dash(specific_item.expiry)

                    else:  # no expiry date for this item
                        date_html_format = ""
                        
                    # set values for specific item
                    a_food_description_content=specific_item.description
                    a_note_content=specific_item.note
                    a_exp_content = date_html_format
                    a_headline="Edit food item"
                    a_change_button="Submit Changes"
                    a_passive_button="Cancel"
                    a_item_id=an_id
                    # create a string in format "dd-mm-yyyy" of the DateProperty yyyy-mm-dd 
                    a_date_created = validation.convert_DateProperty_to_str_dash(specific_item.added_date)
                    
                    f_d_err=""
                    date_err=""
                    add_msg=""


                else:  # no id, set values to a blank "food.html"
                    a_food_description_content=""
                    a_note_content=""
                    a_exp_content = ""
                    a_headline="Add food to Freezer"
                    a_change_button="Add Item"
                    a_passive_button="Return to Frontpage"
                    a_item_id=""
                    a_date_created = ""
                    
                    f_d_err=""
                    date_err=""
                    add_msg=""

                logging.debug("description = " + a_food_description_content)

                # render "food.html" with correct params!
                self.render_foodPage(a_food_description_content, f_d_err, a_note_content, date_err,
                                a_exp_content, a_headline, a_change_button, a_passive_button, a_item_id,
                                a_date_created, add_msg, username)


            else:  # invalid
                self.redirect("/")
        else:  # None
                self.redirect("/")


    def post(self):
        # data that user has entered
        a_food_description = self.request.get("food_description").strip()
        a_note = self.request.get("note").strip()
        an_exp_date_str = self.request.get("expiry_date")  # a string in format "dd-mm-yyyy"
        an_item_id = self.request.get("item_ID")  # this is a string "455646501654613" format
        
        # create objects of class InfoEntered. NB this is not an FoodItem object!!!
        obj_food = validation.is_food_item_valid(a_food_description) # object is created inside is_food_item_valid()
        obj_exp_date = validation.is_exp_date_valid(an_exp_date_str, an_item_id)  # object is created inside is_exp_date_valid()
                      
        # create list for the objects and append them
        obj_list = []
        
        obj_list.append( obj_food )
        obj_list.append( obj_exp_date )
               
        # check if all 'object.validation' are True; is so, a foodItem can be added to db
        if validation.are_all_validation_true(obj_list):
            # check if there is an expiry date entered, if so convert to yyyy-mm-dd
            if an_exp_date_str:
                date_valid = obj_exp_date.get_validation_info()  # returns a Boolean
                if date_valid:
                    # create from string a DateProperty with format yyyy-mm-dd 
                    an_exp_date = datetime.strptime(an_exp_date_str+" 12:00", "%d-%m-%Y %H:%M").date()
            else:
                an_exp_date = None

            # make first letter upper case
            a_food_description = validation.upper_case(a_food_description)

            # check if there is an_item_id to see whether to 'update' or 'create new item in db'
            if an_item_id:  # update already excisting item
                logging.debug("item id: " + an_item_id) 
                # get the specific item
                the_item = FoodItem.get_by_id(int(an_item_id))  # get the item with the specific id (an_item_id)
                # update
                the_item.description = a_food_description
                the_item.note = a_note
                the_item.expiry = an_exp_date
                 
                the_item.put()
                time.sleep(0.1)  # to delay so db table gets displayed correct

                
                
                self.redirect("/frontpage")  # tells the browser to go to '/' and the response is empty
                
            else: # no id 'an_item_id' (a new food is being added)
                logging.debug("No item id" )
                user_id_cookie_value = self.request.cookies.get('user_id')# username_input|hash (cookie)

                if user_id_cookie_value:

                    username = passwordValid.check_secure_val(user_id_cookie_value)

                    if username:

                        current_user_id = dataFunctions.retrieveUserId(username)  # an int
                        
                        # create item in db
                        FI = FoodItem(description = a_food_description,
                                      note = a_note,
                                      expiry = an_exp_date,
                                      is_expired=False,
                                      fk_registered_user_id=current_user_id)
                        FI.put()
                        id_for_FI = str(FI.key().id())
                        time.sleep(0.5)  # to delay so db table gets displayed correct

                        a_food_description_content=""
                        a_note_content=""
                        a_exp_content = ""
                        a_headline="Add food to Freezer"
                        a_change_button="Add Item"
                        a_passive_button="Return to Frontpage"
                        a_item_id=""
                        a_date_created = ""
                        
                        f_d_err=""
                        date_err=""
                        add_msg="Your Food Item was successfully added"

                        
                        self.response.headers.add_header('Set-Cookie', 'sort_code=; Path=/')


                        self.render_foodPage(a_food_description_content, f_d_err, a_note_content, date_err,
                                             a_exp_content, a_headline, a_change_button, a_passive_button, a_item_id,
                                             a_date_created, add_msg, username)
                            
                    else:
                        self.redirect("/logout")
                        
                else:
                    self.redirect("/logout")
                
            
             
        # else re-render 'food.html' with the error messages
        else:
            user_id_cookie_value = self.request.cookies.get('user_id')# username_input|hash (cookie)

            if user_id_cookie_value:

                username = passwordValid.check_secure_val(user_id_cookie_value)

                if username:
                    # decide which params to pass based on 'add' or 'edit'
                    if an_item_id: # edit version
                        specific_item = FoodItem.get_by_id(int(an_item_id))  # get the item with the specific id (an_item_id)

                        the_headline="Edit food item"
                        the_change_button="Submit Changes"
                        the_passive_button="Cancel"
                        the_item_id=an_item_id

                        # create a string in format "dd-mm-yyyy" from the DateProperty yyyy-mm-dd 
                        a_date_created = validation.convert_DateProperty_to_str_dash(specific_item.added_date)

                        f_d_err = obj_food.get_error_msg()
                        date_err = obj_exp_date.get_error_msg()
                        add_msg=""


                    else:  # add version
                        the_headline="Add food to Freezer"
                        the_change_button="Add Item"
                        the_passive_button="Return to Frontpage"
                        the_item_id=""  # ok with empty str. when checking if "" that is False.... But can't use None to put in here...
                        a_date_created = ""

                        f_d_err = obj_food.get_error_msg()
                        date_err = obj_exp_date.get_error_msg()
                        add_msg=""


                    
                    self.render_foodPage(a_food_description, f_d_err, a_note, date_err, an_exp_date_str, the_headline,
                                         the_change_button, the_passive_button, the_item_id, a_date_created, add_msg, username)
                else:
                    self.redirect("/logout")
                    
            else:
                self.redirect("/logout")
          

            

app = webapp2.WSGIApplication([('/', LoginHandler),
                               ('/signup', SignupHandler),
                               ('/logout', LogoutHandler),
                               ('/forgotten', ForgottenHandler),
                               ('/sentpassword', SentPasswordHandler),
                               ('/profile', ProfileHandler),
                               ('/editpassword', EditPasswordHandler),
                               ('/editemail', EditEmailHandler),
                               ('/frontpage', FrontPage),
                               ('/food', FoodPage)], debug=True)
