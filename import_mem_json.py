import json
import re
import os
# need to install python-dateutil
from dateutil import parser
from subprocess import call
from urllib.parse import quote
# for downloading attachments
import requests

MEM_JSON_PATH = 'mems.json'
ATTACHMENT_FOLDER_PATH = 'attachments'
TOUCH_COMMAND_AVAILABLE = True
SETFILE_COMMAND_AVAILABLE = False

SYSTEM_DATE_FORMAT = '%m/%d/%Y %H:%M:%S'
MEM_LINK_PATTERN = r'\(https://mem.ai/m/([A-Za-z0-9]+)\)'
ATTACHMENT_LINK_PATTERN = r'\!\[\]\((https://storage.googleapis.com/memvp-.*/)([^)]+)\)'
FILE_EXTENSION_AND_UUID_PATTERN = r'\.(.+)[a-zA-Z0-9]{8}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{12}$'

# https://www.anthonysmith.me.uk/2008/01/08/moving-files-to-trash-from-the-mac-command-line/
def trash_file(file_path):
    # TOCTTOU oops.
    if os.path.isfile(file_path):
        abs_path = os.path.abspath(file_path).replace('\\', '\\\\').replace('"', '\\"')
        file_clause = f'the POSIX file "{abs_path}"'
        cmd = ['osascript', '-e',
                'tell app "Finder" to move { ' + file_clause + ' } to trash']
        r = call(cmd, stdout=open(os.devnull, 'w'))
        print(f"Trashed {file_path}")

def set_file_timestamps(file_path, created, modified):
    created_command = ""
    if SETFILE_COMMAND_AVAILABLE:
        created_command = f'SetFile -d "{created.strftime(SYSTEM_DATE_FORMAT)}" "{file_path}"'
    elif TOUCH_COMMAND_AVAILABLE:
        created_command = f'touch --date "{created.strftime(SYSTEM_DATE_FORMAT)}" "{file_path}"'
    if created_command!="":
        call(created_command, shell=True)
    modified_command = ""
    if SETFILE_COMMAND_AVAILABLE:
        modified_command = f'SetFile -m "{modified.strftime(SYSTEM_DATE_FORMAT)}" "{file_path}"'
    elif TOUCH_COMMAND_AVAILABLE:
        modified_command = f'touch -m --date "{modified.strftime(SYSTEM_DATE_FORMAT)}" "{file_path}"'
    if modified_command!="":
        call(modified_command, shell=True)

with open(MEM_JSON_PATH) as mems:
    data = json.load(mems)
    id_to_writename = {}
    taken_writenames = set()

    for idx, memJson in enumerate(data):
        # Keep only 40 alphanumerics and spaces.
        title = re.sub(r'[^A-Za-z0-9 ]+', '', memJson['title'])
        name = title[:40] if len(title) > 40 else title
        defaultname = f"{name}.md"
        extended_name = f"{name} {idx}.md"
        writename = extended_name if defaultname in taken_writenames else defaultname
        id_to_writename[memJson['id']] = writename
        taken_writenames.add(writename)
        # Clean up bad imports.
        # trash_file(defaultname)
        # trash_file(extended_name)

    for idx, memJson in enumerate(data):
        writename = id_to_writename[memJson['id']]
        new_note = memJson['markdown']

        # Replace mem.ai links with local links where possible.
        for match in re.finditer(MEM_LINK_PATTERN, new_note):
            mem_id = match.group(1)
            if mem_id in id_to_writename:
                clean_link = quote(id_to_writename[mem_id])
                new_note = new_note.replace(match.group(0), f'({clean_link})')
                print(f"Converted link to local note: {clean_link}.")
            else:
                print(f"Warning: https://mem.ai/m/{mem_id} not found in exported notes.")

        # Replace googleapis attachment links with local links where possible.
        #
        # In the markdown field, for every occurrence of:
        #     ![](https://storage.googleapis.com/memvp-...)
        # download the file, put it in the attachment folder,
        # and replace the link so that it points to the attachment folder.
        # The filename of the attachment should have a suitable extension
        # extracted from the filename.
        # Example:
        #  Given: ![](https://storage.googleapis.com/memvp-25499.appspot.com/images/16288199829444671600345520058319.jpga68d4074-e9cc-4f90-b03f-17e82fbb905c)
        #  Save: 16288199829444671600345520058319.jpga68d4074-e9cc-4f90-b03f-17e82fbb905c
        #  Replace: ![[16288199829444671600345520058319.jpga68d4074-e9cc-4f90-b03f-17e82fbb905c.jpg]]
        #
        for match in re.finditer(ATTACHMENT_LINK_PATTERN, new_note):
            url_full_match = match.group(0)
            url_base = match.group(1)
            url_fname = match.group(2)
            # Attempt to extract an extension from the filename
            local_fname = url_fname
            m=re.search(FILE_EXTENSION_AND_UUID_PATTERN,url_fname)
            if m!=None:
                local_fname = url_fname + "." + m.group(1)
            try:
                r = requests.get(url_base+url_fname, allow_redirects=True)
                with open(ATTACHMENT_FOLDER_PATH+"/"+local_fname, 'wb') as fp:
                    fp.write(r.content)
                new_note = new_note.replace(url_full_match, f'![[{local_fname}]]')
                print(f"Created attachment {local_fname} for remote attachment {url_base+url_fname}")
            except requests.exceptions.RequestException as e:
                print(f"Warning: Unable to download and use {url_base+url_fname}. Will NOT convert to local {local_fname} attachment")

        with open(writename, "w") as new_file:
            new_file.write(new_note)
        created = parser.parse(memJson['created'])
        modified = parser.parse(memJson['updated'])
        set_file_timestamps(writename, created, modified)
        print(f"Wrote note {writename}")
    print(f"Done. Imported {len(data)} notes.")
