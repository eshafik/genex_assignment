import json
import os
from pathlib import Path, PosixPath
from typing import List, Union
import email

from email_content_processor import EmailMetaDataProcessor, EmailContentProcessor
from file_handler import FileHandler


class EmailFileProcessor(FileHandler):
    def __init__(self, file_path: Union[PosixPath, bool]):
        self.file_path = file_path
        self.file_name: Union[str, None] = None
        self.data = []
        super(EmailFileProcessor, self).__init__(file_path, '.eml')

    def extract(self) -> List[dict]:
        email_files = self.file_list()
        if not email_files:
            raise ValueError('No email file found!')
        for email_file in email_files:
            email_f = open(email_file)
            file_name = email_f.name
            # with open(email_file, 'rb') as email_f:
            msg_obj = email.message_from_file(email_f)
            meta_data = EmailMetaDataProcessor(msg_obj=msg_obj)
            caption = meta_data.extract_meta_data()
            email_f.close()
            content_processor = EmailContentProcessor(file_name=file_name)
            content = content_processor.fetch_content(msg_obj)

            pulled_data = {"subject": caption.subject, "from": caption.from_email, "to": caption.to_email,
                           "cc": caption.cc_email, "time": caption.date_time,
                           'body': content.body_html or content.body_text,
                           'attachments': content.attachments, "file_name": os.path.basename(file_name)}
            self.data.append(pulled_data)
        return self.data


if __name__ == '__main__':
    try:
        user_input = input("Enter the path/directory of your file: (If current directory then press enter)\n")
        path = (os.path.exists(user_input) and Path(user_input)) or Path.cwd()
        parser = EmailFileProcessor(path)
        data = parser.extract()
        with open("output.json", "w") as file:
            json.dump(data, file, indent=4, sort_keys=True)
        print("\n\nPlease check the output.json file for the output result\n\n")
    except ValueError as e:
        print(e)
