#!/usr/bin/python

import sqlite3

conn = sqlite3.connect('ei.db')

c = conn.cursor()
c.execute('drop table if exists user;')
c.execute('drop table if exists ei_db;')
c.execute('drop table if exists ei_host;')
c.execute('drop table if exists ei_task;')
c.execute('drop table if exists ei_script;')
c.execute('drop table if exists ei_pack;')
c.execute(''' 
create table user(
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	username varchar(32), 
	password varchar(200), 
	create_time DEFAULT (datetime('now', 'localtime')), -- 用户创建时间
	modify_time DEFAULT (datetime('now', 'localtime')), -- 用户修改时间, 比如修改状态, 修改密码等
	refresh_intervals_host int default 10, --主机实例监控刷新间隔
	refresh_intervals_db int default 10, --数据库实例监控刷新间隔
	is_admin int default 1, --是不是管理员, 管理员可以修改和上传脚本/包
	status int default 0 --用户状态, 0 表示可用, 其它状态表示不可用
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
	status int default 4 -- 0:正常 1:告警  2:down了 3:未知状态
);
''')

c.execute(''' 
create table ei_host(
	host_instance_id INTEGER PRIMARY KEY AUTOINCREMENT,
	host_author varchar(32),
	host_instance_name varchar(200),
	host_type varchar(50),
	host_version varchar(50),
	host_ssh_ip varchar(50),
	host_ssh_port int,
	host_ssh_username varchar(32),
	host_ssh_password varchar(200),
	status int default 4 -- 0:正常 1:告警  2:down了 3:未知状态
);

''')

c.execute(''' 
create table ei_task(
	task_id INTEGER PRIMARY KEY AUTOINCREMENT, -- 主键自增
	task_author varchar(200), -- 执行任务的用户
	task_name varchar(200), --任务名
	task_object varchar(200), --任务对象, 也就是主机名和端口 集群环境的时候有多个,用逗号隔开  host:port, host:port
	task_describe varchar(2000), --任务描述,
	task_start TimeStamp not null default current_timestamp, --任务开始时间
	task_stop TimeStamp , --任务结束时间
	task_pid int , -- 执行这个任务的进程号, 自动检查任务状态的时候, 如果状态为1, 但是进程又没得的话, 就把状态标记为2
	task_shell varchar(5000), --这个任务执行的shell命令 方便重试的时候用的, 目前不考虑重试功能的实现
	task_detail_path varchar(500), -- 任务的详细日志, 不存放到数据库中,写入操作系统的文件里面 文件命令格式: username_starttime_pid. 为什么这么设计呢??? 我感觉直接放到数据库里面是不是更好一点
	task_status int default 1 --任务状态, 0: 完成  1: 进行中   2: 异常  3:不知道
);
''')

c.execute(''' 
create table ei_script(
	script_id INTEGER PRIMARY KEY AUTOINCREMENT, --脚本编号 , 自增,没得实际意义
	script_name varchar(100), --脚本名字, 比如 INSTALL_MYSQL_SINGLE
	script_object varchar(32), --脚本对象, 比如是MYSQL还是PG还是啥. 和ei_pack关联
	script_type varchar(100), --脚本类型, 二进制还是源码包编译安装
	script_path varchar(512), --脚本路径, 以webei为root目录, 含脚本文件名字
	script_version varchar(100), --脚本版本, 和软件包版本没得关系,	仅仅记录脚本的版本而已
	script_describe varchar(3000), --脚本描述, 介绍脚本怎么使用的, 仅供人参考.
	script_des_dir varchar(200) default "/tmp/ddcw", --脚本拷贝到目标端的目录
	script_md5 varchar(64), --脚本的md5校验码, 如果有的话, 就会定时校验, 不对的话就设置状态为2
	script_status int default 0 --脚本状态, 0:正常 1:不存在: 2:校验码不对 3:禁止使用	只有为0的时候才能用
);
''')

c.execute('''
create table ei_pack(
	pack_id INTEGER PRIMARY KEY AUTOINCREMENT, --软件包编号, 自增
	pack_name varchar(100), --软件包名字,比如MYSQL,	ei_script就是通过软件包名字来判断的, 名字固定为: MYSQL POSTGRESQL ORACLE REDIS MONGODB CUSTOMIZE 均为大写, 具体名字在path里面
	pack_path varchar(512), --软件包路径, 含软件包名字
	pack_type varchar(100), --软件包类型,	是二进制包,还是源码包,没得实际意义
	pack_version varchar(100), --软件包版本, 用户可以选择不同版本的软件包 默认为软件包文件名
	pack_describe varchar(3000), --软件包描述. 一般为空
	pack_des_dir varchar(200) default "/tmp/ddcw", --软件包拷贝到目标端的目录, 不含软件包文件名字
	pack_md5 varchar(64), --软件包的md5校验码, 自动检测状态的时候会校验对不对, 不对的话 也会设置状态为2
	pack_status int default 0 --软件包状态. 0:正常 1:不存在: 2:校验码不对 3:禁止使用	只有为0的时候才能用
);
''')


#默认账号
c.execute('insert into user(username,password,is_admin) values("ddcw","123456",0)')
c.execute('insert into user(username,password) values("root","123456")')
c.execute('insert into user(username,password) values("admin","123456")')


#脚本和软件包测试数据
c.execute('insert into ei_script(script_name,script_object,script_path,script_des_dir) values("INSTALL_MYSQL_SINGLE","MYSQL","../script/MysqlInstallerByDDCW_ei_1.0.sh","/tmp/ddcw")')
c.execute('insert into ei_pack(pack_name,pack_path,pack_version,pack_des_dir) values("MYSQL","../pack/mysql-5.7.33-linux-glibc2.12-x86_64.tar.gz","5.7.33","/tmp/ddcw")')

#任务表测试数据
c.execute('insert into ei_task(task_author,task_name,task_object,task_describe,task_detail_path,task_status) values("ddcw","ddcw的测试任务","127.0.0.1:22","仅测试,建议删除此任务","../data/tasks/test.log",0)')
c.execute('insert into ei_task(task_author,task_name,task_object,task_describe,task_detail_path,task_status) values("ddcw","ddcw test task","127.0.0.1:22","仅测试,建议删除此任务","../data/tasks/test.log",1)')

#脚本位置
#c.execute('insert into ei_script(script_author,script_name,script_path,script_describe,script_pack_path,script_target_path) values("ddcw","install_mysql_single","../script/bin/MysqlInstallerByDDCW_ei_1.0.sh","安装mysql单机的脚本","../pack/bin/mysql-5.7.33-linux-glibc2.12-x86_64.tar.gz","/tmp/ddcw")')

#数据库实例 测试数据
c.execute('insert into ei_db(db_author,db_instance_name,db_type,db_version,db_host,db_port,db_user,db_password,status) values("ddcw","first_test_db","mysql","5.7","127.0.0.1",3311,"root","123456",0)')
c.execute('insert into ei_db(db_author,db_instance_name,db_type,db_version,db_host,db_port,db_user,db_password,status) values("ddcw","seccond_test_db","mysql","5.7","127.0.0.1",3311,"root","123456",0)')
c.execute('insert into ei_db(db_author,db_instance_name,db_type,db_version,db_host,db_port,db_user,db_password,status) values("ddcw","test_status1","mysql","5.7","127.0.0.1",3311,"root","123456",1)')
c.execute('insert into ei_db(db_author,db_instance_name,db_type,db_version,db_host,db_port,db_user,db_password,status) values("ddcw","test_status2","mysql","5.7","127.0.0.1",3311,"root","123456",2)')
c.execute('insert into ei_db(db_author,db_instance_name,db_type,db_version,db_host,db_port,db_user,db_password,status) values("ddcw","test_status3","mysql","5.7","127.0.0.1",3311,"root","123456",3)')
c.execute('insert into ei_db(db_author,db_instance_name,db_type,db_version,db_host,db_port,db_user,db_password,status) values("ddcw","test_status4","mysql","5.7","127.0.0.1",3311,"root","123456",4)')


#主机实例 测试数据
c.execute('insert into ei_host(host_author,host_instance_name,host_type,host_version,host_ssh_ip,host_ssh_port,host_ssh_username,host_ssh_password,status) values("ddcw","host1","centos","7.6","127.0.0.1",22,"aa","Ddcw@123.",0)')
c.execute('insert into ei_host(host_author,host_instance_name,host_type,host_version,host_ssh_ip,host_ssh_port,host_ssh_username,host_ssh_password,status) values("ddcw","host2","centos","7.6","127.0.0.1",22,"aa","Ddcw@123.",0)')
c.execute('insert into ei_host(host_author,host_instance_name,host_type,host_version,host_ssh_ip,host_ssh_port,host_ssh_username,host_ssh_password,status) values("ddcw","host2","centos","7.6","127.0.0.1",22,"aa","Ddcw@123.",0)')
c.execute('insert into ei_host(host_author,host_instance_name,host_type,host_version,host_ssh_ip,host_ssh_port,host_ssh_username,host_ssh_password,status) values("ddcw","test_status1","centos","7.6","127.0.0.1",22,"aa","Ddcw@123.",1)')
c.execute('insert into ei_host(host_author,host_instance_name,host_type,host_version,host_ssh_ip,host_ssh_port,host_ssh_username,host_ssh_password,status) values("ddcw","test_status2","centos","7.6","127.0.0.1",22,"aa","Ddcw@123.",2)')
c.execute('insert into ei_host(host_author,host_instance_name,host_type,host_version,host_ssh_ip,host_ssh_port,host_ssh_username,host_ssh_password,status) values("ddcw","test_status3","centos","7.6","127.0.0.1",22,"aa","Ddcw@123.",3)')
c.execute('insert into ei_host(host_author,host_instance_name,host_type,host_version,host_ssh_ip,host_ssh_port,host_ssh_username,host_ssh_password,status) values("ddcw","test_status4","centos","7.6","127.0.0.1",22,"aa","Ddcw@123.",4)')
c.execute('insert into ei_host(host_author,host_instance_name,host_type,host_version,host_ssh_ip,host_ssh_port,host_ssh_username,host_ssh_password,status) values("ddcw","test_status4","centos","7.6","127.0.0.1",22,"aa","Ddcw@123.",4)')
c.execute('insert into ei_host(host_author,host_instance_name,host_type,host_version,host_ssh_ip,host_ssh_port,host_ssh_username,host_ssh_password,status) values("ddcw","test_status4","centos","7.6","127.0.0.1",22,"aa","Ddcw@123.",4)')

#提交&关闭
conn.commit()
conn.close()
