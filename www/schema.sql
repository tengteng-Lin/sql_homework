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
    `admin` bool NOT NULL ,
    PRIMARY KEY (`UserID`),
    UNIQUE KEY `Phone` (`Phone`)
)engine=innodb DEFAULT charset=utf8;

CREATE TABLE buses(
    `BusID` VARCHAR (10) NOT NULL ,
    `BusFrom` VARCHAR (50) NOT NULL ,
    `BusTo` VARCHAR (50) not NULL ,
    `BusDate` VARCHAR (50) NOT NULL,
    `BusEnd` VARCHAR (50) not NULL,
    PRIMARY KEY (`BusID`,`BusDate`)
)engine=innodb DEFAULT charset=utf8;

CREATE TABLE orders(
    `OrderID` VARCHAR (50) NOT NULL ,
    `UserID` VARCHAR (50) NOT NULL ,
    `BusID` VARCHAR (10) NOT NULL ,
    `BusFrom`VARCHAR (50)NOT NULL ,
    `BusTo`VARCHAR (50)NOT NULL ,
    `BusDate` VARCHAR (50) NOT NULL ,
    `Type` VARCHAR (10) NOT NULL ,
    `Coach`INT NOT NULL ,
    `Num`INT NOT NULL,
    PRIMARY KEY (`OrderID`)
)engine=innodb DEFAULT charset=utf8;

CREATE TABLE seats(
  `SeatID` VARCHAR (50) NOT NULL ,
  `BusID` VARCHAR (10) NOT NULL ,
  `Type` VARCHAR (10) NOT NULL ,
  `TicketNum`INT NOT NULL ,
  `Price`FLOAT NOT NULL ,
  `Coach`INT ,
  `Num`INT ,
  PRIMARY KEY (`SeatID`)
)engine=innodb DEFAULT charset=utf8