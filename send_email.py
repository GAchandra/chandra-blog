import ssl,smtplib
from email.mime.text import MIMEText
from email.mime.multipart import  MIMEMultipart

def send_email(sender_email:str, sender_passwrod, receiver_email:str, provided_message:dict, subject):
    message = MIMEMultipart('alternative')
    message['Subject'] = subject
    message['From'] = sender_email
    message['To'] = receiver_email

    text = provided_message['text']
    html = provided_message['html']

    # Turn these into plain/html MIMEText objects
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")

    # Add HTML/plain-text parts to MIMEMultipart message
    # The email client will try to render the last part first
    message.attach(part1)
    message.attach(part2)
    # Create secure connection with server and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL('smtp.mail.yahoo.com', 465 , context=context) as server:
        server.login(sender_email, sender_passwrod)
        server.sendmail(
            sender_email,receiver_email, message.as_string()
        )