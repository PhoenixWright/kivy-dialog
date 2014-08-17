
class Dialog(object):
    """Interface for dialog. Implemented by different formats of dialog, like
    TwineDialog.
    """

    def __init__(self, filepath):
        """
        :param filepath: Filepath to the dialog file.
        :type filepath: str
        :return: The Dialog object.
        :rtype: Dialog
        """
        pass

    @staticmethod
    def next(self, choice):
        """Progress the dialog by selecting a dialog node id to retrieve.
        :param choice: The id of the dialog node to get.
        :type choice: str
        :return: The chosen dialog node.
        :rtype: DialogNode
        """
        pass
