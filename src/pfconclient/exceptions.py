"""
Pfcon exceptions module.
"""


class PfconException(Exception): pass


class PfconRequestException(PfconException):
    def __init__(self, msg, **kwargs):
        self.code = kwargs.get('code')
        super().__init__(msg)


class PfconRequestInvalidTokenException(PfconRequestException): pass


class PfconErrorException(PfconException): pass
