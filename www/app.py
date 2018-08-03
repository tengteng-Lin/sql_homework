import logging;logging.basicConfig(level=logging.INFO)
import asyncio,os,json,time
from datetime import datetime

from aiohttp import web

def index(request):  #requeset包含了浏览器发送过来的http协议的信息，一般不用自己构造
    return web.Response(body=b'<h1>awesome</h1>')   #构造一个http相应  类声明 class aiohttp.web.Response(*, status=200, headers=None, content_type=None, body=None, text=None)

#这是一个  协程
@asyncio.coroutine
def init(loop):
    app=web.Application(loop=loop)  #创建一个服务器app实例，作用是用来处理URL、http协议    【类声明见百度
    app.router.add_route('GET','/',index)  #使用app时，首先要将URLs 注册进router，再用aiohttp.RequestHandlerFactory作为协议簇创建套接字 ，该方法将处理函数与对应的URL绑定，浏览器敲击相应URL时会返回处理函数的内容
    srv = yield from loop.create_server(app.make_handler(),'127.0.0.1',9000)
    logging.info('server started at http://127.0.0.1:9000')
    return srv

loop = asyncio.get_event_loop()  #创建一个事件循环
loop.run_until_complete(init(loop))  #将协程加入到时间循环中去
loop.run_forever()





























































