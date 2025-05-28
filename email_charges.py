import smtplib
from email.message import EmailMessage
from src.folioApi import FolioApi
import logging
import email
import email.message
import email.mime.text

folio = FolioApi(filepath="src/config/config.ini")

def read_charges_as_text(chargesFile) -> str:
    with open(chargesFile, 'r') as file:
        file_text = file.read()
        return file_text

def send_email_external():
    sender = "jrb7f0@umsystem.edu"
    recipient = "jrbrown23@gmail.com"
    message = "Hello world!"

    email = EmailMessage()
    email["From"] = sender
    email["To"] = recipient
    email["Subject"] = "Test Email"
    email.set_content(message)

    smtp = smtplib.SMTP("smtp-mail.outlook.com", port=587)
    smtp.starttls()
    smtp.login(sender, "CAP292tb22!")
    smtp.sendmail(sender, recipient, email.as_string())
    smtp.quit()

def send_email(sender, recipients, subject, message):
    """Sends an email with the given sender, recipient, subject, and message."""
    msg = email.message.Message()
    msg['From'] = sender
    # msg['To'] = recipient
    msg['To'] = ", ".join(recipients)
    msg['Subject'] = subject
    msg.add_header('Content-Type', 'text')
    msg.set_payload(message)

    smtp_server = 'smtpinternal.umsystem.edu'
    smtp_port = 25

    with smtplib.SMTP(host=smtp_server, port=smtp_port) as smtp:
        try:
            smtp.sendmail(sender, recipients, msg.as_string())
            print("Email sent to {} from {}".format(
                recipients,
                sender
            ))
        except Exception as e:
            logging.debug(e)

if __name__ == "__main__":
    send_email_external()
    ### MAIN ###
    # sender = folio.email_sender
    # recipients = [eml for eml in str(folio.email_recipients).split(',')]
    # # sender = 'asklts@missouri.edu'
    # # recipients = ['jrb7f0@missouri.edu']
    # # recipient = 'jrb7f0@missouri.edu'
    # subject = 'Securely emailed lines'
    # # message = 'This is a message.'
    
    # folio_charges = read_charges_as_text('folio_charges_on_2024-06-04.txt')
    # # message = folio_charges
    # # with smtplib.SMTP('smtpinternal.missouri.edu', 25) as smtp:
    # #     smtp.ehlo()
    # send_email(sender, recipients, subject, folio_charges)
