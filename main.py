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
    measure_unit = db.StringProperty(required = False) # gram, kilo etc
    amount = db.StringProperty(required = False)  # a number
    expiry = db.DateProperty(required = False)  # expiry date for food

    is_expired = db.BooleanProperty(required=False)  # is True if exp. date has been exceeded
    is_soon_to_expire = db.BooleanProperty(required=False)  # is True if exp. date is within x days
    days_before_exp =  db.IntegerProperty(required = False) 
    
    created = db.DateTimeProperty(auto_now_add = True)  # more precise than added_date, when sorting    
    added_date = db.DateProperty(auto_now_add = True)  # date the food is added to freezer 
    last_modified = db.DateTimeProperty(auto_now = True)



# handler for '/'
class Frontpage(Handler):
    def render_front(self, parameter="created DESC"):  # 'youngest' created date shown first by default

        all_food_items = db.GqlQuery("SELECT * FROM FoodItem ORDER BY %s" %parameter) #.run(read_policy="STRONG_CONSISTENCY")
        # if you only wanna display the 10 latest: "SELECT * FROM Content ORDER BY created DESC limit 10"

        # loop through all items and set is_expired
        for item in all_food_items:
            if item.expiry:
                if date.today() >= item.expiry:
                    item.is_expired = True
                # check if expiry soon happens and update days_before_exp
                item.is_soon_to_expire, item.days_before_exp = validation.expires_soon(item.expiry)
            else: # no exp date
                item.is_expired = False
                item.is_soon_to_expire = False
                item.days_before_exp = None
            item.put() 

        time.sleep(0.1)  # to delay so db table gets displayed correct

        # toggle function
        descrip_a_d="ASC"
        days_left_a_d="ASC"
        exp_a_d="ASC"

        # decide which sorted code (0-7) you pass into html and also update variables.
        if parameter == "created DESC":
            number_look = 1
            
        else:
            
            if parameter=="description ASC":
                number_look = 2
                descrip_a_d="DESC"
            elif parameter=="description DESC":
                number_look = 3

            elif parameter=="days_before_exp ASC":
                number_look = 4
                days_left_a_d="DESC"
            elif parameter=="days_before_exp DESC":
                number_look = 5

            elif parameter=="expiry ASC":
                number_look = 6
                exp_a_d="DESC"
            else:  # parameter=="expiry DESC"
                number_look = 7
                
            
        self.render("frontpage.html", food_items = all_food_items,
                    descr_asc_desc=descrip_a_d,
                    days_left_asc_desc=days_left_a_d,
                    exp_asc_desc=exp_a_d,
                    look_number=number_look) # passing contents in to the html file
     
        
    def get(self):
        id_descript = self.request.get("id_description")  # if header link 'Description' is clicked 'ASC' or 'DESC' will be assigned
        id_days_left = self.request.get("id_days_to_exp")  # if header link 'Days to exp' is clicked 'ASC' or 'DESC' will be assigned
        id_exp = self.request.get("id_exp_date")  # if header link 'Exp. date' is clicked 'ASC' or 'DESC' will be assigned

        if id_descript: # 'Description' was clicked
            self.render_front(parameter="description %s" %id_descript)
        elif id_days_left:  # 'Days to exp' was clicked
            self.render_front(parameter="days_before_exp %s" %id_days_left)  # the 'oldest' shown first
        elif id_exp:  # 'Exp. date' was clicked
            self.render_front(parameter="expiry %s" %id_exp)  # None exp date comes first then what is next to expire
        else:
            self.render_front()
        
        

    def post(self):
        # get request data

        # 0-7 to see which sorted way the table was before user clicked delete button
        the_sorted_look = self.request.get_all("which_sorted_look")  # returns a list with only one item though

        if int(the_sorted_look[0]) == 1:
            param = "created DESC"

        elif int(the_sorted_look[0]) == 2:
            param = "description ASC"
            
        elif int(the_sorted_look[0]) == 3:
            param = "description DESC"

            
        elif int(the_sorted_look[0]) == 4:
            param = "days_before_exp ASC"

            
        elif int(the_sorted_look[0]) == 5:
            param = "days_before_exp DESC"

            
        elif int(the_sorted_look[0]) == 6:
            param = "expiry ASC"

        elif int(the_sorted_look[0]) == 7:
            param = "expiry DESC"
        else:
            param = "created DESC"
        
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

        self.render_front(parameter=param)
      



# handler for '/food'
class FoodPage(Handler):        
    def get(self):
        an_id = self.request.get("id")  # if an foodItem description is clicked, there is an_id        
        if an_id:  # means there is an item to edit
            specific_item = FoodItem.get_by_id(int(an_id))  # get the item with the specific id (an_id)

            # check if there is an exp. date yyyy-mm-dd
            if specific_item.expiry:  
                #convert it to format mm/dd/yyyy
                date_html_format = validation.convert_date_mmddyyyy(str(specific_item.expiry))

            else:  # no expiry date for this item
                date_html_format = ""
                
            # set values for specific item
            a_food_description_content=specific_item.description
            a_exp_content = date_html_format
            a_amount_content=specific_item.amount
            a_selectedUnit=specific_item.measure_unit
            a_headline="Edit food item"
            a_change_button="Submit Changes"
            a_passive_button="Cancel"
            a_item_id=an_id

        else:  # no id, set values to a blank "food.html"
            a_food_description_content=""
            a_exp_content = ""
            a_amount_content=""
            a_selectedUnit=""
            a_headline="Add food to Freezer"
            a_change_button="Submit"
            a_passive_button="Return to Overview"
            a_item_id=""

        logging.debug("description = " + a_food_description_content)
        # render "food.html" with correct params!
        self.render("food.html", food_description_content=a_food_description_content, food_description_error="",
                    measure_unit_error="", amount_error="", date_error="",
                    exp_content = a_exp_content, amount_content=a_amount_content, list_of_units=list_of_units,
                    selectedUnit=a_selectedUnit, headline=a_headline,
                    change_button=a_change_button, passive_button=a_passive_button,
                    item_id=a_item_id)

            
    def post(self):
        # data that user has entered
        a_food_description = self.request.get("food_description").strip()
        a_measuring_unit = self.request.get("q")
        an_amount = self.request.get("amount")
        an_exp_date_str = self.request.get("expiry_date")  # format mm/dd/yyyy
        an_item_id = self.request.get("item_ID")  # this is a string "455646501654613" format
        
                
        # create objects of class InfoEntered. NB this is not an FoodItem object!!!
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

            # check if there is an_item_id to see whether to 'update' or 'create new item in db'
            if an_item_id:  # update already excisting item
                logging.debug("item id: " + an_item_id) 
                # get the specific item
                the_item = FoodItem.get_by_id(int(an_item_id))  # get the item with the specific id (an_item_id)
                # update
                the_item.description = a_food_description
                the_item.measure_unit = a_measuring_unit
                the_item.amount = an_amount
                the_item.expiry = an_exp_date
                 
                the_item.put()
                time.sleep(0.1)  # to delay so db table gets displayed correct
                self.redirect("/")  # tells the browser to go to '/' and the response is empty
                #self.response.out.write("updated")
            else: # no id
                logging.debug("No item id" ) 
                # create item in db
                FI = FoodItem(description = a_food_description, measure_unit = a_measuring_unit, amount = an_amount, expiry = an_exp_date, is_expired=False)
                FI.put()
                id_for_FI = str(FI.key().id())
                time.sleep(0.1)  # to delay so db table gets displayed correct
                self.redirect("/food")  # tells the browser to go to '/food' and the response is empty
                
            
             
        # else re-render 'food.html' with the error messages
        else:
            # decide which params to pass based on 'add' or 'edit'
            if an_item_id: # edit version
                the_headline="Edit food item"
                the_change_button="Submit Changes"
                the_passive_button="Cancel"
                the_item_id=an_item_id

            else:  # add version
                the_headline="Add food to Freezer"
                the_change_button="Submit"
                the_passive_button="Return to Overview"
                the_item_id=""  # ok with empty str. when checking if "" that is False.... But can't use None to put in here...

            # returns the following in the response
            self.render("food.html", food_description_content=a_food_description , food_description_error=obj_food.get_error_msg(),
                    measure_unit_error=obj_unit.get_error_msg(),
                    amount_error=obj_amount.get_error_msg(),
                    amount_content=an_amount, 
                    date_error=obj_exp_date.get_error_msg(),
                    exp_content = an_exp_date_str,
                    list_of_units=list_of_units,
                    selectedUnit=a_measuring_unit,
                    headline=the_headline,
                    change_button=the_change_button, passive_button=the_passive_button,
                    item_id=the_item_id)
          

            

app = webapp2.WSGIApplication([('/', Frontpage),
                               ('/food', FoodPage)], debug=True)
