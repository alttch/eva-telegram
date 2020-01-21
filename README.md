# eva-telegram

Telegram bot extension for EVA ICS LM PLC

Requires EVA ICS 3.3 or newer.

## Install

* put *telegram.py* to */opt/eva/xc/extensions/*

* put sample configuration file *telegram.yml* to */opt/eva/etc/*

* modify sample configuration

* load extension:

```shell
eva lm ext load tbot telegram
```

## Macro execution

Start chat with your bot and follow the instructions.

## Sending messages from macros

When loaded, e.g. as *tbot*, extension provides functions:

* tbot_send
* tbot_send_photo
* tbot_send_video
* tbot_send_audio
* tbot_send_document

Function arguments are the same as for https://pypi.org/project/tebot/, refer
to module documentation for more info, except first argument should be either
API key ID or list of API key IDs. If "\*" is specified, broadcast message is
sent.

### Examples

Send broadcast message to all

```python
    tbot_send('*', 'this is a test')
```

Send image to users with API key "operator" and "operator2":

```python
    with open('image.jpg', 'rb') as fh:
        tbot_send(['operator', 'operator2'], media=fh.read())
```
