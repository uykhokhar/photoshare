import cgi
import datetime
import urllib
import webapp2
import json
import logging
import uuid

from google.appengine.api import memcache
from google.appengine.ext import ndb
from google.appengine.api import images
from google.appengine.api import users

from models import *






################################################################################
"""The home page of the app"""
class HomeHandler(webapp2.RequestHandler):

    """Show the webform when the user is on the home page"""
    def get(self):
        self.response.out.write('<html><body>')

        # Print out some stats on caching
        stats = memcache.get_stats()
        self.response.write('<b>Cache Hits:{}</b><br>'.format(stats['hits']))
        self.response.write('<b>Cache Misses:{}</b><br><br>'.format(
                            stats['misses']))

        user = self.request.get('user')
        ancestor_key = ndb.Key("User", user or "*notitle*")
        # Query the datastore
        photos = User.query_user(ancestor_key).fetch(100)



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


    #########CHANGE GET TO GET PHOTOS FROM USER
    """Print json or html version of the users photos"""
    def get(self,user,type, id_token):

        #ancestor_key = ndb.Key("User", user)
        #photos = Photo.query_user(ancestor_key).fetch(100)

        #VALIDATE THAT USERS IS CORRECT AND GET PHOTOS FROM USER
        user_q = User.query_user_token(id_token=id_token)
        user_obj = user_q.get()

        if user is None:
            logging.info('The authentication token is not valid')
        else:
            logging.info('Token valid for user: {}'.format(user_obj.username))
            photos = self.get_data(user_obj)
            print("photos: {}".format(photos))

            #CHANGE PHOTOS RETURN TO GET PHOTOS ARRAY FROM USER
            if type == "json":
                output = self.json_results(photos)
            else:
                output = self.web_results(photos)
            self.response.out.write(output)


    def json_results(self,photos):
        """Return formatted json from the datastore query"""
        json_array = []
        for photo in photos:
            photo_key_urlsafe = photo.urlsafe()
            photo_obj = photo.get()
            dict = {}

            if photo_obj is not None:
                #images no longer have urls because they don't have keys
                #remove the following line
                dict['image_url'] = "image/%s/" % photo_key_urlsafe
                dict['caption'] = photo_obj.caption
                dict['date'] = str(photo_obj.date)
                json_array.append(dict)
        return json.dumps({'results' : json_array})

    def web_results(self,photos):
        """Return html formatted json from the datastore query"""
        html = ""
        for photo in photos:
            photo_obj = photo.get()
            if photo_obj is not None:
                html += '<div><hr><div><img src="/image/%s/" width="200" border="1"/></div>' % photo.urlsafe()
                html += '<div><blockquote>Caption: %s<br>Date:%s</blockquote></div></div>' % (cgi.escape(photo_obj.caption),str(photo_obj.date))
        return html

    @staticmethod
    def get_data(user_obj):
        """Get data from the datastore only if we don't have it cached"""
        key = user_obj.username + "_photos"
        data = memcache.get(key)
        if data is not None:
            logging.info("Found in cache")
            return data
        else:
            logging.info("Cache miss")
            data = user_obj.photos
            if not memcache.add(key, data, 3600):
                logging.info("Memcache failed")
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
    def post(self,username, id_token):


        # If we are submitting from the web form, we will be passing
        # the user from the textbox.  If the post is coming from the
        # API then the username will be embedded in the URL
        if self.request.get('user'):
            username = self.request.get('user')
            user_obj_query = User.query_user_object(username)
            user_obj = user_obj_query.get()
            id_token = user_obj.token_id

        # If submitting from webform, the token will be coming from the browser cache (somehow)
        # Otherwise, the token will be coming from the API.

        user_q = User.query_user_token(id_token=id_token)
        user_obj = user_q.get()

        if user_obj is None:
            logging.info('The authentication token is not valid')


        # Be nice to our quotas
        thumbnail = images.resize(self.request.get('image'), 30,30)

        # Create and add a new Photo entity
        #
        # We set a parent key on the 'Photos' to ensure that they are all
        # in the same entity group. Queries across the single entity group
        # will be consistent. However, the write rate should be limited to
        # ~1/second.
        photo = Photo(caption=self.request.get('caption'),
                image=thumbnail)
        photo_key = photo.put()

        user_obj.photos.append(photo_key)
        user_obj.put()
        logging.info('Photo added to user')

        # Clear the cache (the cached version is going to be outdated)
        key = user_obj.username + "_photos"
        memcache.delete(key)

        # Redirect to print out JSON
        #self.redirect('/user/%s/json/?id_token=%s' % username % id_token )
        self.redirect('/user/{}/json/{}/'.format(username, id_token))

################################################################################
class CreateAccountHandler(webapp2.RequestHandler):

    def post(self, username, password):

        #if user exists, don't create new, else create new
        user_q = User.query_user_object(username = username)
        user = user_q.get()

        if user is None:
            #create token and user
            new_token = str(uuid.uuid4())
            user_obj = User(username=username, password=password, token_id=new_token)
            user_obj.put()
            logging.info('User created with username {}, token {}'.format(user_obj.username, user_obj.token_id))
        else:
            logging.info('User already exists')

        """Auth Handling"""

class AuthHandler(webapp2.RequestHandler):
    def post(self, username, password):
        user_q = User.query_user_auth(username=username, password=password)
        user = user_q.get()

        if user is None:
            # create token and user
            logging.info('The user does not exist or the username and password combination was wrong')
        else:
            logging.info('Logged in, token: {}'.format(user.token_id))


################################################################################

class DeleteHandler(webapp2.RequestHandler):

    def post(self, key, id_token):

        user_q = User.query_user_token(id_token=id_token)
        user_obj = user_q.get()

        if user_obj is None:
            logging.info('The authentication token is not valid')

        photo_delete_key = ndb.Key(urlsafe=key)
        logging.info("Photo with key exists {}".format(photo_delete_key))

        self.get_photo(photo_delete_key, user_obj)
        #photo_obj.key.delete()


        #remove user from cache
        key = user_obj.username + "_photos"
        memcache.delete(key)

    def get_photo(self, key_to_delete, user_obj):
        print("method called")
        #all_photos_keys = user_obj.photos
        user_obj.photos.remove(key_to_delete)
        user_obj.put()
        return

    def test(self):
        for photo_key in all_photos_keys:
            #print("key of photo {}".format(photo_key.id()))
            if key_to_delete.id() == photo_key.id() :
                print("key to delete {} key of photo {}".format(key_to_delete, photo_key.id()))
                photo_key.delete()
                user_obj.photos.remove(key_to_delete)
                user_obj.put()
        return


################################################################################

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





################################################################################

app = webapp2.WSGIApplication([
    ('/', HomeHandler),
    #('/', AuthHandler),
    webapp2.Route('/create_account/<username>/<password>/', handler=CreateAccountHandler),
    webapp2.Route('/user/authenticate/<username>/<password>/', handler=AuthHandler),
    webapp2.Route('/logging/', handler=LoggingHandler),
    webapp2.Route('/image/<key>/', handler=ImageHandler),
    webapp2.Route('/post/<username>/<id_token>/', handler=PostHandler),
    webapp2.Route('/user/<user>/<type>/<id_token>/',handler=UserHandler),
    webapp2.Route('/image/<key>/delete/<id_token>/',handler=DeleteHandler)
    ],
    debug=True)
