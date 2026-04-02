import pytest
import json
from humorbot.bot import Humorbot, MORBO_USAGE, FRINK_USAGE


@pytest.fixture
def hb():
    return Humorbot()


def test_parse_args(hb):
    assert hb.parse_args('help') == ('help', '', '')
    assert hb.parse_args('usage') == ('help', '', '')
    assert hb.parse_args('do the hustle') == ('image', 'do the hustle', '')
    assert hb.parse_args('do the hustle -- do the bartman') == ('image', 'do the hustle', 'do the bartman')
    assert hb.parse_args('do the hustle | do the bartman') == ('image', 'do the hustle', 'do the bartman')
    assert hb.parse_args('do the hustle \u2013 do the bartman') == ('image', 'do the hustle', 'do the bartman')
    assert hb.parse_args('do the hustle \u2013 do the bartman   ') == ('image', 'do the hustle', 'do the bartman')
    assert hb.parse_args('do the hustle \u2013 do the bartman -- | \u2013') == ('image', 'do the hustle', 'do the bartman')
    assert hb.parse_args('do the hustle --') == ('image', 'do the hustle', '')
    assert hb.parse_args('image do the hustle --') == ('image', 'do the hustle', '')
    assert hb.parse_args('images do the hustle') == ('images', 'do the hustle', '')
    assert hb.parse_args('images do the hustle -- do the bartman') == ('images', 'do the hustle', 'do the bartman')
    assert hb.parse_args('gif do the hustle') == ('gif', 'do the hustle', '')
    assert hb.parse_args('gif do the hustle -- do the bartman') == ('gif', 'do the hustle', 'do the bartman')


def test_process_command_help(hb):
    assert hb.process_command('morbo', {'text': 'help'}) == {'text': MORBO_USAGE, 'response_type': 'ephemeral'}
    assert hb.process_command('morbo', {'text': 'usage'}) == {'text': MORBO_USAGE, 'response_type': 'ephemeral'}
    assert hb.process_command('frink', {'text': 'help'}) == {'text': FRINK_USAGE, 'response_type': 'ephemeral'}
    assert hb.process_command('frink', {'text': 'usage'}) == {'text': FRINK_USAGE, 'response_type': 'ephemeral'}
    assert hb.process_command('morbo', {'text': ''}) == {'text': MORBO_USAGE, 'response_type': 'ephemeral'}
    assert hb.process_command('frink', {'text': ''}) == {'text': FRINK_USAGE, 'response_type': 'ephemeral'}


@pytest.mark.integration
def test_image(hb):
    res = hb.image('someone', 'do the hustle')
    assert res['response_type'] == 'in_channel'
    assert len(res['blocks']) == 2
    assert res['blocks'][0]['type'] == 'section'
    assert '@someone' in res['blocks'][0]['text']['text']
    assert '/morbo' in res['blocks'][0]['text']['text']
    assert res['blocks'][1]['type'] == 'image'
    assert 'morbotron.com' in res['blocks'][1]['image_url']

    res = hb.image('someone', 'rebigulator', command='frink')
    assert res['response_type'] == 'in_channel'
    assert len(res['blocks']) == 2
    assert '/frink' in res['blocks'][0]['text']['text']
    assert 'frinkiac.com' in res['blocks'][1]['image_url']

    res = hb.image('someone', 'do the hustle', 'lol')
    assert res['response_type'] == 'in_channel'
    assert 'b64lines=' in res['blocks'][1]['image_url']


@pytest.mark.integration
def test_image_random(hb):
    res = hb.image('someone', 'do the hustle', 'lol', random=True)
    assert res['response_type'] == 'in_channel'
    assert len(res['blocks']) == 2


@pytest.mark.integration
def test_images(hb):
    res = hb.images('someone', 'do the hustle')
    assert res['response_type'] == 'ephemeral'
    # 10 images * 2 blocks each (image + actions) + 1 cancel block = 21
    assert len(res['blocks']) == 21
    # Last block should be cancel
    assert res['blocks'][-1]['elements'][0]['action_id'] == 'cancel'


@pytest.mark.integration
def test_gif(hb):
    res = hb.gif('someone', 'do the hustle')
    assert res['response_type'] == 'ephemeral'
    assert res['blocks'][0]['type'] == 'image'
    assert '.gif' in res['blocks'][0]['image_url']
    # Should have image + actions (send/edit/cancel)
    assert res['blocks'][1]['type'] == 'actions'
    action_ids = [e['action_id'] for e in res['blocks'][1]['elements']]
    assert 'send_image' in action_ids
    assert 'edit_gif' in action_ids
    assert 'cancel' in action_ids


@pytest.mark.integration
def test_process_command_image(hb):
    res = hb.process_command('morbo', {'text': 'do the hustle', 'user_name': 'someone'})
    assert res['response_type'] == 'in_channel'
    assert len(res['blocks']) == 2
    assert 'morbotron.com' in res['blocks'][1]['image_url']

    res = hb.process_command('frink', {'text': 'rebigulator', 'user_name': 'someone'})
    assert res['response_type'] == 'in_channel'
    assert 'frinkiac.com' in res['blocks'][1]['image_url']


def test_send(hb):
    payload = {
        'user': {'name': 'testuser'},
        'actions': [{
            'action_id': 'send_image',
            'value': json.dumps({
                'url': 'https://morbotron.com/meme/S05E02/278561.jpg',
                'text': 'Do the Hustle',
                'args': 'do the hustle',
                'command': 'morbo',
            }),
        }],
    }
    res = hb.send(payload)
    assert res['response_type'] == 'in_channel'
    assert res['delete_original'] is True
    assert len(res['blocks']) == 2
    assert '@testuser' in res['blocks'][0]['text']['text']
    assert res['blocks'][1]['image_url'] == 'https://morbotron.com/meme/S05E02/278561.jpg'


def test_update_gif(hb):
    payload = {
        'actions': [{
            'action_id': 'edit_gif',
            'value': json.dumps({
                'args': 'gif do the hustle',
                'text': 'Do the Hustle',
                'episode': 'S05E02',
                'context': [100, 200, 300, 400, 500],
                'start': 200,
                'end': 400,
                'show_text': True,
                'command': 'morbo',
            }),
        }],
    }
    res = hb.update_gif(payload)
    assert res['response_type'] == 'ephemeral'
    # image + actions (send/toggle/cancel) + divider + 5 frames * 2 blocks = 13
    assert len(res['blocks']) == 13
    assert res['blocks'][0]['type'] == 'image'
    assert res['blocks'][1]['type'] == 'actions'
    assert res['blocks'][2]['type'] == 'divider'
    # Frame blocks
    assert res['blocks'][3]['type'] == 'section'
    assert res['blocks'][4]['type'] == 'actions'
