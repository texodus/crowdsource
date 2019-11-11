import tornado.escape
import tornado.web
import ujson
from .base import ServerHandler
from ..persistence.models import Client
from ..utils import _REGISTER, _CLIENT_MALFORMED


class RegisterHandler(ServerHandler):
    @tornado.web.authenticated
    def get(self):
        '''Get the current list of client ids'''
        if self.current_user and self.current_user.decode('utf-8') not in self._clients:
            return self.post()

        # paginate
        page = int(self.get_argument('page', 0))
        self.write(ujson.dumps([c.to_dict() for c in list(self._clients.values())[page * 100:(page + 1) * 100]]))

    def post(self):
        '''Register a client. Client will be assigned a session id'''
        body = tornado.escape.json_decode(self.request.body or '{}')
        username = self.get_argument('username', body.get('username', ''))
        email = self.get_argument('email', body.get('email', ''))
        password = self.get_argument('password', body.get('password', ''))

        if not username or not email or not password:
            self._set_403(_CLIENT_MALFORMED)

        with self.session() as session:
            c = Client(username=username, email=email, password=password)

            try:
                session.add(c)
                session.commit()
                session.refresh(c)
                ret = self._login_post(c)
                self._writeout(ujson.dumps(ret), _REGISTER, ret["client_id"])
                return
            except BaseException:
                self._set_403(_CLIENT_MALFORMED)
                return
