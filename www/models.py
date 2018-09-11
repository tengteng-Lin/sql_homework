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
    admin = BooleanField()

class Bus(Model):
    __table__ = 'buses'

    BusID = StringField(primary_key=True,default=next_id,ddl='char(50)')
    BusFrom = StringField(ddl='varchar(50)')
    BusTo = StringField(ddl='varchar(50)')
    BusDate = StringField(ddl='varchar(50)')  #发车日期
    BusEnd = StringField(ddl='varchar(50)')



class Order(Model):
    __table__='orders'

    OrderID = StringField(primary_key=True,default=next_id,ddl='char(50)')
    UserID = StringField(ddl='varchar(50)')
    BusID = StringField(ddl='char(50)')
    BusFrom = StringField(ddl='varchar(50)')
    BusTo = StringField(ddl='varchar(50)')
    BusDate = StringField(ddl='varchar(50)')
    Type = StringField(ddl='varchar(10)')  #几等座
    Coach = IntegerField(default=1)  # 车厢号
    Num = IntegerField(default=1)  # 车厢第几号

class Seat(Model):
    __table__='seats'

    SeatID = StringField(primary_key=True,default=next_id,ddl='char(50)')
    BusID = StringField(ddl='varchar(10)')
    Type = StringField(ddl='varchar(10)')
    TicketNum = IntegerField(default=0)
    Price = FloatField(default=1)
    Coach = IntegerField(default=1)  # 车厢号
    Num = IntegerField(default=1)  # 车厢第几号

