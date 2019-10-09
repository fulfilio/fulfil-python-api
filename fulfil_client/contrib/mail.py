# -*- coding: utf-8 -*-
import six
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.mime.text import MIMEText

if six.PY2:
    from email.MIMEBase import MIMEBase
    from email import Encoders
else:
    from email.mime.base import MIMEBase
    import email.encoders as Encoders


def render_email(
    from_email, to, subject, text_template=None, html_template=None,
    cc=None, attachments=None, **context
):
    """
    Read the templates for email messages, format them, construct
    the email from them and return the corresponding email message
    object.
    :param from_email: Email From
    :param to: Email IDs of direct recepients (list)
    :param subject: Email subject
    :param text_template: String of rendered template with context
        eg in flask: str(render_template(text_template, **context)
    :param html_template: String of transfomed rendered template with context
        eg in flask: str(transform(render_template(html_template, **context)))
        for transform https://premailer.io python library
    :param cc: Email IDs of Cc recepients (list)
    :param attachments: A dict of filename:string as key value pair
                        [preferable file buffer streams]
    :param context: Context to be sent to template rendering
    :return: Email multipart instance or Text/HTML part
    """
    if not (text_template or html_template):
        raise Exception("Atleast HTML or TEXT template is required")

    text_part = None
    if text_template:
        text_part = MIMEText(
            text_template.encode("utf-8"), 'plain', _charset="UTF-8")

    html_part = None
    if html_template:
        html_part = MIMEText(
            html_template.encode("utf-8"), 'html', _charset="UTF-8")

    if text_part and html_part:
        # Construct an alternative part since both the HTML and Text Parts
        # exist.
        message = MIMEMultipart('alternative')
        message.attach(text_part)
        message.attach(html_part)
    else:
        # only one part exists, so use that as the message body.
        message = text_part or html_part

    if attachments:
        # If an attachment exists, the MimeType should be mixed and the
        # message body should just be another part of it.
        message_with_attachments = MIMEMultipart('mixed')

        # Set the message body as the first part
        message_with_attachments.attach(message)

        # Now the message _with_attachments itself becomes the message
        message = message_with_attachments

        for filename, content in attachments.items():
            part = MIMEBase('application', "octet-stream")
            part.set_payload(content)
            Encoders.encode_base64(part)
            # XXX: Filename might have to be encoded with utf-8,
            # i.e., part's encoding or with email's encoding
            part.add_header(
                'Content-Disposition', 'attachment; filename="%s"' % filename
            )
            message.attach(part)

    # If list of addresses are provided for to and cc, then convert it
    # into a string that is "," separated.
    if isinstance(to, (list, tuple)):
        to = ', '.join(to)
    if isinstance(cc, (list, tuple)):
        cc = ', '.join(cc)

    # We need to use Header objects here instead of just assigning the strings
    # in order to get our headers properly encoded (with QP).
    message['Subject'] = Header(subject, 'ISO-8859-1')

    # TODO handle case where domain contains non-ascii letters
    # https://docs.aws.amazon.com/ses/latest/APIReference/API_Destination.html
    message['From'] = from_email
    message['To'] = to
    if cc:
        message['Cc'] = cc

    return message
