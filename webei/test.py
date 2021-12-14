#!/usr/bin/python

import sqlite3

conn = sqlite3.connect('ei.db')

c = conn.cursor()
#c.execute('drop table if exists user;')
#c.execute('drop table if exists ei_db;')
#c.execute('drop table if exists ei_host;')
#c.execute('drop table if exists ei_task;')
#c.execute('drop table if exists ei_script;')
#c.execute(''' 
#create table user(
#	id INTEGER PRIMARY KEY AUTOINCREMENT,
#	username varchar(32), 
#	password varchar(200), 
#	create_time DEFAULT (datetime('now', 'localtime')), -- 用户创建时间
#	modify_time DEFAULT (datetime('now', 'localtime')), -- 用户修改时间, 比如修改状态, 修改密码等
#	status int default 0 --用户状态, 0 表示可用, 其它状态表示不可用
#	);
#''')
#c.execute(''' 
#create table ei_db(
#	db_instance_id INTEGER PRIMARY KEY AUTOINCREMENT,
#	db_author varchar(32),
#	db_instance_name varchar(200),
#	db_type varchar(15),
#	db_version varchar(20),
#	db_host varchar(32),
#	db_port int,
#	db_user varchar(32),
#	db_password varchar(200),
#	status int default 4 -- 0:正常 1:告警  2:down了 3:未知状态
#);
#''')
#
#c.execute(''' 
#create table ei_host(
#	host_instance_id INTEGER PRIMARY KEY AUTOINCREMENT,
#	host_author varchar(32),
#	host_instance_name varchar(200),
#	host_type varchar(50),
#	host_version varchar(50),
#	host_ssh_ip varchar(50),
#	host_ssh_port int,
#	host_ssh_username varchar(32),
#	host_ssh_password varchar(200),
#	status int default 4 -- 0:正常 1:告警  2:down了 3:未知状态
#);
#
#''')
#
#c.execute(''' 
#create table ei_task(
#	task_id INTEGER PRIMARY KEY AUTOINCREMENT, -- 主键自增
#	task_author varchar(200), -- 执行任务的用户
#	task_name varchar(200), --任务名
#	task_object varchar(200), --任务对象, 也就是主机名和端口 集群环境的时候有多个,用逗号隔开  host:port, host:port
#	task_describe varchar(2000), --任务描述,
#	task_start TimeStamp not null default current_timestamp, --任务开始时间
#	task_stop TimeStamp , --任务结束时间
#	task_pid int , -- 执行这个任务的进程号, 自动检查任务状态的时候, 如果状态为1, 但是进程又没得的话, 就把状态标记为2
#	task_shell varchar(5000), --这个任务执行的shell命令 方便重试的时候用的, 目前不考虑重试功能的实现
#	task_detail_path varchar(500), -- 任务的详细日志, 不存放到数据库中,写入操作系统的文件里面 文件命令格式: username_starttime_pid. 为什么这么设计呢??? 我感觉直接放到数据库里面是不是更好一点
#	task_status int default 1 --任务状态, 0: 完成  1: 进行中   2: 异常  3:不知道
#);
#''')
#
#c.execute(''' 
#	create table ei_script(
#	script_id INTEGER PRIMARY KEY AUTOINCREMENT, --脚本编号 , 自增,  没得实际意义
#	script_author varchar(200) default 'ddcw', --脚本持有者, 脚本持有者才能修改脚本的信息. 其它用户只能读取脚本的信息
#	script_share int default 0, --脚本是否共享 0:共享, 1:不共享   共享的时候, 就所有人都能使用, 但是不能修改
#	script_name varchar(200), --脚本逻辑名字, 比如安装mysql单机的名字就叫 install_mysql_single 是固定的, 即使脚本名字变了, 这个名字也不变, 只修改脚本路径就行
#	script_version varchar(32), --脚本版本, 
#	script_type varchar(20), --脚本类型, 集群,单机,主从,源码编译, 二进制安装等.. 目前没得啥用
#	script_path varchar(512), --脚本路径, 相对路径和绝对路径都行, 这个路径含脚本名字
#	script_describe varchar(2000), --脚本描述, 介绍这个脚本的, 比如 用法啊,功能啊之类的
#	script_pack_path varchar(512), -- 脚本需要的tar包的路径, 相对路径绝对路径都行, 多个tar包之间用逗号隔开
#	script_pack_version varchar(100), --软件包的版本
#	script_target_path varchar(512), --脚本需要拷贝到的目标端路径, 绝对路径, 且包含脚本名字
#	script_status int default 0 --脚本状态 0:可用  2:开发中 3:改BUG中  4:不知道 
#);
#''')
#
#c.execute('insert into ei_task(task_author,task_name,task_object,task_describe,task_detail_path,task_status) values("ddcw","ddcw的第一个任务","127.0.0.1:22","测试而已","../data/tasks/test.log",0)')
#c.execute('insert into ei_task(task_author,task_name,task_object,task_describe,task_detail_path,task_status) values("ddcw","ddcw的第二个任务","127.0.0.1:22","测试而已","../data/tasks/test.log",1)')
#c.execute('insert into ei_script(script_author,script_name,script_path,script_describe,script_pack_path,script_target_path) values("ddcw","install_mysql_single","../script/bin/MysqlInstallerByDDCW_ei_1.0.sh","安装mysql单机的脚本","../pack/bin/mysql-5.7.33-linux-glibc2.12-x86_64.tar.gz","/tmp/ddcw")')
#c.execute('insert into user(username,password) values("ddcw","123456")')
#c.execute('insert into user(username,password) values("root","123456")')
#c.execute('insert into user(username,password) values("admin","123456")')
#c.execute('insert into ei_db(db_author,db_instance_name,db_type,db_version,db_host,db_port,db_user,db_password,status) values("ddcw","first_test_db","mysql","5.7","127.0.0.1",3311,"root","123456",0)')
#c.execute('insert into ei_db(db_author,db_instance_name,db_type,db_version,db_host,db_port,db_user,db_password,status) values("ddcw","seccond_test_db","mysql","5.7","127.0.0.1",3311,"root","123456",0)')
#c.execute('insert into ei_db(db_author,db_instance_name,db_type,db_version,db_host,db_port,db_user,db_password,status) values("ddcw","test_status1","mysql","5.7","127.0.0.1",3311,"root","123456",1)')
#c.execute('insert into ei_db(db_author,db_instance_name,db_type,db_version,db_host,db_port,db_user,db_password,status) values("ddcw","test_status2","mysql","5.7","127.0.0.1",3311,"root","123456",2)')
#c.execute('insert into ei_db(db_author,db_instance_name,db_type,db_version,db_host,db_port,db_user,db_password,status) values("ddcw","test_status3","mysql","5.7","127.0.0.1",3311,"root","123456",3)')
#c.execute('insert into ei_db(db_author,db_instance_name,db_type,db_version,db_host,db_port,db_user,db_password,status) values("ddcw","test_status4","mysql","5.7","127.0.0.1",3311,"root","123456",4)')
#c.execute('insert into ei_host(host_author,host_instance_name,host_type,host_version,host_ssh_ip,host_ssh_port,host_ssh_username,host_ssh_password,status) values("ddcw","host1","centos","7.6","127.0.0.1",22,"aa","Ddcw@123.",0)')
#c.execute('insert into ei_host(host_author,host_instance_name,host_type,host_version,host_ssh_ip,host_ssh_port,host_ssh_username,host_ssh_password,status) values("ddcw","host2","centos","7.6","127.0.0.1",22,"aa","Ddcw@123.",0)')
#c.execute('insert into ei_host(host_author,host_instance_name,host_type,host_version,host_ssh_ip,host_ssh_port,host_ssh_username,host_ssh_password,status) values("ddcw","host2","centos","7.6","127.0.0.1",22,"aa","Ddcw@123.",0)')
#c.execute('insert into ei_host(host_author,host_instance_name,host_type,host_version,host_ssh_ip,host_ssh_port,host_ssh_username,host_ssh_password,status) values("ddcw","test_status1","centos","7.6","127.0.0.1",22,"aa","Ddcw@123.",1)')
#c.execute('insert into ei_host(host_author,host_instance_name,host_type,host_version,host_ssh_ip,host_ssh_port,host_ssh_username,host_ssh_password,status) values("ddcw","test_status2","centos","7.6","127.0.0.1",22,"aa","Ddcw@123.",2)')
#c.execute('insert into ei_host(host_author,host_instance_name,host_type,host_version,host_ssh_ip,host_ssh_port,host_ssh_username,host_ssh_password,status) values("ddcw","test_status3","centos","7.6","127.0.0.1",22,"aa","Ddcw@123.",3)')
#c.execute('insert into ei_host(host_author,host_instance_name,host_type,host_version,host_ssh_ip,host_ssh_port,host_ssh_username,host_ssh_password,status) values("ddcw","test_status4","centos","7.6","127.0.0.1",22,"aa","Ddcw@123.",4)')
#c.execute('insert into ei_host(host_author,host_instance_name,host_type,host_version,host_ssh_ip,host_ssh_port,host_ssh_username,host_ssh_password,status) values("ddcw","test_status4","centos","7.6","127.0.0.1",22,"aa","Ddcw@123.",4)')
#c.execute('insert into ei_host(host_author,host_instance_name,host_type,host_version,host_ssh_ip,host_ssh_port,host_ssh_username,host_ssh_password,status) values("ddcw","test_status4","centos","7.6","127.0.0.1",22,"aa","Ddcw@123.",4)')
#c.execute('update user set password="aaa" where username="ddcw" and password="123456"')
#c.execute('update user set password="1234" where username="ddcw" and password="aaa"')
#c.execute('update ei_host set host_type="CentOS Linux",host_version="7 (Core)",status=0 where host_instance_name="Linux_127.0.0.1_22" and host_ssh_ip="127.0.0.1" and host_ssh_port=22 and host_ssh_username="aa";')
#print(list(c.execute("select * from ei_host where host_instance_name='Linux_127.0.0.1_22';")))
#print(list(c.execute("select * from user;")))
#print(list(c.execute("select * from ei_db;")))
#print(list(c.execute('delete from ei_host where db_author = "ddcw" and db_instance_name in ("host2")')))
#print(list(c.execute("select * from ei_host;")))
#print(list(c.execute("select host_instance_name,host_type,host_version,host_ssh_ip,host_ssh_port,status from ei_host where host_author = 'ddcw'")))
c.execute('delete ei_task where task_author="ddcw" and task_name="ddcw的第一个任务"')
conn.commit()
conn.close()
