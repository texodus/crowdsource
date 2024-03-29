import logging
import tornado.ioloop
import tornado.web
from contextlib import contextmanager
from jinja2 import Environment, FileSystemLoader, TemplateNotFound


class ServerHandler(tornado.web.RequestHandler):
    '''Just a default handler'''

    def get_current_user(self):
        return self.get_secure_cookie('user')

    def _set_400(self, log_message, *args):
        logging.info(log_message, *args)
        self.clear()
        self.set_status(400)
        self.finish('{"error":"400"}')
        raise tornado.web.HTTPError(400)

    def _set_401(self, log_message, *args):
        logging.info(log_message, *args)
        self.clear()
        self.set_status(401)
        self.finish('{"error":"401"}')
        raise tornado.web.HTTPError(401)

    def _set_403(self, log_message, *args):
        logging.info(log_message, *args)
        self.clear()
        self.set_status(403)
        self.finish('{"error":"403"}')
        raise tornado.web.HTTPError(403)

    def _writeout(self, message, log_message, *args):
        logging.info(log_message, *args)
        self.set_header("Content-Type", "text/plain")
        self.write(message)

    def _validate(self, validation_method=None):
        return validation_method(self) if validation_method else {}

    def _login_post(self, client):
        if client and client.client_id and client.client_id in self._clients:
            self._set_login_cookie(client)
            return {'client_id': str(client.client_id), 'username': client.username}

        elif client and client.id:
            self._clients[client.client_id] = client
            self._set_login_cookie(client)
            return {'client_id': str(client.client_id), 'username': client.username}
        else:
            return False

    def _set_login_cookie(self, client):
        self.set_secure_cookie('user', str(client.client_id))

    @contextmanager
    def session(self):
        """Provide a transactional scope around a series of operations."""
        session = self._sessionmaker()
        try:
            yield session
            session.commit()
        except:  # noqa: E722
            session.rollback()
            raise
        finally:
            session.close()

    def redirect(self, path):
        if path[:len(self.basepath)] == self.basepath:
            return super(ServerHandler, self).redirect(path)
        return super(ServerHandler, self).redirect(self.basepath + path)

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

    def initialize(self, sessionmaker, clients, competitions, submissions, leaderboards, stash, basepath='/', wspath='ws:localhost:8080/', proxies=None, *args, **kwargs):
        '''Initialize the server competition registry handler

        This handler is responsible for managing competition
        registration.

        Arguments:
            competitions {dict} -- a reference to the server's dictionary of competitions
        '''
        super(ServerHandler, self).initialize(*args, **kwargs)
        self._sessionmaker = sessionmaker
        self._clients = clients
        self._competitions = competitions
        self._submissions = submissions
        self._leaderboards = leaderboards
        self._to_score_later = stash

        self.basepath = basepath
        self.wspath = wspath
        self.proxies = proxies

    def render_template(self, template, **kwargs):
        if hasattr(self, 'template_dirs'):
            template_dirs = self.template_dirs
        else:
            template_dirs = []

        if self.settings.get('template_path', ''):
            template_dirs.append(
                self.settings["template_path"]
            )
        env = Environment(loader=FileSystemLoader(template_dirs))

        try:
            template = env.get_template(self.template)
        except TemplateNotFound:
            raise TemplateNotFound(self.template)

        kwargs['current_user'] = self.current_user.decode('utf-8') if self.current_user else ''
        kwargs['basepath'] = self.basepath
        kwargs['wspath'] = self.wspath
        content = template.render(**kwargs)
        return content
