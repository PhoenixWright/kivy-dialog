
class DialogNode:
    def __init__(self, text, choices):
        """A node of dialog with text and choices. The text is a list of strings
        that are progressed through, and the choices are a dictionary of
        choice ids->choice text.
        :param text: List of text items in the node.
        :type text: list[str]
        :param choices: List of choices in the node.
        :type choices: list[str]
        :return: The DialogNode object.
        :rtype: DialogNode
        """
        self.text = text
        self.choices = choices
