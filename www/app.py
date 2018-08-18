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
        block_start_string = kw.get('block_start_string','{%')
    )

def index(request):  #requeset包含了浏览器发送过来的http协议的信息，一般不用自己构造
    return web.Response(body=b'<h1>awesome</h1>')   #构造一个http相应  类声明 class aiohttp.web.Response(*, status=200, headers=None, content_type=None, body=None, text=None)

#用asyncio提供的@asyncio.coroutine  可以把一个generator标记为coroutine类型，然后在内部用yield from调用另一个coroutine实现异步操作
#异步操作需要在coroutine中通过yield from完成，多个coroutine可以封装成一组Task然后并发执行
@asyncio.coroutine
def init(loop):
    app=web.Application(loop=loop)  #创建一个服务器app实例，作用是用来处理URL、http协议    【类声明见百度
    app.router.add_route('GET','/',index)  #使用app时，首先要将URLs 注册进router，再用aiohttp.RequestHandlerFactory作为协议簇创建套接字 ，该方法将处理函数与对应的URL绑定，浏览器敲击相应URL时会返回处理函数的内容
    srv = yield from loop.create_server(app.make_handler(),'127.0.0.1',9000)  #用协程创建监听服务，loop为传入函数的协程。 yield from返回一个创建好的，绑定IP、端口、HTTP协议簇的监听服务的协程。
    logging.info('server started at http://127.0.0.1:9000')
    return srv

loop = asyncio.get_event_loop()  #创建协程
loop.run_until_complete(init(loop))  #运行协程，直到完成
loop.run_forever() #运行协程，直到调用stop





























































