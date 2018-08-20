import logging;logging.basicConfig(level=logging.INFO)
import asyncio,os,json,time  #asyncio的编程模型就是一个消息循环。我们从asyncio模块中直接获取一个EventLoop的引用，然后把需要执行的协程扔到EventLoop中执行，就实现了异步IO
from datetime import datetime
from aiohttp import web #基于协程的异步模型    异步编程的原则：一旦确定使用异步，则系统的每一层都要异步
from jinja2 import Environment,FileSystemLoader
import orm
from coroweb import add_routes,add_static

def init_jinja2(app,**kw):
    logging.info('init jinja2')
    options = dict(
        autoescape = kw.get('autoescape',True),
        block_start_string = kw.get('block_start_string','{%'),
        block_end_string = kw.get('block_end_string','%}'),
        variable_start_string = kw.get('variable_start_string','{{'),
        variable_end_string = kw.get('variable_end_string','}}'),
        auto_reload = kw.get('auto_reload',True)
    )
    path = kw.get('path',None)
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'templates')
    logging.info('set jinja2 template path:%s ' % path)
    env = Environment(loader=FileSystemLoader(path),**options)
    filters = kw.get('filters',None)
    if filters is not None:
        for name,f in filters.items():
            env.filters[name] = f
    app['__templating__'] = env

async def logger_factory(app,handler):
    async def logger(request):
        logging.info('Request:%s %s' % (request.method,request.path))
        return (await handler(request))
    return logger

async  def data_factory(app,handler):
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
    async def response(request):
        logging.info('Response handler...')
        r = await handler(request)
        if isinstance(r,web.StreamResponse):
            return r
        if isinstance(r,bytes):
            resp = web.Response(body=r)
            resp.content_type = 'application/octet-stream'
            return resp
        if isinstance(r,dict):
            template = r.get('__template__')
            if template is None:
                resp = web.Response(body=json.dumps(r,ensure_ascii=False,default=lambda o:o.__dict__).encode('utf-8'))
                resp.content_type = 'application/json;charset=utf-8'
                return resp
            else:
                resp = wen.Response(body=app['__templating__'].get_template(template).render(**r).encode('utf-8'))
                resp.content_type = 'text/html;charset=utf-8'
                return resp
        if isinstance(r,int) and r>=100 and r <600 :
            return web.Response(r)
        if isinstance(r,tuple) and len(r) == 2:
            t,m = r
            if isinstance(t,int) and t >= 100 and t <600:
                return web.Response(t,str(m))
        #default:
        resp = web.Response(body=str(r).encode('utf-8'))
        resp.content_type = 'text/plain;charset=utf-8'
        return resp
    return response

def datetime_filter(t):
    delta = int(time.time() - t)
    if delta < 60:
        return u'1分钟前'
    if delta < 3600:
        return u'%s分钟前' % (delta // 60)
    if delta <86400:
        return u'%s小时前' % (delta // 3600)
    if delta <604800:
        return u'%s天前' % (delta // 86400)
    dt = datatime.fromtimestamp(t)
    return u'%s年%s月%s日' % (dt.year,dt.month,dt.day)

async def init(loop):
    await orm.create_pool(loop=loop,host='127.0.0.1',post=3306,user='www',password='www',db='awesome')
    app = web.Application(loop=loop,middlewares=[
        logger_factory,response_factory
    ])
    init_jinja2(app,filters=dict(datetime=datetime_filter))
    add_routes(app,'handlers')
    add_static(app)
    srv = await loop.create_server(app.make_handler(),'127.0.0.1',9000)
    logging.info('server started at http://127.0.0.1:9000...')
    return srv






#
# def index(request):  #requeset包含了浏览器发送过来的http协议的信息，一般不用自己构造
#     return web.Response(body=b'<h1>awesome</h1>')   #构造一个http相应  类声明 class aiohttp.web.Response(*, status=200, headers=None, content_type=None, body=None, text=None)
#
# #用asyncio提供的@asyncio.coroutine  可以把一个generator标记为coroutine类型，然后在内部用yield from调用另一个coroutine实现异步操作
# #异步操作需要在coroutine中通过yield from完成，多个coroutine可以封装成一组Task然后并发执行
# @asyncio.coroutine
# def init(loop):
#     app=web.Application(loop=loop)  #创建一个服务器app实例，作用是用来处理URL、http协议    【类声明见百度
#     app.router.add_route('GET','/',index)  #使用app时，首先要将URLs 注册进router，再用aiohttp.RequestHandlerFactory作为协议簇创建套接字 ，该方法将处理函数与对应的URL绑定，浏览器敲击相应URL时会返回处理函数的内容
#     srv = yield from loop.create_server(app.make_handler(),'127.0.0.1',9000)  #用协程创建监听服务，loop为传入函数的协程。 yield from返回一个创建好的，绑定IP、端口、HTTP协议簇的监听服务的协程。
#     logging.info('server started at http://127.0.0.1:9000')
#     return srv

loop = asyncio.get_event_loop()  #创建协程
loop.run_until_complete(init(loop))  #运行协程，直到完成
loop.run_forever() #运行协程，直到调用stop





























































