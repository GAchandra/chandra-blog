from itsdangerous import URLSafeTimedSerializer
from main import app, db, User

class Token:
    def __init__(self, user, expiration=3600):
        self.user = user
        self.token = None
        self.expiration = expiration
    def generate_confirmation_token(self):
        serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        self.token = serializer.dumps(self.user.email, salt=app.config['SECURITY_PASSWORD_SALT'])

    def confirm_token(self):
        serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        try:
            email = serializer.loads(
                self.token,
                salt=app.config['SECURITY_PASSWORD_SALT'],
                max_age=self.token
            )
        except:
            return False
        return email
