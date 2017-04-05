import cgi
import datetime
import urllib
import webapp2
import json
import logging

from google.appengine.ext import ndb
from google.appengine.api import images

from models import *

################################################################################
"""The home page of the app"""
class HomeHandler(webapp2.RequestHandler):

    """Show the webform when the user is on the home page"""
    def get(self):
        self.response.out.write('<html><body>')
        user = self.request.get('user')
        ancestor_key = ndb.Key("User", user or "*notitle*")
        # Query the datastore
        photos = Photo.query_user(ancestor_key).fetch(20)


        self.response.out.write("""
        <form action="/post/default/" enctype="multipart/form-data" method="post">
        <div><textarea name="caption" rows="3" cols="60"></textarea></div>
        <div><label>Photo:</label></div>
        <div><input type="file" name="image"/></div>
        <div>User <input value="default" name="user"></div>
        <div><input type="submit" value="Post"></div>
        </form>
        <hr>
        </body>
        </html>""")


################################################################################
"""Handle activities associated with a given user"""
class UserHandler(webapp2.RequestHandler):

    """Print json or html version of the users photos"""
    def get(self,user,type):
        ancestor_key = ndb.Key("User", user)
        photos = Photo.query_user(ancestor_key).fetch(100)
        if type == "json":
            output = self.json_results(photos)
        else:
            output = self.web_results(photos)
        self.response.out.write(output)

    def json_results(self,photos):
        """Return formatted json from the datastore query"""
        json_array = []
        for photo in photos:
            dict = {}
            dict['image_url'] = "image/%s/" % photo.key.urlsafe()
            dict['caption'] = photo.caption
            dict['user'] = photo.user
            dict['date'] = str(photo.date)
            json_array.append(dict)
        return json.dumps({'results' : json_array})

    def web_results(self,photos):
        """Return html formatted json from the datastore query"""
        html = ""
        for photo in photos:
            html += '<div><hr><div><img src="/image/%s/" width="200" border="1"/></div>' % photo.key.urlsafe()
            html += '<div><blockquote>Caption: %s<br>User: %s<br>Date:%s</blockquote></div></div>' % (cgi.escape(photo.caption),photo.user,str(photo.date))
        return html

    def get_data():
        data = memcache.get('key')
        if data is not None:
            return data
        else:
            data = query_for_data()
            memcache.add('key', data, 60)
        return data

################################################################################
"""Handle requests for an image ebased on its key"""
class ImageHandler(webapp2.RequestHandler):

    def get(self,key):
        """Write a response of an image (or 'no image') based on a key"""
        photo = ndb.Key(urlsafe=key).get()
        if photo.image:
            self.response.headers['Content-Type'] = 'image/png'
            self.response.out.write(photo.image)
        else:
            self.response.out.write('No image')


################################################################################
class PostHandler(webapp2.RequestHandler):
    def post(self,user):

        # If we are submitting from the web form, we will be passing
        # the user from the textbox.  If the post is coming from the
        # API then the username will be embedded in the URL
        if self.request.get('user'):
            user = self.request.get('user')

        # Be nice to our quotas
        thumbnail = images.resize(self.request.get('image'), 30,30)

        # Create and add a new Photo entity
        #
        # We set a parent key on the 'Photos' to ensure that they are all
        # in the same entity group. Queries across the single entity group
        # will be consistent. However, the write rate should be limited to
        # ~1/second.
        photo = Photo(parent=ndb.Key("User", user),
                user=user,
                caption=self.request.get('caption'),
                image=thumbnail)
        photo.put()
        logging.info("1.")
        self.redirect('/user/%s/json/' % user)



class LoggingHandler(webapp2.RequestHandler):
    """Demonstrate the different levels of logging"""

    def get(self):
        logging.debug('This is a debug message')
        logging.info('This is an info message')
        logging.warning('This is a warning message')
        logging.error('This is an error message')
        logging.critical('This is a critical message')

        try:
            raise ValueError('This is a sample value error.')
        except ValueError:
            logging.exception('A example exception log.')

        self.response.out.write('Logging example.')


################################################################################

app = webapp2.WSGIApplication([
    ('/', HomeHandler),
    webapp2.Route('/logging/', handler=LoggingHandler),
    webapp2.Route('/image/<key>/', handler=ImageHandler),
    webapp2.Route('/post/<user>/', handler=PostHandler),
    webapp2.Route('/user/<user>/<type>/',handler=UserHandler)
    ],
    debug=True)
