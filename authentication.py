import jwt
from send_email import send_email
from main import *

email = None
jwt_token_g_date = None
secret_key = None
def email_confirmation(user_email, username):
    global email, jwt_token_g_date, jwt_token, secret_key
    email = user_email
    secret = os.urandom(20).hex()
    secret_key = secret
    now = datetime.now()
    payload_value =  f"{generate_password_hash(user_email, salt_length=10)}t?{now}"
    jwt_token_g_date = str(now)
    encoded = jwt.encode(key=secret,headers={"alg":"HS256", "typ": "JWT"}, payload={'payload': payload_value })
    link = f'http://localhost:5000/account-confirmation/email/{encoded}'
    message = {
        'text':  f"""
            Hello {username}, Your Account Communication Link:{link} Please visit 
        """,
        'html': f"""
            <h1>Hello <b>{username}</b>,</h1>
            <p>Here is your Account Confirmation in 'Chandra's Blog'</p>
            <p>Copy and Past this in to your browser url bar to confirm your account<p>
            <b>{link}</b>
        """
    }

    send_email('c_damayanthi@yahoo.com', 'yvkrjnjwyvssnbml', user_email, message, "Account Confirmation")
def check_email_confirmation(token):
    global email, jwt_token_g_date
    decoded_data = jwt.decode(token, key=secret_key, algorithms=["HS256"])
    payload = decoded_data['payload'].split('t?')
    user_email_hash = payload[0]
    now = payload[1]
    is_matches = check_password_hash(user_email_hash, email)
    if is_matches:
        if jwt_token_g_date == now:
            return email
        else:
            return False
    else:
        return False