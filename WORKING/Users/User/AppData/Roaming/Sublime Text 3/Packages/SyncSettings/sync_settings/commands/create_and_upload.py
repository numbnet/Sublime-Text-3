# -*- coding: utf-8 -*-

import sublime
import sublime_plugin

from . import decorators
from ..libs import gist
from ..libs.logger import logger
from ..libs import settings
from .. import sync_version as version, sync_manager as manager
from ..thread_progress import ThreadProgress


class SyncSettingsCreateAndUploadCommand(sublime_plugin.WindowCommand):
    @decorators.check_settings('access_token')
    def run(self):
        sublime.set_timeout(lambda: self.window.show_input_panel(
            caption='Enter gist description',
            initial_text='',
            on_done=self.on_done,
            on_change=None,
            on_cancel=None
        ), 10)

    def on_done(self, description):
        files = manager.get_files()
        if not len(files):
            sublime.status_message('Sync Settings: there are not files to upload')
            return
        data = {'files': files}
        if description:
            data.update({'description': description})
        ThreadProgress(
            target=lambda: self.create(data),
            message='creating gist'
        )

    @staticmethod
    def create(data):
        try:
            g = gist.Gist(
                token=settings.get('access_token'),
                http_proxy=settings.get('http_proxy'),
                https_proxy=settings.get('https_proxy')
            ).create(data)
            msg = (
                'Sync Settings:\n\n'
                'Your gist `{}` was created successfully\n\n'
                'Do you want to overwrite the current `gist_id` property with the created gist?'
            )
            answer = sublime.yes_no_cancel_dialog(msg.format(g['id']))
            if answer == sublime.DIALOG_NO:
                sublime.set_clipboard(g['id'])
                sublime.status_message('Sync Settings: the created gist`s id, has been copied to clipboard')
            if answer == sublime.DIALOG_YES:
                commit = g['history'][0]
                settings.update('gist_id', g['id'])
                version.update_config_file({
                    'hash': commit['version'],
                    'created_at': commit['committed_at'],
                })
                sublime.status_message('Sync Settings: gist created')
        except gist.NotFoundError as e:
            msg = (
                'Sync Settings:\n\n'
                'Apparently the token was not created with gist scope enabled.\n\n'
                'Please, check your token or create a new one.\n\n'
                'more info: https://help.github.com/articles/creating-a-personal-access-token-for-the-command-line/'
            )
            sublime.message_dialog(msg.format(str(e)))
        except Exception as e:
            logger.exception(e)
            sublime.message_dialog('Sync Settings:\n\n{}'.format(str(e)))
