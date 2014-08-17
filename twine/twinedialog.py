import re
import json

from kivydialog.dialog import Dialog
from kivydialog.dialognode import DialogNode


class TwineDialogEntry(object):
    def __init__(self, title, text, tags, created, modified, modifier):
        """The class representing the Twine json nodes for each dialog node.
        :param title: The title of the dialog entry (the node id).
        :type title: str
        :param text: The text in the dialog entry.
        :type text: str
        :param tags: The tags the dialog entry has.
        :type tags: list[str]
        :param created: Timestamp of when the dialog was created.
        :type created: int
        :param modified: Timestamp of when the dialog was modified.
        :type modified: int
        :param modifier: The name of the person or program that modified the entry.
        :type modifier: int
        :return: The TwineDialogEntry.
        :rtype: TwineDialogEntry
        """
        self.title = title
        self.text = text
        self.tags = tags
        self.created = created
        self.modified = modified
        self.modifier = modifier


class TwineDialog(Dialog):
    variable_regex = r'<<[\w\d\s\$=\"]*>>'
    choice_regex = r'\[\[.*\]\]'

    def __init__(self, filepath):
        """
        :param filepath: Filepath to the dialog file.
        :type filepath: str
        :return: The TwineDialog object.
        :rtype: TwineDialog
        """
        super(TwineDialog, self).__init__(filepath)

        self.dialog_entries = dict()
        with open(filepath) as f:
            twine_json = json.load(f)

        for entry in twine_json['data']:
            tde = TwineDialogEntry(
                entry['title'],
                entry['text'],
                entry['tags'],
                entry['created'],
                entry['modified'],
                entry['modifier']
            )
            self.dialog_entries[tde.title] = tde

    def next(self, choice):
        """Progress the dialog by selecting a dialog node id to retrieve.
        :param choice: The id of the dialog node to get.
        :type choice: str
        :return: The chosen dialog node.
        :rtype: DialogNode
        """
        next_node = self.dialog_entries[choice]

        # get the text to perform some cleanup and splitting
        next_node_text = next_node.text

        # get rid of the double bracket variable stuff
        next_node_text = re.sub(self.variable_regex, '', next_node_text).strip()

        # remove the choices from the text
        next_node_text = re.sub(self.choice_regex, '', next_node_text).strip()

        # split the text by double newlines
        if next_node_text:
            next_node_text = next_node_text.split('\n\n')
        else:
            next_node_text = []

        # parse the choices out of the text
        choices = self._parse_choices(next_node.text)

        return DialogNode(next_node_text, choices)

    def _parse_choices(self, text):
        """Returns a dict of choice ids -> choice text.

        Finds a choice and determines if the id of the next node is just the
        choice text or specified in the double brackets.

        Format is either [[{node_id}]] or [[{text}|{node_id}]]

        :param text: The dialog to parse choices out of.
        :type text: str
        :return: A dictionary of choice ids -> choice text.
        :rtype: dict(str, str)
        """
        choices = dict()

        matches = re.findall(self.choice_regex, text)
        for match in matches:
            # remove the brackets
            match = match.replace('[[', '')
            match = match.replace(']]', '')

            if '|' in match:
                # format is {text}|{node_id}, the text and node id are different
                text, node_id = match.split('|')
                choices[node_id] = text
            else:
                choices[match] = match

        return choices
