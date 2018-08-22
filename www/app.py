import logging;logging.basicConfig(level=logging.INFO)
import asyncio,os,json,time  #asyncio的编程模型就是一个消息循环。我们从asyncio模块中直接获取一个EventLoop的引用，然后把需要执行的协程扔到EventLoop中执行，就实现了异步IO
from datetime import datetime
from aiohttp import web #基于协程的异步模型    异步编程的原则：一旦确定使用异步，则系统的每一层都要异步

#jinja2是仿照Django模板的配置环境，FileSystemLoader是文件系统加载器，用来加载模板路径
from jinja2 import Environment,FileSystemLoader
import orm
from www.coroweb import add_static,add_routes


def init_jinja2(app,**kw):
    '''
    初始化jinja2，以便其他函数使用jinja2模板，配置jinja2的环境
    :param app: 
    :param kw: 
    :return: 
    '''
    logging.info('init jinja2')
    #设置解析模板需要用到的环境变量
    options = dict(
        autoescape = kw.get('autoescape',True), #自动转义xml/html的特殊字符
        block_start_string = kw.get('block_start_string','{%'),  #设置代码起始字符串
        block_end_string = kw.get('block_end_string','%}'),
        variable_start_string = kw.get('variable_start_string','{{'),  #设置变量的起始和结束字符串
        variable_end_string = kw.get('variable_end_string','}}'),  #{{}}中间是变量（例子见templates目录下的test.html文件
        auto_reload = kw.get('auto_reload',True)  #当模板文件被修改后，下次请求加载该模板文件的时候会自动加载修改后的模板文件

    )
    path = kw.get('path',None)  #从kw中获取模板路径，如果没有传入这个参数则默认为None
    #如果path为None，则将当前文件所在目录下的templates目录设为模板文件目录   （可能是第一次进入/运行  时？？
    if path is None:
        #os.path.abspath(__file__) 取当前文件的绝对目录
        #os.path.dirname(）取绝对目录的路径部分
        #os.path.join(path,name)把目录和名字组合
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'templates')  #os.path.join用于拼接文件路径
    logging.info('set jinja2 template path:%s ' % path)
    #loader=FileSystemLoadere(path)指的是到哪个目录下加载模板文件，**options就是前面的options
    env = Environment(loader=FileSystemLoader(path),**options)
    filters = kw.get('filters',None)  #filters=>过滤器
    if filters is not None:
        for name,f in filters.items():
            env.filters[name] = f  #在env中添加过滤器
    app['__templating__'] = env  #前面已经把jinja2的环境配置都赋值给env了，这里再把env存入app的dict中，这样app就知道要去哪里找模板，怎么解析模板


async def logger_factory(app,handler):
    '''
    记录URL日志的logger   协程，两个参数
    当http请求时，通过logging。info输出请求的信息，其中包括请求的方法和路径
    :param app: 
    :param handler: 
    :return: 
    '''
    async def logger(request):
        logging.info('Request:%s %s' % (request.method,request.path))  #日志
        return (await handler(request))
    return logger



async  def data_factory(app,handler):
    '''
    只有当请求方法为POST时这个函数才起作用
    :param app: 
    :param handler: 
    :return: 
    '''
    async def parse_data(request):
        if request.method == 'POST':
            if request.content_type.startswith('application/json'):
                request.__data__ = await request.json()
                logging.info('request join: %s' % str(request.__data__))
            elif request.content_type.startswith('application/x-www-form-urlencoded'):
                request.__data__ = await request.post()
                logging.info('request form: %s' % str(request.__data__))
        return (await handler(request))
    return parse_data


async def response_factory(app,handler):
    '''
    函数返回值转化为‘web.Response’对象
    :param app: 
    :param handler: 
    :return: 
    '''
    async def response(request):
        logging.info('Response handler...')
        r = await handler(request)
        if isinstance(r,web.StreamResponse):
            #如果相应结果为StreamResponse，直接返回
            #StreamResponse是aiohttp定义response的基类，即所有响应类型都继承自该类
            #StreamResponse主要为流式数据而设计
            return r
        if isinstance(r,bytes):
            #如果响应结果为字节流，则将其作为应答的body部分，并设置响应类型为流型
            resp = web.Response(body=r)
            resp.content_type = 'application/octet-stream'
            return resp
        if isinstance(r,str):
            if r.startswith('redirect'):
                return web.HTTPFound(r[9:])  #即把r字符串啊之前的‘redirect：’去掉
            #然后以utf8对其编码，并设置响应类型为html型
            resp = web.Response(body=r.encode('utf-8'))
            resp.content_type = 'text/html;charset=utf-8'
            return resp
        if isinstance(r,dict):
            #如果响应结果是字典，则获取他的jinja2模板信息，此处为jinja2.env
            template = r.get('__template__')
            if template is None:
                #若不存在对应模板，则 将字典调整为json格式返回，并设置响应类型为json
                resp = web.Response(body=json.dumps(r,ensure_ascii=False,default=lambda o:o.__dict__).encode('utf-8'))
                resp.content_type = 'application/json;charset=utf-8'
                return resp
            else: #jinja2模板
                resp = web.Response(body=app['__templating__'].get_template(template).render(**r).encode('utf-8'))
                resp.content_type = 'text/html;charset=utf-8'
                return resp
        if isinstance(r,int) and r>=100 and r <600 :
            #如果响应结果为整数型，且在100和600之间
            #此时r为状态码，即404,500等
            return web.Response(r)
        if isinstance(r,tuple) and len(r) == 2:
            #如果响应结果为长度为2的元组，元组第一个值为整数型且在100和600之间，则t为http状态码，m为错误描述，返回状态码和错误描述
            t,m = r
            if isinstance(t,int) and t >= 100 and t <600:
                return web.Response(t,str(m))
        #default:  默认以字符串形式返回响应结果，设置类型为普通文本
        resp = web.Response(body=str(r).encode('utf-8'))
        resp.content_type = 'text/plain;charset=utf-8'
        return resp
    return response

def datetime_filter(t):
    '''
    时间过滤器，作用是返回日志创建时间，用于显示在日志标题下面
    :param t: 
    :return: 
    '''
    delta = int(time.time() - t)
    if delta < 60:
        return u'1分钟前'
    if delta < 3600:
        return u'%s分钟前' % (delta // 60)
    if delta <86400:
        return u'%s小时前' % (delta // 3600)
    if delta <604800:
        return u'%s天前' % (delta // 86400)
    dt = datetime.fromtimestamp(t)
    return u'%s年%s月%s日' % (dt.year,dt.month,dt.day)

async def init(loop):
    '''
    调用asyncio实现异步IO
    :param loop:
    :return:
    '''

    await orm.create_pool(loop=loop, host='127.0.0.1', post=3306, user='root', password='password', db='awesome') # 创建数据库连接池
    app = web.Application(loop=loop,middlewares=[
        logger_factory,response_factory
    ])  #创建app对象，同时传入上文定义的拦截器middlewares
    init_jinja2(app,filters=dict(datetime=datetime_filter))  #初始化jinja2模板，并传入时间过滤器
    add_routes(app,'handlers')  #handlers指的是handlers模块也就是handlers.py
    add_static(app)
    srv = await loop.create_server(app.make_handler(),'127.0.0.1',9000)
    logging.info('server started at http://127.0.0.1:9000...')
    return srv
#
# #
# # def index(request):  #requeset包含了浏览器发送过来的http协议的信息，一般不用自己构造
# #     return web.Response(body=b'<h1>awesome</h1>')   #构造一个http相应  类声明 class aiohttp.web.Response(*, status=200, headers=None, content_type=None, body=None, text=None)
# #
# # #用asyncio提供的@asyncio.coroutine  可以把一个generator标记为coroutine类型，然后在内部用yield from调用另一个coroutine实现异步操作
# # #异步操作需要在coroutine中通过yield from完成，多个coroutine可以封装成一组Task然后并发执行
# # @asyncio.coroutine
# # def init(loop):
# #     app=web.Application(loop=loop)  #创建一个服务器app实例，作用是用来处理URL、http协议    【类声明见百度
# #     app.router.add_route('GET','/',index)  #使用app时，首先要将URLs 注册进router，再用aiohttp.RequestHandlerFactory作为协议簇创建套接字 ，该方法将处理函数与对应的URL绑定，浏览器敲击相应URL时会返回处理函数的内容
# #     srv = yield from loop.create_server(app.make_handler(),'127.0.0.1',9000)  #用协程创建监听服务，loop为传入函数的协程。 yield from返回一个创建好的，绑定IP、端口、HTTP协议簇的监听服务的协程。
# #     logging.info('server started at http://127.0.0.1:9000')
# #     return srv
#
loop = asyncio.get_event_loop()  #创建协程
loop.run_until_complete(init(loop))  #运行协程，直到完成
loop.run_forever() #运行协程，直到调用stop





























































