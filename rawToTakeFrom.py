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


import os
import webapp2
import jinja2
from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=True)


class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)
    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)
    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

class FoodItem(db.Model):
    #subject = db.StringProperty(required = True)
    description = db.TextProperty(required = True)
    added_date = db.DateTimeProperty(auto_now_add = True)
    last_modified = db.DateTimeProperty(auto_now = True)


# handler for /blog/newpost
class NewpostPage(Handler):
    def render_front(self, subject="", content="", error=""):
        self.render("pset3_build_blog.html", subject=subject, content=content, error = error)
        
    def get(self):
        self.render_front()

    def post(self):
        subject = self.request.get("subject") 
        content = self.request.get("content")

        if subject and content:
            c = Content(subject = subject, content = content)
            c.put()
            id_for_content = str(c.key().id())
            self.redirect("/blog/"+id_for_content)
        else:
            error = "we need both a subject and some content!"
            self.render_front(subject, content, error)


# handler for /blog/#a_number_id
class SuccessPage(Handler):        
    def get(self, content_id):
        content = Content.get_by_id(int(content_id))
        self.render("one_content.html", content=content)


# handler for /
class Frontpage(Handler):
    """
    def render_front(self, subject="", content="", error=""):
        contents = db.GqlQuery("SELECT * FROM Content ORDER BY created DESC limit 10")
        # if you only wanna display the 10 latest: "SELECT * FROM Content ORDER BY created DESC limit 10"
        self.render("all_posts.html", contents = contents) # passing contents in to the html file
        """
    def render_front(self):
        #contents = db.GqlQuery("SELECT * FROM Content ORDER BY created DESC limit 10")
        # if you only wanna display the 10 latest: "SELECT * FROM Content ORDER BY created DESC limit 10"
        self.render("frontpage.html"#, contents = contents) # passing contents in to the html file
        
    def get(self):
        self.render_front()

    def post(self):
        buttonId = self.request.get("addFood") 
        if buttonId:
            self.redirect("/addfood")


# handler for /addfood
class AddFoodPage(Handler):        
    def get(self):
        self.render("add_food.html", food_description_content="")


app = webapp2.WSGIApplication([('/', Frontpage),
                               ('/addfood', AddFoodPage),
                               ('/blog/(\d+)', SuccessPage)], debug=True)
