import re
import json
import logging
from random import choice
from .backend import Frinkiac, Morbotron

log = logging.getLogger()

MORBO_USAGE = """Display this help:
`/morbo help`
Generate a still image for _do the hustle_:
`/morbo do the hustle`
`/morbo image do the hustle`
Generate a still image for search term _do the hustle_ with a different text overlay (rather than the subtitles):
`/morbo do the hustle | do the bartman`
`/morbo image do the hustle | do the bartman`
Generate a still image for the search term _do the hustle_ with no text overlay:
`/morbo do the hustle |`
Generate a selection of still images for _do the hustle_:
`/morbo images do the hustle`
Generate a GIF for _do the hustle_:
`/morbo gif do the hustle`
Generate a GIF with search term _sure baby, i know it_ but text overlay _shut up baby, i know it_ (because Morbotron has the wrong subtitles so it won't match properly):
`/morbo gif sure baby, i know it | shut up baby, i know it`
Generate a selection of GIFs for _seymour_:
`/morbo gifs seymour`
"""

FRINK_USAGE = """Display this help:
`/frink help`
Generate a still image for _don't mind if i do_:
`/frink don't mind if i do`
`/frink image don't mind if i do`
Generate a still image for search term _don't mind if i do_ with a different text overlay (rather than the subtitles):
`/frink don't mind if i do | snare sux`
`/frink image don't mind if i do | snare sux`
Generate a still image for the search term _don't mind if i do_ with no text overlay:
`/frink don't mind if i do |`
Generate a selection of still images for _don't mind if i do_:
`/frink images don't mind if i do`
Generate a GIF for _don't mind if i do_:
`/frink gif don't mind if i do`
Generate a GIF for _don't mind if i do_ with a different text overlay:
`/frink gif don't mind if i do | do mind if I don't`
Generate a selection of GIFs for _rebigulator_:
`/frink gifs rebigulator`
"""

MAX_IMAGES = 10
MAX_GIFS = 5
MAX_EDITOR_FRAMES = 20


class Humorbot:
    def __init__(self):
        self.frink = Frinkiac()
        self.morbo = Morbotron()

    def backend(self, name):
        if 'frink' in name:
            return self.frink
        else:
            return self.morbo

    def parse_args(self, text):
        tokens = text.split()
        valid_actions = ['help', 'usage', 'image', 'images', 'random', 'gif', 'gifs']
        if len(tokens) and tokens[0] in valid_actions:
            action = tokens[0]
            tokens.pop(0)
        elif len(tokens) == 0:
            action = 'help'
        else:
            action = 'image'
        if action == 'usage':
            action = 'help'
        rest = ' '.join(tokens)

        tokens = re.split(r'(--|–|\|)', rest)
        if len(tokens) > 2:
            query = tokens[0]
            overlay = tokens[2]
        else:
            query = rest
            overlay = ''

        return (action.strip(), query.strip(), overlay.strip())

    def process_command(self, command, data):
        (action, query, overlay) = self.parse_args(data['text'])

        log.debug('Processing /{} {} action with query \'{}\' and text overlay \'{}\''.format(
            command, action, query, overlay
        ))
        log.info('command={}, username={}, team_domain={}, text={}'.format(
            command, data.get('user_name', ''), data.get('team_domain', ''), data['text']
        ))

        if action == 'help':
            if 'morbo' in command:
                res = {'text': MORBO_USAGE, 'response_type': 'ephemeral'}
            else:
                res = {'text': FRINK_USAGE, 'response_type': 'ephemeral'}
        elif action in ['image', 'random']:
            res = self.image(data.get('user_name', 'someone'), query, overlay, command, random=(action == 'random'))
        elif action == 'images':
            res = self.images(data.get('user_name', 'someone'), query, overlay, command)
        elif action == 'gif':
            res = self.gif(data.get('user_name', 'someone'), query, overlay, command)
        elif action == 'gifs':
            res = self.gifs(data.get('user_name', 'someone'), query, overlay, command)
        else:
            res = {'text': 'Unknown action.', 'response_type': 'ephemeral'}

        return res

    def image(self, username, query, overlay='', command='morbo', random=False):
        backend = self.backend(command)
        search_result = backend.search(query)
        if len(search_result):
            r = choice(search_result) if random else search_result[0]
            args = '{} | {}'.format(query, overlay) if overlay else '{}{}'.format('random ' if random else '', query)
            if not overlay:
                overlay = backend.caption_for_query(r['Episode'], r['Timestamp'], query)
            url = backend.image_url(r['Episode'], r['Timestamp'], overlay)
            res = {
                'response_type': 'in_channel',
                'blocks': [
                    {
                        'type': 'section',
                        'text': {'type': 'mrkdwn', 'text': '@{}: /{} {}'.format(username, command, args)},
                    },
                    {
                        'type': 'image',
                        'image_url': url,
                        'alt_text': '{} {}'.format(command, args),
                    },
                ],
            }
        else:
            res = {'text': "No match for '{}'".format(query), 'response_type': 'ephemeral'}

        return res

    def images(self, username, query, overlay='', command='morbo'):
        backend = self.backend(command)
        search_result = backend.search(query)

        blocks = []
        ol = overlay
        for r in search_result[:min(MAX_IMAGES, len(search_result))]:
            args = 'images {} | {}'.format(query, overlay) if overlay else 'images {}'.format(query)
            if not overlay:
                ol = backend.caption_for_query(r['Episode'], r['Timestamp'], query)
            url = backend.image_url(r['Episode'], r['Timestamp'], ol)
            blocks.append({
                'type': 'image',
                'image_url': url,
                'alt_text': ol or query,
            })
            blocks.append({
                'type': 'actions',
                'elements': [{
                    'type': 'button',
                    'text': {'type': 'plain_text', 'text': 'Send'},
                    'style': 'primary',
                    'action_id': 'send_image',
                    'value': json.dumps({
                        'url': url,
                        'text': ol,
                        'args': args,
                        'command': command,
                    }),
                }],
            })

        blocks.append({
            'type': 'actions',
            'elements': [{
                'type': 'button',
                'text': {'type': 'plain_text', 'text': 'Cancel'},
                'action_id': 'cancel',
                'value': 'cancel',
            }],
        })

        return {
            'response_type': 'ephemeral',
            'blocks': blocks,
        }

    def gif(self, username, query, overlay='', command='morbo'):
        backend = self.backend(command)
        search_result = backend.search(query)

        if len(search_result):
            context = backend.context_frames(search_result[0]['Episode'], search_result[0]['Timestamp'])
            if len(context):
                args = 'gif {} | {}'.format(query, overlay) if overlay else 'gif {}'.format(query)
                if not overlay:
                    overlay = backend.caption_for_query(
                        search_result[0]['Episode'], search_result[0]['Timestamp'], query
                    )
                url = backend.gif_url(
                    context[0]['Episode'], context[0]['Timestamp'], context[-1]['Timestamp'], overlay
                )
                res = {
                    'response_type': 'ephemeral',
                    'blocks': [
                        {
                            'type': 'image',
                            'image_url': url,
                            'alt_text': 'GIF preview',
                        },
                        {
                            'type': 'actions',
                            'elements': [
                                {
                                    'type': 'button',
                                    'text': {'type': 'plain_text', 'text': 'Send'},
                                    'style': 'primary',
                                    'action_id': 'send_image',
                                    'value': json.dumps({
                                        'url': url,
                                        'text': overlay,
                                        'args': args,
                                        'command': command,
                                    }),
                                },
                                {
                                    'type': 'button',
                                    'text': {'type': 'plain_text', 'text': 'Edit'},
                                    'action_id': 'edit_gif',
                                    'value': json.dumps({
                                        'args': args,
                                        'text': overlay,
                                        'episode': context[0]['Episode'],
                                        'context': [i['Timestamp'] for i in context],
                                        'start': context[0]['Timestamp'],
                                        'end': context[-1]['Timestamp'],
                                        'show_text': True,
                                        'command': command,
                                    }),
                                },
                                {
                                    'type': 'button',
                                    'text': {'type': 'plain_text', 'text': 'Cancel'},
                                    'action_id': 'cancel',
                                    'value': 'cancel',
                                },
                            ],
                        },
                    ],
                }
            else:
                res = {'text': 'Failed to get context', 'response_type': 'ephemeral'}
        else:
            res = {'text': "No match for '{}'".format(query), 'response_type': 'ephemeral'}

        return res

    def gifs(self, username, query, overlay='', command='morbo'):
        backend = self.backend(command)
        search_result = backend.search(query)

        blocks = []
        ol = overlay
        for r in search_result[:min(MAX_GIFS, len(search_result))]:
            context = backend.context_frames(r['Episode'], r['Timestamp'])
            if len(context):
                args = 'gifs {} | {}'.format(query, overlay) if overlay else 'gifs {}'.format(query)
                if not overlay:
                    ol = backend.caption_for_query(r['Episode'], r['Timestamp'], query)
                url = backend.gif_url(
                    context[0]['Episode'], context[0]['Timestamp'], context[-1]['Timestamp'], ol
                )
                blocks.append({
                    'type': 'image',
                    'image_url': url,
                    'alt_text': 'GIF preview',
                })
                blocks.append({
                    'type': 'actions',
                    'elements': [
                        {
                            'type': 'button',
                            'text': {'type': 'plain_text', 'text': 'Send'},
                            'style': 'primary',
                            'action_id': 'send_image',
                            'value': json.dumps({
                                'url': url,
                                'text': ol,
                                'args': args,
                                'command': command,
                            }),
                        },
                        {
                            'type': 'button',
                            'text': {'type': 'plain_text', 'text': 'Edit'},
                            'action_id': 'edit_gif',
                            'value': json.dumps({
                                'args': args,
                                'text': ol,
                                'episode': context[0]['Episode'],
                                'context': [i['Timestamp'] for i in context],
                                'start': context[0]['Timestamp'],
                                'end': context[-1]['Timestamp'],
                                'show_text': True,
                                'command': command,
                            }),
                        },
                    ],
                })

        blocks.append({
            'type': 'actions',
            'elements': [{
                'type': 'button',
                'text': {'type': 'plain_text', 'text': 'Cancel'},
                'action_id': 'cancel',
                'value': 'cancel',
            }],
        })

        return {
            'response_type': 'ephemeral',
            'blocks': blocks,
        }

    def send(self, payload):
        action = payload['actions'][0]
        data = json.loads(action['value'])
        username = payload['user']['name']
        return {
            'response_type': 'in_channel',
            'delete_original': True,
            'blocks': [
                {
                    'type': 'section',
                    'text': {
                        'type': 'mrkdwn',
                        'text': '@{}: /{} {}'.format(username, data['command'], data['args']),
                    },
                },
                {
                    'type': 'image',
                    'image_url': data['url'],
                    'alt_text': '{} {}'.format(data['command'], data['args']),
                },
            ],
        }

    def update_gif(self, payload):
        action = payload['actions'][0]
        data = json.loads(action['value'])
        backend = self.backend(data['command'])
        url = backend.gif_url(
            data['episode'], data['start'], data['end'],
            data['text'] if data['show_text'] else ''
        )

        blocks = [
            {
                'type': 'image',
                'image_url': url,
                'alt_text': 'GIF preview',
            },
        ]

        show_hide_data = dict(data)
        show_hide_data['show_text'] = not show_hide_data['show_text']

        blocks.append({
            'type': 'actions',
            'elements': [
                {
                    'type': 'button',
                    'text': {'type': 'plain_text', 'text': 'Send'},
                    'style': 'primary',
                    'action_id': 'send_image',
                    'value': json.dumps({
                        'url': url,
                        'text': data['text'],
                        'args': data['args'],
                        'command': data['command'],
                    }),
                },
                {
                    'type': 'button',
                    'text': {'type': 'plain_text', 'text': '{} text'.format(
                        'Hide' if data['show_text'] else 'Show'
                    )},
                    'action_id': 'toggle_text',
                    'value': json.dumps(show_hide_data),
                },
                {
                    'type': 'button',
                    'text': {'type': 'plain_text', 'text': 'Cancel'},
                    'action_id': 'cancel',
                    'value': 'cancel',
                },
            ],
        })

        blocks.append({'type': 'divider'})

        # Limit frames to stay within Slack's 50-block cap
        context = data['context']
        if len(context) > MAX_EDITOR_FRAMES:
            # Center around current start frame
            start_idx = context.index(data['start'])
            half = MAX_EDITOR_FRAMES // 2
            begin = max(0, start_idx - half)
            end = begin + MAX_EDITOR_FRAMES
            if end > len(context):
                end = len(context)
                begin = max(0, end - MAX_EDITOR_FRAMES)
            context = context[begin:end]

        start_idx = context.index(data['start']) if data['start'] in context else 0
        end_idx = context.index(data['end']) if data['end'] in context else len(context) - 1

        for i, timestamp in enumerate(context):
            in_range = start_idx <= i <= end_idx
            marker = ':large_green_circle:' if in_range else ':white_circle:'

            start_data = dict(data)
            start_data['start'] = timestamp
            end_data = dict(data)
            end_data['end'] = timestamp

            blocks.append({
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': '{} Frame {} of episode {}'.format(marker, timestamp, data['episode']),
                },
                'accessory': {
                    'type': 'image',
                    'image_url': backend.thumb_url(data['episode'], timestamp),
                    'alt_text': 'Frame {}'.format(timestamp),
                },
            })
            blocks.append({
                'type': 'actions',
                'elements': [
                    {
                        'type': 'button',
                        'text': {'type': 'plain_text', 'text': 'Start frame'},
                        'action_id': 'set_start_{}'.format(i),
                        'value': json.dumps(start_data),
                    },
                    {
                        'type': 'button',
                        'text': {'type': 'plain_text', 'text': 'End frame'},
                        'action_id': 'set_end_{}'.format(i),
                        'value': json.dumps(end_data),
                    },
                ],
            })

        return {
            'response_type': 'ephemeral',
            'blocks': blocks,
        }
