import time
import logging
import threading
import concurrent.futures
from django.core.mail import EmailMessage

logger = logging.getLogger(__name__)

def _email_check(input_payload):
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
    return "Successful email check with concurrent.futures"




def check_email(input_task):
    """Checks if username is a State government email address"""
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(_email_check, input_task.data)
        return_value = future.result()
    return return_value
    