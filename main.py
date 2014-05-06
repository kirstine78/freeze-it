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
import info_entered
import os
import webapp2
import jinja2
import time
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
    measure_unit = db.StringProperty(required = False) # gram, kilo etc
    amount = db.StringProperty(required = False)  # a number
    expiry = db.DateProperty(required = False)  # expiry date for food
    days_before_exp =  db.IntegerProperty(required = False) 
    
    is_expired = db.BooleanProperty(required=False)  # is True if exp. date has been exceeded
    is_soon_to_expire = db.BooleanProperty(required=False)  # is True if exp. date is within x days
    
    created = db.DateTimeProperty(auto_now_add = True)  # more precise than added_date, when sorting    
    added_date = db.DateProperty(auto_now_add = True)  # date the food is added to freezer 
    last_modified = db.DateTimeProperty(auto_now = True)


    


# handler for '/'
class Frontpage(Handler):
    def render_front(self, parameter="created DESC"):  # 'youngest' created date shown first by default

        
        all_food_items = db.GqlQuery("SELECT * FROM FoodItem ORDER BY %s" %parameter)
        # if you only wanna display the 10 latest: "SELECT * FROM Content ORDER BY created DESC limit 10"

        
        # loop through all items and set is_expired
        for item in all_food_items:
            if item.expiry:
                if date.today() >= item.expiry:
                    item.is_expired = True
                # check if expiry soon happens and update days_before_exp
                item.is_soon_to_expire, item.days_before_exp = validation.expires_soon(item.expiry)
                item.put() 

                  
        time.sleep(0.1)  # to delay so db table gets displayed correct
        self.render("frontpage.html", food_items = all_food_items) # passing contents in to the html file
        
    def get(self):
        self.render_front()

    def post(self):
        # get request data
        
        # id data (which check boxes has user checked) put in a variable
        list_of_id_checked = self.request.get_all("delete")  # returns a list of id strings

        # delete button data (if delete button clicked, list will have 1 item else no item in list)
        one_item_delete_button_list = self.request.get_all("delete_button")  # there is only 1 delete_button

        # desription button data (if desription button clicked, list will have 1 item else no item in list)
        one_item_description_button_list = self.request.get_all("description_button")  # there is only 1 description_button

        # date added button data (if date added button clicked, list will have 1 item else no item in list)
        one_item_days_before_button_list = self.request.get_all("days_before_button")  # there is only 1 date_added_button

        # expiry date button data (if expiry date button clicked, list will have 1 item else no item in list)
        one_item_exp_date_button_list = self.request.get_all("exp_date_button")  # there is only 1 exp_date_button

        
        # delete button is clicked
        if len(one_item_delete_button_list) == 1:
            # loop through list_of_id_checked and remove matches from db
            for an_id in list_of_id_checked:
                # find the item with the specific id in db
                match = FoodItem.get_by_id(int(an_id))
                # remove the item
                if match:
                    FoodItem.delete(match)
            time.sleep(0.1)  # to delay so db table gets displayed correct
            self.render_front()
        
        elif len(one_item_description_button_list) == 1: # 'Description' is clicked
            self.render_front(parameter="description ASC")


        
        elif len(one_item_days_before_button_list) == 1: # 'Days before expiry' is clicked
            self.render_front(parameter="days_before_exp ASC")  # the 'oldest' shown first

        
        elif len(one_item_exp_date_button_list) == 1: #expiry date clicked
            self.render_front(parameter="expiry ASC")  # None exp date comes first then what is next to expire 
        
            


# handler for '/addfood'
class AddFoodPage(Handler):        
    def get(self):
        self.render("add_food.html", food_description_content="", food_description_error="",
                    measure_unit_error="", amount_error="", date_error="", list_of_units=list_of_units, selectedUnit="")

    def post(self):
        # data that user has entered
        a_food_description = self.request.get("food_description").strip()
        a_measuring_unit = self.request.get("q")
        an_amount = self.request.get("amount")
        an_exp_date_str = self.request.get("SnapHost_Calendar")  # format mm/dd/yyyy
                
        # create objects of class InfoEntered
        obj_food = validation.is_food_description_valid(a_food_description) # object is created inside food_description_valid()
        obj_unit = validation.is_measure_unit__valid(a_measuring_unit, an_amount)  # object is created inside measure_unit__valid()
        obj_amount = validation.is_amount_valid(an_amount, a_measuring_unit)  # object is created inside exp_date_valid()
        obj_exp_date = validation.is_exp_date_valid(an_exp_date_str)  # object is created inside exp_date_valid()
                      
        # create list for the objects and append them
        obj_list = []
        
        obj_list.append( obj_food )
        obj_list.append( obj_unit )
        obj_list.append( obj_amount )
        obj_list.append( obj_exp_date )
               
        # check if all 'object.validation' are True so a foodItem can be added to db
        if validation.are_all_validation_true(obj_list):
            # check if there is a date, and if so convert to yyyy-mm-dd
            if an_exp_date_str:
                date_valid = obj_exp_date.get_validation_info()  # returns a Boolean
                if date_valid:
                    #convert to YYYY-MM-DD
                    an_exp_date = datetime.strptime(an_exp_date_str+" 12:00", "%m/%d/%Y %H:%M").date()
            else:
                an_exp_date = None

            # make first letter upper case
            a_food_description = validation.upper_case(a_food_description)

            # create item in db
            FI = FoodItem(description = a_food_description, measure_unit = a_measuring_unit, amount = an_amount, expiry = an_exp_date, is_expired=False)
            FI.put()
            id_for_FI = str(FI.key().id())
            self.redirect("/addfood")
            
        # else re-render '/addfood' with the error messages
        else:
            self.render("add_food.html", food_description_content=a_food_description ,
                        food_description_error=obj_food.get_error_msg(),
                        measure_unit_error=obj_unit.get_error_msg(),
                        amount_error=obj_amount.get_error_msg(),
                        amount_content=an_amount, 
                        date_error=obj_exp_date.get_error_msg(),
                        list_of_units=list_of_units,
                        selectedUnit=a_measuring_unit)
        


app = webapp2.WSGIApplication([('/', Frontpage),
                               ('/addfood', AddFoodPage)], debug=True)
