import requests
import base64
import textwrap
import re
import logging
from thefuzz import process

MORBO_BASE_URL = 'https://morbotron.com'
FRINK_BASE_URL = 'https://frinkiac.com'
WRAP_WIDTH = 24

log = logging.getLogger()


class RequestFailedException(Exception):
    pass


class Frinkotron:
    """
    An interface to the common Morbotron/Frinkiac back end.
    """
    def __init__(self, name='morbo'):
        self.name = name
        if name == 'morbo':
            self.base = MORBO_BASE_URL
        elif name == 'frink':
            self.base = FRINK_BASE_URL
        else:
            raise Exception('Wat')

    def search(self, key):
        res = requests.get('{}/api/search?q={}'.format(self.base, key))
        if res.ok:
            return res.json()
        else:
            raise RequestFailedException()

    def context_frames(self, episode, timestamp, before=4000, after=4000):
        url = '{base}/api/frames/{episode}/{ts}/{before}/{after}'.format(
            base=self.base, episode=episode, ts=timestamp, before=before, after=after
        )
        res = requests.get(url)
        if res.ok:
            return res.json()
        else:
            raise RequestFailedException()

    def captions(self, episode, timestamp):
        url = '{base}/api/caption?e={episode}&t={timestamp}'.format(
            base=self.base, episode=episode, timestamp=timestamp
        )
        res = requests.get(url)
        if res.ok:
            return res.json()['Subtitles']
        else:
            raise RequestFailedException()

    def caption_for_query(self, episode, timestamp, query):
        caps = self.captions(episode, timestamp)
        return process.extract(query, [c['Content'] for c in caps], limit=1)[0][0]

    def image_url(self, episode, timestamp, text=''):
        b64 = base64.b64encode(
            '\n'.join(textwrap.wrap(text, WRAP_WIDTH)).encode('utf-8'), b'-_'
        ).decode('ascii')
        param = '?b64lines={}'.format(b64) if len(text) else ''
        return '{base}/meme/{episode}/{timestamp}.jpg{param}'.format(
            base=self.base, episode=episode, timestamp=timestamp, param=param
        )

    def gif_url(self, episode, start, end, text=''):
        b64 = base64.b64encode(
            '\n'.join(textwrap.wrap(text, WRAP_WIDTH)).encode('utf-8'), b'-_'
        ).decode('ascii')
        param = '?b64lines={}'.format(b64) if len(text) else ''
        return '{base}/gif/{episode}/{start}/{end}.gif{param}'.format(
            base=self.base, episode=episode, start=start, end=end, param=param
        )

    def thumb_url(self, episode, timestamp):
        return '{base}/img/{episode}/{timestamp}/small.jpg'.format(
            base=self.base, episode=episode, timestamp=timestamp
        )


class Morbotron(Frinkotron):
    def __init__(self):
        super().__init__('morbo')


class Frinkiac(Frinkotron):
    def __init__(self):
        super().__init__('frink')
