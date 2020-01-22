# eva-telegram

Telegram bot extension for [EVA ICS](https://www.eva-ics.com/) LM PLC

Requires EVA ICS 3.3 or newer.

## Install

* install [tebot](https://pypi.org/project/tebot/) module

* put *telegram.py* to */opt/eva/xc/extensions/*

* put sample configuration file *telegram.yml* to */opt/eva/etc/*

* modify sample configuration

* load extension:

```shell
eva lm ext load tbot telegram -y
```

## Macro execution

Start chat with your bot and follow the instructions.

* if macros is started as "/macro some args", args are added to macro arguments.

* current *chat_id* is passed into macro kwargs and may be used later.

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

Send a message only to user who called macro

```python
# chat_id variable is available in macro, as it was sent in kwargs
tbot_send(None, 'this is a reply', chat_id=chat_id)
```

Send broadcast message to all

```python
tbot_send('*', 'this is a test')
```

Send image to users with API key IDs "operator" and "operator2":

```python
with open('image.jpg', 'rb') as fh:
    tbot_send(['operator', 'operator2'], media=fh.read())
```

## Command autocomplete

After log in, use */getcommands* command, go to [Telegram
BotFather](https://telegram.me/BotFather), enter */setcommands* and paste it
as-is.

## Exclude command from the keyboard

To exclude command from the inline keyboard, put dot before macro in "menu"
section of the configuration.

## Security

* using master key is not recommended

* write dedicated macros

* if possible - use dedicated instance of LM PLC

