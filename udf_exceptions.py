# encoding:utf-8
'''
自定义异常
'''


class BadRefreshException(Exception):
    def __init__(self, err='captha refresh times beyond limitation'):
        Exception.__init__(self, err)


class CjyConectionError(Exception):
    def __init__(self, err='chaojiying connection failed'):
        Exception.__init__(self, err)


class CjyRecognizeException(Exception):
    def __init__(self, err='chaojiying api cannot return captha result'):
        Exception.__init__(self, err)


class CjyApiError(Exception):
    def __init__(self, err='chaojiying service error'):
        Exception.__init__(self, err)


class CjyDecodeException(Exception):
    def __init__(self, err='chaojiying response decode error'):
        Exception.__init__(self, err)


class CapthaNotRefreshException(Exception):
    def __init__(self, err='captha cannot refresh'):
        Exception.__init__(self, err)
