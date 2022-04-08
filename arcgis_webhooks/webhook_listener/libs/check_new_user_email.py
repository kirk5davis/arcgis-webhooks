from ..utils import send_html_mail
import time
import logging

logger = logging.getLogger(__name__)

# signin_example_payload = {'events': 
#                             [{'id': 'kirk.davis@ocio.wa.gov', 'operation': 'signin', 'properties': {}, 'source': 'users', 'userId': 'e0d5b07c672c422baf83dd7a9f221bbc', 'username': 'kirk.davis@ocio.wa.gov', 'when': 1645134525842}], 
#                             'info': {'portalURL': 'https://geoportal2.watech.wa.gov/portal/', 'webhookId': '4edcf3c9ab0246f5a041d1225d0619f3', 'webhookName': 'all_webhooks', 'when': 1645134525845}, 
#                             'properties': {}}


def check_email(input_payload):
    # should check for users actual email, assumes the username is the email
    email_address = next(i['username'] for i in input_payload['events'])
    email_domain = email_address.split("@")[-1]
    if ".wa.gov" in email_domain:
        send_html_mail("[SIGNIN] GeoPortal 2.0 Notification", f"<h1>Successful Government domain sign-in to GeoPortal 2.0</h1><p>User: {email_address}</p><p>Processed {time.ctime()}</p>", ["kirk.davis@watech.wa.gov"], "kirk.davis@watech.wa.gov")
        return True
    # notify of bad sign-in
    send_html_mail("[BAD SIGNIN] GeoPortal 2.0 Notification", f"<h1>Successful Government domain sign-in to GeoPortal 2.0</h1><p>User: {email_address}</p><p>Processed: {time.ctime()}</p>", ["kirk.davis@watech.wa.gov"], "kirk.davis@watech.wa.gov")
    return False

