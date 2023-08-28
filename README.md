# Migrate Mem

Converts the output of a Mem.ai export to standard markdown files, such as for obsidian.md, on MacOS using Python.

- Correctly sets metadata like created and updated times.
- Tags should just work out of the box.
- Links will be correctly converted to local links where possible in the standard `[text](file.md)` format.
  - Not the `[[note]]` format since this is a less surprising way to preserve the `text` and handles hairy corner cases like nesting.
- Attachments are downloaded locally and their links converted to local links

## Usage

1. Export from Mem.ai as a JSON.
2. Create a subfolder in vault.
3. Move the JSON file to the sub folder.
4. Move `import_mem_json.py` to the subfolder.
5. Double check `MEM_JSON_PATH`, `ATTACHMENT_FOLDER_PATH`, `TOUCH_COMMAND_AVAILABLE`, and `SETFILE_COMMAND_AVAILABLE`.
6. `pip install python-dateutil` or env equivalent.
7. `python import_mem_json.py`
8. Done!

https://www.buymeacoffee.com/jksg
