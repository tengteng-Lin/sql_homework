import re,time,json,logging,hashlib,base64,asyncio

from www.coroweb import get,post

from www.models import User,Bus,Order,next_id

@get('/')
async def index(request):
    users = await User.findAll()
    print(users)
    return {
        '__template__': 'test.html',
        'users': users
    }




