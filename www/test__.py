import orm
from models import User,Bus,Order

async def test(loop):
    await orm.create_pool(loop,user='www-data',password='www-data',database='awesome')

    u=User(User='测试',Sex='female',Phone='12345678901')

    await u.save()

async def find(loop):
    await orm.create_pool(loop,user='www-data',password='www-data',db='awesome')
    rs = await User.findAll()
    print('查找测试： %s' % rs)

loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.wait([test(loop),find(loop)]))
loop.run_forever()
