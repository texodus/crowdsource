import tornado.web
from crowdsource.handlers import RegisterHandler
from crowdsource.login import null_login
from crowdsource.persistence import null_persist
from crowdsource.registration import null_register
from mock import MagicMock


class TestRegister:
    def setup(self):
        self.app = tornado.web.Application(cookie_secret='test')
        self.app._transforms = []

    def test_RegistrationHandler(self):
        req = MagicMock()
        req.body = ''
        context = {'clients': {},
                   'competitions': {},
                   'leaderboards': {},
                   'submissions': {},
                   'stash': [],
                   'login': null_login,
                   'register': null_register,
                   'persist': null_persist}
        x = RegisterHandler(self.app, req, **context)
        x._transforms = []
        x.get_current_user = lambda: b'test'
        x.get()

        # initial registration
        x.post()

        # fixed id
        req.body = '{"id":1234}'
        x.post()
        x.get()

        # reregister
        x.post()
