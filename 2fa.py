import imaplib
import os

username = os.environ.get('AHTAVARASMUSGMAIL')
password = os.environ.get('AHTAVARASMUSPASSWORD')
gmail_host = 'imap.gmail.com'

def receive_email_body():

    mail = imaplib.IMAP4_SSL(gmail_host)

    #login
    mail.login(username, password)

    #select inbox
    mail.select("INBOX")

    #select specific mails
    _, selected_mails = mail.search(None, f'(FROM {current_user.email})')


    for idx,num in enumerate(selected_mails[0].split()):
        if idx != len(selected_mails[0].split())-1:
           continue 
        _, data = mail.fetch(num , '(RFC822)')
        _, bytes_data = data[0]

        #convert the byte data to message
        email_message = email.message_from_bytes(bytes_data)

        #access data
        for part in email_message.walk():
            if part.get_content_type()=="text/plain" or part.get_content_type()=="text/html":
                message = part.get_payload(decode=True)
                body_text = message.decode()
                list_raw = re.split("\s.{2}\s\d\d",body_text,1)
                message = list_raw[0]
                days_date = re.search(".{2}\s\d\d[.]\s\w+[.]\s\d\d\d\d",body_text).group()
                year = re.search("\d\d\d\d", days_date).group()
                day = re.search("\d\d",days_date,1).group()
                month_raw = re.search("\s\D+[.]",days_date).group()

                if "tammi" in month_raw:
                    month = "1" 
                elif "helmi" in month_raw:
                    month = "2"
                elif "maalis" in month_raw:
                    month = "3"
                elif "huhti" in month_raw:
                    month = "4"
                elif "touko" in month_raw:
                    month = "5"
                elif "kesä" in month_raw:
                    month = "6"
                elif "heinä" in month_raw:
                    month = "7"
                elif "elo" in month_raw:
                    month = "8"
                elif "syys" in month_raw:
                    month = "9"
                elif "loka" in month_raw:
                    month = "10"
                elif "marras" in month_raw:
                    month = "11"
                elif "joulu" in month_raw:
                    month = "12"

                return message,day,month,year
                break

    return 'no messages:('

