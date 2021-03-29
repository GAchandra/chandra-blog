import os
from datetime import datetime
import jwt
from jwt.exceptions import InvalidSignatureError
from flask import request
from send_email import send_email
from my_encryption import MyEncryption
from constants import *

my_encryption = MyEncryption()


class Authentication:
    def __init__(self, user=None):
        if user is None:
            pass
        self.user_data = user
        self.my_encryption = MyEncryption()
        self.headers = {
            'alg': 'HS256',
            'typ': 'JWT'
        }
        self.sender_email = os.environ.get('EMAIL_ADDRESS')
        self.sender_password = os.environ.get('EMAIL_PASSWORD')
        self.email_confirmation_data = {}
        self.secret_key = os.urandom(20).hex()
        self.encrypted_another_data = {}

    def _generate_jwt_token(self):
        now = str(datetime.now())
        email = self.user_data.email
        encrypted_email = self.my_encryption.encrypt_data(email)
        encrypted_now = self.my_encryption.encrypt_data(str(now))
        payload_value = f'{encrypted_email}t?{encrypted_now}'
        encoded_jwt_token = jwt.encode(key=self.secret_key, headers=self.headers,
                                       payload={'payload': payload_value,
                                                'encrypted_another_data': self.encrypted_another_data})
        self.email_confirmation_data = {
            'send_email': email,
            'send_time': now
        }
        return encoded_jwt_token

    def get_req_data(self):
        return {
            'ip_address': request.remote_addr,
            'name': self.user_data.name,
            'email': self.user_data.email,
            'time': datetime.now()
        }

    def back_to_default(self, user):
        self.user_data = user
        self.email_confirmation_data = {}
        self.encrypted_another_data = {}
        self.secret_key = os.urandom(20).hex()

    def email_confirmation(self, text_message: str, subheading: str, description: str, subject: str,
                           end_point: str = "account-confirmation/email", another_data=None):

        if another_data is None:
            another_data = {}
        else:
            for (key, value) in another_data.items():
                self.encrypted_another_data[key] = self.my_encryption.encrypt_data(value)

        encoded_jwt_token = self._generate_jwt_token()
        self.email_confirmation_data['another_data'] = another_data

        link = f'{request.host_url}{end_point}/{encoded_jwt_token}'
        req_data = self.get_req_data()
        message = {
            'text': f"Hello {self.user_data.name}, {text_message}: {link}",
            'html': f"""
                        <html>
                            <head></head>
                            <body>
                                <h1> Hello <b>{self.user_data.name}</b>, </h1>
                                <br>
                                <h2>{subheading}<h2>
                                <div style='color: blue;'>
                                    <h3 style='border: 2px solid bottom;'>Confirmation from: </h3>
                                    <p>Ip address: {req_data['ip_address']}</p>
                                    <p>Name: {req_data['name']}</p>
                                    <p>Email: {req_data['email']}</p>
                                    <p>Time: {req_data['time']}</p>
                                    
                                </div>
                                <p>{description}</p>
                                <p>
                                    Confirm your email using billow "Confirm my email" link  clicking
                                    <a href='{link}'>Confirm my email</a>
                                </p>
                            </body>
                        </html>
                    """
        }
        email = self.user_data.email
        send_email(self.sender_email, self.sender_password, email, message, subject)

    def check_email_confirmation(self, jwt_token):
        try:
            decoded_data = jwt.decode(jwt_token, key=self.secret_key, algorithms=["HS256"])
        except InvalidSignatureError:
            return False
        else:
            payload = decoded_data['payload'].split('t?')
            another_data = decoded_data['encrypted_another_data']
            decoded_another_data = {}
            another_data_items = another_data.items()
            is_another_data_not_empty = len(another_data_items) > 0
            if is_another_data_not_empty:
                for (key, value) in another_data_items:
                    decoded_another_data[key] = self.my_encryption.decrypt_data(value)

            encrypted = {'email': payload[0], 'now': payload[1]}

            # Decrypt
            decrypted = {
                'email': self.my_encryption.decrypt_data(encrypted['email']),
                'now': self.my_encryption.decrypt_data(encrypted['now'])
            }
            is_error = True
            if self.email_confirmation_data is not None:
                sent_email = self.email_confirmation_data['send_email']
                sent_time = self.email_confirmation_data['send_time']

                if is_another_data_not_empty:
                    for (key, value) in decoded_another_data.items():
                        for (k, v) in self.email_confirmation_data['another_data'].items():
                            if key == k:
                                if value == v:
                                    is_error = False
                else:
                    is_error = False

                if decrypted['now'] == sent_time:
                    email = decrypted['email']
                    if email == sent_email and not is_error:
                        if is_another_data_not_empty:
                            return {'email': email, 'another_data': decoded_another_data}
                        else:
                            return email
                    else:
                        return False
                else:
                    return False
