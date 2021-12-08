#!/usr/bin/python

import sqlite3

conn = sqlite3.connect('ei.db')

c = conn.cursor()
c.execute('drop table if exists user;')
c.execute('drop table if exists ei_db;')
c.execute('drop table if exists ei_host;')
c.execute(''' 
create table user(
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	username varchar(32), 
	password varchar(200), 
	create_time DEFAULT (datetime('now', 'localtime')),
	status int default 0
	);
''')
c.execute(''' 
create table ei_db(
	db_instance_id INTEGER PRIMARY KEY AUTOINCREMENT,
	db_author varchar(32),
	db_instance_name varchar(200),
	db_type varchar(15),
	db_version varchar(20),
	db_host varchar(32),
	db_port int,
	db_user varchar(32),
	db_password varchar(200),
	status int
);
''')

c.execute(''' 
create table ei_host(
	host_instance_id INTEGER PRIMARY KEY AUTOINCREMENT,
	host_author varchar(32),
	host_instance_name varchar(200),
	host_type varchar(20),
	host_version varchar(20),
	host_ssh_ip varchar(32),
	host_ssh_port int,
	host_ssh_username varchar(32),
	host_ssh_password varchar(200),
	status int
);

''')
c.execute('insert into user(username,password) values("ddcw","123456")')
c.execute('insert into user(username,password) values("root","123456")')
c.execute('insert into user(username,password) values("admin","123456")')
c.execute('insert into ei_db(db_author,db_instance_name,db_type,db_version,db_host,db_port,db_user,db_password,status) values("ddcw","first_test_db","mysql","5.7","127.0.0.1",3311,"root","123456",0)')
c.execute('insert into ei_db(db_author,db_instance_name,db_type,db_version,db_host,db_port,db_user,db_password,status) values("ddcw","seccond_test_db","mysql","5.7","127.0.0.1",3311,"root","123456",0)')
c.execute('insert into ei_db(db_author,db_instance_name,db_type,db_version,db_host,db_port,db_user,db_password,status) values("ddcw","test_status1","mysql","5.7","127.0.0.1",3311,"root","123456",1)')
c.execute('insert into ei_db(db_author,db_instance_name,db_type,db_version,db_host,db_port,db_user,db_password,status) values("ddcw","test_status2","mysql","5.7","127.0.0.1",3311,"root","123456",2)')
c.execute('insert into ei_db(db_author,db_instance_name,db_type,db_version,db_host,db_port,db_user,db_password,status) values("ddcw","test_status3","mysql","5.7","127.0.0.1",3311,"root","123456",3)')
c.execute('insert into ei_db(db_author,db_instance_name,db_type,db_version,db_host,db_port,db_user,db_password,status) values("ddcw","test_status4","mysql","5.7","127.0.0.1",3311,"root","123456",4)')
c.execute('insert into ei_host(host_author,host_instance_name,host_type,host_version,host_ssh_ip,host_ssh_port,host_ssh_username,host_ssh_password,status) values("ddcw","host1","centos","7.6","127.0.0.1",22,"aa","Ddcw@123.",0)')
c.execute('insert into ei_host(host_author,host_instance_name,host_type,host_version,host_ssh_ip,host_ssh_port,host_ssh_username,host_ssh_password,status) values("ddcw","host2","centos","7.6","127.0.0.1",22,"aa","Ddcw@123.",0)')
c.execute('insert into ei_host(host_author,host_instance_name,host_type,host_version,host_ssh_ip,host_ssh_port,host_ssh_username,host_ssh_password,status) values("ddcw","host2","centos","7.6","127.0.0.1",22,"aa","Ddcw@123.",0)')
c.execute('insert into ei_host(host_author,host_instance_name,host_type,host_version,host_ssh_ip,host_ssh_port,host_ssh_username,host_ssh_password,status) values("ddcw","test_status1","centos","7.6","127.0.0.1",22,"aa","Ddcw@123.",1)')
c.execute('insert into ei_host(host_author,host_instance_name,host_type,host_version,host_ssh_ip,host_ssh_port,host_ssh_username,host_ssh_password,status) values("ddcw","test_status2","centos","7.6","127.0.0.1",22,"aa","Ddcw@123.",2)')
c.execute('insert into ei_host(host_author,host_instance_name,host_type,host_version,host_ssh_ip,host_ssh_port,host_ssh_username,host_ssh_password,status) values("ddcw","test_status3","centos","7.6","127.0.0.1",22,"aa","Ddcw@123.",3)')
c.execute('insert into ei_host(host_author,host_instance_name,host_type,host_version,host_ssh_ip,host_ssh_port,host_ssh_username,host_ssh_password,status) values("ddcw","test_status4","centos","7.6","127.0.0.1",22,"aa","Ddcw@123.",4)')
c.execute('insert into ei_host(host_author,host_instance_name,host_type,host_version,host_ssh_ip,host_ssh_port,host_ssh_username,host_ssh_password,status) values("ddcw","test_status4","centos","7.6","127.0.0.1",22,"aa","Ddcw@123.",4)')
c.execute('insert into ei_host(host_author,host_instance_name,host_type,host_version,host_ssh_ip,host_ssh_port,host_ssh_username,host_ssh_password,status) values("ddcw","test_status4","centos","7.6","127.0.0.1",22,"aa","Ddcw@123.",4)')
#c.execute('update user set password="aaa" where username="ddcw" and password="123456"')
#c.execute('update user set password="1234" where username="ddcw" and password="aaa"')
#print(list(c.execute("select * from user;")))
#print(list(c.execute("select * from ei_db;")))
#print(list(c.execute('delete from ei_host where db_author = "ddcw" and db_instance_name in ("host2")')))
#print(list(c.execute("select * from ei_host;")))
#print(list(c.execute("select host_instance_name,host_type,host_version,host_ssh_ip,host_ssh_port,status from ei_host where host_author = 'ddcw'")))
conn.commit()
conn.close()
