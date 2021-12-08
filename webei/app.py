import configparser
import os
import paramiko
from flask import Flask , redirect, url_for, request,render_template,make_response,session
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
import sqlite3
from flask import g
from flask_sockets import Sockets
import time
import datetime
import random
import logging
import pymysql

DATABASE="ei.db"

#定义全局变量
DEFAULT_CONFIG_FILE = "conf/ei.conf"

#获取配置文件参数
config = configparser.ConfigParser()
config.read(DEFAULT_CONFIG_FILE)

EI_WEB_PORT = config.get('ei','port')
EI_WEB_ADDRESS = config.get('ei','address')
EI_WEB_DEBUG = config.get('ei','debug')

app = Flask(__name__)
sockets = Sockets(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ei.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.secret_key = "20210608 1533 6121"
#app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
db = SQLAlchemy(app)

class User(db.Model):
	__tablename__ = 'user'
	id = db.Column('id',db.Integer, primary_key = True)
	username = db.Column('username',db.String(32))
	password = db.Column('password',db.String(200))
	status = db.Column('status',db.Integer)


@app.route('/index')
def index():
	if 'username' in session:
		username = session['username']
		sql_db_instance = 'select db_instance_name, db_type, db_host, db_port, status from ei_db where db_author = "' + username + '"'
		sql_host_instance = 'select host_instance_name,host_type,host_version,host_ssh_ip,host_ssh_port,status from ei_host where host_author = "' + username + '"'
		try:
			items_db = db.session.execute(sql_db_instance)
			items_host = db.session.execute(sql_host_instance)
			db_norm = list(db.session.execute('select count(db_instance_name) from ei_db where db_author = "' + username + '" and status = 0'))[0][0]
			db_warn = list(db.session.execute('select count(db_instance_name) from ei_db where db_author = "' + username + '" and status = 1'))[0][0]
			db_error = list(db.session.execute('select count(db_instance_name) from ei_db where db_author = "' + username + '" and status = 2'))[0][0]
			db_un = list(db.session.execute('select count(db_instance_name) from ei_db where db_author = "' + username + '" and status not in (0,1,2)'))[0][0]
			host_norm = list(db.session.execute('select count(host_instance_name) from ei_host where host_author = "' + username + '" and status = 0'))[0][0]
			host_warn = list(db.session.execute('select count(host_instance_name) from ei_host where host_author = "' + username + '" and status = 1'))[0][0]
			host_error = list(db.session.execute('select count(host_instance_name) from ei_host where host_author = "' + username + '" and status = 2'))[0][0]
			host_un = list(db.session.execute('select count(host_instance_name) from ei_host where host_author = "' + username + '" and status not in (0,1,2)'))[0][0]
		except:
			items_db="NO DB CONFIG, you can add db"
			items_host="NO HOST, you can add host"
		return render_template('index.html',username=username, db_list=list(items_db), host_list=list(items_host), db_norm = db_norm, db_warn = db_warn, db_error = db_error, db_un = db_un, host_norm = host_norm, host_warn = host_warn, host_error = host_error, host_un = host_un)
	return  redirect(url_for('login'))

@app.route('/')
def default_index():
	#return	app.send_static_file('index.html')
	#return render_template('index.html',username=username)
	return redirect(url_for('index'))


@sockets.route('/echo')
def echo_socket(ws):
	while not ws.closed:
		now = datetime.datetime.now().isoformat() + 'Z'
		ws.send(now)
		time.sleep(1)

@app.route('/login',methods = ['POST','GET'])
def login():
	error = None
	if request.method == 'POST':
		sql_exec = 'select password from user where username = "' + request.form['username'] + '"'
		try:
			items = db.session.execute(sql_exec)
			password = list(items)[0][0]
			need_to_password = request.form['password']
			if password == need_to_password:
				resp = make_response("success")
				session['username'] = request.form['username']
				resp.set_cookie("flaskkey","falskkey",max_age=3600)
				return redirect(url_for('index'))
			else:
				error =  "Invalid username or password , Please try again"
		except:
			error = "用户名/密码错了"
	return render_template('/auth/login.html',error = error)

@app.route('/logout')
def logout():
	session.pop('username',None)
	return redirect('index')

@app.route('/register')
def register():
	return "暂不支持注册!"


@app.route('/modifypassword',methods = ['POST','GET'])
def modifypassword():
	error = None
	if request.method == 'POST':
		username = session['username']
		sql_exec1 = 'select password from user where username = "' + username + '"'
		password_old = request.form['password_old']
		password_new = request.form['password_new']
		sql_exec2 = 'update user set password="' + password_new + '" where username="' + username + '" and password="' + password_old + '";'
		try:
			items = db.session.execute(sql_exec1)
			password = list(items)[0][0]
			if password == password_old:
				try:
					items2 = db.session.execute(sql_exec2)
					db.session.execute("commit;")
					flash('修改成功')
				except:
					error = "修改密码失败"
			else:
				error =  "Invalid username or password , Please try again"
		except:
			error = "用户名/密码错了"
	return render_template('index.html',error = error, username = username)


@app.route('/api/database/mysql', methods = ['POST','GET'])
def api_db_mysql():
	if request.method == 'GET':
		username=request.args.get("usr_name")
		scriptname = request.args.get("scriptname")
		com_str = 'sh scripts/' + scriptname + ' ' + username 
		value = os.popen(com_str).read()
	elif request.method == 'POST':
		username=request.form['user_name']
	return value
		

@app.route('/adddb', methods = ['POST','GET'])
def add_db_instance():
	error = None
	if 'username' in session:
		dbtype = request.args.get("dbtype")
		if dbtype == "mysql":
			username = session['username']
			instance_name = request.form['instance_name']
			mysql_host = request.form['mysql_host']
			mysql_port = request.form['mysql_port']
			mysql_user = request.form['mysql_user']
			mysql_password = request.form['mysql_password']
			if len(instance_name) == 0:
				instance_name = "mysql_" + mysql_host + "_" + mysql_port
			sql_insert = 'insert into ei_db(db_author,db_instance_name,db_type,db_version,db_host,db_port,db_user,db_password,status) values("' + username + '","' + instance_name + '","'+ dbtype +'","NULL","'+ mysql_host +'",' + mysql_port + ',"' +mysql_user +'","' + mysql_password + '",4)'
			try:
				db.session.execute(sql_insert)
				db.session.execute("commit")
				message = "添加成功:" + instance_name
				return redirect('/index')
				return render_template('index.html', username = username, message = message)
			except:
				db.session.execute("rollback")
				error = "添加失败:" + instance_name
		else:
			error = "暂不支持其他添加数据库"
		
		return render_template('index.html',error = error, username = username)
	return redirect('/login')

@app.route('/addhost', methods = ['POST','GET'])
def add_host_instance():
	error = None
	if 'username' in session:
		username = session['username']
		instance_name = request.form['instance_name']
		host_host = request.form['host_host']
		host_port = request.form['host_port']
		host_user = request.form['host_user']
		host_password = request.form['host_password']
		if len(instance_name) == 0:
			instance_name = "Linux_" + host_host + "_" + host_port
		sql_insert = 'insert into ei_host(host_author,host_instance_name,host_type,host_version,host_ssh_ip,host_ssh_port,host_ssh_username,host_ssh_password,status) values("'+username+'","'+instance_name+'","xxxx","xx","'+host_host+'",'+host_port+',"'+host_user+'","'+host_password+'",4)'
		try:
			db.session.execute(sql_insert)
			db.session.execute("commit")
			message = "添加成功:" + instance_name
			return redirect('/index')
			return render_template('index.html', username = username, message = message)
		except:
			db.session.execute("rollback")
			error = "添加失败:" + instance_name
	return redirect('/login')

@app.route('/deldb', methods = ['POST','GET'])
def del_db_instance():
	error = None
	if 'username' in session:
		username = session['username']
		db_instance_list = request.form.getlist('del_instance')
		if len(db_instance_list):
			instance_name_str = '","'.join(db_instance_list)
			sql_del = 'delete from ei_db where db_author = "' + username + '" and db_instance_name in ("' + instance_name_str + '")'
			try:
				db.session.execute(sql_del)
				db.session.execute("commit")
				message = "删除成功" + ','.join(db_instance_list)
				return redirect('/index')
				return render_template('index.html', username = username, message = message)
			except:
				db.session.execute("rollback")
				error = "删除失败" + ','.join(db_instance_list)
		else:
			return "不能选择为空"
	return redirect('/login')


@app.route('/delhost', methods = ['POST','GET'])
def del_host_instance():
	error = None
	if 'username' in session:
		username = session['username']
		host_instance_list = request.form.getlist('del_instance_host')
		if len(host_instance_list):
			instance_name_str = '","'.join(host_instance_list)
			sql_del = 'delete from ei_host where host_author = "' + username + '" and host_instance_name in ("' + instance_name_str + '")'
			try:
				db.session.execute(sql_del)
				db.session.execute("commit")
				message = "删除成功" + ','.join(host_instance_list)
				return redirect('/index')
				return render_template('index.html', username = username, message = message)
			except:
				db.session.execute("rollback")
				error = "删除失败" + ','.join(host_instance_list)
		else:
			return "不能选择空"
	return redirect('/login')


@app.route('/db/mysql',methods = ['POST','GET'])
def monitor_db_mysql():
	error = None
	#result_mysql_variables = "bb"
	#return app.send_static_file('db/mysql.html')
	if 'username' in session:
		instance_name=request.args.get("instance_name")
		username = session['username']
		sql_info = 'select db_host,db_port,db_user,db_password from ei_db where db_author="' + username + '" and db_instance_name="' + instance_name + '" limit 1'
		try:
			items = list(db.session.execute(sql_info))
			mysql_host = list(items)[0][0]
			mysql_port = list(items)[0][1]
			mysql_user = list(items)[0][2]
			mysql_password = list(items)[0][3]
			conn_mysql = pymysql.connect(host=mysql_host, port=mysql_port, user=mysql_user, passwd=mysql_password)
			cursor_mysql = conn_mysql.cursor()
			sql_mysql_variables = "show variables;"
			sql_mysql_processlist = 'select ID,USER,HOST,DB,COMMAND,TIME,STATE,INFO from information_schema.processlist where command != "Sleep";'
			sql_mysql_user = 'select user,host,plugin,password_last_changed from mysql.user;'
			sql_mysql_db = 'select table_schema, concat(round(sum(data_length/1024/1024),2),"MB") as data_length_MB  , concat(round(sum(index_length/1024/1024),2),"MB") as index_length_MB from information_schema.tables where TABLE_SCHEMA not in ("test","sys","mysql","information_schema","performance_schema") group by table_schema order by 2,3;'
			sql_mysql_lock = 'select requesting_trx_id, requested_lock_id, blocking_trx_id, blocking_lock_id from information_schema.innodb_lock_waits;'
			sql_mysql_innodb_status = 'show engine innodb status'
			sql_mysql_NO_primary_key = 'select table_schema, table_name from information_schema.tables where table_name not in (select distinct table_name from information_schema.columns where column_key = "PRI") AND table_schema not in ("mysql", "performance_schema", "information_schema", "sys");'
			sql_mysql_total_table = "select count(TABLE_NAME) from information_schema.tables where TABLE_SCHEMA not in ('test','sys','mysql','information_schema','performance_schema') and TABLE_TYPE='BASE TABLE';"
			sql_mysql_total_size = " select round(sum(index_length + DATA_LENGTH)/1024/1024/1024,3) from information_schema.tables where TABLE_SCHEMA not in ('test','sys','mysql','information_schema','performance_schema');"
			sql_mysql_rep_index = "SELECT a.table_schema, a.table_name, a.index_name , b.index_name, a.column_name FROM information_schema.statistics a JOIN information_schema.statistics b ON a.table_schema = b.table_schema  AND a.table_name = b.table_name  AND a.seq_in_index = b.seq_in_index  AND a.column_name = b.column_name  WHERE a.seq_in_index = 1  AND a.index_name != b.index_name;"
			sql_mysql_no_index = "select TABLE_SCHEMA,TABLE_NAME from information_schema.tables where (table_schema,TABLE_NAME) not  in (select TABLE_SCHEMA,TABLE_NAME from information_schema.statistics) and  TABLE_SCHEMA not in ('test','sys','mysql','information_schema','performance_schema');"
			cursor_mysql.execute(sql_mysql_variables)
			result_mysql_variables = cursor_mysql.fetchall()
			cursor_mysql.execute(sql_mysql_processlist)
			result_mysql_processlist = cursor_mysql.fetchall()
			cursor_mysql.execute(sql_mysql_user)
			result_mysql_user = cursor_mysql.fetchall()
			cursor_mysql.execute(sql_mysql_db)
			result_mysql_db = cursor_mysql.fetchall()
			cursor_mysql.execute(sql_mysql_lock)
			result_mysql_lock = cursor_mysql.fetchall()
			cursor_mysql.execute(sql_mysql_innodb_status)
			result_mysql_innodb_status = cursor_mysql.fetchall()
			cursor_mysql.execute(sql_mysql_NO_primary_key)
			result_mysql_NO_primary_key = cursor_mysql.fetchall()
			cursor_mysql.execute(sql_mysql_total_table)
			result_mysql_total_table_count = cursor_mysql.fetchall()
			cursor_mysql.execute(sql_mysql_total_size)
			result_mysql_total_size = cursor_mysql.fetchall()
			cursor_mysql.execute(sql_mysql_rep_index)
			result_mysql_rep_index = cursor_mysql.fetchall()
			cursor_mysql.execute(sql_mysql_no_index)
			result_mysql_no_index = cursor_mysql.fetchall()

			#performance_shema.global_status库的结果, 但是这个库可能没有启用
			sql_qps = 'show global status like "Questions"'
			sql_tps_1 = 'show global status like "Com_commit"'
			sql_tps_2 = 'show global status like "Com_rollback"'
			cursor_mysql.execute(sql_qps)
			result_qps_s = cursor_mysql.fetchall()
			cursor_mysql.execute(sql_tps_1)
			result_tps_1_s = cursor_mysql.fetchall()
			cursor_mysql.execute(sql_tps_2)
			result_tps_2_s = cursor_mysql.fetchall()
			time.sleep(1)
			cursor_mysql.execute(sql_qps)
			result_qps_e = cursor_mysql.fetchall()
			cursor_mysql.execute(sql_tps_1)
			result_tps_1_e = cursor_mysql.fetchall()
			cursor_mysql.execute(sql_tps_2)
			result_tps_2_e = cursor_mysql.fetchall()
			mysql_qps = int(list(result_qps_e)[0][1]) - int(list(result_qps_s)[0][1])
			mysql_tps = int(list(result_tps_1_e)[0][1]) + int(list(result_tps_2_e)[0][1]) - int(list(result_tps_1_s)[0][1]) - int(list(result_tps_2_s)[0][1])
			

			cursor_mysql.close()
			conn_mysql.close()

			return render_template('db/mysql.html', instance_name = instance_name, error = error, mysql_var = result_mysql_variables, processlist = result_mysql_processlist, users = result_mysql_user, db = result_mysql_db, db_lock = result_mysql_lock, innodb = result_mysql_innodb_status, primary_key = result_mysql_NO_primary_key, tps = mysql_tps, qps = mysql_qps,total_table_count = result_mysql_total_table_count, db_total_size = result_mysql_total_size, rpl_index = result_mysql_rep_index,  no_index = result_mysql_no_index )
		except:
			error = "error"
			return str(instance_name) + " 该实例信息不对,账号/密码/端口/主机"
		return render_template('db/mysql.html', instance_name = instance_name, error = error, mysql_var="aaaa")
	return redirect('/login')

@app.route('/host',methods = ['POST','GET'])
def monitor_host():
	error = None
	#result_mysql_variables = "bb"
	#return app.send_static_file('db/mysql.html')
	if 'username' in session:
		instance_name=request.args.get("instance_name")
		username = session['username']
		sql_info = 'select host_ssh_ip,host_ssh_port,host_ssh_username,host_ssh_password from ei_host where host_author = "' + username + '" and host_instance_name = "' + instance_name + '"'
		try:
			items = list(db.session.execute(sql_info))
			host_host = list(items)[0][0]
			host_port = list(items)[0][1]
			host_ssh_username = list(items)[0][2]
			host_ssh_password = list(items)[0][3]
			ssh = paramiko.SSHClient()
			ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
			ssh.connect(hostname=host_host, port=host_port, username=host_ssh_username, password=host_ssh_password)
			stdin, stdout, stderr = ssh.exec_command("/usr/bin/head -1 /proc/stat | /usr/bin/awk '{print $2+$3+$4+$5+$6+$7+$8+$9+$(10),$5}'")
			time.sleep(0.1)
			cpu_b = stdout.read()
			stdin, stdout, stderr = ssh.exec_command("/usr/bin/head -1 /proc/stat | /usr/bin/awk '{print $2+$3+$4+$5+$6+$7+$8+$9+$(10),$5}'")
			cpu_e = stdout.read()
			cpu_total = int(cpu_e.split()[0]) - int(cpu_b.split()[0])
			cpu_idle = int(cpu_e.split()[1]) - int(cpu_b.split()[1])
			cpu_p = (cpu_total - cpu_idle ) / cpu_total
			cpu_p100 = round((cpu_total - cpu_idle ) / cpu_total * 100)


			stdin, stdout, stderr = ssh.exec_command("/usr/bin/grep MemTotal /proc/meminfo | /usr/bin/awk '{print $2}'")
			mem_total = stdout.read()
			stdin, stdout, stderr = ssh.exec_command("/usr/bin/grep MemAvailable /proc/meminfo | /usr/bin/awk '{print $2}'")
			mem_ali = stdout.read()
			mem_p = (int(mem_total) - int(mem_ali)) / int(mem_total)
			mem_p100 = round((int(mem_total) - int(mem_ali)) / int(mem_total) * 100)


			#stdin, stdout, stderr = ssh.exec_command("/usr/bin/df -P / | /usr/bin/tail -n +2 | /usr/bin/awk '{sub(/%/,"") ;{print $(NF-1)}'")
			stdin, stdout, stderr = ssh.exec_command("/usr/bin/df -P / | /usr/bin/tail -n +2 | /usr/bin/awk '{print $(NF-1)}' | /usr/bin/sed 's/%//'")
			root_dir_p100 = float(stdout.read())
			root_dir_p = round(float(root_dir_p100) / 100, 2)

			stdin, stdout, stderr = ssh.exec_command("/usr/bin/awk '{print $1,$2,$3}' /proc/loadavg")
			loadavg = stdout.readlines()[0].rstrip()


			stdin, stdout, stderr = ssh.exec_command("/usr/bin/wc -l /proc/net/tcp | /usr/bin/awk '{print $1-1}'")
			tcp4_sockets = int(stdout.read())
			stdin, stdout, stderr = ssh.exec_command("/usr/bin/wc -l /proc/net/tcp6 | /usr/bin/awk '{print $1-1}'")
			tcp6_sockets = int(stdout.read())

			stdin, stdout, stderr = ssh.exec_command("/usr/bin/cat /proc/uptime")
			uptime_res = stdout.read()
			uptime = round(float(uptime_res.split()[0])/60/60/24,2)
			cpu_p_total = round((float(uptime_res.split()[0]) - float(uptime_res.split()[1]))/float(uptime_res.split()[0])*100,3)

			stdin, stdout, stderr = ssh.exec_command("/usr/bin/w | /usr/bin/tail -n +3 | /usr/bin/wc -l")
			online_users = int(stdout.read())


			stdin, stdout, stderr = ssh.exec_command("/usr/bin/ps -ef | /usr/bin/grep mysqld | /usr/bin/grep -v mysqld_safe | /usr/bin/grep -v grep | /usr/bin/wc -l")
			mysql_server = int(stdout.read())
			stdin, stdout, stderr = ssh.exec_command("/usr/bin/ps -ef | /usr/bin/grep redis-server | /usr/bin/grep -v grep | /usr/bin/wc -l")
			redis_server = int(stdout.read())
			stdin, stdout, stderr = ssh.exec_command("/usr/bin/ps -ef | /usr/bin/grep ora_pmon_ | /usr/bin/grep -v grep | /usr/bin/wc -l")
			oracle_server = int(stdout.read())
			stdin, stdout, stderr = ssh.exec_command("/usr/bin/ps -ef | /usr/bin/grep nginx | /usr/bin/grep -v grep | /usr/bin/grep master | /usr/bin/wc -l")
			nginx_server = int(stdout.read())
			stdin, stdout, stderr = ssh.exec_command("/usr/bin/ps -ef | /usr/bin/grep php-fpm | /usr/bin/grep -v grep | /usr/bin/grep master | /usr/bin/wc -l")
			php_server = int(stdout.read())
			stdin, stdout, stderr = ssh.exec_command("/usr/bin/ps -ef | /usr/bin/grep haproxy | /usr/bin/grep -v grep | /usr/bin/awk '{$1="";$2="" ; print $0}' | /usr/bin/uniq | /usr/bin/wc -l")
			haproxy_server = int(stdout.read())

			stdin, stdout, stderr = ssh.exec_command("/usr/bin/grep -v '^#' /etc/sysctl.conf | /usr/bin/sed '/^$/d'")
			sysctl_parameter = stdout.readlines()


			stdin, stdout, stderr = ssh.exec_command("/usr/bin/systemctl status firewalld >/dev/null 2>&1 && /usr/bin/echo 'ON' || /usr/bin/echo 'OFF'")
			firewalld_status = str(stdout.read().rstrip())
			stdin, stdout, stderr = ssh.exec_command("/usr/sbin/getenforce")
			selinux_status = str(stdout.read().rstrip())

			stdin, stdout, stderr = ssh.exec_command("/usr/bin/grep -ri enabled=1 /etc/yum.repos.d/  2>/dev/null | /usr/bin/wc -l")
			yum_repo_count = int(stdout.read())

			stdin, stdout, stderr = ssh.exec_command("/usr/bin/uname -m")
			host_platform = str(stdout.read().rstrip())
			stdin, stdout, stderr = ssh.exec_command("/usr/bin/uname -r")
			kernel_version = str(stdout.read().rstrip())
			stdin, stdout, stderr = ssh.exec_command("/usr/bin/cat /proc/sys/kernel/hostname")
			host_name1 = str(stdout.read().rstrip())
			stdin, stdout, stderr = ssh.exec_command("/usr/bin/grep NAME= /etc/os-release | /usr/bin/head -1")
			os_name = str(stdout.read().rstrip())
			stdin, stdout, stderr = ssh.exec_command("/usr/bin/grep VERSION= /etc/os-release | /usr/bin/head -1")
			os_version1 = str(stdout.read().rstrip())
			os_version = os_name.split('"')[1] + " " + os_version1.split('"')[1]
			stdin, stdout, stderr = ssh.exec_command("/usr/bin/lscpu  | /usr/bin/grep 'Socket(s)' | /usr/bin/awk '{print $NF}'")
			cpu_sock = int(stdout.read().rstrip())
			stdin, stdout, stderr = ssh.exec_command("/usr/bin/lscpu  | /usr/bin/grep 'Core(s)' | /usr/bin/awk '{print $NF}'")
			cpu_core = int(stdout.read().rstrip())
			stdin, stdout, stderr = ssh.exec_command("/usr/bin/lscpu  | /usr/bin/grep 'Thread(s)' | /usr/bin/awk '{print $NF}'")
			cpu_thread = int(stdout.read().rstrip())
			cpu_count = cpu_sock * cpu_core * cpu_thread
			mem_total_MB = round( int(mem_total) / 1024 , 1 )
			stdin, stdout, stderr = ssh.exec_command("/usr/bin/grep SwapTotal /proc/meminfo | /usr/bin/awk '{print $2}'")
			swap_total = int(stdout.read())
			swap_total_MB = round( swap_total / 1024 , 1 ) 
			stdin, stdout, stderr = ssh.exec_command("/usr/bin/cat /proc/sys/vm/swappiness")
			swappiness = int(stdout.read())

			return render_template('host.html',username=username, instance_name=instance_name, cpu_p = cpu_p, cpu_p100 = cpu_p100, mem_p = mem_p, mem_p100 = mem_p100, root_dir_p = root_dir_p, root_dir_p100 = root_dir_p100, loadavg = loadavg, tcp4_sockets = tcp4_sockets, tcp6_sockets = tcp6_sockets, uptime = uptime, cpu_p_total = cpu_p_total, online_users = online_users , mysql_server = mysql_server, redis_server = redis_server, oracle_server = oracle_server, nginx_server = nginx_server, php_server = php_server, haproxy_server = haproxy_server, sysctl_parameter = sysctl_parameter, firewalld_status = firewalld_status, selinux_status = selinux_status, yum_repo_count = yum_repo_count, host_platform = host_platform, kernel_version = kernel_version, host_name = host_name1, os_version = os_version, cpu_sock = cpu_sock, cpu_core = cpu_core, cpu_thread = cpu_thread, cpu_count = cpu_count, mem_total_MB = mem_total_MB, swap_total_MB = swap_total_MB, swappiness = swappiness)
		except:
			return "失败,自己慢慢排查, 可能是实例有问题,也可能是连接有问题, 反正就是ei里面记录的账号问题"
		return render_template('host.html',username=username, instance_name=instance_name)
	return redirect('/login')
	


@app.route('/api/other/zookeeper_1')
def install_zookeeper_1():
	ssh = paramiko.SSHClient()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	if request.method == 'GET':
		host=request.args.get("host")
		rootpassword = request.args.get("rootpassword")
		zk_version = request.args.get("version")
	elif request.method == 'POST':
		host=request.form['host']

	ssh.connect(hostname=host, port=22, username='root', password=rootpassword)
	local_path_soft="software/other/zookeeper-"+zk_version+".tar.gz"
	local_path_script="scripts/zookeeper/ZK_PseudoCluster.sh"
	server_path_soft="/tmp/zookeeper-"+zk_version+".tar.gz"
	server_path_script="/tmp/ZK_PseudoCluster.sh"
	sftp_upload_file(server_path_soft,local_path_soft,host,rootpassword)
	sftp_upload_file(server_path_script,local_path_script,host,rootpassword)
	stdin, stdout, stderr = ssh.exec_command('sh /tmp/ZK_PseudoCluster.sh')
	value = stdout.read()
	ssh.close()
	return value
	
def sftp_upload_file(server_path, local_path, host, rootpassword):
	try:
		ts = paramiko.Transport((host,22))
		ts.connect(username="root", password=rootpassword)
		sftp = paramiko.SFTPClient.from_transport(ts)
		sftp.put(local_path, server_path)
		ts.close()
	except Exception as  e:
		print(e)



@app.route('/api/database/redis-single-instance')
def install_redis_single_instance():
	ssh = paramiko.SSHClient()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	if request.method == 'GET':
		host=request.args.get("host")
		rootpassword = request.args.get("rootpassword")
		redis_version = request.args.get("version")
	elif request.method == 'POST':
		host=request.form['host']

	#
	value='host: '+host+' rootpassword:'+rootpassword+' redis_version:'+redis_version
	ssh.connect(hostname=host, port=22, username='root', password=rootpassword)
	local_path_soft="scripts/redis/redis-5.0.5-update20201123.tar.gz"
	server_path_soft="/tmp/redis-5.0.5-update20201123.tar.gz"
	sftp_upload_file(server_path_soft,local_path_soft,host,rootpassword)
	stdin, stdout, stderr = ssh.exec_command('cd /tmp && tar -xf redis-5.0.5-update20201123.tar.gz && cd redis-5.0.5-update20201123 && sh installRedisStand.sh')
	value = stdout.read()
	ssh.close()
	return value

@app.route('/api/database/redis-PseudoCluster')
def install_redis_PseudoCluster():
	ssh = paramiko.SSHClient()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	if request.method == 'GET':
		host=request.args.get("host")
		rootpassword = request.args.get("rootpassword")
		redis_version = request.args.get("version")
	elif request.method == 'POST':
		host=request.form['host']

	#
	value='host: '+host+' rootpassword:'+rootpassword+' redis_version:'+redis_version
	ssh.connect(hostname=host, port=22, username='root', password=rootpassword)
	local_path_soft="scripts/redis/redis-5.0.5-update20201123.tar.gz"
	server_path_soft="/tmp/redis-5.0.5-update20201123.tar.gz"
	sftp_upload_file(server_path_soft,local_path_soft,host,rootpassword)
	stdin, stdout, stderr = ssh.exec_command('cd /tmp && tar -xf redis-5.0.5-update20201123.tar.gz && cd redis-5.0.5-update20201123 && sh installRedisPseudoCluster.sh')
	value = stdout.read()
	ssh.close()
	return value


@app.route('/api/database/mysql_single')
def install_mysql_single_instance():
	ssh = paramiko.SSHClient()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	if request.method == 'GET':
		host=request.args.get("host")
		rootpassword = request.args.get("rootpassword")
		mysql_version = request.args.get("version")
		mysql_port = request.args.get("port")
		mysql_password = request.args.get("mysqlpassword")
	elif request.method == 'POST':
		host=request.form['host']

	#
	value='host: '+host+' rootpassword:'+rootpassword+' redis_version:'+mysql_version
	ssh.connect(hostname=host, port=22, username='root', password=rootpassword)
	local_path_soft="software/mysql/mysql-"+mysql_version+"-linux-glibc2.12-x86_64.tar.gz"
	local_path_script="scripts/mysql/installMYSQL.sh"
	server_path_soft="/tmp/mysql-"+mysql_version+"-linux-glibc2.12-x86_64.tar.gz"
	server_path_script="/tmp/installMYSQL.sh"
	sftp_upload_file(server_path_soft,local_path_soft,host,rootpassword)
	sftp_upload_file(server_path_script,local_path_script,host,rootpassword)
	commd="cd /tmp && sh installMYSQL.sh version="+str(mysql_version)+" port="+str(mysql_port)+" password="+str(mysql_password)
	stdin, stdout, stderr = ssh.exec_command(commd)
	value = stdout.read()
	ssh.close()
	return value


if __name__ == '__main__':
    app.run(host=EI_WEB_ADDRESS, debug=EI_WEB_DEBUG, port=EI_WEB_PORT)
#if __name__ == "__main__":
#	from gevent import pywsgi
#	from geventwebsocket.handler import WebSocketHandler
#	server = pywsgi.WSGIServer(('', 6121), app, handler_class=WebSocketHandler)
#	print('server start')
#	server.serve_forever()
