import asyncio,logging
import aiomysql

def log(sql,args=()):
    logging.info('SQL: %s' % sql)

async def create_pool(loop,**kw):
    '''
    创建一个全局的连接池，每个HTTP请求都从连接池中直接获取数据库连接。从而不必频繁地打开和关闭数据库连接。
    :param loop: 
    :param kw: 
    :return: 
    '''
    logging.info('create database connection pool...')
    global __pool  #连接池由全局变量__pool 存储
    __pool = await aiomysql.create_pool(
        host = kw.get('host','localhost'),
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
    log(sql,args)
    global __pool
    async with __pool.get() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(sql.replace('?',"%s"),args or ())
            if size:
                rs = await cur.fetchmany(size)
            else:
                rs = await cur.fetchall()
        logging.info('rows returned:%s'% len(rs))
        return rs

async def execute(sql,args,autocommit=True):
    log(sql)
    async with __pool.get() as conn:
        if not autocommit:
            await conn.begin()
        try:
            async with conn.cursor(aiomysql.DictCursor) as cur:
