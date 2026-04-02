import pytest
from humorbot.backend import Morbotron, Frinkiac


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


def test_image_url(morbo):
    assert morbo.image_url('S09E06', 729604) == 'https://morbotron.com/meme/S09E06/729604.jpg'
    assert morbo.image_url('S09E06', 729604, 'xxx') == 'https://morbotron.com/meme/S09E06/729604.jpg?b64lines=eHh4'


def test_thumb_url(morbo):
    assert morbo.thumb_url('S09E06', 729604) == 'https://morbotron.com/img/S09E06/729604/small.jpg'


def test_gif_url(morbo):
    assert morbo.gif_url('S09E06', 729604, 729605) == 'https://morbotron.com/gif/S09E06/729604/729605.gif'
    assert morbo.gif_url('S09E06', 729604, 729605, 'xxx') == 'https://morbotron.com/gif/S09E06/729604/729605.gif?b64lines=eHh4'
