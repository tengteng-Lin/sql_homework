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

    global __pool
    #初始化连接池参数
    __pool = await aiomysql.create_pool(
        host=kw.get('host','localhost'),  #get（）方法是dict的，如果有则返回，没有则返回第二个参数即默认值
        port=kw.get('port',3306),
        user=kw['user'],
        password=kw['password'],
        db=kw['db'],
        charset=kw.get('charset','utf8'),
        autocommit=kw.get('autocommit',True),
        maxsize=kw.get('maxsize',10),
        minsize=kw.get('minsize',1),
        loop=loop
    )

    return


async def select(sql,args,size=None):
    '''
    数据库查询函数
    :param sql: sql语句
    :param args: sql语句中的参数
    :param size: 要查询的数量
    :return: 查询结果
    '''
    log(sql,args)
    print('进入了select')
    global __pool
    # async调用一个子协程，并直接返回调用的结果。这里是从连接池中返回一个连接，这个地方已经创建了进程池并和进程池连接了，进程池的创建被封装到了create__pool函数里
    # async with是一个异步上下文管理器（是因为一异步都异步吗？
    async with __pool.get() as conn:  #with可以用来处理异常，__enter()__和__exit()__方法   with……as……，因为conn和cursor都需要close最后
        async with conn.cursor(aiomysql.DictCursor) as cur:  #创建一个结果为字典的游标
            #在协程函数中，可以通过await语法来挂起自身的协程，并等待另一个协程完成直到返回结果
            await cur.execute(sql.replace('?',"%s"),args or ())  #执行sql语句，将sql语句中的？替换成%s
            print(sql.replace('?',"%s"),args or ())
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
    #print('进入了execute')

    async with __pool.get() as conn:
        if not autocommit:
            await conn.begin() #python中连接对象开始一个事务的方法
        try:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                print(sql.replace('?', '%s'))
                await cur.execute(sql.replace('?', '%s'), args)
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
    return ','.join(L)

class Field(object):
    def __init__(self,name,column_type,primary_key,default):
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default

    def __str__(self):
        return '<%s,%s:%s>' % (self.__class__.__name__,self.column_type,self.name)

class StringField(Field):
    def  __init__(self,name=None,primary_key=False,default=None,ddl='varchar(100)'):
        super().__init__(name,ddl,primary_key,default)

class BooleanField(Field):
    def  __init__(self,name=None,default=False):
        super().__init__(name,'boolean',False,default)

class IntegerField(Field):
    def __init__(self,name=None,primary_key=False,default=0):
        super().__init__(name,'bigint',primary_key,default)

class FloatField(Field):
    def __init__(self,name=None,primary_key=False,default=0.0):
        super().__init__(name,'real',primary_key,default)

class TextField(Field):
    def __init__(self,name=None,default=None):
        super().__init__(name,'text',False,default)

class ModelMetaclass(type):
    def __new__(cls, name,bases,attrs):
        '''
        创建模型与表映射的基类
        :param name: 类名
        :param bases: 父类
        :param attrs: 类的属性列表
        :return: 模型元类
        '''
        #排除Model类本身
        if name=='Model':
            return type.__new__(cls,name,bases,attrs)
        #获取表名，如果没有表名则将类名作为表名
        tableName = attrs.get('__table__',None) or name
        logging.info('found model: %s (table: %s)' % (name,tableName))
        #获取所有的类属性和主键名
        mappings = dict()  #存储属性名和字段信息的映射关系
        fields = []       #存储所有非主键的属性
        primaryKey = None   #存储主键属性
        for k,v in attrs.items():  #遍历类的所有属性，k为属性名，v为该属性对应的字段信息
            if isinstance(v,Field):  #如果v是自己定义的字段类型
                logging.info('found mappings:%s ==> %s' % (k,v))
                mappings[k] = v  #存储映射关系
                if v.primary_key: #如果该属性是主键（看上面Field，有个primary_key的“属性”
                    #找到主键
                    if primaryKey:
                        raise StandardError('Dupliacte primary key for field: %s' % k)  #主键重复
                    primaryKey = k
                else:  #不是主键，存储到fields中
                    fields.append(k)
        if not primaryKey:   #遍历了所有属性都没有找到主键，则主键没有定义
            raise StandardError('Primary key not found')
        for k in mappings.keys():
            attrs.pop(k)     #清空attrs
        #将fields中属性名以“属性名”的方式 装饰起来
        escaped_fields = list(map(lambda f: '`%s`' % f,fields ))
        #重新设置attrs【确实是重新设置了，散的集中起来只剩四项了
        attrs['__mappings__'] = mappings #保存属性和列的映射关系
        attrs['__table__'] = tableName
        attrs['__primary_key__'] = primaryKey #主键属性名
        attrs['__fields__'] = fields #除主键外的属性名

        #构造默认的select等语句
        attrs['__select__'] = 'select `%s`,%s from `%s`' % (primaryKey,','.join(escaped_fields),tableName)
        attrs['__insert__'] = 'insert into `%s` (%s, `%s`) values (%s)' % (tableName, ', '.join(escaped_fields), primaryKey, create_args_string(len(escaped_fields) + 1))
        attrs['__update__'] = 'update `%s` set %s where `%s`=?' %  (tableName,','.join(map(lambda f:'`%s`=?' % (mappings.get(f).name or f),fields)),primaryKey)
        attrs['__delete__'] = 'delete from `%s` where `%s` = ?' % (tableName,primaryKey)
        return type.__new__(cls,name,bases,attrs)

class Model(dict,metaclass=ModelMetaclass):
    def __init__(self,**kw):
        super(Model,self).__init__(**kw)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Model' object has no attribute '%s' " % key)

    def __setattr__(self, key, value):
        self[key] = value

    def getValue(self,key):
        return getattr(self,key,None)

    def getValueOrDefault(self,key):
        value = getattr(self,key,None)
        if value is None: #如果没有找到value，也就是说不是外面的“大的”属性
            #在mappings里找到这个属性
            field = self.__mappings__[key]  #Model的父类是ModelMetaclass，所以“属性”里自然有mappings
            if field.default is not None:
                value = field.default() if callable(field.default) else field.default  #callable用于检查一个对象是否是可调用的
                logging.debug('using default value for %s:%s' % (key,str(value)))
                setattr(self,key,value)
        return value

    @classmethod #可以通过类来进行调用
    async def findAll(cls,where=None,args=None,**kw):  #普通方法第一个参数为self，表示一个具体的实例本身；用@classmethod标识的方法第一个参数是cls，表示这个类本身
        '''
        通过where查找多条记录对象
        :param where: where查询条件
        :param args: sql参数   
        :param kw: 查询条件列表
        :return: 多条记录集合
        '''
        'find objects by where clause'
        sql = [cls.__select__]  #__select__在ModelMetaclass的属性列表里面
        #print('to  enter  findAll')
        if where:
            sql.append('where')
            sql.append(where)
        if args is None:
            args = []
        orderBy = kw.get('orderBy',None)
        if orderBy:
            sql.append('order by')
            sql.append(orderBy)
        limit = kw.get('limit',None)
        if limit is not None:
            sql.append('limit')  #limit是返回的数目
            if isinstance(limit,int):
                sql.append('?')
                args.append(limit)  #没错，在sql语句上加limit ？就可以了，在args（参数）上加上具体的数目
            elif isinstance(limit,tuple) and len(limit) == 2:
                sql.append('?,?')
                args.extend(limit)
            else:
                raise ValueError('Invalid limit value: %s' % str(limit))
        rs=await select(' '.join(sql),args)   #返回形式是一个元素是tuple的list
        return [cls(**r) for r in rs]  #  **r是关键字参数，构成了一个cls类的列表，其实就是每一条记录对应的实例

    @classmethod
    async def findNumber(cls,selectField,where=None,args=None):
        '''
        查询某个字段的数量
        :param cls: 
        :param selectField: 要查询的字段
        :param where: 查询条件
        :param args: 参数列表
        :return:数量 
        '''
        'find number by select and where'
        sql = ['select count(%s) _num_ from `%s`' % (selectField,cls.__table__) ]
        if where:
            sql.append('where')
            sql.append(where)
        rs = await select(' '.join(sql),args,1)
        if len(rs) == 0:
            return None
        return rs[0]['_num_']

    @classmethod
    async def find(cls,pk):
        '''
        通过主键查询
        :param cls: 
        :param pk: 主键
        :return: 一条记录
        '''
        'find object by primary key'
        rs = await select('%s where `%s` = ?' % (cls.__select__,cls.__primary_key__),[pk],1)
        if len(rs)==0:
            return None
        return cls(**rs[0])

    async def save(self):   #会自动‘计算’缺省值
        #print(self)
        args = list(map(self.getValueOrDefault,self.__fields__))

        args.append(self.getValueOrDefault(self.__primary_key__))

        rows = await execute(self.__insert__, args)
        if rows != 1:
            logging.warn('failed to insert record:affected rows: %s' % rows)

    async def update(self):
        '''
        将__fields__保存的除主键外的所有属性一次传递到getValueOrDefault函数中获取值
        :param self: 
        :return: 
        '''
        args = list(map(self.getValue,self.__fields__))
        args.append(self.getValue(self.__primary_key__))  #获取主键值
        rows = await execute(self.__update__,args)  #执行insert语句
        if rows != 1:
            logging.warn('failed to update by primary key: affected rows: %s' % rows)

    async def remove(self):
        args = [self.getValue(self.__primary_key__)]
        rows = await execute(self.__delete__,args)
        if rows!=1:
            logging.warn('failed to remove by primary key: affected rows:%s' % rows)
