drop database if exists awesome;

create database awesome;

use awesome;

grant select, insert, update, delete on awesome.* to 'www-data'@'localhost' identified by 'www-data';

create table users(
    `UserID` VARCHAR (50) NOT NULL ,
    `User` VARCHAR (50) NOT NULL ,
    `Pass` VARCHAR (50) NOT NULL ,
    `Sex` VARCHAR (50),
    `Phone` CHAR (11),
    PRIMARY KEY (`UserID`),
    UNIQUE KEY `Phone` (`Phone`)
)engine=innodb DEFAULT charset=utf8;

CREATE TABLE buses(
    `BusID` VARCHAR (50) NOT NULL ,
    `BusFrom` VARCHAR (50) NOT NULL ,
    `BusTo` VARCHAR (50) not NULL ,
    `BusDate` VARCHAR (50) NOT NULL,
    `BusEnd` VARCHAR (50) not NULL,
    `TicketNum` int NOT NULL,
    `Price` FLOAT NOT NULL,
    PRIMARY KEY (`BusID`,`BusDate`)
)engine=innodb DEFAULT charset=utf8;

CREATE TABLE orders(
    `OrderID` VARCHAR (50) NOT NULL ,
    `UserID` VARCHAR (18) NOT NULL ,
    `BusID` VARCHAR (10) NOT NULL ,
    `BusDate` VARCHAR (50) NOT NULL ,
    `OrderDate` FLOAT NOT NULL ,
    `OrderNum` INT NOT NULL ,
    `Total` FLOAT NOT NULL,
    PRIMARY KEY (`OrderID`)
)engine=innodb DEFAULT charset=utf8