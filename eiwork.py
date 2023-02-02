import time
import ddcw_ssh
import ddcw_mysql
import os
import gzip
import datetime
import install_mysql
#更新task的
def worksub(conf,db_queue,log,db_conn):
	log.info('worksub start.')
	#初始化表结构
	cursor = db_conn['db_task'].cursor()
	sql = """
create table task(
  task_name varchar(40) primary key,
  task_type int, -- 0:巡检 1:压测 2:数据校验,3,安装mysql ...
  create_time int,
  start_time int, -- 现在不区分create_time,start_time,
  end_time int,
  cost_time int default 0, -- 秒,不存储, 由前端计算.....
  status int, -- 0:未开始 1:运行中 2:成功 3:失败 4:未知
  failed_count int, --失败次数
  detail text, -- 详情.之前计划是记录log位置. 但是发现log也不多,就直接记录了. 也不使用socketio交互了.
  input_var text, -- task参数, 重启task可能需要. 后面再说吧.
  extra_info text -- 额外信息, 可能需要展示到前台的.(比如安装mysql的账号信息之类的)
)
"""
	cursor.execute(sql)
	#cursor.fetchall() #懒得判断了, 反正后面会变更存储的.
	while True:
		data = db_queue.get()
		#data['type']  create_task, update_task(更新部分字段), delete_task
		#data['task_name']  data['state'] 完成时,自动计算cost_time
		if data['type'] == 'create_task':
			sql = f"insert into task values('{data['task_name']}',{data['task_type']},{int(time.time())}, {int(time.time())}, 0,0,1,{data['failed_count']},'','','')"
		elif data['type'] == 'update_task':
			sql = f"update task set status={data['status']},failed_count={data['failed_count']},detail='{data['detail']}',extra_info='{data['extra_info']}' where task_name='{data['task_name']}'"
		elif data['type'] == 'delete_task':
			sql = f"delete from task where task_name='{data['task_name']}'"
		else:
			sql = "select 1+1;"
		log.info(sql)
		cursor = db_conn['db_task'].cursor()
		try:
			cursor.execute(sql)
			#cursor.fetchall() #
		except Exception as e:
			log.error(e)
		try:
			cursor.execute('commit')
		except:
			pass

#定时更新host,db,cluster监控数据
def update(conf,log,db_conn):
	log.info('update start.')
	#初始化表结构
	cursor_host = db_conn['db_host'].cursor()
	cursor_db = db_conn['db_db'].cursor()
	cursor_cluster = db_conn['db_cluster'].cursor()
	sql_host = """
create table if not exists host(
  host varchar(50),
  port int(2),
  user varchar(50),
  password varchar(128),
  private_key varchar(256), -- 暂不支持
  create_time int,
  last_update int,
  primary key(host,port)
)
"""
	sql_db = """
create table if not exists db(
  type int default 0, -- 0:mysql 目前只支持mysql
  host varchar(50),
  port int(2),
  user varchar(50),
  password varchar(100),
  socket varchar(100), -- 不支持, 后面可以考虑给mysql_agent加个访问socket的功能
  create_time int,
  last_update int,
  primary key(host,port)
)
"""
	sql_cluster = """
create table if not exists cluster(
  cluster_type int, -- 0:主从 1:主主 2:MGR 3:PXC
  cluster_name varchar(100) primary key,
  cluster_member text, -- 不支持列表, 所以后面可能不会使用sqlite3了
  create_time int,
  last_update int,
  status int
)
"""
	cursor_host.execute(sql_host)
	cursor_db.execute(sql_db)
	cursor_cluster.execute(sql_cluster)

	#monitor信息
	sql_monitor_host = """
create table if not exists host(
  host varchar(50),
  port int(2),
  osname varchar(30),
  cpu_socket int,
  cpu_core int,
  cpu_thread int,
  mem_total BIGINT, -- 字节
  mem_ava BIGINT,
  swap BIGINT,
  swapness int,
  firewalld int, -- 0:禁用, 1:启用
  selinux int, -- 0:enforcing 1:permissive 2:disabled
  status int, -- 0 在线  1:离线 
  disk text, -- lsblk -d -o NAME,KNAME,SIZE,RO,STATE,ROTA,SCHED,UUID
  fs text, -- df -PT --direct -k 文件系统信息
  last_update time,
  is_virtual int, -- 是否为虚拟机
  status int,
  failed_count int, -- 成功更新之后就清零
  primary key(host,port)
)
"""
	sql_monitor_db = """
create table if not exists db(
  host varchar(50),
  port int(2),
  version varchar(16),
  connect int, -- 连接数
  threads int, -- 线程数
  status int, -- 0:运行 1:未运行
  uptime int, -- 运行时间
  last_update int, -- 最后更新时间, 为时间戳. 懒得整date类型, 不同数据库可能不同.
  failed_count int, -- 成功更新之后就清零
  primary key(host,port)
)
"""
	sql_monitor_cluster_ms = "" #ms, mgr, pxc TODO
	cursor_monitor = db_conn['db_monitor'].cursor()
	cursor_monitor.execute(sql_monitor_host)
	cursor_monitor.execute(sql_monitor_db)
	
	while True:
		#更新host
		_host_sql = "select host,port,user,password from host"
		_host_cursor = db_conn['db_host'].cursor()
		_host_cursor.execute(_host_sql)
		_host_info = _host_cursor.fetchall()
		_host_cursor.close()
		for rows in _host_info:
			host = rows[0]
			port = rows[1]
			user = rows[2]
			password = rows[3]
			data = monitor_host(host,port,user,password)
			if data['status'] == 0:#成功
				_host_sql = f"replace into host values('{host}',{port},'{data['osname']}', '{data['cpu_socket']}', '{data['cpu_core']}', '{data['cpu_thread']}', '{data['mem_total']}', '{data[mem_ava]}', '{data[swap]}', '{data[swapness]}', '{'firewalld'}', '{data['selinux']}', '{data['status']}', '{data['disk']}', '{data['fs']}', '{data['last_update']}', '{data['is_virtual']}', '{data['status']}', '{data[failed_count]}' )"
			elif data['status'] == 1:#失败
				_host_sql = f"update host set failed_count = failed_count+1 where host='{host}' and port = {port}"
			else:
				_host_sql = 'select 1+1'
			cursor = db_conn['db_monitor'].cursor()
			cursor.execute(_host_sql)
			try:
				cursor.execute('commit')
			except:
				pass
			cursor.close()


		#更新db
		_db_sql = "select host,port,user,password from db"
		_db_cursor = db_conn['db_db'].cursor()
		_db_cursor.execute(_db_sql)
		_db_info = _db_cursor.fetchall()
		_db_cursor.close()
		for rows in _db_info:
			host = rows[0]
			port = rows[1]
			user = rows[2]
			password = rows[3]
			data = monitor_mysql(host,port,user,password)
			if data['status'] == 0:
				_db_sql = f"replace into db values('{host}',{port}, '{data['osname']}', '{conf['version']}', '{conf['connect']}', '{conf['threads']}', '{conf['status']}', '{conf['uptime']}', '{conf['last_update']}', '{conf['failed_count']}')"
			elif data['status'] == 1:
				_db_sql = f"update db set failed_count = failed_count+1 where host='{host}' and port = {port}"
			else:
				_db_sql = 'select 1+1'
			cursor = db_conn['db_monitor'].cursor()
			cursor.execute(_db_sql)
			try:
				cursor.execute('commit')
			except:
				pass
			cursor.close()

		#更新cluster TODO

		#等待下一次更新
		time.sleep(conf['UPDATE_INTERVAL'])

def worker(conf,task_queue,task_dict,log,x): #task_dict记录task详情的. 每次任务完成都全刷task_dict
	msg = f'work {x} start.'
	log.info(msg)
	while True:
		task = task_queue.get()
		taskname = task['taskname']
		task_dict[taskname]['start_time'] = datetime.datetime.now() #设置为开始
		task_dict[taskname]['status'] = 1
		task_type = task['task_type']
		host = task['opt']['host']
		port = task['opt']['port']
		user = task['opt']['user']
		password = task['opt']['password']
		if task_type == 1: #安装Mysql
			log.info('begin install mysql AAAAAAAA')
			mysql_password = task['opt']['mysql_password']
			var = task['opt']['var']
			isENFORCE = True
			pack = conf['MYSQL_PACK'] #懒得去判断是否存在了... 本来该由前端选择安装哪个版本的. 算了.
			_task_instance = install_mysql.install_mysql(host,port,user,password,mysql_password,var,log,isENFORCE,pack)
			if _task_instance.status:
				task_dict[taskname]['log'] += "\nbegin install."
				if _task_instance.install(): #懒得去try了, install_mysql也没必要raise了
					task_dict[taskname]['status'] = 2 if _task_instance.status else 3
				else:
					task_dict[taskname]['status'] = 3
			else:
				task_dict[taskname]['log'] += "\ncant install"
				task_dict[taskname]['status'] = 3
			task_dict[taskname]['log'] += _task_instance.msg
		#for i in range(10):
		#	task_dict[taskname]['log'] += f'a{i}\n'
		#task_dict[taskname]['status'] = 2
		task_dict[taskname]['end_time'] =  datetime.datetime.now()
		log.info(task)

def monitor_mysql(host,port,user,password):
	tmysql = ddcw_mysql.set(host=host,port=port,user=user,password=password)
	if tmysql.set()['status']: #账号密码正确
		data = {
			'host':host,
			'port':port,
			'version':tmysql.get_result_dict('select @@version;')['data'][0][0],
			'connect':0,#懒得去判断了
			'threads':0,#懒得去判断了
			'status':0,
			'uptime':tmysql.get_result_dict("show global status like 'uptime'")['data'][0][1],
			'last_update':int(time.time()),
			'failed_count':0,
		}
		tmysql.close()
		return data
	else:
		return {'host':host,'port':port,'status':1}

def monitor_host(host,port,user,password):
	tssh = ddcw_ssh.set(host=host,port=port,user=user,password=password)
	if tssh.set()['status']: #账号密码正确
		data =  {
			'host':host,
			'port':port,
			'osname':tssh.get_result_dict('uname -n')['stdout'],
			'cpu_socket':tssh.get_result_dict("lscpu | grep 'Socket(s)' | awk '{print $NF}'")['stdout'],
			'cpu_core':tssh.get_result_dict("lscpu | grep 'Core(s)' | awk '{print $NF}'")['stdout'],
			'cpu_thread':tssh.get_result_dict("lscpu | grep 'Thread(s)' | awk '{print $NF}'")['stdout'],
			'mem_total':tssh.get_result_dict("""cat /proc/meminfo | awk  '{ if ( $1 == "MemTotal:") print $2}'""")['stdout'],
			'mem_ava':tssh.get_result_dict("""cat /proc/meminfo | awk  '{ if ( $1 == "MemAvailable:") print $2}'""")['stdout'],
			'swap':tssh.get_result_dict("""cat /proc/meminfo | awk  '{ if ( $1 == "SwapTotal:") print $2}'""")['stdout'],
			'swapness':tssh.get_result_dict("""cat /proc/sys/vm/swappiness""")['stdout'],
			'firewalld':0, #懒得去判断了
			'selinux':0, #懒得去判断了
			'status':0,
			'disk':tssh.get_result_dict("""lsblk -d -o NAME,KNAME,SIZE,RO,STATE,ROTA,SCHED,UUID | tail -n +2""")['stdout'],
			'fs':tssh.get_result_dict("""df -PT --direct -k | tail -n +2""")['stdout'],
			'last_update':int(time.time()),
			'is_virtual':0, #懒得去判断了. virt-what需要root权限...
			'failed_count':0
			}
		tssh.close()
		return data
	else:
		return {'host':host,'port':port,'status':1}

def monitor(conf,log,host_dict,db_dict,cluster_dict,host_monitor_info,db_monitor_info,cluster_monitor_info):
	log.info('monitor start.')
	while True:
		try:
			for k,rows in host_dict.items():
				host = rows['host']
				port = rows['port']
				user = rows['user']
				password = rows['password']
				host_monitor_info[k] = monitor_host(host,port,user,password)
				
			for k,rows in db_dict.items():
				host = rows['host']
				port = rows['port']
				user = rows['user']
				password = rows['password']
				db_monitor_info[k] = monitor_mysql(host,port,user,password)

			for k,rows in cluster_dict.items():
				pass
		except Exception as e:
			msg = f'server monitor error. {e}'
			log.error(msg)
		time.sleep(60)


def readdata(conf,host,port,startdate,rows): 
	thisday_seconds = startdate.hour*3600+startdate.minute*69+startdate.second
	if (24*3600 - thisday_seconds) > rows: #只读这个文件就够了
		DATE = startdate
		filename = f"{conf['MONITORDIR']}/{host}_{port}_{DATE.year}_{DATE.month:02}_{DATE.day:02}.data"
		filenamegz = f"{conf['MONITORDIR']}/{host}_{port}_{DATE.year}_{DATE.month:02}_{DATE.day:02}.data.gz"
		if os.path.exists(filename):
			f = open(filename,'rb')
			f.seek(thisday_seconds*1024,0)
			bdata = f.read(rows*1024)
			f.close()
		elif os.path.exists(filenamegz):
			f = gzip.open(filename,'rb')
			f.seek(thisday_seconds*1024,0)
			bdata = f.read(rows*1024)
			f.close()
		else:
			bdata = b''
		#print(bdata,host,port,startdate,rows,filename,filenamegz)
		return bdata
		
	else: #跨天读 后面再说...
		print('跨天读, TODO')
		return b''
