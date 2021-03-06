from tornado.web import RequestHandler, UIModule, Application, removeslash
from tornado.gen import coroutine
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
# other libraries
from motor import MotorClient as Client
import os
import env
import json
import uuid
import base64

db = Client(env.DB_LINK)['quizzy']
c_question_count = 0


class User(object):
    username = ""
    password = ""
    is_logged_in = False


class NoConnectionException(Exception):
    pass


class QuestionsModule(UIModule):
    def render(self, *args, **kwargs):
        print(args)
        return self.render_string('questions.html')


# pylint: disable=abstract-method
class IndexHandler(RequestHandler, User):
    @coroutine
    @removeslash
    def get(self):
        if self.get_secure_cookie('username') is None:
            User.is_logged_in = False
            self.redirect('/log')
        else:
            User.username = self.get_secure_cookie('username')
            User.password = self.get_secure_cookie('password')
            User.is_logged_in = True
            self.redirect('/node')


# TODO- add cookie secret

class Log(RequestHandler):
    @coroutine
    @removeslash
    def get(self):
        """
        right submission successful in case of signup or submission failed
        and login failed in case of login
        :return: None
        """
        self.render('log1.html')


class LoginHandler(RequestHandler, User):
    def data_received(self, chunk):
        pass

    @removeslash
    @coroutine
    def post(self):
        username = self.get_argument('username')
        password = self.get_argument('password')
        print(username)
        user = yield db['accounts'].find_one({'username': username})
        print(user)
        redirect = 'none'
        if user is None:
            message = "Not registered"
        elif user['password'] != password:
            message = 'Wrong Password'

        else:
            User.username = username
            User.password = password
            User.is_logged_in = True
            self.set_secure_cookie('username', User.username)
            self.set_secure_cookie('password', User.password)
            message = "loading..."
            redirect = '/node'

        self.write(json.dumps({
            'status': 200,
            'message': message,
            'redirect': redirect
        }))

    def write_error(self, status_code, **kwargs):
        self.write(str(status_code) + ' You are living in dinosaur age')


class SignUpHandler(RequestHandler, User):
    def data_received(self, chunk):
        pass

    @removeslash
    @coroutine
    def post(self):

        name = self.get_argument('name').lower().strip()
        username = self.get_argument('username').strip()
        password = self.get_argument('password')
        email = self.get_argument('email')

        u_account = yield db['accounts'].find_one({'username': username})
        e_account = yield db['accounts'].find_one({'email': email})
        message = 'unsuccessful'
        if u_account:
            message = 'Username unavailable'

        if e_account:
            message = 'email already registered'

        try:
            yield db['accounts'].insert_one({'name': name, 'username': username, 'password': password, 'email': email})
            message = 'successfully registered'
        except NoConnectionException:
            self.write_error(400)

        self.write(json.dumps({
            'status': 200,
            'message': message
        }))

    def write_error(self, status_code):
        self.write(str(status_code) + ' ERROR..')


class HomePage(RequestHandler, User):
    def data_received(self, chunk):
        pass

    def get(self):
        self.render('home.html')


class LogoutHandler(RequestHandler):
    def data_received(self, chunk):
        pass

    def get(self):
        self.clear_all_cookies()
        self.redirect('/')


class TakeQuiz(RequestHandler, User):
    def data_received(self, chunk):
        pass


class CreateQuiz(RequestHandler, User):
    def data_received(self, chunk):
        pass

    def get(self):
        self.render('cquiz.html')

    def post(self):
        pass
# TODO - give a different id to all quiz.. and save them on database of all available and a link to the author's id


settings = dict(
    db=db,
    cookie_secret=base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes),
    debug=True
)

app = Application(
    handlers=[
        (r'/', IndexHandler),  # controls index if logged in then /node else /log
        (r'/log', Log),
        (r'/logout/$', LogoutHandler),
        (r'/login/$', LoginHandler),  # Login if clicks login
        (r'/signup/$', SignUpHandler),
        (r'/node/$', HomePage),  # Home page
        (r'/cquiz/$', CreateQuiz),  # Creating quiz portal
        (r'/tquiz/$', TakeQuiz)  # Take quiz portal
    ],
    template_path=os.path.join(os.path.dirname(__file__), "template"),
    static_path=os.path.join(os.path.dirname(__file__), "static"),
    ui_modules={'questions_module': QuestionsModule},
    **settings
)

if __name__ == "__main__":
    server = HTTPServer(app)
    server.listen(8080)
    IOLoop.current().start()
