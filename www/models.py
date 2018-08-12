import time,uuid

from orm import Model,StringField,BooleanField,FloatField,TextField,IntegerField

def next_id():
    #print('%015d%s000' % (int(time.time() * 1000),uuid.uuid4().hex))
    return '%015d%s000' % (int(time.time() * 1000),uuid.uuid4().hex)

class User(Model):
    __table__ = 'users'

    UserID = StringField(primary_key=True,default=next_id,ddl='char(50)')
    User = StringField(ddl='varchar(50)')
    Sex = StringField(ddl='varchar(50)')
    Phone = StringField(ddl='char(11)')

class Bus(Model):
    __table__ = 'buses'

    BusID = StringField(primary_key=True,default=next_id,ddl='char(10)')
    BusFrom = StringField(ddl='varchar(50)')
    BusTo = StringField(ddl='varchar(50)')
    BusDate = FloatField(default=time.time)  #发车日期
    BusEnd = FloatField(default=time.time)
    TicketNum = IntegerField() #剩余票数
    Price = IntegerField()  #票价

class Order(Model):
    __table__='orders'

    OrderID = StringField(primary_key=True,default=next_id,ddl='char(10)')
    UserID = StringField(ddl='char(18)')
    BusID = StringField(ddl='char(10)')
    BusDate = FloatField(default=time.time)
    OrderDate = FloatField(default=time.time)  #订购日期
    OrderNum = IntegerField()  #订购票数
    Total = IntegerField()  #总价
