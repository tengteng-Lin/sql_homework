'''
JSON API definition
'''

import json,logging,inspect,functools

class APIError(Exception):
    '''
    the base APIError which contains error(required),data(optional) and message(optional).
    基础的APIError，包含错误类型（必要），数据（可选），信息（可选）
    '''

    def __init__(self,error,data='',message=''):
        super(APIError, self).__init__(message)
        self.error = error
        self.data = data
        self.message = message

class APIValueError(APIError):
    '''
    Indicate the input value has error or invalid. The data specifies the error field of input form.
    表名输入数据有问题，data说明输入的错误字段
    '''

    def __init__(self,field,message=''):
        super(APIValueError, self).__init__('value:invalid',field,message)

class APISourceNotFoundError(APIError):
    '''
    Indicate the resource was not found.The data specifies the resource name.
    找不到资源，data说明资源名字
    '''
    def __init__(self,field,message=''):
        super(APISourceNotFoundError, self).__init__('value:not found',field,message)

class APIPermissionError(APIError):
    '''
    Indicate the api has no permission
    接口没有权限
    '''
    def __init__(self,message=''):
        super(APIPermissionError,self).__init__('permission:forbidden','perssion',message)