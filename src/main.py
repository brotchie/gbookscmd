import sys
import math
import httplib2
import logging

import yaml

from apiclient.discovery import build

from oauth2client.client import OAuth2WebServerFlow
from oauth2client.file import Storage
from oauth2client.tools import run

log = logging.getLogger(__file__)

TOKEN_FILE_NAME = 'books.dat'
OAUTH2_CREDENTIALS_FILE_NAME = 'oauth2.yaml'

BOOKSHELF_FAVORITES = 0
BOOKSHELF_PURCHASED = 1
BOOKSHELF_TOREAD = 2
BOOKSHELF_READINGNOW = 3
BOOKSHELF_HAVEREAD = 4
BOOKSHELF_REVIEWED = 5
BOOKSHELF_RECENTLYVIEWED = 6
BOOKSHELF_MYEBOOKS = 7

MAX_VOLUMES_PER_REQUEST = 40

def build_oauth2_flow():
    credentials = yaml.load(file(OAUTH2_CREDENTIALS_FILE_NAME))
    return OAuth2WebServerFlow(
        client_id=credentials['oauth2credentials']['client_id'],
        client_secret=credentials['oauth2credentials']['client_secret'],
        scope='https://www.googleapis.com/auth/books',
        user_agent='google-books-viewer')

def get_bookshelf_volumes(service, userId, shelf):
    bookshelf = service.bookshelves().get(userId=userId, shelf=shelf).execute()
    volumeCount = bookshelf.get('volumeCount', 0)
    log.info('Fetching %i volumes.' % (volumeCount))
    volumes = []
    for i in range(int(math.ceil(volumeCount / float(MAX_VOLUMES_PER_REQUEST)))):
        log.info('Fetching set %i.' % (i,))
        result = service.bookshelves().volumes().list(userId=userId, shelf=shelf, startIndex=MAX_VOLUMES_PER_REQUEST*i, maxResults=MAX_VOLUMES_PER_REQUEST).execute()
        volumes.extend(result.get('items', []))
    return volumes

def main():
    if len(sys.argv) != 2:
        sys.stderr.write('Usage:\n')
        sys.stderr.write(' %s userid\n' % (sys.argv[0],))
        sys.exit(1)
    else:
        userid = sys.argv[1]

    storage = Storage(TOKEN_FILE_NAME)
    credentials = storage.get()
    if not credentials or credentials.invalid:
        credentials = run(build_oauth2_flow(), storage)

    http = httplib2.Http()
    http = credentials.authorize(http)
    service = build('books', 'v1', http=http)

    volumes = get_bookshelf_volumes(service, userid, BOOKSHELF_TOREAD)
    for volume in volumes:
        print '%s - %s' % (volume['volumeInfo']['title'], ', '.join(volume['volumeInfo']['authors']))

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
