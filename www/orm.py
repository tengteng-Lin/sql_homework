import asyncio,logging
import aiomysql

def log(sql,args=()):
    logging.info('SQL: %s' % sql)

async def create_pool(loop,**kw):  #kw是一个dict
    '''
    创建一个全局的连接池，每个HTTP请求都从连接池中直接获取数据库连接。从而不必频繁地打开和关闭数据库连接。
    async和await简化标识IO
    :param loop: 事件循环处理程序
    :param kw: 数据库配置参数集合
    :return: 无
    '''
    logging.info('create database connection pool...')
    global __pool  #连接池由全局变量__pool 存储
    #初始化连接池参数
    __pool = await aiomysql.create_pool(
        host = kw.get('host','localhost'),  #get（）方法是dict的，如果有则返回，没有则返回第二个参数即默认值
        port = kw.get('port',3306),
        user = kw['user'],
        password = kw['password'],
        db = kw['db'],
        charset = kw.get('charset','utf8'),
        autocommit = kw.get('autocommit',True),
        maxsize = kw.get('maxsize',10),
        minsize = kw.get('minsize',1),
        loop = loop

    )

async def select(sql,args,size=None):
    '''
    数据库查询函数
    :param sql: sql语句
    :param args: sql语句中的参数
    :param size: 要查询的数量
    :return: 查询结果
    '''
    log(sql,args)
    global __pool
    # async调用一个子协程，并直接返回调用的结果。这里是从连接池中返回一个连接，这个地方已经创建了进程池并和进程池连接了，进程池的创建被封装到了create__pool函数里
    # async with是一个异步上下文管理器（是因为一异步都异步吗？
    async with __pool.get() as conn:  #with可以用来处理异常，__enter()__和__exit()__方法   with……as……，因为conn和cursor都需要close最后
        async with conn.cursor(aiomysql.DictCursor) as cur:  #创建一个结果为字典的游标
            #在协程函数中，可以通过await语法来挂起自身的协程，并等待另一个协程完成直到返回结果
            await cur.execute(sql.replace('?',"%s"),args or ())  #执行sql语句，将sql语句中的？替换成%s
            if size:
                rs = await cur.fetchmany(size)
            else:
                rs = await cur.fetchall()
        logging.info('rows returned:%s'% len(rs))
        return rs

async def execute(sql,args,autocommit=True):
    '''
    insert、update、delete操作的公共执行函数
    :param sql: sql语句
    :param args: sql参数
    :param autocommit: 自动提交事务
    :return: 
    '''
    log(sql)
    async with __pool.get() as conn:
        if not autocommit:
            await conn.begin() #python中连接对象开始一个事务的方法
        try:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(sql.replace('?','%s'),args)
                affected = cur.rowcount #获取操作记录数
            if not autocommit:
                await conn.commit()
        except BaseException as e:
            if not autocommit:
                await conn.rollback()
            raise #显示地显示异常，触发异常后后面的“特定的”代码不能执行
        return affected #返回结果数

#似乎是给那个prepareStatement用的
def create_args_string(num):
    '''
    用来计算需要拼接多少个占位符
    :param num: 
    :return: 
    '''
    L = []
    for n in range(num):
        L.append('?')
    return '?'.join(L)

