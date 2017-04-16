from google.appengine.ext import ndb

class Photo(ndb.Model):
    """Models a user uploaded photo entry"""

    user = ndb.StringProperty()
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
