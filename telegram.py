__author__ = "Altertech, https://www.altertech.com/"
__copyright__ = "Copyright (C) 2020 Altertech Group"
__license__ = "Apache License 2.0"
__version__ = "1.0.0"
__description__ = "Telegram bot"
__api__ = 6
__mods_required__ = ['tebot']

__config_help__ = [{
    'name': 'cf',
    'help': 'Config file (default: {dir_eva}/etc/telegram.yml)',
    'type': 'str',
    'required': False
}]

__functions__ = {
    'send(apikey_id, *args, **kwargs)': 'Send message',
    'send_photo(apikey_id, *args, **kwargs)': 'Send file as a photo',
    'send_video(apikey_id, *args, **kwargs)': 'Send file as a video',
    'send_audio(apikey_id, *args, **kwargs)': 'Send file as an audio',
    'send_document(apikey_id, *args, **kwargs)': 'Send file as a document',
}

__help__ = """
Telegram bot extension

Requires https://pypi.org/project/tebot/ module

Please see module help for the "send*" functions arguments.

When using "send*" functions, api key id (string or list) specifies target
users. If api key id is specified as "*", the broadcast message is sent.
"""

import importlib
import yaml
import os
import eva.core
import eva.apikey

from eva.lm.extensions.generic import LMExt as GenericExt
from eva.lm.extapi import log_traceback
from eva.lm.extapi import ext_constructor
from eva.lm.extapi import get_timeout

from eva.lm.lmapi import api

from eva.exceptions import AccessDenied, ResourceNotFound


class LMExt(GenericExt):

    @ext_constructor
    def __init__(self, **kwargs):
        try:
            try:
                cf = self.cfg.get('cf')
                if not cf: cf = eva.core.dir_etc + '/telegram.yml'
                with open(cf) as fh:
                    config = yaml.load(fh.read())
            except:
                self.log_error(f'unable to parse {cf}')
                raise
            try:
                mod = importlib.import_module('tebot')
            except:
                self.log_error('tebot Python module not installed')
                raise
            self.tebot = mod.TeBot(interval=config.get('interval', 2),
                                   on_error=log_traceback)
            self.tebot.set_token(config['token'])
            self.tebot.retry_interval = config.get('retry-interval')
            self.tebot.timeout = get_timeout()
            self.wait = float(config.get('wait', 60))
            self.reply_markup = {'inline_keyboard': []}
            self.bot_commands = []
            self.bot_help = []
            self.bot_help_builtin = ['help - get help', 'logout - log out']
            try:
                menu = config['menu']
                for row in menu:
                    row_data = []
                    self.reply_markup['inline_keyboard'].append(row_data)
                    for col in row:
                        data, text = col.split(':', 1)
                        row_data.append({
                            'text': text,
                            'callback_data': f'/{data}'
                        })
                        self.bot_help.append(f'{data} - {text}')
                        self.bot_commands.append(data)
                self.bot_commands = sorted(self.bot_commands)
                self.bot_help = sorted(self.bot_help)
            except:
                self.log_error('unable to parse menu')
                raise
            self.tebot.register_route(self.h_message, methods='message')
            self.tebot.register_route(self.h_start, path=['/start', '/help'])
            self.tebot.register_route(self.h_getcommands, path='/getcommands')
            self.tebot.register_route(self.h_logout, path='/logout')
            self.tebot.register_route(self.h_command, methods='*')
            with self.data_lock:
                self.data['auth'] = {}
                self.data_modified = True
        except:
            log_traceback()
            self.ready = False

    def start(self):
        self.tebot.start()
        return True

    def stop(self):
        self.tebot.stop()
        return True

    def h_start(self, chat_id, **kwargs):
        key_id = self.data['auth'].get(str(chat_id))
        if key_id:
            self._send_help(key_id)
        else:
            self.tebot.send('Enter valid API key to start')

    def _send_help(self, key_id):
        bot_help = ''.join([f'/{x}\n' for x in self.bot_help])
        bot_help_builtin = ''.join([f'/{x}\n' for x in self.bot_help_builtin])
        self.tebot.send(f'Usage:\n\n{bot_help}\n{bot_help_builtin}\n' +
                        f'current API key: {key_id}',
                        reply_markup=self.reply_markup)

    def h_getcommands(self, **kwargs):
        self.tebot.send('\n'.join(self.bot_help + self.bot_help_builtin))

    def h_message(self, chat_id, text, **kwargs):
        with self.data_lock:
            key_id = self.data['auth'].get(str(chat_id))
        if key_id:
            self.tebot.send(f'API key: <b>{key_id}</b>',
                            reply_markup=self.reply_markup)
        else:
            key_id = eva.apikey.key_id(text.strip())
            if key_id == 'unknown':
                self.tebot.send(f'Invalid API key. Try again')
            else:
                with self.data_lock:
                    self.data['auth'][str(chat_id)] = key_id
                    self.data_modified = True
                self.tebot.send(f'Registered API key: {key_id}')
                self._send_help(key_id)

    def h_logout(self, chat_id, **kwargs):
        with self.data_lock:
            try:
                del self.data['auth'][str(chat_id)]
                self.data_modified = True
                self.tebot.send(
                    'API key unregistered. Enter new API key to continue')
            except KeyError:
                self.tebot.send('API key not registered')
            except:
                log_traceback()

    def h_command(self, chat_id, path, query_string, **kwargs):
        with self.data_lock:
            key_id = self.data['auth'].get(str(chat_id))
        if not key_id:
            self.tebot.send(
                'Please enter valid API key before launching commands')
            return
        k = eva.apikey.key_by_id(key_id)
        cmd = path[1:]
        if cmd in self.bot_commands:
            try:
                result = api.run(k=k,
                                 i=cmd,
                                 a=query_string,
                                 kw={'chat_id': chat_id},
                                 w=self.wait)
                exitcode = result.get('exitcode')
                if exitcode is None:
                    self.tebot.send(f'{path} is still executing')
                else:
                    if exitcode:
                        self.tebot.send(f'{path} execution error',
                                        reply_markup=self.reply_markup)
                    else:
                        out = result.get('out')
                        self.tebot.send(f'{path} executed' +
                                        (f', output:\n{out}' if out else ''),
                                        reply_markup=self.reply_markup)
            except AccessDenied:
                self.tebot.send(f'Unable to execute {path}: access denied',
                                reply_markup=self.reply_markup)
            except ResourceNotFound:
                self.tebot.send(f'Unable to execute {path}: macro not found',
                                reply_markup=self.reply_markup)
            except:
                self.tebot.send(f'Unable to execute {path}',
                                reply_markup=self.reply_markup)
                log_traceback()
        else:
            self.tebot.send(f'Invalid command: {path}',
                            reply_markup=self.reply_markup)

    def send(self, apikey_id, *args, **kwargs):
        return self._send(self.tebot.send, apikey_id, *args, **kwargs)

    def send_photo(self, apikey_id, *args, **kwargs):
        return self._send(self.tebot.send_photo, apikey_id, *args, **kwargs)

    def send_video(self, apikey_id, *args, **kwargs):
        return self._send(self.tebot.send_video, apikey_id, *args, **kwargs)

    def send_audio(self, apikey_id, *args, **kwargs):
        return self._send(self.tebot.send_audio, apikey_id, *args, **kwargs)

    def send_audio(self, apikey_id, *args, **kwargs):
        return self._send(self.tebot.send_audio, apikey_id, *args, **kwargs)

    def send_document(self, apikey_id, *args, **kwargs):
        return self._send(self.tebot.send_document, apikey_id, *args, **kwargs)

    def _format_rcpt_list(self, apikey_id):
        with self.data_lock:
            if apikey_id == '*':
                return list(self.data['auth'])
            else:
                if not isinstance(apikey_id, list) and not isinstance(
                        apikey_id, tuple):
                    apikey_id = [apikey_id]
                rcpt = []
                for chat_id, v in self.data['auth'].items():
                    if v in apikey_id:
                        rcpt.append(chat_id)
                return rcpt

    def _send(self, send_func, apikey_id, *args, **kwargs):
        if apikey_id is None:
            if 'chat_id' in kwargs:
                send_func(*args, **kwargs)
            else:
                raise ValueError(
                    'either apikey_id or chat_id must be specified')
        else:
            receipients = self._format_rcpt_list(apikey_id)
            kwargs = kwargs.copy()
            for r in receipients:
                self.log_debug(f'sending message to chat_id {r}')
                kwargs['chat_id'] = r
                send_func(*args, **kwargs)
