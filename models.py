from google.appengine.ext import ndb

class Photo(ndb.Model):
    """Models a user uploaded photo entry"""

    image = ndb.BlobProperty()
    caption = ndb.StringProperty()
    date = ndb.DateTimeProperty(auto_now_add=True)

    @classmethod
    def query_user(cls, ancestor_key):
        """Return all photos for a given user"""
        return cls.query(ancestor=ancestor_key).order(-cls.date)

    @classmethod
    def query_user_alternate(cls, ancestor_key):
        """Return all photos for a given user using the gql syntax.
        It returns the same as the above method.
        """
        return ndb.gql('SELECT * '
                        'FROM Photo '
                        'WHERE ANCESTOR IS :1 '
                        'ORDER BY date DESC LIMIT 10',
                        ancestor_key)


class User(ndb.Model):

    name = ndb.StringProperty()
    email = ndb.StringProperty()
    unique_id = ndb.StringProperty()
    photos = ndb.KeyProperty(kind='Photo', repeated=True)
    username = ndb.StringProperty()
    password = ndb.StringProperty()
    token_id = ndb.StringProperty()


    @classmethod
    def query_user(cls, ancestor_key):
        return cls.query(ancestor=ancestor_key)

    @classmethod
    def query_user_object(cls, username):
        return cls.query(cls.username == username)

    @classmethod
    def query_user_auth(cls, username, password):
        return cls.query(ndb.AND((cls.username == username), cls.password == password))

    @classmethod
    def query_user_token(cls, id_token):
        return cls.query(cls.token_id == id_token)


