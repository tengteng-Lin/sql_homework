import asyncio,os,inspect,logging,functools   #functools高阶函数模块，提供常用的高阶函数，如wraps

from urllib import parse
from aiohttp import web
from apis import APIError

def get(path):
    '''
    Define decorator @get('/path')
    @get 装饰器，给处理函数绑定URL和HTTP method-GET的属性
    这是个三层嵌套的装饰器，目的是可以在decorator本身传入参数
    这个装饰器将一个函数映射为一个URL处理函数
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

    def decorator(func):  #传入参数是函数
        #python内置的functools.wraps装饰器作用是把装饰后的函数的__name__属性变为原始的属性
        #因为当使用装饰器后，函数的__name__属性会变为wrapper
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)
        wrapper.__method__ = 'POST'  #给原始函数添加请求方法‘post’
        wrapper.__route__ = path   #给原始函数添加请求路径path
        return wrapper
    return decorator    #这样，一个函数通过@post（path）的装饰就附带了URL信息

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

def has_named_kw_args(fn):  #判断有没有关键字参数
    params = inspect.signature(fn).parameters
    for name,param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            return True

def has_var_kw_arg(fn):  #判断有没有可变的关键词参数（**），如果有就输出True
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


#定义RequestHandler类，封装url处理函数
#RequestHandler的目的是从url函数中分析需要提取的参数，从request中获取必要的参数
#调用url参数，将结果转换为web.response
#fn就是handler中的函数
class RequestHandler(object):   #从URL函数中分析其需要接收的参数，从request中获取必要的参数，调用URL函数
    '''
    1. __init__()的作用是初始化某个类的一个实例。 
    2. __call__()的作用是使实例能够像函数一样被调用，同时不影响实例本身的生命周期（__call__()不影响一个实例的构造和析构）。但是__call__()可以用来改变实例的内部成员的值。
    '''
    def __init__(self,app,fn):  #接受app参数
        self._app = app
        self._func = fn
        #下面的属性是对传入的fn的参数的一些判断
        self._has_request_arg = has_request_arg(fn)
        self._has_var_kw_arg = has_var_kw_arg(fn)
        self._has_named_kw_args = has_named_kw_args(fn)
        self._named_kw_args = get_named_kw_args(fn)
        self._required_kw_args = get__required_kw_args(fn)

    async def __call__(self, request):
        kw = None  #假设不存在关键字参数
        #如果fn的参数有可变的关键字参数或关键字参数
        if self._has_var_kw_arg or self._has_named_kw_args or self._required_kw_args:
            if request.method == 'POST':
                if not request.content_type:  #查询有没有提交数据的格式
                    return web.HTTPBadRequest(text='Missing Content-type')
                ct = request.content_type.lower()
                if ct.startwith('application/json'):  #表示消息主体是序列化后的json字符串
                    params = await request.json()  #read request body decoded asjson
                    if not isinstance(params,dict):   #如果读取出来的信息类型不是dict，
                        return web.HTTPBadRequest(text='JSON body must be object') #那json对象一定有问题
                    kw = params  #把读取出来的dict赋值给kw
                #以下两种 content type都表示消息主体是表单
                elif ct.startwith('application/x-www-form-urlencoded') or ct.startwith('multipart/form-data'):
                    #request.post方法从request  body读取post参数，即表单信息，并包装成字典赋给kw变量
                    params = await request.post()
                    kw = dict(**params)
                #post的消息主体既不是json对象，也不是浏览器表单，只能返回不支持该消息类型
                else:
                    return web.HTTPBadRequest(text='Unsupported Content-Type:%s' % (request.content_type))


            if request.method == 'GET':
                qs = request.query_string  #表示url中的查询字符串
                # 比如我百度ReedSun，得到网址为https://www.baidu.com/s?ie=UTF-8&wd=ReedSun
                # 其中‘ie=UTF-8&wd=ReedSun’就是查询字符串
                if qs:
                    kw = dict()
                    for k,v in parse.parse_qs(qs,True).items():  #parse a query string given as a string argument.Data are returned as a dictionary. The dictionary keys are the unique query variable names and the values are lists of values for each name.
                        #parse.parse_qs   分析http查询字符串，返回字典格式
                        # parse.parse_qs(qs, keep_blank_values=False, strict_parsing=False)函数的作用是解析一个给定的字符串
                        # keep_blank_values默认为False，指示是否忽略空白值，True不忽略，False忽略
                        # strict_parsing如果是True，遇到错误是会抛出ValueError错误，如果是False会忽略错误
                        # 这个函数将返回一个字典，其中key是等号之前的字符串，value是等号之后的字符串但会是列表
                        # 比如上面的例子就会返回{'ie': ['UTF-8'], 'wd': ['ReedSun']}
                        kw[k] = v[0]
        #如果经过以上处理，kw是None，即上面if语句块没有被执行
        #则获取请求的abstract math info（抽象数学信息），并以字典形式存入kw
        #match_info主要是保存像@get('/blog/{id}')里面的id，就是路由路径里的参数
        if kw is None:
            kw = dict(**request.match_info)
        else:
            # 如果经过以上处理了，kw不为空了，而且没有可变的关键字参数，但是有关键字参数
            if not self._has_var_kw_arg and self._named_kw_args:
                #remove all unamed kw
                #剔除kw中kw中key不是fn的关键字参数的项
                copy = dict()
                for name in self._named_kw_args:
                    if name in kw:
                        copy[name] = kw[name]
                kw = copy
            #check named arg:
            #遍历request.match_info(abstract math info),再把abstract math info的值加入kw中
            #若其key既存在于abstract math  info又存在于kw中，发出重复参数警告
            for k,v in request.match_info.items():
                if k in kw:
                    logging.warning('Duplicate arg name in named arg and kw args:%s' % k)
                kw[k] = v
        #如果fn的参数有request，则再给kw中加上request的key和值
        if self._has_request_arg:
            kw['request'] = request
        #check required kw
        if self._required_kw_args:
            for name in self._required_kw_args:
                #kw必须包含 全部没有默认值的关键字参数，如果发现遗漏则说明有参数没传入，报错
                if not name in kw:
                    return web.HTTPBadRequest('Missing argument:%s' % name)
        #以上过程即为从request中获得必要的参数，并组成kw


        #以下调用handler处理，并返回response
        logging.info('call with args:%s' % str(kw))
        try:
            r = await self._func(**kw)   # 执行handler模块里的函数
            return r
        except APIError as e:
            return dict(error=e.error,data=e.data,message=e.message)


def add_static(app):
    '''
    向app中添加静态文件目录
    :param app: 
    :return: 
    '''

    #os.path.abspath(__file__)，返回当前脚本的绝对路径（包括文件名）
    #os.path.dirname()，去掉文件名，返回目录路径
    #os.path.join()，将分离的各部分组合成一个路径名
    #因此以下操作就是将本文件同目录下的static目录（即www/static/)加入到应用的路由管理器中
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'static')
    app.router.add_static('/static/',path)
    logging.info('add static %s => %s' % ('/static/',path))


def add_route(app,fn):
    '''
    用来注册一个URL处理函数
    :param app: 
    :param fn: 
    :return: 
    '''
    method = getattr(fn,'__method__',None)
    path = getattr(fn,'__route__',None)
    if path is None or method is None:
        # print(path,'路径')
        # print(method,'方法')
        raise ValueError('@get or @post not defined in %s.' % str(fn))
    if not asyncio.iscoroutinefunction(fn) and not inspect.isgeneratorfunction(fn):   #判断是否为协程且生成器，不是则把这个函数变成协程
        fn = asyncio.coroutine(fn)
    logging.info('add route %s %s => %s(%s)' % (method,path,fn.__name__,','.join(inspect.signature(fn).parameters.keys())))
    app.router.add_route(method,path,RequestHandler(app,fn))   #注册request handler

def add_routes(app,moudle_name):
    '''
    可以批量注册的函数，只需向这个函数提供要批量注册函数的文件路径，新编写的函数就会筛选，注册文件内所有符合注册条件的函数
    :param app: 
    :param moudle_name: 
    :return: 
    '''
    n = moudle_name.rfind('.')  #rfind（）返回字符串最后一次出现的位置（从右向左查询），如果没有匹配项则返回-1
    '''
    返回'.'最后出现的位置
    如果为-1，说明是 module_name中不带'.',例如(只是举个例子) handles 、 models
    如果不为-1,说明 module_name中带'.',例如(只是举个例子) aiohttp.web 、 urlib.parse()    n分别为 7 和 5 
    我们在app中调用的时候传入的module_name为handles,不含'.',if成立, 动态加载module

    '''
    if n == (-1):
        mod = __import__(moudle_name,globals(),locals())   #用于动态加载类和函数
    else:
        name = moudle_name[n+1:]
        mod = getattr(__import__(moudle_name[:n],globals(),locals(),[name]),name)
    for attr in dir(mod):
        if attr.startswith('_'):
            continue  #排除私有属性
        fn  = getattr(mod,attr)
        if callable(fn):  #查看提取出来的属性是不是函数
            method = getattr(fn,'__method__',None)
            path = getattr(fn,'__route__',None)
            # print(method)
            # print(path)
            if method and path:
                add_route(app,fn)
