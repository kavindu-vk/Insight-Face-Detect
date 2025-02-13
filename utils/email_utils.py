import base64
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from django.conf import settings
from django.core.files.base import ContentFile
from io import BytesIO

def send_email_via_sendinblue(subject, content, to_emails, attachment=None):
    # Configure Sendinblue API client
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = settings.SENDINBLUE_API_KEY

    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

    sender = {"name": "University Admin", "email": settings.EMAIL_SENDER}
    to_list = [{"email": email} for email in to_emails]

    email = {
        "sender": sender,
        "to": to_list,
        "subject": subject,
        "htmlContent": content,
    }

    if attachment:
        attachment_content = attachment.read()
        encoded_content = base64.b64encode(attachment_content).decode('utf-8')
        email["attachment"] = [{
            "content": encoded_content,
            "name": attachment.name
        }]


    try:
        api_instance.send_transac_email(email)
        print(f"Email successfully sent to: {', '.join(to_emails)}")
    except ApiException as e:
        print(f"Error sending email: {e}")