import requests
import requests_oauthlib
import os
import urllib.request
import base64
import time
import json
import PIL
import tweepy
from pprint import pprint
# initialize the API client

import requests


# authentication setting using user name and password
api_key = 'acc_6bce1547c2cfbcc'
api_secret = '223cdba47129a87a4d40c033d0eecd00'
"""
These api keys are for imagga

"""

#Create a dict of tags that we want to detect for in an image
custom_tags = set(["gun", "revolver", "weapon", "pistol", "firearm", "machine gun", "rifle"])

client_key = "3L0sSUuDyTxxSvVSy7vrQ2j1X"
client_secret = "mEuvmFnxSysdSC73Y21s0zSr0jZcMmZpkQDbU3ekiJv9Swb2HK"
token = "3030963886-ltID6D8xMD5p9qyjzh49aTcGTS65RTUjiJUXekn"
token_secret = "BwkpeCw57nWxghvCkelruzkiX38deEaLdiklmXV69kQDx"
#Twitter API auth settings
oauth = requests_oauthlib.OAuth1(client_key, client_secret, token, token_secret)
#Setup out connection to twitter for later use

#
# Download Tweets from a user profile
#
"""
This function takes a screen name and gets the latest 2000 tweets
Built in error checking for HTTP status codes included for debugging


Params: screen_name
Returns 
	tweets
"""
def download_tweets(screen_name, max_id=None):
    api_url = "https://api.twitter.com/1.1/statuses/user_timeline.json?"
    api_url += "screen_name=%s&" % screen_name
    api_url += "count=200"

    if max_id is not None:
        api_url += "&max_id=%d" % max_id

    # send request to Twitter
    response = requests.get(api_url, auth=oauth)

    if response.status_code == 200:

        tweets = json.loads(response.content)

        return tweets

    else:

        print("[*] Twitter API FAILED! %d" % response.status_code)

    return None


#
# Takes a username and begins downloading all Tweets
#


"""
Store the tweets and create an id list of all the tweets

Params:

Username

Returns:
	the full list of tweets that are downloaded
"""
def download_all_tweets(username):
    full_tweet_list = []
    max_id = 0

    # grab the first 200 Tweets
    tweet_list = download_tweets(username)

    # grab the oldest Tweet
    if tweet_list is None:
        return

    oldest_tweet = tweet_list[-1]

    # continue retrieving Tweets
    while max_id != oldest_tweet['id']:

        full_tweet_list.extend(tweet_list)

        # set max_id to latest max_id we retrieved
        max_id = oldest_tweet['id']

        print("[*] Retrieved: %d Tweets (max_id: %d)" % (len(full_tweet_list), max_id))

        # sleep to handle rate limiting
        time.sleep(3)

        # send next request with max_id set
        tweet_list = download_tweets(username, max_id - 1)

        # grab the oldest Tweet
        if len(tweet_list):
            oldest_tweet = tweet_list[-1]

    # add the last few Tweets
    full_tweet_list.extend(tweet_list)

    # return the full Tweet list
    return full_tweet_list


#
# Uploads image file to Imagga for processing.
#


"""
Take the path of the image and auth to the imagga api and store the pic under personal uploads


Returns the content ID of the image
"""
def upload_file(image_path):
    try:
        response = requests.post('https://api.imagga.com/v2/categories/personal_photos',
	auth=(api_key, api_secret),
	files={'image': open(image_path, 'rb')})
        #response = content_api.upload(image_path)

        return response.to_dict()["uploaded"][0]["id"]

    except:

        return None

#
# Submits an uploaded file to the tagging API.
#


"""
Take the content ID and send it to the image tagging end point

Store the tags and check if they match out list
"""
def tag_image(content_id):
    response = requests.get('https://api.imagga.com/v2/tags?image_url%s' % image_path,
			auth=(api_key, api_secret))
	#tagging_api = Imagga.TaggingApi(api_client)

    response = response.json(content=content_id)
    result = response.to_dict()

    tags = []

    for i in result['results'][0]['tags']:
        tags.append(i['tag'])

    tags = set(tags)

    matches = tags.intersection(custom_tags)

    if len(matches):
        print( "[*] Image matches! => ")
        for match in matches:
            print(match)


        return True

    return False


#
# Splits image into thirds both vertically and horizontally.
#

"""
Take the image and split it up into thirds
This is done to help API detect images
Needed for the old version of the api to get decent results
V2 it still helps
"""
def split_image(image_path):
    ext = image_path.split(".")[-1]

    im = Image.open(image_path)
    width, height = im.size

    step_horizontal = width / 3
    step_vertical = height / 3

    for i in range(3):

        start = i * step_horizontal
        end = start + step_horizontal

        box = (0, start, width, end)

        new = im.crop(box)

        new.save("test.%s" % ext)

        content_id = upload_file("test.%s" % ext)

        if content_id is not None:

            result = tag_image(content_id)

            if result == True:
                return result

    for i in range(3):

        start = i * step_vertical
        end = start + step_vertical

        box = (start, 0, end, height)

        new = im.crop(box)

        new.save("test.%s" % ext)

        content_id = upload_file("test.%s" % ext)

        if content_id is not None:

            result = tag_image(content_id)

            if result == True:
                return result
    return False


#
# Wrapper function that kicks off the entire detection process.
#


"""
Start searching for images
"""
def detect_guns(image_path):
    print("[*] Trying image %s" % image_path)

    # test the full image first
    content_id = upload_file(image_path)

    if content_id != None:
        result = tag_image(content_id)

        if result is False:

            result = split_image(image_path)
            return result

        else:

            print("[*] Image matches!")
            return True

#The user name to get all the tweets from
full_tweet_list = download_all_tweets("NRA")

print("[*] Retrieved %d Tweets. Processing now..." % len(full_tweet_list))

#Make a folder for gunphotos
if not os.path.exists("gunphotos"):
    os.mkdir("gunphotos")

photo_count = 0
match_count = 0
"""
Take the list of tweets
and check the response from the twitter API for media
Check to see if the media is an image and store the URL
Download the image to the gunphotos folder
"""
for tweet in full_tweet_list:
    try:
        for media in tweet['extended_entities']['media']:

            print("[*] Downloading photo %s" % media['media_url'])

            photo_count += 1

            response = requests.get(media['media_url'])

            file_name = media['media_url'].split("/")[-1]

            # write out the file
            fd = open("gunphotos/%s" % file_name, "wb")
            fd.write(response.content)
            fd.close()

            # now test for guns!
            result = detect_guns("gunphotos/%s" % file_name)

            if result != True:
                os.remove("gunphotos/%s" % file_name)
            else:
                match_count += 1
    except: 
        pass

print("[*] Finished! Checked %d photos found %d with weapons present." % (photo_count, match_count))
