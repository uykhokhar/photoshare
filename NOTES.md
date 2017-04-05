greetings = ndb.gql('SELECT * '
                        'FROM Greeting '
                        'WHERE ANCESTOR IS :1 '
                        'ORDER BY date DESC LIMIT 10',
                        guestbook_key(guestbook_name))



* Memcache
  - https://cloud.google.com/appengine/docs/standard/python/memcache/
  - [Memcache Examples  |  App Engine standard environment for Python  |  Google Cloud Platform](https://cloud.google.com/appengine/docs/standard/python/memcache/examples)
