drop database if exists awesome;

create database awesome;

use awesome;

grant select ,insert ,update,delete on awesome * to 'www-data'@'localhost' identified by 'www-data';

create table users(
    'UserID'
)