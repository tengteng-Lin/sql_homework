import re, time, json, logging, hashlib, base64, asyncio
from www.coroweb import get, post
from aiohttp import web
from www.models import User, Bus, Order, next_id,Admin
import www.markdown2  # 支持markdown文本输入的模块
from www.apis import APIPermissionError, APISourceNotFoundError, APIValueError, APIError
from www.config import configs


COOKIE_NAME = 'awesession'  # cookie名，用于设置cookie
_COOKIE_KEY = configs.session.secret  # cookie密钥，作为加密cookie原始字符串的一部分

def check_admin(request):
    if request.__user__ is None or not request.__user__.admin:
        raise APIPermissionError()

'----------------------------------------------------------------首页-------------------------------------------------------------'
@get('/')
def index(request):
    #print('来到首页'+request.__user__.UserID)  没问题
    if request.__user__:
        if request.__user__.admin:
            return {
                '__template__': 'admin.html',
                '__user__': request.__user__
            }
        else:
            return {
                '__template__': 'tobuy.html',
                '__user__': request.__user__
            }
    else:
        return {
            '__template__': 'tobuy.html',
            '__user__': request.__user__
        }

'----------------------------------------------------------------验证身份工具-------------------------------------------------------------'
def user2cookie(user, max_age):
    expires = str(int(time.time() + max_age))
    s = '%s-%s-%s-%s' % (user.Phone, user.Pass, expires, _COOKIE_KEY)
    L = [user.Phone, expires, hashlib.sha1(s.encode('utf-8')).hexdigest()]
    return '-'.join(L)

@asyncio.coroutine
def cookie2user(cookie_str):
    if not cookie_str:
        return None
    try:
        L = cookie_str.split('-')
        if len(L) != 3:
            return None
        uid, expires, sha1 = L
        print(uid)
        if int(expires) < time.time():
            return None
        user = yield from User.findAll('Phone=?', [uid])
        if user is None:
            print('无')
            return None
        s = '%s-%s-%s-%s' % (uid, user[0].Pass, expires, _COOKIE_KEY)
        if sha1 != hashlib.sha1(s.encode('utf-8')).hexdigest():
            logging.info('invalid sha1')
            return None
        user[0].Pass = '******'
        return user
    except Exception as e:
        logging.exception(e)
        return None

'----------------------------------------------------------------登录注册退出-------------------------------------------------------------'
@get('/register')
def register():
    return {
        '__template__': "register.html"
    }

@get('/signin')
def signin():
    return {
        '__template__': 'signin2.html'
    }

@post('/api/authenticate')
@asyncio.coroutine  # 同理，教程中没有这一句
def authenticate(*, Phone, Pass):
    print('进来验证了。。。')
    if not Phone:
        raise APIValueError('Phone', 'Invalid PhoneNumber')
    if not Pass:
        raise APIValueError('Pass', 'Invalid password')
    users = yield from User.findAll('Phone=?', [Phone])
    if len(users) == 0:
        raise APIValueError('Phone', 'Phone not exists')
    user = users[0]
    # 检查密码
    sha1 = hashlib.sha1()
    sha1.update(user.Phone.encode('utf-8'))
    sha1.update(b':')
    sha1.update(Pass.encode('utf-8'))
    if user.Pass != sha1.hexdigest():
        raise APIValueError('password', 'invalid password')
    # 验证通过，设置cookie
    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
    user.Pass = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r

@get('/signout')
def signout(request):
    referer = request.headers.get('Referer')
    r = web.HTTPFound(referer or '/')
    r.set_cookie(COOKIE_NAME, '-deleted-', max_age=0, httponly=True)
    logging.info('user signed out')
    return r

_RE_SHA1 = re.compile(r'^[0-9a-f]{40}$')

@post('/api/users')
@asyncio.coroutine  # 惹，这里和教程中有出入。是版本的问题还是？？ 如果没有这句，会出现“协程对象不可出现在非协程函数中”这样的错误。
def api_register_user(*, UserID, Phone, name, Pass):
    print(UserID)
    if not UserID:
        raise APIValueError('身份证号')
    if not name:
        raise APIValueError('姓名')
    if not Pass or not _RE_SHA1.match(Pass):
        raise APIValueError('密码')
    if not Phone:
        raise APIValueError('手机号')
    users = yield from User.findAll('Phone=?', [Phone])
    if len(users) > 0:
        raise APIError('register:failed', 'phone', 'Phone is already in use.')

    sha1_Pass = '%s:%s' % (Phone, Pass)
    user = User(UserID=UserID, User=name, Pass=hashlib.sha1(sha1_Pass.encode('utf-8')).hexdigest(), Phone=Phone)
    yield from user.save()

    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
    user.Pass = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=True).encode('utf-8')
    return r

'----------------------------------------------------------------查询列车-------------------------------------------------------------'
@post('/api/query_buses')
@asyncio.coroutine
def api_query_buses(*, BusFrom, BusTo, BusDate):
    print('查询列车')
    if not BusDate:
        raise APIValueError('发车时间')
    if not BusFrom:
        raise APIValueError('始发地')
    buses1 = yield from Bus.findAll('BusFrom=?', [BusFrom])
    buses2 = yield from Bus.findAll('BusTo=?', [BusTo])
    buses = [i for i in buses1 if i in buses2]
    #    retB = list(set(buses1).intersection(set(buses2)))
    r = web.Response()
    r.content_type = 'application/json'
    r.body = json.dumps(buses, ensure_ascii=True).encode('utf-8')
    return r


@post('/api/add_order')
@asyncio.coroutine
def add_order(*, UserID, BusID, BusFrom, BusTo, BusDate, OrderDate, OrderNum=1, Total=1):

    logging.info('添加订单。。。')
    buses1 = yield from Bus.findAll('BusID=?', [BusID])
    buses2 = yield from Bus.findAll('BusDate=?', [BusDate])
    buses = [i for i in buses1 if i in buses2]
    if buses[0].TicketNum!=0:
        if buses[0].Num<50:
            order = Order(UserID=UserID, BusID=BusID, BusDate=BusDate, BusFrom=BusFrom, BusTo=BusTo,Coach=buses[0].Coach,Num=buses[0].Num)
            buses[0].Num+=1
            buses[0].TicketNum-=1
            yield from buses[0].update()
            yield from order.save()

            L=[]
            L.append(buses)
            L.append(order)

            r = web.Response()
            r.content_type = 'application/json'
            r.body = json.dumps(L, ensure_ascii=True).encode('utf-8')
            return r


@get('/api/my_order')
@asyncio.coroutine
def my_order(request):
    orders = yield from Order.findAll('UserID=?', request.__user__.UserID)
    return {
        '__template__': 'refund.html',
        'orders': orders
    }

@post('/api/refund')
@asyncio.coroutine
def refund(*,UserID,OrderID):
    order = yield from Order.find(OrderID)
    yield from order.remove()

    orders = yield from Order.findAll('UserID=?', UserID)
    r = web.Response()
    r.content_type = 'application/json'
    r.body = json.dumps(orders, ensure_ascii=True).encode('utf-8')
    return r

@post('/manage/add_tickets')
@asyncio.coroutine
def add_tickets(*,BusID,BusFrom,BusTo,BusDate,BusEnd,TicketNum,Price):


    b = Bus(BusID=BusID,BusFrom=BusFrom,BusTo=BusTo,BusDate=BusDate,BusEnd=BusEnd,TicketNum=TicketNum,Price=Price,Coach=1,Num=1)
    yield from b.save()

    r = web.Response()
    r.content_type = 'application/json'
    r.body = json.dumps(b, ensure_ascii=True).encode('utf-8')
    return r

@get('/api/admin_add_tickets')
def api_admin_add_tickets():
    return {
        '__template__':'admin.html'
    }

@get('/api/admin_delete_tickets')
@asyncio.coroutine
def api_admin_delete_tickets():
    buses =yield from Bus.findAll()

    return {
        '__template__':'delete_tickets.html',
        'buses': buses
    }

@post('/manage/delete_tickets')
@asyncio.coroutine
def delete_tickets(*,BusID,BusDate):
    logging.info('删除车票')
    bus1 =yield from Bus.findAll('BusID=?',[BusID])
    bus2 =yield from Bus.findAll('BusDate=?',[BusDate])
    bus = [i for i in bus1 if i in bus2]
    print(bus)

    for b in bus:
        yield from b.remove()

    #buses = yield from Bus.findAll()
    r = web.Response()
    # r.content_type = 'application/json'
    # r.body = json.dumps(buses, ensure_ascii=True).encode('utf-8')
    return r

@get('/api/admin_users')
@asyncio.coroutine
def admin_users():
    users = yield from User.findAll()
    return {
        '__template__':'users.html',
        'users':users
    }

@post('/manage/users')
@asyncio.coroutine
def manage_users(*,UserID):
    user = yield from User.find(UserID)
    yield from user.remove()

    r = web.Response()
    return r
