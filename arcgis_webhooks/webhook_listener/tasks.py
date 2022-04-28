import time
from celery import shared_task
from django.core.mail import EmailMessage
from django.conf import settings
from arcgis.gis import GIS


def _check_for_agency_group_access(gis_obj, input_email_domain):
    """returns a group to which a new user should be added based on an input email domain.
        Example: 'watech.wa.gov', agency domain returned would be 'watech'.
        A group with the tag 'agency-group' and 'watech' would need to exist for this funtion
        to return anything."""
    for sub_string in settings.ACCEPTED_GOVERNMENT_USER_DOMAIN_SUBSTRINGS:
        input_email_domain = input_email_domain.replace(sub_string, "")
    agency_domain = input_email_domain
    possible_agency_groups = gis_obj.groups.search("agency_group")
    for group in possible_agency_groups:
        if agency_domain in group.tags:
            return group
    return None


def _check_for_org_share_tag(item_obj, gis_obj):
    pass


@shared_task
def send_test_webhook_email(input_data_dict):
    msg = EmailMessage('[TEST FUNCTION] send_test_webhook_email', str(input_data_dict), settings.DEFAULT_NOTIFICATION_SENDER, [settings.DEFAULT_NOTIFICATION_SENDER])
    msg.content_subtype = 'html'
    msg.send()
    return "Successful function run"
    

@shared_task
def new_user_email_check(input_payload):
    gis = GIS(settings.ARCGIS_ENTERPRISE_URL, settings.ARCGIS_ENTERPRISE_ADMIN, settings.ARCGIS_ENTERPRISE_ADMIN_PW)
    new_userid = next(i for i in input_payload['events'])['id']
    new_user_email = gis.users.get(username=new_userid).email
    email_domain = new_user_email.split("@")[-1].lower()
    if any(sub_string in email_domain for sub_string in settings.ACCEPTED_GOVERNMENT_USER_DOMAIN_SUBSTRINGS):
        # government email exists, check for agency group and update user
        status = "SUCCESSFUL"
        html_content = f"""
                        <h2><b>{status}</b> new user added to GeoPortal 2.0</h2> 
                        <p>Username: {new_userid} - Email: {new_user_email}</p><p>Processed: {time.ctime()}</p>
                    """
        agency_group = _check_for_agency_group_access(gis, email_domain)
        if agency_group:
            agency_group.add_users(usernames=[new_userid])
            html_content += f"""
                        <p><b>Additional actions taken:</b> <ul><li>Added user to agency group -- {agency_group.title}</li></ul></p>
                    """
        else:
            html_content += f"""
                        <p><b>Additional actions taken:</b> None, Agency group not yet created for <b>{email_domain}</b></p>
                    """
    else:
        # non-government email, quarantine the user
        # found under portal admin https://geoportal2.watech.wa.gov/portal/sharing/rest/portals/0123456789ABCDEF/roles
        quarantined_role_id = "4tp5IdAF1x1grmVB"
        quarantined_group = gis.groups.get("f63dbf4254744dbaa38268343d7ba572")
        training_resources_group = gis.groups.get("4424d80fd12e45d2b0def73c5fbac816")

        # adjust the user's settings  
        new_user = gis.users.get(new_userid)
        quarantined_group.add_users(usernames=[new_userid])
        training_resources_group.remove_users(usernames=[new_userid])
        new_user.update_role(quarantined_role_id)

        status = "QUARANTINED"
        html_content = f"""
                        <h2><b>{status}</b> new user added to GeoPortal 2.0</h2> 
                        <p>Due to administrative policies of GeoPortal 2.0, your new account appears to be linked to a non-governmental email address and has been quarantined. 
                        Your account request will be reviewed by GeoPortal 2.0 administrators.</p>
                        <p>User: {new_userid} - Email: {new_user_email}</p><p>Processed: {time.ctime()}</p>
                    """
        
    email_subject = f"[GP2-Notification] Check new user process: {status}"
    recipient_list = [new_user_email]
    msg = EmailMessage(email_subject, html_content, settings.DEFAULT_NOTIFICATION_SENDER, recipient_list, cc=settings.DEFAULT_NOTIFICATION_RECIPIENTS)
    msg.content_subtype = 'html'
    msg.send()
    return f"{time.ctime()} -- Completed email check of new users: {new_userid} - {new_user_email} - Status: {status}\n"


@shared_task
def share_item_with_org_check(input_payload):
    gis = GIS(settings.ARCGIS_ENTERPRISE_URL, settings.ARCGIS_ENTERPRISE_ADMIN, settings.ARCGIS_ENTERPRISE_ADMIN_PW)
    item_id_guid = next(i for i in input_payload['events'])['id']
    item_obj = gis.content.get(item_id_guid)
    if _check_for_org_share_tag(item_obj, gis):
        try:
            item_obj.share(org=True)
            success_message = "Tag-based organizational share successful."
            return (True, f"{success_message}, Item 'shared-with' info: {item_obj.shared_with}")
        except Exception as e:
            fail_message = f"Tag-based organizational share requested and failed, Exception thrown: {e}"
            return (False, f"{fail_message}, Item 'shared-with' info: {item_obj.shared_with}")
    return (True, "Item does not contain an organizational share tag.")
