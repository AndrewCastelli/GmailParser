import email.utils
import os
import imaplib
import random
from tika import parser


def separate_content(filename, email_parts, dictionary, directory):
    """
    Download attachments, making sure names don't conflict/repeat.
    Separate email content into plain/body, html/body, and attachments
    :param filename: filename associated with each payload
    :param email_parts: parts of email iterated over with .walk()
    :param dictionary: Dictionary created in parse_email()
    :param directory: Directory where you want your attachments saved.
    :return:
    """
    if bool(filename):
        print('Downloading Attachment(s)')
        print(filename)
        path = os.path.join(directory, filename)
        
        # Split names, add random digits to avoid identical names
        while os.path.isfile(path):
            split_name = filename.split('.')
            filename = split_name[0] + '_' + str(random.randint(0, 99)) + '.' + split_name[1]
            path = os.path.join(directory, filename)

        fp = open(path, 'wb')
        dictionary['attachments'].append(filename)
        fp.write(email_parts.get_payload(decode=True))
        fp.close()
        # Finally, check if attachment is a pdf - get text if it is
        deal_with_pdf(directory, filename)

    else:  # save plain text and html to our dictionary
        if email_parts.get_content_type() == 'text/plain':
            dictionary['body_plain'] = email_parts.get_payload(decode=True).decode('utf-8')

        elif email_parts.get_content_type() == 'text/html':
            dictionary['body_html'] = email_parts.get_payload(decode=True).decode('utf-8')


def deal_with_pdf(path, filename):
    """
    :param path: Path to pdf attachment saved with separate_contents().
    :param filename: Filename grabbed .get_filename() in parse_email().
    :return: Content of pdf as text.
    """
    if '.pdf' in filename:
        path = os.path.join(path, filename)
        raw = parser.from_file(path, service='text')
        pdf_text = str(raw['content'])
        print(pdf_text)
        return pdf_text
    else:
        print('No pdf found.')


def parse_email():
    """
    Prompt user for login credentials, folder, and subject of desired email.
    Parse useful email parts from bytes string.
    Set up dictionary to save relevant parts, store parts in dictionary.
    """
    # First, we log in and get the bytes data from desired email
    m = imaplib.IMAP4_SSL("imap.gmail.com")
    user = input('Enter your gmail username:')
    pwd = input('Enter your gmail password:')
    folder = input('Enter the folder the email is in:')
    subject = input('Enter part or all of the emails subject:')
    storage_dir = input('Enter path where you want to store attachments: ')
    search = 'SUBJECT'
    subject = '({} \"{}\")'.format(search, subject)
    m.login(user, pwd)
    m.select(folder)
    _, email_data = m.search(None, subject)
    email_data = email_data[0]

    for parts in email_data.split():
        _, data = m.fetch(parts, '(RFC822)')
        parsed_email = email.message_from_bytes(data[0][1])
        # Store parts in dictionary
        parsed_dict = {
            'from': email.utils.parseaddr(parsed_email['From']),
            'to': parsed_email['to'],
            'subject': parsed_email['Subject'],
            'body_plain': '',
            'body_html': '',
            'attachments': []
        }
        # Use walk generator to iterate parts of emails
        for part in parsed_email.walk():
            filename = part.get_filename()
            separate_content(filename, part, parsed_dict, storage_dir)

        print(parsed_dict)
        return parsed_dict


if __name__ == '__main__':

    parse_email()


