class StructFromDict:
    """
    Simple struct that is constructed dynamically from a dictionary.
    All keys from the dictionary will get their own member.

    NOTE: not using namedtuple for this, because I want to be able to change the values later.
    """

    def __init__(self, **entries):
        """
        Initialize by creating all the necessary members.
        """
        self.__dict__.update(entries)


    def setValues(self, **values):
        """
        Set new values to (possibly) present members.
        WARNING: If the member is not already present, a new member will be generated,
        this can lead to some unwanted side effects.
        """
        self.__dict__.update(values)
