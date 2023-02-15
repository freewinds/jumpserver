import os
import time

import winreg
import win32api
import win32con

import const as c

from pywinauto import Application
from pywinauto.keyboard import send_keys
from pywinauto.controls.uia_controls import (
    EditWrapper, ComboBoxWrapper, ButtonWrapper
)

from common import wait_pid, BaseApplication, _messageBox

_default_path = r'C:\Program Files\PremiumSoft\Navicat Premium 16\navicat.exe'


class AppletApplication(BaseApplication):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.path = _default_path
        self.username = self.account.username
        self.password = self.account.secret
        self.privileged = self.account.privileged
        self.host = self.asset.address
        self.port = self.asset.get_protocol_port(self.protocol)
        self.db = self.asset.spec_info.db_name
        self.name = '%s-%s-%s' % (self.host, self.db, int(time.time()))
        self.pid = None
        self.app = None

    @staticmethod
    def clean_up():
        protocols = (
            'NavicatMARIADB', 'NavicatMONGODB', 'Navicat',
            'NavicatORA', 'NavicatMSSQL', 'NavicatPG'
        )
        for p in protocols:
            sub_key = r'Software\PremiumSoft\%s\Servers' % p
            try:
                win32api.RegDeleteTree(winreg.HKEY_CURRENT_USER, sub_key)
            except Exception:
                pass

    def launch(self):
        # 清理因为异常未关闭的会话历史记录
        self.clean_up()
        sub_key = r'Software\PremiumSoft\NavicatPremium'
        try:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, sub_key)
            # 禁止弹出欢迎页面
            winreg.SetValueEx(key, 'AlreadyShowNavicatV16WelcomeScreen', 0, winreg.REG_DWORD, 1)
            # 禁止开启自动检查更新
            winreg.SetValueEx(key, 'AutoCheckUpdate', 0, winreg.REG_DWORD, 0)
            # 禁止弹出初始化界面
            winreg.SetValueEx(key, 'ShareUsageData', 0, winreg.REG_DWORD, 0)
        except Exception as err:
            print('Launch error: %s' % err)

    @staticmethod
    def _exec_commands(commands):
        for command in commands:
            pre_check = command.get('pre_check', lambda: True)
            if not pre_check():
                _messageBox('程序启动异常,请重新连接!!', 'Error', win32con.MB_DEFAULT_DESKTOP_ONLY)
                return
            time.sleep(0.5)
            if command['type'] == 'key':
                send_keys(' '.join(command['commands']))
            elif command['type'] == 'action':
                for f in command['commands']:
                    f()

    def _pre_check_is_password_input(self):
        try:
            self.app.window(best_match='Connection Password')
        except Exception:
            return False
        return True

    def _action_not_remember_password(self):
        conn_window = self.app.window(best_match='Dialog'). \
            child_window(title_re='New Connection')
        remember_checkbox = conn_window.child_window(best_match='Save password')
        remember_checkbox.click()

    def _fill_mysql_auth_info(self):
        conn_window = self.app.window(best_match='Dialog'). \
            child_window(title_re='New Connection')

        name_ele = conn_window.child_window(best_match='Edit5')
        EditWrapper(name_ele.element_info).set_edit_text(self.name)

        host_ele = conn_window.child_window(best_match='Edit4')
        EditWrapper(host_ele.element_info).set_edit_text(self.host)

        port_ele = conn_window.child_window(best_match='Edit2')
        EditWrapper(port_ele.element_info).set_edit_text(self.port)

        username_ele = conn_window.child_window(best_match='Edit1')
        EditWrapper(username_ele.element_info).set_edit_text(self.username)

    def _get_mysql_commands(self):
        commands = [
            {
                'type': 'key',
                'commands': [
                    '%f', c.DOWN, c.RIGHT, c.ENTER
                ],
            },
            {
                'type': 'action',
                'commands': [
                    self._fill_mysql_auth_info, self._action_not_remember_password
                ]
            },
            {
                'type': 'key',
                'commands': [c.ENTER]
            }
        ]
        return commands

    def _get_mariadb_commands(self):
        commands = [
            {
                'type': 'key',
                'commands': [
                    '%f', c.DOWN, c.RIGHT, c.DOWN * 5, c.ENTER,
                ],
            },
            {
                'type': 'action',
                'commands': [
                    self._fill_mysql_auth_info, self._action_not_remember_password
                ]
            },
            {
                'type': 'key',
                'commands': [c.ENTER]
            }
        ]
        return commands

    def _fill_mongodb_auth_info(self):
        conn_window = self.app.window(best_match='Dialog'). \
            child_window(title_re='New Connection')

        auth_type_ele = conn_window.child_window(best_match='ComboBox2')
        ComboBoxWrapper(auth_type_ele.element_info).select('Password')

        name_ele = conn_window.child_window(best_match='Edit5')
        EditWrapper(name_ele.element_info).set_edit_text(self.name)

        host_ele = conn_window.child_window(best_match='Edit4')
        EditWrapper(host_ele.element_info).set_edit_text(self.host)

        port_ele = conn_window.child_window(best_match='Edit2')
        EditWrapper(port_ele.element_info).set_edit_text(self.port)

        db_ele = conn_window.child_window(best_match='Edit6')
        EditWrapper(db_ele.element_info).set_edit_text(self.db)

        username_ele = conn_window.child_window(best_match='Edit1')
        EditWrapper(username_ele.element_info).set_edit_text(self.username)

    def _get_mongodb_commands(self):
        commands = [
            {
                'type': 'key',
                'commands': [
                    '%f', c.DOWN, c.RIGHT, c.DOWN * 6, c.ENTER,
                ],
            },
            {
                'type': 'action',
                'commands': [
                    self._fill_mongodb_auth_info, self._action_not_remember_password
                ]
            },
            {
                'type': 'key',
                'commands': [c.ENTER]
            }
        ]
        return commands

    def _fill_postgresql_auth_info(self):
        conn_window = self.app.window(best_match='Dialog'). \
            child_window(title_re='New Connection')

        name_ele = conn_window.child_window(best_match='Edit6')
        EditWrapper(name_ele.element_info).set_edit_text(self.name)

        host_ele = conn_window.child_window(best_match='Edit5')
        EditWrapper(host_ele.element_info).set_edit_text(self.host)

        port_ele = conn_window.child_window(best_match='Edit2')
        EditWrapper(port_ele.element_info).set_edit_text(self.port)

        db_ele = conn_window.child_window(best_match='Edit4')
        EditWrapper(db_ele.element_info).set_edit_text(self.db)

        username_ele = conn_window.child_window(best_match='Edit1')
        EditWrapper(username_ele.element_info).set_edit_text(self.username)

    def _get_postgresql_commands(self):
        commands = [
            {
                'type': 'key',
                'commands': [
                    '%f', c.DOWN, c.RIGHT, c.DOWN, c.ENTER,
                ],
            },
            {
                'type': 'action',
                'commands': [
                    self._fill_postgresql_auth_info, self._action_not_remember_password
                ]
            },
            {
                'type': 'key',
                'commands': [c.ENTER]
            }
        ]
        return commands

    def _fill_sqlserver_auth_info(self):
        conn_window = self.app.window(best_match='Dialog'). \
            child_window(title_re='New Connection')

        name_ele = conn_window.child_window(best_match='Edit5')
        EditWrapper(name_ele.element_info).set_edit_text(self.name)

        host_ele = conn_window.child_window(best_match='Edit4')
        EditWrapper(host_ele.element_info).set_edit_text('%s,%s' % (self.host, self.port))

        db_ele = conn_window.child_window(best_match='Edit3')
        EditWrapper(db_ele.element_info).set_edit_text(self.db)

        username_ele = conn_window.child_window(best_match='Edit6')
        EditWrapper(username_ele.element_info).set_edit_text(self.username)

    def _get_sqlserver_commands(self):
        commands = [
            {
                'type': 'key',
                'commands': [
                    '%f', c.DOWN, c.RIGHT, c.DOWN * 4, c.ENTER,
                ],
            },
            {
                'type': 'action',
                'commands': [
                    self._fill_sqlserver_auth_info, self._action_not_remember_password
                ]
            },
            {
                'type': 'key',
                'commands': [c.ENTER]
            }
        ]
        return commands

    def _fill_oracle_auth_info(self):
        conn_window = self.app.window(best_match='Dialog'). \
            child_window(title_re='New Connection')

        name_ele = conn_window.child_window(best_match='Edit6')
        EditWrapper(name_ele.element_info).set_edit_text(self.name)

        host_ele = conn_window.child_window(best_match='Edit5')
        EditWrapper(host_ele.element_info).set_edit_text(self.host)

        port_ele = conn_window.child_window(best_match='Edit3')
        EditWrapper(port_ele.element_info).set_edit_text(self.port)

        db_ele = conn_window.child_window(best_match='Edit2')
        EditWrapper(db_ele.element_info).set_edit_text(self.db)

        username_ele = conn_window.child_window(best_match='Edit')
        EditWrapper(username_ele.element_info).set_edit_text(self.username)

        if self.privileged:
            conn_window.child_window(best_match='Advanced', control_type='TabItem').click_input()
            role_ele = conn_window.child_window(best_match='ComboBox2')
            ComboBoxWrapper(role_ele.element_info).select('SYSDBA')

    def _get_oracle_commands(self):
        commands = [
            {
                'type': 'key',
                'commands': [
                    '%f', c.DOWN, c.RIGHT, c.DOWN * 2, c.ENTER,
                ],
            },
            {
                'type': 'action',
                'commands': [
                    self._action_not_remember_password, self._fill_oracle_auth_info
                ]
            },
            {
                'type': 'key',
                'commands': [c.ENTER]
            }
        ]
        return commands

    def run(self):
        self.launch()
        self.app = Application(backend='uia')
        work_dir = os.path.dirname(self.path)
        self.app.start(self.path, work_dir=work_dir)
        self.pid = self.app.process

        # 检测是否为试用版本
        try:
            trial_btn = self.app.top_window().child_window(
                best_match='Trial', control_type='Button'
            )
            ButtonWrapper(trial_btn.element_info).click()
            time.sleep(0.5)
        except Exception:
            pass

        # 根据协议获取相应操作命令
        action = getattr(self, '_get_%s_commands' % self.protocol, None)
        if action is None:
            raise ValueError('This protocol is not supported: %s' % self.protocol)
        commands = action()
        # 关闭掉桌面许可弹框
        commands.insert(0, {'type': 'key', 'commands': (c.ESC,)})
        # 登录
        commands.extend([
            {
                'type': 'key',
                'commands': (
                    '%f', c.DOWN * 5, c.ENTER
                )
            },
            {
                'type': 'key',
                'commands': (self.password, c.ENTER),
                'pre_check': self._pre_check_is_password_input
            }
        ])
        self._exec_commands(commands)

    def wait(self):
        try:
            wait_pid(self.pid)
        except Exception:
            pass
        finally:
            self.clean_up()
