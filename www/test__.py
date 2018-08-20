import orm
from models import User,Bus,Order
import asyncio

from aiohttp import web
import asyncio
from coroweb import add_routes,add_static
from app import init_jinja2,datetime_filter,logger_factory,response_factory
import logging; logging.basicConfig(level=logging.INFO)

#编写web框架测试
async def init(loop):
    app = web.Application(loop=loop,middlewares=[logger_factory,response_factory])
    init_jinja2(app,filters=dict(datetime=datetime_filter),path = r"D:\sql_homework\www\templates")
    add_routes(app,'webframe_test_handler')
    add_static(app)
    srv = await loop.create_server(app.make_handler(),'127.0.0.1',9000)
    logging.info('Server started at http://1227.0.0.1:9000...')
    return srv

#数据库测试
# async def test(loop):
#     await orm.create_pool(loop,user='www-data',password='www-data',db='awesome')
#
#     u=User(User='测试',Sex='female',Phone='12345678901')
#
#
#     await u.save()
#
# async def find(loop):
#     await orm.create_pool(loop,user='www-data',password='www-data',db='awesome')
#     rs = await User.findAll()
#     print('查找测试： %s' % rs)

loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()
