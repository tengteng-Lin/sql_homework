drop database if exists awesome;

create database awesome;

use awesome;

grant select ,insert ,update,delete on awesome * to 'www-data'@'localhost' identified by 'www-data';

create table users(
    'UserID' VARCHAR (18) NOT NULL ,
    'User' VARCHAR (50) NOT NULL ,
    'Sex' VARCHAR (50),
    'Phone'INT NOT NULL
)engine=innodb DEFAULT charset=utf8

CREATE TABLE buese(
    'BusID'VARCHAR (10) NOT NULL ,
    'BusFrom'VARCHAR (50) NOT NULL ,
    'BusTo' VARCHAR (50) not NULL ,
    'BusDate'FLOAT NOT NULL
    'BusEnd'FLOAT not NULL
    'TicketNum'int NOT NULL
    'Price' INT NOT NULL
)engine=innodb DEFAULT charset=utf8

CREATE TABLE