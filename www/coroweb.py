import asyncio,os,inspect,logging,functools

from urllib import parse
from aiohttp import web
from apis import APIError

def get(path):
    '''
    Define decorator @get('/path')
    @get 装饰器，给处理函数绑定URL和HTTP method-GET的属性
    :param path: 
    :return: 
    '''

    def decorator(func):
        @functools.wraps(func)  #保证装饰器不会对被装饰函数造成影响
        def wrapper(*args,**kw):  #装饰函数
            return func(*args,**kw)
        wrapper.__method__ = 'GET'  #存储方法信息
        wrapper.__route__ = path  #存储路径信息
        return wrapper
    return decorator


def post(path):
    '''
    Define decorator @post('/path')
    @post装饰器，给处理函数绑定URL和HTTP method-POST的属性
    :param path: 
    :return: 
    '''

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)
        wrapper.__method__ = 'POST'
        wrapper.__route__ = path
        return wrapper
    return decorator

#运用inspect模块，创建几个函数用于获取URL处理函数与request参数之间的关系
def get__required_kw_args(fn):
    '''
    收集没有默认值的命名关键字参数
    :param fn: 
    :return: 
    '''
    args = []
    params = inspect.signature(fn).parameters  #获取函数fn的参数
    for name,param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY and param.default == inspect.Parameter.empty:   #找到没有默认值的所有仅关键字参数
            #kind描述参数值如何绑定到参数  KEYWORD_ONLY值必须作为关键字参数提供。仅关键字参数是出现在python函数定义中的条目*或*args条目之后的参数
            #default描述参数的默认值
            args.append(name)
    return tuple(args)

def get_named_kw_args(fn):  #获取命名关键字参数
    args = []
    params = inspect.signature(fn).parameters
    for name,param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            args.append(name)
    return tuple(args)

def has_named_kw_args(fn):  #判断有没有命名关键字参数
    params = inspect.signature(fn).parameters
    for name,param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            return True

def has_var_kw_arg(fn):  #判断有没有关键字参数
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.VAR_KEYWORD:
            # VAR_KEYWORD  不绑定到任何其他参数的关键字参数的字典。这对应**kwargs于python函数定义中的参数
            return True

def has_request_arg(fn):  #判断是否含有名为‘request’参数，且该参数是否为最后一个参数
    sig = inspect.signature(fn)
    params = sig.parameters
    found = False
    for name,param in params.items():
        if name == 'request':
            found = True
            continue
        if found and (param.kind != inspect.Parameter.VAR_POSITIONAL and param.kind != inspect.Parameter.KEYWORD_ONLY and param.kind != inspect.Parameter.VAR_KEYWORD):
            # VAR_POSITIONAL一个未绑定到任何其他参数的位置参数元组。这对应*args于python函数定义中的参数
            raise ValueError('request parameter must be the last named parameter in function:%s%s' % (fn.__name__,str(sig)))
    return found



class RequestHandler(object):   #从URL函数中分析其需要接收的参数，从request中获取必要的参数，调用URL函数
    def __init__(self,app,fn):  #接受app参数
        self._app = app
        self._func = fn
        self._has_request_arg = has_request_arg(fn)
        self._has_var_kw_arg = has_var_kw_arg(fn)
        self._has_named_kw_args = has_named_kw_args(fn)
        self._named_kw_args = get_named_kw_args(fn)
        self._required_kw_args = get__required_kw_args(fn)

    async def __call__(self, request):  #构造协程
        kw = None
        if self._has_var_kw_arg or self._has_named_kw_args or self._required_kw_args:
            if request.method == 'POST':
                if not request.content_type:  #查询有没有提交数据的格式
                    return web.HTTPBadRequest(text='Missing Content-type')
                ct = request.content_type.lower()
                if ct.startwith('application/json'):
                    params = await request.json()  #read request body decoded asjson
                    if not isinstance(params,dict):
                        return web.HTTPBadRequest(text='JSON body must be object')
                    kw = params
                elif ct.startwith('application/x-www-form-urlencoded') or ct.startwith('multipart/form-data'):
                    params = await request.post()  #reads POST parameters from request body.If method is not POST,PUT,PATCH,TEACE or DELETE or content_type is not empty or application/x-www-form-urlencoded or multipart/form-data returns empty multidict.
                    kw = dict(**params)
                else:
                    return web.HTTPBadRequest(text='Unsupported Content-Type:%s' % (request.content_type))
            if request.method == 'GET':
                qs = request.query_string  #The query string in the URL
                if qs:
                    kw = dict()
                    for k,v in parse.parse_qs(qs,True).items():  #parse a query string given as a string argument.Data are returned as a dictionary. The dictionary keys are the unique query variable names and the values are lists of values for each name.
                        #parse.parse_qs   分析http查询字符串，返回字典格式
                        kw[k] = v[0]
        if kw is None:
            kw = dict(**request.match_info)
        else:
            if not self._has_var_kw_arg and self._named_kw_args:  #但函数参数没有关键字参数时，移去request除命名关键字参数所有的参数信息
                #remove all unamed kw
                copy = dict()
                for name in self._named_kw_args:
                    if name in kw:
                        copy[name] = kw[name]
                kw = copy
            #check named arg:
            for k,v in request.match_info.items():
                if k in kw:
                    logging.warning('Duplicate arg name in named arg and kw args:%s' % k)
                kw[k] = v
        if self._has_request_arg:
            kw['request'] = request
        #check required kw
        if self._required_kw_args:
            for name in self._required_kw_args:
                if not name in kw:
                    return web.HTTPBadRequest('Missing argument:%s' % name)
        logging.info('call with args:%s' % str(kw))
        try:
            r = await self._func(**kw)
            return r
        except APIError as e:
            return dict(error=e.error,data=e.data,message=e.message)


def add_static(app):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'static')
    app.router.add_static('/static/',path)
    logging.info('add static %s => %s' % ('/static/',path))

def add_route(app,fn):
    method = getattr(fn,'__method__',None)
    path = getattr(fn,'route',None)
    if path is None or method is None:
        raise ValueError('@get or @post not defined in %s.' % str(fn))
    if not asyncio.iscoroutinefunction(fn) and not inspect.isgeneratorfunction(fn):
        fn = asyncio.coroutine(fn)
    logging.info('add route %s %s => %s(%s)' % (method,path,fn.__name__,','.join(inspect.signature(fn).parameters.keys())))
    app.router.add_route(method,path,RequestHandler(app,fn))

def add_routes(app,moudle_name):
    n = moudle_name.rfind('.')
    if n == (-1):
        mod = __import__(moudle_name,globals(),locals())
    else:
        name = moudle_name[n+1:]
        mod = getattr(__import__(moudle_name[:n],globals(),locals(),[name]),name)
    for attr in dir(mod):
        if attr.startswith('_'):
            continue
        fn  = getattr(mod,attr)
        if callable(fn):
            method = getattr(fn,'__method__',None)
            path = getattr(fn,'__route__',None)
            if method and path:
                add_route(app,fn)
