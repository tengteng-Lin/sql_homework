from www.orm import create_pool
from www.models import User
import asyncio,sys


from aiohttp import web
import asyncio
# from coroweb import add_routes,add_static
# from app import init_jinja2,datetime_filter,logger_factory,response_factory
import logging; logging.basicConfig(level=logging.INFO)


#数据库测试
async def test(loop):
    await create_pool(loop,user='www-data', password='www-data', db='awesome')

    u=User(User='哈哈哈哈哈',Sex='male',Phone='00000000001')

    await u.save()




loop = asyncio.get_event_loop()
loop.run_until_complete( test(loop) )
loop.close()


# pool = aiomysql.create_pool(
#     host= 'localhost',  # get（）方法是dict的，如果有则返回，没有则返回第二个参数即默认值
#     port= 3306,
#     user='root',
#     password='password',
#     db='awesome',
#     # charset='utf8'),
#     # autocommit=kw.get('autocommit', True),
#     # maxsize=kw.get('maxsize', 10),
#     # minsize=kw.get('minsize', 1),
#     # loop=loop
# )
#
#
# #
# print(pool)