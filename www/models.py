import time,uuid

from orm import Model,StringField,BooleanField,FloatField,TextField,IntegerField

def next_id():
    return '%015d%s000' % (int(time.time() * 1000),uuid.uuid4().hex)

class User(Model):
    __table__ = 'users'

    id = IntegerField(primary_key=True,default=next_id,ddl='varchar(50)')
    name = StringField(ddl='varchar(50)')
    sex = StringField(ddl='varchar(50)')
    phone = IntegerField(ddl='varchar(100)')