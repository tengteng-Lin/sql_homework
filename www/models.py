import time,uuid

from orm import Model,StringField,BooleanField,FloatField,TextField,IntegerField

def next_id():
    #print('%015d%s000' % (int(time.time() * 1000),uuid.uuid4().hex))
    return '%015d%s000' % (int(time.time() * 1000),uuid.uuid4().hex)

class User(Model):
    __table__ = 'users'

    UserID = StringField(primary_key=True,default=next_id,ddl='char(50)')
    User = StringField(ddl='varchar(50)')
    Pass = StringField(ddl='varchar(50)')
    Sex = StringField(ddl='varchar(50)')
    Phone = StringField(ddl='char(11)')
    Admin = BooleanField(default = False)

class Bus(Model):
    __table__ = 'buses'

    BusID = StringField(primary_key=True,default=next_id,ddl='char(50)')
    BusFrom = StringField(ddl='varchar(50)')
    BusTo = StringField(ddl='varchar(50)')
    BusDate = StringField(ddl='varchar(50)')  #发车日期
    BusEnd = StringField(ddl='varchar(50)')
    TicketNum = IntegerField() #剩余票数
    Price = FloatField()  #票价

class Order(Model):
    __table__='orders'

    OrderID = StringField(primary_key=True,default=next_id,ddl='char(50)')
    UserID = StringField(ddl='char(50)')
    BusID = StringField(ddl='char(50)')
    BusFrom = StringField(ddl='varchar(50)')
    BusTo = StringField(ddl='varchar(50)')
    BusDate = StringField(ddl='varchar(50)')
    OrderDate = FloatField(default=time.time)  #订购日期
    OrderNum = IntegerField(default=1)  #订购票数
    Total = FloatField(default=1)  #总价
