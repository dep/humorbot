# humorbot

A Slack app for searching and sharing screenshots and GIFs from [Frinkiac](https://frinkiac.com) (The Simpsons) and [Morbotron](https://morbotron.com) (Futurama).

## Commands

- `/frink <search>` - Search Frinkiac for Simpsons screenshots
- `/morbo <search>` - Search Morbotron for Futurama screenshots

### Modes

| Mode | Example | Description |
|------|---------|-------------|
| Default | `/frink homer` | Returns the first matching image |
| `random` | `/frink random homer` | Returns a random match |
| `images` | `/frink images homer` | Shows a selection of images to choose from |
| `gif` | `/frink gif homer` | Generates an animated GIF with an editor |
| `gifs` | `/frink gifs homer` | Shows a selection of GIFs to choose from |
| `help` | `/frink help` | Shows usage instructions |

### Text overlays

Use `|` or `--` to specify custom overlay text:

```
/frink do the hustle | do the bartman
/morbo gif shut up and take my money | just take it
```

Use a trailing `|` with nothing after it to remove the overlay entirely:

```
/frink homer |
```

## Setup

1. Create a Slack app from manifest at https://api.slack.com/apps
2. Set environment variables (see `.env.example`):
   - `SLACK_BOT_TOKEN` - Bot token from OAuth & Permissions (starts with `xoxb-`)
   - `SLACK_SIGNING_SECRET` - From app Basic Information page
3. Deploy to Heroku or run locally with `gunicorn "humorbot:create_app()"`

## Development

```
pip install -e ".[dev]"
pytest
```

## Credits

Originally built by [snare](https://github.com/snare/humorbot) in 2016. Completely reworked and modernized in 2026 — updated from legacy Slack APIs to [Bolt for Python](https://docs.slack.dev/tools/bolt-python/), replaced deprecated dependencies, converted to Block Kit, and brought back online for a new generation of Simpsons and Futurama shitposting.

[Frinkiac](https://frinkiac.com) and [Morbotron](https://morbotron.com) were built by their respective developers — all credit to them for the amazing screenshot databases.
