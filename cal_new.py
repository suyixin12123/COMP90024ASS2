# import twitter
# api = twitter.Api(consumer_key='gKXNjLGKoh9D2mNxOVTHHBdWI',
#                   consumer_secret='CAQ0534UcpjUV9tZmr3vSEANgkEokkQUw3VylReNZHGhZVgcUg',
#                   access_token_key='1118325454031601664-Gu6XlEc8F9G12Oh7hvcgGSCQqo01zH',
#                   access_token_secret='oBXXKzvNRNnjChBG8EdVSQt0YxPs6NfIfdhWkrIMvkJrp')

# # results = api.GetSearch(
# #     raw_query='l=&q=near%3A"Melbourne%2C Victoria" within%3A15mi')

# query = api.GetSearch(q = "", geocode = "%f,%f,%dkm" % (51.474144, -0.035401, 1))

# print(results[1])

# from twython import TwythonStreamer

# class MyStreamer(TwythonStreamer):
#     def on_success(self, data):
#         if 'text' in data:
#             print(data['text'])

#     def on_error(self, status_code, data):
#         print(status_code)
#         self.disconnect()

# stream = MyStreamer('gKXNjLGKoh9D2mNxOVTHHBdWI',
#                     'CAQ0534UcpjUV9tZmr3vSEANgkEokkQUw3VylReNZHGhZVgcUg',
#                     '1118325454031601664-Gu6XlEc8F9G12Oh7hvcgGSCQqo01zH',
#                     'oBXXKzvNRNnjChBG8EdVSQt0YxPs6NfIfdhWkrIMvkJrp')

# stream.statuses.filter(track='nasa')


#Import the necessary methods from tweepy library
import tweepy
import json
import hashlib
import re
import couchdb
from tweepy.utils import import_simplejson

#Variables that contains the user credentials to access Twitter API 
access_token_key = "1118325454031601664-VUsElYVD2Q2o9IcdCHOco9IrIVgv2q"
access_token_secret = "1USXZpEIuWqQQkhMSDyuWUBk63vYztLRZm6TDah958tNn"
consumer_key = "uwoENMuaDBaK2S3pyCbKDTeqg"
consumer_secret = "CmX2yWJeT5gKVZCPuj3FKEkCqe2N3jsljeZcx15ukftDYAYfz8"

#stream listener object
class StreamListener(tweepy.StreamListener):
    json = import_simplejson()

    def on_status(self, tweet):
        print 'Ran on_status'

    def on_error(self, status_code):
        print(status_code)
        return False

    def on_data(self, data):
        if data[0].isdigit():
            pass
        else:
            jdata = json.loads(data)
            db.save(jdata)

#This is a basic listener that just prints received tweets to stdout.
json = import_simplejson()
try:
    couchclient = couchdb.Server()
except:
    print "Cannot find CouchDB Server ... Exiting\n"
    print "----_Stack Trace_-----\n"
    raise

#Try to use the twitter bucket or else switch to use default bucket
try:
    db = couchclient['melbourne']
    print "Using melbourne bucket"
except:
    db = couchclient['s']
    print "Using default bucket"

#OAuth
auth1 = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth1.set_access_token(access_token_key, access_token_secret)
l = StreamListener()

def getTweets(auth1, l):
    try:
        streamer = tweepy.Stream(auth=auth1, listener=l)
        streamer.filter(locations=[152.84,-27.67,153.28,-27.21])
    except:
        getTweets(auth1, l)

getTweets(auth1, l)
    
