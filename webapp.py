from flask import url_for,Flask,request,redirect,send_file, render_template
import flask_login
import os
from gevent import pywsgi
import socket
import logging
from mysql_agent import COMMAND
import json
import pickle
import datetime
from mysql_agent import mysql_status_pack
import configparser
import ddcw_ssh
import random

def get_host_info_for_mysql(data):
	port = 3306
	mem = 0
	status = False
	msg = ''
	host_instance = ddcw_ssh.set(host=data['host'],port=data['port'],user=data['user'],password=data['password'])
	if host_instance.test()['status']: #懒得去返回错误信息了
		host_instance.set()
		mem = host_instance.get_result_dict("""cat /proc/meminfo | awk  '{ if ( $1 == "MemTotal:") print $2}'""")['stdout'],
		conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		for x in range(100):
			try:
				conn.connect((data['host'],port))
				port += 2
			except:
				break
		host_instance.close()
		status = True
	return {'port':port,'status':status,'mem':mem,'msg':msg}

def recv_data(conn,PACK):
	PACK_MAX_SIZE = int.from_bytes(PACK[1:5],'big')
	ROWS = int.from_bytes(PACK[5:9],'big')
	LENGTH = int.from_bytes(PACK[9:13],'big')
	LASTPACK_SIZE = int.from_bytes(PACK[13:17],'big')
	BDATA = b''
	for x in range(ROWS):
		BDATA += conn.recv(PACK_MAX_SIZE)
	if LASTPACK_SIZE > 0:
		BDATA += conn.recv(LASTPACK_SIZE)
	conn.send(COMMAND.EI_OK.to_bytes(1,'big'))
	return BDATA

def remove_password_and_to_list(old_data):
	data = []
	for k,v in old_data.items():
		v['password'] = ''
		data.append(v)
	return data


class testweb:
	def __init__(self,conf):
		self.conf = conf

		#初始化log
		logfilename = self.conf['LOG']
		fmt = '%(asctime)s %(levelname)s %(message)s'
		logging.basicConfig(level=logging.INFO,format=fmt,filename=logfilename)
		log = logging.getLogger('eidatalog')
		self.log = log

	def connect(self):
		HOST = self.conf['HOST']
		PORT = self.conf['PORT']
		#初始化server连接 #server挂了之后, 只有重启web
		conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			conn.connect((HOST,PORT))
			if conn.send(COMMAND.EI_AUTH.to_bytes(1,'big') + int(1).to_bytes(2,'big') + self.conf["AUTHKEY"]) == 1024:
				if int.from_bytes(conn.recv(1),'big') == COMMAND.EI_OK:
					self.log.info('Connect Server Succeeded.')
					self.conn = conn
					return True
				else:
					msg = f'Login Failed. Server Host:{HOST} Server Port:{PORT}'
					self.log.error(msg)
					return False
			else:
				self.log.error('SEND AUTHKEY FAILED.')
				return False
		except Exception as e:
			msg = f'transclient Connect Server Faild. {e}'
			self.log.error(msg)
			return False


	def run(self,*args,**kwargs):

		_conn = self.conn
		log = self.log
		conf = self.conf
		
		app = Flask('app')
		#app.config['JSON_AS_ASCII'] = False #返回中文问题
		app.secret_key = 'test'
	
		login_manager = flask_login.LoginManager()
		login_manager.init_app(app)
		users = {str(self.conf['WEB_ADMIN']):str(self.conf['WEB_PASSWORD'])}

		class User(flask_login.UserMixin,):
			pass

		@login_manager.user_loader
		def user_loader(username):
			if username not in users:
				return
			user = User()
			user.id = username
			return user
		@login_manager.request_loader
		def request_loader(request):
			username = request.form.get('username')
			if username not in users:
				return
			user = User()
			user.id = email
			return user

		@login_manager.unauthorized_handler
		def unauthorized_handler():
			return '未登录... <a href="login">点此登录</a>', 401

		@app.route('/logout')
		def logout():
			flask_login.logout_user()
			return 'Logged out'

		@app.route('/login', methods=['GET', 'POST'])
		def login():
			if request.method == 'GET':
				return app.send_static_file('login.html')
			username = request.form['username']
			#print(users[username],)
			if username in users and request.form['password'] == users[username]:
				user = User()
				user.id = username
				flask_login.login_user(user)
				return redirect(url_for('index'))
			return 'Bad login( may be user and password not match)'
		
		@app.route('/')
		@flask_login.login_required
		def index():
			#return app.send_static_file('index.html')
			return render_template('index.html')
		@app.route('/test')
		def test():
			#return render_template('test.html')
			return app.send_static_file('index.html')

		@app.route('/install')
		@flask_login.login_required
		def install1():
			return render_template('install.html')

		@app.route('/conf')
		@flask_login.login_required
		def conf1():
			return render_template('conf.html')

		@app.route('/monitor')
		@flask_login.login_required
		def monitor1():
			return render_template('monitor.html')

		@app.route('/tool')
		@flask_login.login_required
		def tool1():
			return render_template('tool.html')

		@app.route('/task')
		@flask_login.login_required
		def task1():
			return render_template('task.html')

		@app.route('/set')
		@flask_login.login_required
		def set1():
			return render_template('set.html')

		@app.route('/api/<api_action>',methods=['POST','GET'])
		@flask_login.login_required
		def api(api_action):
			if api_action != 'mysql_status':
				_data = request.get_data().decode()
				_data_dict = json.loads(_data) #懒得去校验了.
				obj = _data_dict['obj']
				data = _data_dict['data']
				log.info(_data_dict)
			#bdata = pickle.dumps(data)
			if api_action == 'add': #添加host,mysql
				sendpack = COMMAND.EI_ADD.to_bytes(1,'big')
				if obj == 'addhost':
					sendpack += int(1).to_bytes(1,'big')
				elif obj == 'adddb':
					sendpack += int(2).to_bytes(1,'big')
				elif obj == 'addcluster': #集群的信息需要单独发包, 后面再写
					sendpack += int(3).to_bytes(1,'big')
				else:
					return {'status':False,'data':'unknown'}
				bdata = pickle.dumps(data)
				sendpack += len(bdata).to_bytes(4,'big') #下个包大小
				sendpack += int(2).to_bytes(1,'big') #强制添加
				sendpack += int(0).to_bytes(25,'big') #填充字段(一共32字节)

				IS_OK = False
				CLIENT_MSG = ''
				if _conn.send(sendpack) == 32:
					if _conn.send(bdata) == len(bdata):
						_recv_data = _conn.recv(1)
						if int.from_bytes(_recv_data[0:1],'big') == COMMAND.EI_OK:
							IS_OK = True
							CLIENT_MSG = 'add success.'
						else:
							CLIENT_MSG = 'add failed.'
				return {'status':IS_OK,'data':CLIENT_MSG}
			elif api_action == 'del':
				sendpack = COMMAND.EI_ADD.to_bytes(1,'big') #没想到吧,删除也是走EI_ADD, 我也没想到..
				sendpack += int(obj).to_bytes(1,'big') #懒得去校验obj是不是1-2了
				bdata = pickle.dumps(data)
				sendpack += len(bdata).to_bytes(4,'big') #下个包大小
				sendpack += int(1).to_bytes(1,'big') #强制添加
				sendpack += int(0).to_bytes(25,'big') #填充字段(一共32字节)
				if _conn.send(sendpack) == 32:
					if _conn.send(bdata) == len(bdata):
						_recv_data = _conn.recv(1)
						if int.from_bytes(_recv_data[0:1],'big') == COMMAND.EI_OK:
							return {'status':True,'data':''}
						else:
							return {'status':False,'data':'server delete faild'}
					else:
						return {'status':False,'data':'send pack faild'}
				else:
					return {'status':False,'data':'send action pack faild'}


			elif api_action == "get": #获取host,mysql
				if obj == 'host':
					sendpack = COMMAND.EI_GET.to_bytes(1,'big') + int(1).to_bytes(1,'big') + int(0).to_bytes(30,'big')
				elif obj == 'db':
					sendpack = COMMAND.EI_GET.to_bytes(1,'big') + int(2).to_bytes(1,'big') + int(0).to_bytes(30,'big')
				elif obj == 'task':
					sendpack = COMMAND.EI_GET.to_bytes(1,'big') + int(5).to_bytes(1,'big') + int(0).to_bytes(30,'big')
				else:
					return {'status':False,'data':'unknown'}
				if _conn.send(sendpack) == 32:
					_recv_data = _conn.recv(32)
					status = int.from_bytes(_recv_data[0:1],'big')
					if status == COMMAND.EI_OK:
						bdata = recv_data(_conn,_recv_data)
						data = pickle.loads(bdata)
						print('recvdata: ',data)
						data = remove_password_and_to_list(data)
						return {'status':True,'data':data}
					else:
						return {'status':False,'data':'server faild'}
				else:
						return {'status':False,'data':'send faild'}
			elif api_action == "delete": #删除某个实例
				pass
			elif api_action == "mysql_status": #查看mysql_status
				mysql_host = request.args.get('mysql_host')
				mysql_port = request.args.get('mysql_port')
				sendpack = COMMAND.EI_GET.to_bytes(1,'big')
				sendpack += int(4).to_bytes(1,'big')
				sendpack += int(mysql_port).to_bytes(2,'big')
				sendpack += socket.inet_aton(mysql_host)
				sendpack += int((datetime.datetime.now() + datetime.timedelta(minutes=-30)).timestamp()).to_bytes(4,'big')
				sendpack += int(600).to_bytes(4,'big')
				sendpack += int(0).to_bytes(16,'big')
				if _conn.send(sendpack) == 32:
					_recv_data = _conn.recv(32)
					status = int.from_bytes(_recv_data[0:1],'big')
					if status == COMMAND.EI_OK:
						bdata = recv_data(_conn,_recv_data)
						_mysql_status_dict = {}
						_mysql_status_dict['Queries'] = [] #这种事情本来该浏览器做的
						_mysql_status_dict['Bytes_received'] = []
						_mysql_status_dict['Bytes_sent'] = []
						_mysql_status_dict['itime'] = []

			
						for x in range(int(len(bdata)/1024)):
							if bdata[x*1024:x*1024+1024][0:4] == b'\x00\x00\x00\x00':
								continue
							else:
								_tdata = mysql_status_pack.mysql_status_unpack(bdata[x*1024:x*1024+1024])
								_mysql_status_dict['Queries'].append(_tdata['Queries'])
								_mysql_status_dict['Bytes_received'].append(_tdata['Bytes_received'])
								_mysql_status_dict['Bytes_sent'].append(_tdata['Bytes_sent'])
								_mysql_status_dict['itime'].append(_tdata['itime'])

								#_mysql_status_list.append(mysql_status_pack.mysql_status_unpack(bdata[x*1024:x*1024+1024]))
						return render_template('mysql_status.html',data=_mysql_status_dict)
					else:
						return {'status':False,'data':'server faild','len':0}

				else:
					return {'status':False,'data':'send faild','len':0}
			elif api_action == "task": #task日志
				pass
			elif api_action == "install_mysql_1": #根据主机信息获取mysql安装需要的信息的(再根据模板计算相应的值返回前端)
				#获取主机信息和返回参数由web来做, server只负责安装的task 本来也该server做的, 不能保证web能访问的server也能访问, 但是懒得去整了....
				mysql_config = configparser.ConfigParser()
				mysql_config.read(conf['MYSQL_CNF_FILE'])
				host_info = get_host_info_for_mysql(data) #主要是返回可用端口, 和内存, 磁盘之类的懒得整了

				if host_info['status']:
					innodb_mem = str(int(int(host_info['mem'][0])*0.8))
					mysql_port = host_info['port']
					mysql_config['mysqld']['basedir'] = f'/data/mysql_{mysql_port}/mysqlbase/mysql'
					mysql_config['mysqld']['datadir'] = f'/data/mysql_{mysql_port}/mysqldata'
					mysql_config['mysqld']['innodb_data_home_dir'] = f'/data/mysql_{mysql_port}/mysqldata'
					mysql_config['mysqld']['port'] = str(mysql_port)
					mysql_config['mysqld']['socket'] = f'/data/mysql_{mysql_port}/run/mysql.sock'
					mysql_config['mysqld']['pid_file'] = f'/data/mysql_{mysql_port}/run/mysql.pid'
					mysql_config['mysqld']['server_id'] = f'{int(random.uniform(1, 42948))}{mysql_port}'
					mysql_config['mysqld']['tmpdir'] = f'/data/mysql_{mysql_port}/mysqllog/tmp'
					mysql_config['mysqld']['log_error'] = f'/data/mysql_{mysql_port}/mysqllog/dblogs/mysql.err'
					mysql_config['mysqld']['slow_query_log_file'] = f'/data/mysql_{mysql_port}/mysqllog/dblogs/slow.log'
					mysql_config['mysqld']['general_log_file'] = f'/data/mysql_{mysql_port}/mysqllog/dblogs/general.log'
					mysql_config['mysqld']['log_bin'] = f'/data/mysql_{mysql_port}/mysqllog/binlog/m{mysql_port}'
					mysql_config['mysqld']['innodb_log_group_home_dir'] = f'/data/mysql_{mysql_port}/mysqllog/redolog'
					mysql_config['mysqld']['innodb_buffer_pool_size'] = innodb_mem #懒得去取整了
					mysql_config['mysqld']['relay_log'] = f'/data/mysql_{mysql_port}/mysqllog/relay/relay.log'
					return {'status':True,'data':dict(mysql_config['mysqld'])}
				else:
					return {'status':False,'data':host_info['msg']}

				pass
			elif api_action == "install_mysql_2": #安装mysql, 返回taskname , 前端根据 taskname去获取详情(懒得整websocket了)
				#懒得解包了,直接把data发过去...
				sendpack = COMMAND.EI_TASK.to_bytes(1,'big')
				sendpack += int(1).to_bytes(1,'big') #1:安装mysql
				bdata = pickle.dumps(data)
				sendpack += len(bdata).to_bytes(4,'big')
				sendpack += int(0).to_bytes(26,'big') #填充数据
				if _conn.send(sendpack) == 32:
					if _conn.send(bdata) == len(bdata):
						_recv_data = _conn.recv(32)
						status = int.from_bytes(_recv_data[0:1],'big')
						if status == COMMAND.EI_OK:
							return {'status':True,'data':int.from_bytes(_recv_data[1:4],'big')}
						else:
							return {'status':False, 'data':'create task faild.'}
					else:
						return {'status':False,'data':'send  data faild'}
						
				else:
					return {'status':False,'data':'send faild'}
						
				pass
			else:
				return {'status':False,'data':'unknown'}

		app.debug = True
		return app
		#server = pywsgi.WSGIServer((self.conf['WEB_HOST'], self.conf['WEB_PORT']), app)
		#server.serve_forever()
