import os
import random
import re
import string
from collections import namedtuple
from typing import List, Union
from email.message import Message


__all__ = ['EmailMetaDataProcessor', 'EmailContentProcessor']


class EmailMetaDataProcessor:
    """Extract email meta data"""
    def __init__(self, msg_obj: Message):
        self.msg_obj = msg_obj

    @staticmethod
    def remove_special_characters(input_str: str) -> Union[str, None]:
        """Remove some special characters from string"""
        if not isinstance(input_str, str):
            return None
        pattern = '[!"#$%&\'()*+,/:;=?@[\\]^`{|}~]'
        return re.sub(pattern, '', input_str)

    def extract_meta_data(self) -> namedtuple:
        """Extracts: From, To, Cc, Subject and Date """
        Captions = namedtuple('Captions', ['from_email', 'to_email', 'cc_email', 'subject', 'date_time'])
        date_time = self.remove_special_characters((self.msg_obj.__contains__("date") and self.msg_obj['date'].strip())
                                                   ) or ''
        from_email = self.remove_special_characters((self.msg_obj.__contains__("from") and self.msg_obj['from'].strip())
                                                    ) or ''
        to_email = self.remove_special_characters((self.msg_obj.__contains__("to") and self.msg_obj['to'].strip())
                                                  ) or ''
        cc_email = self.remove_special_characters((self.msg_obj.__contains__("cc") and self.msg_obj['cc'].strip())
                                                  ) or ''
        subject = self.remove_special_characters((self.msg_obj.__contains__("subject"
                                                                            ) and self.msg_obj['subject'].strip())
                                                 ) or ''
        return Captions(from_email, to_email, cc_email, subject, date_time)


class EmailContentProcessor:
    """Email file (.eml) processor class"""
    def __init__(self, file_name: str):
        self.file_name: Union[str, None] = file_name

    def process_attachment(self, msg_obj: Message) -> str:
        """Process attachment file"""
        attachment_name = msg_obj.get_filename()
        attachment_path = self.construct_attached_file_name(attachment_name)
        self.save_attachment_file(attachment_path, msg_obj.get_payload(decode=True))
        return attachment_path

    def process_packed_file(self, msg_obj: Message) -> str:
        """Process packed file"""
        # get content type from email
        content_type = msg_obj.get("content-type")
        # check name string is exists or not
        name_index_from = content_type.find("name=")
        # if no name string found the return none
        if name_index_from == -1:
            return ''
        # get the index of ';' if exists
        name_index_to = content_type.find(";", name_index_from)
        if name_index_to == -1:
            name_index_to = None
        # start index after 'name='
        name_index_from += 5
        # get the attachment name
        attachment_name = content_type[name_index_from:name_index_to]
        attachment_name = self.remove_unwanted_symbol(attachment_name)
        attachment_path = self.construct_attached_file_name(attachment_name)
        self.save_attachment_file(attachment_path, msg_obj.get_payload(decode=True))
        return attachment_path

    def construct_attached_file_name(self, attachment_name: str) -> str:
        """Construct a file name of attachment or packed file"""
        random_str = ''.join(random.choices(string.ascii_letters, k=6))
        return f'{self.file_name.split(".")[0]}_{random_str}_{attachment_name}'

    @staticmethod
    def remove_unwanted_symbol(name: str) -> str:
        """Remove single/double quotation, < or > symbol from name"""
        name = name.strip()
        if (name.startswith("'") and name.endswith("'")) or (name.startswith('"') and name.endswith('"')):
            name = name[1:-1]
        if name.startswith("<") and name.endswith(">"):
            name = name[1:-1]
        return name

    @staticmethod
    def save_attachment_file(name: str, content: bytes):
        """Save file"""
        file = open(os.path.join(name), "wb")
        file.write(content)
        file.close()

    def parse_single_part_email(self, msg_obj: Message, body_text: str, body_html: str,
                                attachments: List, total_part: int) -> namedtuple:
        Mail = namedtuple('Mail', ['body_text', 'body_html', 'attachments', 'total_part'])

        # Attachment
        if msg_obj.get_filename():
            attachment_path = self.process_attachment(msg_obj)
            attachments.append(attachment_path)
            total_part += 1
            return Mail(body_text, body_html, attachments, total_part)
        # No attachment!
        # Text/html/other data:
        content_type = msg_obj.get_content_type()
        if content_type == "text/plain":
            body_text += str(msg_obj.get_payload(decode=True))
        elif content_type == "text/html":
            body_html += str(msg_obj.get_payload(decode=True))
        else:
            # Sometimes packed file and name is contained in content-type headers
            attachment_path = self.process_packed_file(msg_obj)
            if attachment_path:
                attachments.append(attachment_path)
            total_part += 1
            return Mail(body_text, body_html, attachments, total_part)
        total_part += 1
        return Mail(body_text, body_html, attachments, total_part)

    def parse_multi_part_email(self, msg_obj: Message, body_text: str, body_html: str,
                               attachments: List, total_part: int) -> namedtuple:
        Mail = namedtuple('Mail', ['body_text', 'body_html', 'attachments', 'total_part'])
        part = 0
        while True:
            # If we cannot get the payload, it means we hit the end:
            try:
                payload = msg_obj.get_payload(part)
            except:
                break
            # payload is a new Message object which goes back to fetch_content
            content = self.fetch_content(payload)
            body_text += content.body_text
            body_html += content.body_html
            attachments += content.attachments
            total_part += content.total_part
            part += 1
        return Mail(body_text, body_html, attachments, total_part)

    def fetch_content(self, msg_obj: Message) -> namedtuple:
        """Extract content from e-mail file and return namedtuple with body_text, body_html, attachments, total_part"""
        body_text = ''
        body_html = ''
        total_part = 0
        attachments = []
        # for single part email
        if not msg_obj.is_multipart():
            return self.parse_single_part_email(msg_obj, body_text, body_html, attachments, total_part)
        # for multi part email
        return self.parse_multi_part_email(msg_obj, body_text, body_html, attachments, total_part)
