import asyncio
import base64
import email
import email.header
import email.message
import email.utils
import imaplib
import logging
import os
import quopri
import re
import time

import pandoc

import telebot.types
from botInstance import bot

# Email Server Information
EMAIL_SERVER = os.environ.get('EMAIL_SERVER')
IMAP_PORT = int(str(os.environ.get('IMAP_PORT')))
EMAIL_LOGIN = os.environ.get('EMAIL_LOGIN')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')


def filter_mail(msg: str) -> str:
    if 'BEGIN:VCALENDAR' in msg:
        return 'Calendar Widget'
    return msg


def isOK(s: str) -> bool:
    return s == 'OK'


def isOKe(s: str) -> bool:
    res = s == 'OK'
    if not res:
        raise RuntimeError('The server respond was not OK')
    return res


def imap_connect() -> imaplib.IMAP4_SSL | None:
    imap = imaplib.IMAP4_SSL(EMAIL_SERVER, 993)
    status, _ = imap.login(EMAIL_LOGIN, EMAIL_PASSWORD)
    return imap if isOK(status) else None


def extract_html(doc: str) -> str:
    # with open (f'pages/{time.clock_gettime_ns(time.CLOCK_REALTIME)}.html', 'w') as f:
    #     f.write(doc)
    #     f.flush()
    #     f.close()
    pandas = pandoc.write(pandoc.read(doc, format='html'), format='plain', options=[
                          '--columns=65', '--wrap=auto']).split('\n')
    i, current_line = 1, re.search(r'[a-zA-Z0-9]', pandas[0]) is None
    while i < len(pandas) - 1:
        next_line = re.search(r'[a-zA-Z0-9]', pandas[i]) is None
        if next_line and current_line:
            del pandas[i]
            continue
        current_line = next_line
        i += 1
    doc = '\n'.join(pandas)
    return doc


def extract_mail_part(part: email.message.Message) -> str:
    if part["Content-Transfer-Encoding"] in (None, "7bit", "8bit", "binary"):
        return part.get_payload()
    elif part["Content-Transfer-Encoding"] == "base64":
        encoding = part.get_content_charset()
        return base64.b64decode(part.get_payload()).decode(encoding)
    elif part["Content-Transfer-Encoding"] == "quoted-printable":
        encoding = part.get_content_charset()
        return quopri.decodestring(part.get_payload()).decode(encoding)
    else:  # all possible types: quoted-printable, base64, 7bit, 8bit, and binary
        return part.get_payload()


def extract_email_text(msg: email.message.Message) -> str:
    if msg.is_multipart():
        parts = []
        for part in msg.walk():
            if part.get_content_maintype() == "text":
                extract_part = extract_mail_part(part)
                if part.get_content_subtype() == "html":
                    mail_text = extract_html(extract_part)
                else:
                    mail_text = extract_part.strip()
                parts.append(filter_mail(mail_text))
        mail_text = '\n-----\n'.join(parts)
    else:
        if msg.get_content_maintype() == "text":
            extract_part = extract_mail_part(msg)
            if msg.get_content_subtype() == "html":
                mail_text = extract_html(extract_part)
            else:
                mail_text = extract_part
    return mail_text.replace("\xa0", " ").strip()


def decode_attachment_names(names: str):
    encoded_names = re.findall(r'\=\?.*?\?\=', names)
    if len(encoded_names) == 1:
        encoding = email.header.decode_header(encoded_names[0])[0][1]
        decode_name = email.header.decode_header(
            encoded_names[0])[0][0].decode(encoding)
        return names.replace(encoded_names[0], decode_name)
    if len(encoded_names) > 1:
        nm = []
        for part in encoded_names:
            encoding = email.header.decode_header(part)[0][1]
            decode_name = email.header.decode_header(
                part)[0][0].decode(encoding)
            nm.append(decode_name)
        names = names.replace(encoded_names[0], ''.join(nm))
        for c, i in enumerate(encoded_names):
            if c > 0:
                names = names.replace(
                    encoded_names[c], "").replace('"', "").rstrip()
    return names


def get_attachments(msg: email.message.Message):
    attachments = []
    for part in msg.walk():
        if (
            part["Content-Type"]
            and "name" in part["Content-Type"]
            and part.get_content_disposition() == "attachment"
        ):
            attachments.append(decode_attachment_names(part["Content-Type"]))
    return attachments


def assemble_message(id: str = 'No id',
                     date: str = '-',
                     _from: str = 'Noname',
                     subject: str = 'No subject',
                     body: str = 'Empty message',
                     attach: list[str] = []) -> str:
    attachstr = "\n".join(attach)
    return f'ID: {id}\nFrom: {_from}\nDate: {date}\n-----\n{subject}\n-----\n{body}\n-----\nAttachments:\n{attachstr}\n'


def from_subj_decode(header: email.header.Header):
    if not header:
        return None
    encoding = email.header.decode_header(header)[0][1]
    header = email.header.decode_header(header)[0][0]
    if isinstance(header, bytes):
        header = header.decode(encoding)
    return str(header).strip("<>").replace("<", "")


def email_to_message(msg: email.message.Message) -> str:
    if msg["Message-ID"]:
        msg_id = msg["Message-ID"].lstrip("<").rstrip(">")
    else:
        msg_id = msg["Received"]
    msg_from = from_subj_decode(msg["From"])
    msg_subj = from_subj_decode(msg["Subject"])
    msg_body = extract_email_text(msg)
    msg_attachments = get_attachments(msg)
    return assemble_message(msg_id,
                            msg['Date'],
                            msg_from,
                            msg_subj,
                            msg_body,
                            msg_attachments)


async def check_email(subs: list[int]):
    if(not subs):
        logging.info('Subscriber list is empty, skipping the operation.')
        return False
    mail = imap_connect()
    if(not mail):
        logging.error('Unable to connect')
        return False
    try:
        flag, _ = mail.select('INBOX')
        isOKe(flag)
        # Search for all unseen emails
        ans, response = mail.search(None, 'UNSEEN')
        isOKe(ans)

        if not (len(response) == 1 and response[0] == b''):
            unread_msg_nums = response[0].split(b' ')
            for e_id in unread_msg_nums:
                ans, res = mail.fetch(e_id, '(RFC822)')
                if (not isOK(ans)):
                    continue

                msg = email_to_message(email.message_from_bytes(res[0][1]))
                tasks = []
                for sub in subs:
                    if len(msg) >= 4096:
                        c = 0
                        while c < len(msg):
                            tasks.append(asyncio.create_task(
                                bot.send_message(sub, msg[c:c+4096])))
                            c += 4096
                    else:
                        tasks.append(asyncio.create_task(
                            bot.send_message(sub, msg)))
                for t in tasks:
                    await t
    except Exception as e:
        logging.error(e.with_traceback())
        return False
    mail.close()
    mail.logout()
    return True
