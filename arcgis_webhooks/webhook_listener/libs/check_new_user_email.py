import time
import logging
import threading
from django.core.mail import EmailMessage

logger = logging.getLogger(__name__)


class BaseThread(threading.Thread):
    def __init__(self, input_task):
        self.input_task = input_task
        threading.Thread.__init__(self)

    def run(self):
        input_payload = self.input_task.data
        email_address = next(i['username'] for i in input_payload['events'])
        email_domain = email_address.split("@")[-1]
        if ".wa.gov" in email_domain:
            status = "SUCCESSFUL"
        else:
            status = "NOTICE"
        email_subject = f"[GP2-Notification] Check new user process: {status}"
        html_content = f"""
                            <h2><b>{status}</b> Government domain sign-in to GeoPortal 2.0</h2> 
                            <p>User: {email_address}</p><p>Processed {time.ctime()}</p>
                        """
        sender = "kirk.davis@watech.wa.gov"
        recipient_list = ["kirk.davis@watech.wa.gov"]
        msg = EmailMessage(email_subject, html_content, sender, recipient_list)
        msg.content_subtype = 'html'
        msg.send()
        return True




def check_email(input_task):
    """Checks if username is a State government email address"""
    BaseThread(input_task).start()
    

