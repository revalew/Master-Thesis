class ReadFailedException(Exception):
    """
    Exception for read failures.
    """

    def __init__(self, message: str):
        super().__init__(message)