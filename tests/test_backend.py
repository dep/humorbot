import json
import pytest
from unittest.mock import patch, MagicMock
from humorbot.backend import Morbotron, Frinkiac, RequestFailedException


@pytest.fixture
def morbo():
    return Morbotron()


@pytest.fixture
def frink():
    return Frinkiac()


@pytest.mark.integration
def test_search(morbo, frink):
    res = morbo.search('do the hustle')
    assert len(res) == 36
    res = frink.search('glayvin')
    assert len(res) == 36


@pytest.mark.integration
def test_context_frames(morbo, frink):
    res = morbo.context_frames('S09E06', 729604)
    assert len(res) == 38
    res = frink.context_frames('S15E01', 437270)
    assert len(res) == 29


@pytest.mark.integration
def test_captions(morbo, frink):
    res = morbo.captions('S05E02', 278561)
    assert len(res) == 2
    assert res[0]['Content'] == '( "The Hustle" plays )'
    assert res[1]['Content'] == '\u266a Do the Hustle... \u266a'

    res = frink.captions('S15E01', 437270)
    assert len(res) == 2
    assert 'PROF. FRINK: Great glayvin in a glass!' in res[0]['Content']
    assert res[1]['Content'] == 'The Nobel prize.'


@pytest.mark.integration
def test_caption_for_query(morbo):
    assert morbo.caption_for_query('S05E02', 278561, 'do the hustle') == '\u266a Do the Hustle... \u266a'
    assert morbo.caption_for_query('S05E02', 278561, 'the hustle') == '\u266a Do the Hustle... \u266a'
    assert morbo.caption_for_query('S05E02', 278561, 'plays') == '( "The Hustle" plays )'


def _mock_render_response(*events):
    res = MagicMock()
    res.ok = True
    res.iter_lines.return_value = [json.dumps(e) for e in events]
    return res


def test_image_url(morbo):
    with patch('humorbot.backend.requests.post', return_value=_mock_render_response(
        {'progress': 0.5}, {'url': '/video/S09E06/abc123.gif'},
    )) as mpost:
        assert morbo.image_url('S09E06', 729604, 'xxx') == 'https://morbotron.com/video/S09E06/abc123.gif'
        payload = mpost.call_args.kwargs['json'][0]
        assert payload['episode'] == 'S09E06'
        assert payload['start'] == 729604
        assert payload['end'] == 730604
        assert payload['overlays'][0]['text'] == 'xxx'


def test_thumb_url(morbo):
    assert morbo.thumb_url('S09E06', 729604) == 'https://morbotron.com/img/S09E06/729604/small.jpg'


def test_gif_url(morbo):
    with patch('humorbot.backend.requests.post', return_value=_mock_render_response(
        {'url': 'https://morbotron.com/video/S09E06/def456.gif'},
    )):
        assert morbo.gif_url('S09E06', 729604, 729605, 'xxx') == 'https://morbotron.com/video/S09E06/def456.gif'


def test_render_error(morbo):
    with patch('humorbot.backend.requests.post', return_value=_mock_render_response(
        {'error': 'end must be greater than start'},
    )):
        with pytest.raises(RequestFailedException):
            morbo.gif_url('S09E06', 729604, 729604)
