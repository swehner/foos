#!/usr/bin/env python
import http.client
import httplib2
import os
import random
import sys
import time
import threading

from apiclient.discovery import build
from apiclient.errors import HttpError
from apiclient.http import MediaFileUpload
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow

from bus import Event

# Explicitly tell the underlying HTTP transport library not to retry, since
# we are handling retry logic ourselves.
httplib2.RETRIES = 1

# Maximum number of times to retry before giving up.
MAX_RETRIES = 10

# Always retry when these exceptions are raised.
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, http.client.NotConnected,
  http.client.IncompleteRead, http.client.ImproperConnectionState,
  http.client.CannotSendRequest, http.client.CannotSendHeader,
  http.client.ResponseNotReady, http.client.BadStatusLine)

# Always retry when an apiclient.errors.HttpError with one of these status
# codes is raised.
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

CLIENT_SECRETS_FILE = "client_secrets.json"


def get_authenticated_service():
    upload_scope = 'https://www.googleapis.com/auth/youtube.upload'
    flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE, scope=upload_scope)
    storage = Storage("%s-oauth2.json" % sys.argv[0])
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        flags = argparser.parse_args(args=['--noauth_local_webserver'])
        credentials = run_flow(flow, storage, flags)

    return build('youtube', 'v3', http=credentials.authorize(httplib2.Http()))

def initialize_upload(youtube, file):
    tags = ['foos']
    title = 'Tuenti foos replay' + file
    body = {
        'snippet': {
            'title': title,
            'description': title,
            'tags': tags,
            'categoryId': 22,
        },
        'status': {'privacyStatus': 'unlisted'}
    }

    # Call the API's videos.insert method to create and upload the video.
    insert_request = youtube.videos().insert(
        part=",".join(list(body.keys())),
        body=body,
        # The chunksize parameter specifies the size of each chunk of data, in
        # bytes, that will be uploaded at a time. Set a higher value for
        # reliable connections as fewer chunks lead to faster uploads. Set a lower
        # value for better recovery on less reliable connections.
        media_body=MediaFileUpload(file, chunksize=-1, resumable=True))

    return resumable_upload(insert_request)

# This method implements an exponential backoff strategy to resume a
# failed upload.
def resumable_upload(insert_request):
    response = None
    error = None
    retry = 0
    while response is None:
        try:
            status, response = insert_request.next_chunk()
            if 'id' in response:
                print("Video id '%s' was successfully uploaded." % response['id'])
                return response['id']
            else:
                print("The upload failed with an unexpected response: %s" % response)
                return False
        except HttpError as e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                error = "A retriable HTTP error %d occurred:\n%s" % (e.resp.status, e.content)
            else:
                raise
        except RETRIABLE_EXCEPTIONS as e:
            error = "A retriable error occurred: %s" % e

        if error is not None:
            print(error)
            retry += 1
            if retry > MAX_RETRIES:
                print("No longer attempting to retry.")

            max_sleep = 2 ** retry
            sleep_seconds = random.random() * max_sleep
            print("Sleeping %f seconds and then retrying..." % sleep_seconds)
            time.sleep(sleep_seconds)


def upload(file):
    youtube = get_authenticated_service()
    video_id = None
    try:
        video_id = initialize_upload(youtube, file)
    except HttpError as e:
        print("An HTTP error %d occurred:\n%s" % (e.resp.status, e.content))
        raise
        
    return 'http://www.youtube.com/watch?v={}'.format(video_id)

if __name__ == '__main__':
    file = sys.argv[1]
    if not os.path.exists(file):
        print('File not found', file)

    upload(file)
