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

import my_helper_functions
import os
import webapp2
import jinja2
from datetime import datetime
from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=True)

list_of_units = ["", "gram", "liter", "kilo", "piece"]

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)
    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)
    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

class FoodItem(db.Model): # abbreviated 'FI'
    #subject = db.StringProperty(required = True)
    description = db.TextProperty(required = True)  # food description
    measure_unit = db.TextProperty(required = False) # gram, kilo etc
    amount = db.TextProperty(required = False)  # a number
    expiry = db.DateProperty(required = False)  # expiry date for food
    added_date = db.DateProperty(auto_now_add = True)  # date the food is added to freezer
    created = db.DateTimeProperty(auto_now_add = True)
        
    last_modified = db.DateTimeProperty(auto_now = True)


# handler for '/'
class Frontpage(Handler):
    def render_front(self):
        all_food_items = db.GqlQuery("SELECT * FROM FoodItem ORDER BY created DESC")
        # if you only wanna display the 10 latest: "SELECT * FROM Content ORDER BY created DESC limit 10"
        self.render("frontpage.html", food_items = all_food_items) # passing contents in to the html file
        
    def get(self):
        self.render_front()


    

# handler for '/addfood'
class AddFoodPage(Handler):        
    def get(self):
        self.render("add_food.html", food_description_content="", food_description_error="",
                    measure_unit_error="", amount_error="", date_error="", list_of_units=list_of_units, selectedUnit="")

    def post(self):
        a_food_description = self.request.get("food_description").strip()
        a_measuring_unit = self.request.get("q")
        an_amount = self.request.get("amount")
        an_exp_date_str = self.request.get("SnapHost_Calendar")
        
        
        if an_exp_date_str:
            
            date_valid = my_helper_functions.validate_date(an_exp_date_str)  # returns a Boolean
            
            if date_valid:
                #convert to YYYY-MM-DD
                an_exp_date = datetime.strptime(an_exp_date_str+" 12:00", "%m/%d/%Y %H:%M").date()
                error_date = ""
            else:
                an_exp_date = an_exp_date_str
                error_date = "Incorrect data format, should be MM/DD/YYYY"
                
        else:
            an_exp_date = None
            date_valid = True            
            error_date = ""

        error_food_descr = "You need a 'Food description'"
        error_measure = "If you put in 'Amount' you also need 'Measuring unit'"
        error_amount_empty = "If you put in 'Measuring unit' you also need 'Amount'"
        error_amount_number = "This is not a number!"

        
        if my_helper_functions.food_description_valid(a_food_description):
            # Make first letter uppercase
            if a_food_description[0:1] in "abcdefghijklmnopqrstuvwxyz":
                first_letter_to_upper = a_food_description[0:1].upper()
                if len(a_food_description) > 1:
                    a_food_description = first_letter_to_upper + a_food_description[1:]
                else:
                    a_food_description = first_letter_to_upper
            if a_measuring_unit=="gram" or a_measuring_unit=="kilo" or a_measuring_unit=="liter" or a_measuring_unit=="piece": #valid unit chosen
                if an_amount:
                    # check if an_amount is valid number
                    try:
                        float(an_amount)

                        if date_valid:
                            FI = FoodItem(description = a_food_description, measure_unit = a_measuring_unit, amount = an_amount, expiry = an_exp_date)
                            FI.put()
                            id_for_FI = str(FI.key().id())
                            self.redirect("/")
                        else:
                            self.performRender(a_food_description, "", "" , "", an_amount, a_measuring_unit, error_date)
                    except:
                        self.performRender(a_food_description, "", "" , error_amount_number, an_amount, a_measuring_unit, error_date)
                                            
                else: # invalid
                    self.performRender(a_food_description , "", "", error_amount_empty, "", a_measuring_unit, error_date)
                    
                    
            else: # a_measuring_unit=="no unit"
                if an_amount:
                    # invalid
                    try:
                        float(an_amount)
                        self.performRender(a_food_description, "", error_measure , "",
                                           an_amount, a_measuring_unit, error_date)
                        
                    except:
                        self.performRender(a_food_description, "", error_measure, error_amount_number,
                                           an_amount, a_measuring_unit, error_date)
                else: 
                    # valid
                    if date_valid:
                        FI = FoodItem(description = a_food_description, measure_unit = a_measuring_unit, amount = an_amount, expiry = an_exp_date)
                        FI.put()
                        id_for_FI = str(FI.key().id())
                        self.redirect("/")
                    else:
                        self.performRender(a_food_description, "", "" , "", an_amount, a_measuring_unit, error_date)


        else:  # empty a_food_description
            if a_measuring_unit=="gram" or a_measuring_unit=="kilo" or a_measuring_unit=="liter" or a_measuring_unit=="piece": #valid unit chosen 
                if an_amount:
                    # check if an_amount is valid
                    try:
                        float(an_amount)
                        # would like to keep the measure unit showing don't know how!!!
                        self.performRender("", error_food_descr, "", "", an_amount, a_measuring_unit, error_date)
                        
                    except:
                        # would like to keep the measure unit showing don't know how!!!
                        self.performRender("", error_food_descr, "", error_amount_number,
                                           an_amount, a_measuring_unit, error_date)

                else: # invalid
                    # would like to keep the measure unit showing don't know how!!!
                    self.performRender("", error_food_descr, "", error_amount_empty, "", a_measuring_unit, error_date)

            else: # a_measuring_unit=="no unit"
                if an_amount:
                    # invalid
                    try:
                        float(an_amount)
                        self.performRender("", error_food_descr, error_measure, "", an_amount, a_measuring_unit, error_date)
                    except:
                        # would like to keep the measure unit showing don't know how!!!
                        self.performRender("", error_food_descr, error_measure, error_amount_number,
                                           an_amount, a_measuring_unit, error_date)
                else:
                    self.performRender("", error_food_descr, "", "", an_amount, a_measuring_unit, error_date)

    def performRender(self, foodDescr, foodDescrErr, measureUnitErr, amountErr, amountContent, measureUnit, exp_date_error):
        
        
        self.render("add_food.html", food_description_content=foodDescr , food_description_error=foodDescrErr,
                    measure_unit_error=measureUnitErr, amount_error=amountErr, amount_content=amountContent,
                    date_error=exp_date_error, list_of_units=list_of_units, selectedUnit=measureUnit)

    


app = webapp2.WSGIApplication([('/', Frontpage),
                               ('/addfood', AddFoodPage)], debug=True)
