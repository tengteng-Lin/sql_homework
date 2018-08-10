drop database if exists awesome;

create database awesome;

use awesome;

grant select, insert, update, delete on awesome.* to 'www-data'@'localhost' identified by 'www-data';

create table users(
    `UserID` VARCHAR (18) NOT NULL ,
    `User` VARCHAR (50) NOT NULL ,
    `Sex` VARCHAR (50),
    `Phone` INT NOT NULL,
    PRIMARY KEY (`UserID`)
)engine=innodb DEFAULT charset=utf8;

CREATE TABLE buses(
    `BusID` VARCHAR (10) NOT NULL ,
    `BusFrom` VARCHAR (50) NOT NULL ,
    `BusTo` VARCHAR (50) not NULL ,
    `BusDate` FLOAT NOT NULL,
    `BusEnd` FLOAT not NULL,
    `TicketNum` int NOT NULL,
    `Price` INT NOT NULL,
    PRIMARY KEY (`BusID`,`BusDate`)
)engine=innodb DEFAULT charset=utf8;

CREATE TABLE orders(
    `OrderID` VARCHAR (10) NOT NULL ,
    `UserID` VARCHAR (18) NOT NULL ,
    `BusID` VARCHAR (10) NOT NULL ,
    `BusDate` FLOAT NOT NULL ,
    `OrderDate` FLOAT NOT NULL ,
    `OrderNum` FLOAT NOT NULL ,
    `Total` FLOAT NOT NULL,
    PRIMARY KEY (`OrderID`)
)engine=innodb DEFAULT charset=utf8