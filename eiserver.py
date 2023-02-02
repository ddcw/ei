from mysql_agent import daemon
from mysql_agent import COMMAND
from mysql_agent import compressdata
import transdataforserver as transdata
#from mysql_agent import transdata
import logging
import datetime,time
from multiprocessing import Queue
from threading import Thread #使用多线程
import socket
import binascii
import os
import eiwork
#import sqlite3
import _encrypt
import ddcw_mysql,ddcw_ssh

PACK_MAX_SIZE = 32*1024

import pickle
def flush_with_pickle(obj,filename):
	with open(filename,'wb') as f:
		pickle.dump(obj,f)

class server(daemon.Daemon):
	def close(self,):
		try:
			self.log.info('closed.')
			#关闭本地打开的那几个字典, host_dict,db_dict,cluster_dict,task_dict
		except:
			pass

	def _stop(self,):
		print('stop')

	def read(self,host,port,startdate,rows):
		fdname = f"{host}_{port}_{startdate.year}_{startdate.month:02}_{startdate.day:02}.data"
		#如果是压缩文件要先解压. TODO
		if fdname in self.rfd:
			self.rfd[fdname][0] = datetime.datetime.now()
			f = self.rfd[fdname][1]
		else:
			f = open(f'{self.conf["DATADIR"]}/{fdname}','rb')
			self.rfd[fdname] = [datetime.datetime.now(),f]
		offset = (startdate.hour*3600 + startdate.minute*60 + startdate.second)*1024
		f.seek(offset,0)
		return f.read(1024*rows)

	def accept_client(self,):
		#接收客户端连接, 多线程, 只管连接. 认证传数据之类的都交给handler
		self.log.info('server start finish.')
		while True:
			conn, addr = self.socket_server.accept()
			thread = Thread(target=self.handler,args=(conn,addr),daemon=True)
			thread.start()

	def close_client(self,host_port):
		#发送clsoed并清除线程池, 然后close,exit
		if host_port not in self.conn_pool:
			msg = f'NO CONNECT FOR {host_port}'
			self.log.warning(msg)
			return
		else:
			conn = self.conn_pool[host_port]
			conn.close()
			self.conn_pool.pop(host_port)
			msg = f'{host_port} is closed.'
			self.log.info(msg)

	def handler(self,conn,addr):
		#处理具体的指令, 比如 传输数据, 压缩文件之类的
		AUTH_PACK = conn.recv(1024)
		if AUTH_PACK[0:1] != COMMAND.EI_AUTH.to_bytes(1,'big'):
			return
		else:
			HOST = addr[0]
			PORT = int.from_bytes(AUTH_PACK[1:3],'big')

		host_port = f'{HOST}_{PORT}'
		if self.conf['AUTHKEY'] == AUTH_PACK[3:] and PORT != 1:
			if host_port in self.conn_pool:
				try:
					self.conn_pool[host_port].close()
					msg = f'closed connect {host_port}'
					self.log.info(msg)
				except:
					pass
			self.conn_pool[host_port] = conn
			conn.send(COMMAND.EI_OK.to_bytes(1,'big'))
			msg = f'{HOST}:{PORT} CONNECT SUCCESS.'
			self.log.info(msg)
		elif self.conf['AUTHKEY'] == AUTH_PACK[3:] and PORT == 1: #web连接
			msg = f'web connect. {HOST}:{addr[1]}'
			self.log.info(msg)
			conn.send(COMMAND.EI_OK.to_bytes(1,'big'))
		else:
			conn.send(COMMAND.EI_FAILED.to_bytes(1,'big'))
			msg = f'{HOST}:{PORT} CONNECT FAILED, PLEASE CHECK AUTHKEY.'
			self.log.warning(msg)
			return
			
		while True:
			try:
				PACK = conn.recv(32)
			except Exception as e:
				self.log.warning(e)
				break
			ACTION = int.from_bytes(PACK[0:1],'big')
			if ACTION == COMMAND.EI_DATA:
				DATA_TYPE = int.from_bytes(PACK[1:2],'big')
				PACK_MAX_SIZE = int.from_bytes(PACK[2:6],'big')
				ROWS = int.from_bytes(PACK[6:10],'big')
				LENGTH = int.from_bytes(PACK[10:14],'big')
				LASTPACK_SIZE = int.from_bytes(PACK[14:18],'big')
				DATE = datetime.datetime.fromtimestamp(int.from_bytes(PACK[18:22],'big'))
				CRC32DATA = int.from_bytes(PACK[22:26],'big') #crc32比md5快, 而且只有4字节. 所以使用的crc32
				BDATA = b''
				#self.log.info('get EI_DATA')
				for x in range(ROWS):
					BDATA += conn.recv(PACK_MAX_SIZE)
				if LASTPACK_SIZE > 0:
					BDATA += conn.recv(LASTPACK_SIZE)

				#校验包完整性
				if LENGTH != len(BDATA):
					msg = f'PACK NOT COMPLETE. Require Size:{LENGTH} Actual:{len(BDATA)} ROWS:{ROWS} LASTPACK_SIZE:{LASTPACK_SIZE} PACK_MAX_SIZE:{PACK_MAX_SIZE} DATA_TYPE:{DATA_TYPE}'
					self.log.warning(msg)
					conn.send(COMMAND.EI_FAILED.to_bytes(1,'big'))

				if DATA_TYPE == COMMAND.EI_MONITOR_DATA:
					data_rows = int(len(BDATA)/1024)
					for x in range(data_rows):
						self.qdata.put({'host':HOST,'port':PORT,'data':BDATA[x*1024:x*1024+1024]})
					conn.send(COMMAND.EI_OK.to_bytes(1,'big'))

				elif DATA_TYPE == COMMAND.EI_MONITOR_FILEGZ:
					filename = f"{self.conf['MONITORDIR']}/{HOST}_{PORT}_{DATE.year}_{DATE.month:02}_{DATE.day:02}.data.gz"
					if binascii.crc32(BDATA) != CRC32DATA:
						msg = f'ACTION PACK CRC32DATA:{CRC32DATA}  ACTUAL:{binascii.crc32(BDATA)}'
						self.log.error(msg)
						continue #crc32校验失败, 继续
					try:
						with open(filename,'wb') as f:
							f.write(BDATA)
						msg = f'WRITE FILE {filename}'
						self.log.info(msg)
						conn.send(COMMAND.EI_OK.to_bytes(1,'big'))
					except Exception as e:
						msg = f'WRITE FILE FAILED WITH {e}'
						self.log.error(msg)
						conn.send(COMMAND.EI_FAILED.to_bytes(1,'big'))
				else:
					conn.send(COMMAND.EI_UNKNOWN.to_bytes(1,'big'))
					
			elif ACTION == COMMAND.EI_TASK:
				task_type = int.from_bytes(PACK[1:2],'big')
				pack_size = int.from_bytes(PACK[2:6],'big')
				_data = conn.recv(pack_size)
				data = pickle.loads(_data)
				if task_type == 1: #安装mysql
					taskname = str(int(datetime.datetime.now().timestamp()))
					task_dict[taskname] = {'taskname':taskname,'task_type':task_type,'create_time':datetime.datetime.now(),'start_time':'','end_time':'','status':'0','opt':data,'log':''} #status 0:未开始, 1:运行中, 2成功, 3:失败
					self.task_queue.put(task_dict[taskname])
					sendpack = COMMAND.EI_OK.to_bytes(1,'big') + int(taskname).to_bytes(4,'big') + int(0).to_bytes(27,'big')
					conn.send(sendpack)

				else:
					sendpack = COMMAND.EI_TODO.to_bytes(1,'big') + int(0).to_bytes(31,'big')
					conn.send(sendpack)


			#这个包会先回复是否有数据和数据大小(固定32字节), 没得数据就不发送了, 客户端需要自己判断是否需要接收数据
			elif ACTION == COMMAND.EI_GET: #获取信息(监控数据db_monitor,host_monitor,实例信息,mysql_status)
				get_type = int.from_bytes(PACK[1:2],'big')
				if get_type == 1: #获取所有主机信息host_monitor_info
					monitorpack = pickle.dumps(host_monitor_info)
					transdata.senddataforserver(conn,monitorpack) #懒得去判断成功失败了...

				elif get_type == 2: #获取所有db信息 db_monitor
					monitorpack = pickle.dumps(db_monitor_info)
					transdata.senddataforserver(conn,monitorpack) 

				elif get_type == 3: #获取所有集群信息  cluster_monitor
					monitorpack = pickle.dumps(cluster_monitor_info)
					transdata.senddataforserver(conn,monitorpack) 

				elif get_type == 4: #获取 指定mysql实例的 status 信息 只读取一次. 没得持续发送,没得websocket
					mysql_port = int.from_bytes(PACK[2:4],'big')
					mysql_host = socket.inet_ntoa(PACK[4:8])
					starttimestamp = int.from_bytes(PACK[8:12],'big')
					startdate = datetime.datetime.fromtimestamp(starttimestamp)
					rows = int.from_bytes(PACK[12:16],'big')
					monitorpack = eiwork.readdata(self.conf,mysql_host,mysql_port,startdate,rows)
					transdata.senddataforserver(conn,monitorpack) 

				elif get_type == 5: #获取所有task信息(不含详情)
					monitorpack = pickle.dumps(self.task_dict)
					transdata.senddataforserver(conn,monitorpack) 

				elif get_type == 6: #获取指定task的详情 懒得去判断是否存在了...
					task_name = int.from_bytes(PACK[2:6],'big')
					monitorpack = pickle.dumps(task_dict[task_name])
					transdata.senddataforserver(conn,monitorpack)

				else:
					sendpack = COMMAND.EI_FAILED.to_bytes(1,'big') + int(0).to_bytes(31,'big')
					conn.send(sendpack)

			elif ACTION == COMMAND.EI_ADD:
				add_type = int.from_bytes(PACK[1:2],'big')
				pack_size = int.from_bytes(PACK[2:6],'big')
				specical_col = int.from_bytes(PACK[6:7],'big') #特殊字段, 辅助判断的
				_data = conn.recv(pack_size) #添加的信息(没限制大小, 所有前端那边限制下 其实也不多,不限制也没啥),
				data = pickle.loads(_data)
				data['create'] = datetime.datetime.now()
				data['last_update'] = datetime.datetime.now()
				if add_type == 1: #添加主机实例(懒得去判断是否存在了,是否强制添加了, 直接账号密码不对就不添加)
					host_name = f"{data['host']}_{data['port']}"
					filename = f'{self.conf["DATADIR"]}/host.obj'
					self.log.info(host_name)
					if specical_col == 1: #删除 想不到吧,删除是在这里, 我也没想到,只是不想写了...
						try:
							del self.host_dict[host_name]
							del host_monitor_info[host_name]
							flush_with_pickle(self.host_dict,filename)
							conn.send(COMMAND.EI_OK.to_bytes(1,'big'))
						except:
							conn.send(COMMAND.EI_FAILED.to_bytes(1,'big'))
					elif specical_col == 2: #强制添加(不判断连接是否成功)
						try:
							self.host_dict[host_name] = data
							flush_with_pickle(self.host_dict,filename)
							conn.send(COMMAND.EI_OK.to_bytes(1,'big'))
						except Exception as e:
							self.log.error(e)
							conn.send(COMMAND.EI_FAILED.to_bytes(1,'big'))
					elif specical_col == 3: #账号密码正确才添加
						hostinstance = ddcw_ssh.set(host=data['host'], port=data['port'], user=data['user'], password=data['password'])
						if hostinstance.test():
							self.host_dict[host_name] = data
							flush_with_pickle(self.host_dict,filename)
							conn.send(COMMAND.EI_OK.to_bytes(1,'big'))
						else:
							conn.send(COMMAND.EI_FAILED.to_bytes(1,'big'))
					else:
						conn.send(COMMAND.EI_FAILED.to_bytes(1,'big'))

				elif add_type == 2: #添加db信息
					host_name = f"{data['host']}_{data['port']}"
					filename = f'{self.conf["DATADIR"]}/db.obj'
					if specical_col == 1: #删除 想不到吧,删除是在这里, 我也没想到,只是不想写了...
						try:
							del self.db_dict[host_name]
							del db_monitor_info[host_name] #别忘了删除monitor的
							flush_with_pickle(self.db_dict,filename)
							conn.send(COMMAND.EI_OK.to_bytes(1,'big'))
						except:
							conn.send(COMMAND.EI_FAILED.to_bytes(1,'big'))
					elif specical_col == 2: #强制添加(不判断连接是否成功)
						try:
							self.db_dict[host_name] = data
							flush_with_pickle(self.db_dict,filename)
							conn.send(COMMAND.EI_OK.to_bytes(1,'big'))
						except:
							conn.send(COMMAND.EI_FAILED.to_bytes(1,'big'))
					elif specical_col == 3:
						dbinstance = ddcw_mysql.set(host=data['host'], port=data['port'], user=data['user'], password=data['password'])
						if dbinstance.test():
							self.db_dict[f"{data['host']}_{data['port']}"] = data
							flush_with_pickle(self.db_dict,filename)
							conn.send(COMMAND.EI_OK.to_bytes(1,'big'))
						else:
							conn.send(COMMAND.EI_FAILED.to_bytes(1,'big'))
					else:
						conn.send(COMMAND.EI_FAILED.to_bytes(1,'big'))
	

				elif add_type == 3: #添加集群信息
					conn.send(COMMAND.EI_TODO.to_bytes(1,'big'))
				else:
					conn.send(COMMAND.EI_TODO.to_bytes(1,'big'))
				

			elif ACTION == COMMAND.EI_CLOSE:
				try:
					conn.send(COMMAND.EI_CLOSE.to_bytes(1,'big'))
				except:
					pass
				break
					


			elif ACTION == 0x00:
				break #client gg 了
			else:
				msg = f'Unknown action {ACTION}'
				self.log.error(msg)
				try:
					conn.send(COMMAND.EI_UNKNOWN.to_bytes(1,'big'))
				except Exception as e:
					self.log.warning(e)
					break
		self.close_client(host_port)



	def start(self,):
		self.set_daemon()
		logfilename = self.conf['SERVER_LOG']
		fmt = '%(asctime)s %(levelname)s %(message)s'
		logging.basicConfig(level=logging.INFO,format=fmt,filename=logfilename)
		log = logging.getLogger('eiserverlog')

		#初始化连接池之类的
		self.conn_pool = {}
		self.host = self.conf['HOST']
		self.port = self.conf['PORT']
		self.listens = self.conf['LISTENS']
		self.log = log
		self.rfd = {} #读的fd dict #cleaner也会定期来清理.{host_port_date:[lastaccess,fd]}


		#SQLite objects created in a thread can only be used in that same thread
		#打开本地数据库  db_host, db_db, db_cluster, db_monitor, db_task
		#db_conn = {}
		#db_conn['db_host'] = sqlite3.connect(f'{self.conf["DATADIR"]}/host.db')
		#db_conn['db_db'] = sqlite3.connect(f'{self.conf["DATADIR"]}/db.db')
		#db_conn['db_cluster'] = sqlite3.connect(f'{self.conf["DATADIR"]}/cluster.db')
		#db_conn['db_monitor'] = sqlite3.connect(f'{self.conf["DATADIR"]}/monitor.db')
		#db_conn['db_task'] = sqlite3.connect(f'{self.conf["DATADIR"]}/task.db')
		#self.db_conn = db_conn #查询的时候需要

		#读取host,db的账号密码信息(Key:host_port, Value:host,port,user,password)
		global host_dict,db_dict,cluster_dict,task_dict
		host_dict_filename = f'{self.conf["DATADIR"]}/host.obj'
		db_dict_filename = f'{self.conf["DATADIR"]}/db.obj'
		cluster_dict_filename = f'{self.conf["DATADIR"]}/cluster.obj'
		task_dict_filename = f'{self.conf["DATADIR"]}/task.obj'
		if os.path.exists(host_dict_filename):
			with open(host_dict_filename,'rb') as _f:
				host_dict = pickle.load(_f)
		else:
			host_dict = {}
		if os.path.exists(db_dict_filename):
			with open(db_dict_filename,'rb') as _f:
				db_dict = pickle.load(_f)
		else:
			db_dict = {}
		if os.path.exists(cluster_dict_filename):
			with open(cluster_dict_filename,'rb') as _f:
				cluster_dict = pickle.load(_f)
		else:
			cluster_dict = {}
		if os.path.exists(task_dict_filename):
			with open(task_dict_filename,'rb') as _f:
				task_dict = pickle.load(_f)
		else:
			task_dict = {}

		self.host_dict = host_dict
		self.db_dict = db_dict
		self.cluster_dict = cluster_dict
		self.task_dict = task_dict
		#监控信息(只有最新的, 所以直接存内存了...)
		global host_monitor_info, db_monitor_info,cluster_monitor_info
		host_monitor_info = {}
		db_monitor_info = {}
		cluster_monitor_info = {}

		global fd_dict #writer 打开的fd, 其实连接线程自己管理自己需要的fd更方便...
		fd_dict = {}
		qdata = Queue() #trans_client发过来的监控数据的队列.
		self.qdata = qdata

		#CLEANER
		P_cleaner = Thread(target=cleaner,args=(self.conf,fd_dict,log),daemon=True) #daemon = True 主线程挂了会拉着子进程一起去世
		P_cleaner.start()

		#WRITER
		P_writer = {}
		for x in range(0,self.conf['WRITER']):
			fd_dict[x] = {}
			#msg = f'will start writer {x}'
			#log.info(msg)
			P_writer[x] = Thread(target=writer,args=(self.conf,qdata,fd_dict,log,x),daemon=True)
		for x in range(0,self.conf['WRITER']):
			P_writer[x].start()
			#msg = f'start writer {x} done'
			#log.info(msg)


		#P_update = Thread(target=eiwork.update,args=(self.conf,log,db_conn),daemon=True)
		#P_update.start()
		P_monitor = Thread(target=eiwork.monitor,args=(self.conf,log,host_dict,db_dict,cluster_dict,host_monitor_info,db_monitor_info,cluster_monitor_info),daemon=True)
		P_monitor.start() #定时更新监控信息

		#WORK_SUB 负责写task进数据库的... 单线程
		#db_queue = Queue()
		#P_worksub = Thread(target=eiwork.worksub,args=(self.conf,db_queue,log,db_conn),daemon=True)
		#P_worksub.start()

		#WORKER
		task_queue = Queue()
		self.task_queue = task_queue
		P_worker = {}
		for x in range(0,self.conf['WORKER']):
			P_worker[x] = Thread(target=eiwork.worker,args=(self.conf,task_queue,task_dict,log,x),daemon=True)
		for x in range(0,self.conf['WORKER']):
			P_worker[x].start()
			

		#SERVER
		try:
			socket_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			socket_server.bind((self.host, self.port)) #绑定端口
			socket_server.listen(self.listens) #监听
			self.socket_server = socket_server
		except Exception as e:
			log.error(e)
			self.error = e

		accept_client_thread = Thread(target=self.accept_client,daemon=True)
		accept_client_thread.start()
		accept_client_thread.join() #


def cleaner(conf,fd_dict,log): #fd_dict {p0:{fd1:xxx, fd2:xxx}}
	msg = f'cleaner start.'
	log.info(msg)
	while True:
		for p,pd in fd_dict.items():
			for fdname,d_f in pd.items():
				timediff = datetime.datetime.now() - d_f[0]
				#关闭超过1小时的fd
				if timediff.total_seconds() > 3600:
					try:
						os.close(d_f[1])
						msg = f'close fd {fdname}'
						log.info(msg)
						del fd_dict[p][fdname]
					except Exception as e:
						msg = f'{e} {type(d_f[1])}'
						log.error(msg)
				
		time.sleep(60)

def writer(conf, qdata, fd_dict, log, p): #qdata Queue    p:process_n
	msg = f'writer {p} start.'
	log.info(msg)
	flushs = 1
	while True:
		ddata = qdata.get()
		bdata = ddata['data']
		if bdata[0:4] == b'\x00\x00\x00\x00':
			continue
		host = ddata['host']
		port = ddata['port']
		itime = datetime.datetime.fromtimestamp(int.from_bytes(bdata[0:4],'big'))
		fdname = f'{host}_{port}_{itime.year}_{itime.month}_{itime.day}'
		if fdname in fd_dict[p]:
			fd = fd_dict[p][fdname][1]
			fd_dict[p][fdname][0] = datetime.datetime.now()
		else:
			filename = f"{conf['MONITORDIR']}/{host}_{port}_{itime.year}_{itime.month:02}_{itime.day:02}.data"
			fd = os.open(filename, os.O_RDWR|os.O_CREAT, 0o644)
			fd_dict[p][fdname] = [datetime.datetime.now(),fd]
		offset = (itime.hour*3600 + itime.minute*60 + itime.second) * 1024
		os.lseek(fd, offset, 0)
		os.write(fd, bdata)
		if conf['FLUSH_SYNC'] == flushs:
			os.fsync(fd)
			flushs = 1
		else:
			flushs += 1


