import requests
import json
import re
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from thefuzz import process

MORBO_BASE_URL = 'https://morbotron.com'
FRINK_BASE_URL = 'https://frinkiac.com'
REQUEST_TIMEOUT = 10
RENDER_TIMEOUT = 30
DEFAULT_FONT = 'akbar'
DEFAULT_COLOR = [255, 255, 255, 255]

log = logging.getLogger()


class RequestFailedException(Exception):
    pass


def _build_session():
    session = requests.Session()
    retry = Retry(
        total=2,
        backoff_factor=0.5,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=['GET'],
        respect_retry_after_header=False,
    )
    session.mount('https://', HTTPAdapter(max_retries=retry))
    return session


_session = _build_session()


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
        res = _session.get('{}/api/search?q={}'.format(self.base, key), timeout=REQUEST_TIMEOUT)
        if res.ok:
            return res.json()
        else:
            raise RequestFailedException()

    def context_frames(self, episode, timestamp, before=4000, after=4000):
        url = '{base}/api/frames/{episode}/{ts}/{before}/{after}'.format(
            base=self.base, episode=episode, ts=timestamp, before=before, after=after
        )
        res = _session.get(url, timeout=REQUEST_TIMEOUT)
        if res.ok:
            return res.json()
        else:
            raise RequestFailedException()

    def captions(self, episode, timestamp):
        url = '{base}/api/caption?e={episode}&t={timestamp}'.format(
            base=self.base, episode=episode, timestamp=timestamp
        )
        res = _session.get(url, timeout=REQUEST_TIMEOUT)
        if res.ok:
            return res.json()['Subtitles']
        else:
            raise RequestFailedException()

    def caption_for_query(self, episode, timestamp, query):
        caps = self.captions(episode, timestamp)
        return process.extract(query, [c['Content'] for c in caps], limit=1)[0][0]

    def _render(self, episode, start, end, text=''):
        overlays = []
        if text:
            overlays.append({
                'text': text,
                'font': DEFAULT_FONT,
                'size': 0,
                'color': DEFAULT_COLOR,
                'x': 50,
                'y': 97,
                'text_align': 'c',
                'all_caps': False,
                'start': 0,
                'end': end - start,
            })

        res = requests.post(
            '{}/api/render/gif/stream'.format(self.base),
            json=[{'episode': episode, 'start': start, 'end': end, 'overlays': overlays}],
            stream=True,
            timeout=RENDER_TIMEOUT,
        )
        if not res.ok:
            raise RequestFailedException('Render request failed with status {}'.format(res.status_code))

        for line in res.iter_lines(decode_unicode=True):
            if not line:
                continue
            event = json.loads(line)
            if 'error' in event:
                raise RequestFailedException(event['error'])
            if 'url' in event:
                url = event['url']
                return url if url.startswith('http') else '{}{}'.format(self.base, url)

        raise RequestFailedException('Render stream ended without a result')

    def image_url(self, episode, timestamp, text=''):
        return self._render(episode, timestamp, timestamp + 1000, text)

    def gif_url(self, episode, start, end, text=''):
        return self._render(episode, start, end, text)

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
