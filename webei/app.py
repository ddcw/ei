import configparser
import os
import paramiko
from flask import Flask , redirect, url_for, request,render_template,make_response,session,send_file,jsonify
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
import sqlite3
from flask import g
from flask_sockets import Sockets
from flask_socketio import send, emit
import time
import datetime
import random
import logging
import pymysql
from flask_apscheduler import APScheduler
from threading import Lock
import subprocess
from werkzeug.utils import secure_filename
import json

DATABASE="ei.db"

#定义全局变量
DEFAULT_CONFIG_FILE = "conf/ei.conf"

#获取配置文件参数
config = configparser.ConfigParser()
config.read(DEFAULT_CONFIG_FILE)

EI_WEB_PORT = config.get('ei','port')
EI_WEB_ADDRESS = config.get('ei','address')
EI_WEB_DEBUG = config.get('ei','debug')
EI_HOST_INTERVALS_SECOND=config.get('ei','host_status_check_intervals')
EI_DB_INTERVALS_SECOND=config.get('ei','db_status_check_intervals')
EI_LOG = config.get('ei','log')
#EI_LOG_FORMAT = config.get('ei','log_format')
EI_LOG_FORMAT = "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"

app = Flask(__name__)
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()
#sockets = Sockets(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.secret_key = "20210608 1533 6121"
#app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
db = SQLAlchemy(app)

#socketio = SocketIO(app,cors_allowed_origins="*")
socketio = SocketIO(app)
thread = None
thread_lock = Lock()


@socketio.on('connect')
def socket_connection():
	#app.logger.info("someone connect: ", msg)
	app.logger.info("someone connect")

@socketio.on('disconnect')
def socket_connection():
	#app.logger.info("disconnect: ",msg)
	app.logger.info("someone disconnect")

#todo delete数据库后, 把系统上的日志 改名 加个后缀.rm  在调定时任务删除 .rm结尾的
@socketio.on('delete_task')
def delete_task(msg):
	if 'username' in session:
		username = session['username']
		task_name = str(msg['task_name'])
		evt_name = str(msg['evt_name'])
		del_task_sql = 'delete from ei_task where task_author="' + username + '" and task_name="' + task_name + '";'
		try:
			db.session.execute(del_task_sql)
			db.session.commit()
			return_message = {"status":0,"object_name":task_name,"opt":"删除任务成功: ","hide_id":task_name}
		except Exception as ed:
			app.logger.error('删除任务失败:  ',task_name, "sql:  ",del_task_sql)
			return_message = {"status":1,"object_name":task_name,"opt":"删除任务失败: ","hide_id":task_name}
		finally:
			socketio.emit(evt_name,return_message)
	else:
		return  redirect(url_for('login'))

#@socketio.on('returntaskdetail')
def returntaskdetail(msg):
	if 'username' in session:
		username = session['username']
		task_name = str(msg['task_name'])
		task_file = str(msg['taskfile'])
		evt_name = str(msg['evtname'])
		evt_name_err = str(msg['evtnameerror'])
		try:
			with open(task_file,'r') as f:
				return_message = f.read()
			socketio.emit(evt_name,return_message)
		except Exception as  e:
			 socketio.emit(evt_name_err,"有问题,应该是文件的问题,比如权限")
	else:
		return  redirect(url_for('login'))
socketio.on_event('returntaskdetail', returntaskdetail)


#@socketio.on('get_script_info')
def get_script_info(msg):
	if 'username' in session:
		username = session['username']
		evt_name = str(msg['evt_name'])
		sql = "select script_id,script_name,script_object,script_type,script_path,script_version,script_describe,script_des_dir,script_md5,script_status from ei_script"
		try:
			sql_result = list(db.session.execute(sql))
			if str(len(sql_result)) == "0":
				socketio.emit(evt_name,{"ROWS":0})
				return None
			addtype = 0
			for rows in sql_result:
				socketio.emit(evt_name,{"data":list(rows),"add":addtype})
				addtype = 1
				#socketio.sleep(0.5)
		except Exception as e:
			socketio.emit(evt_name,str(e))
	else:
		return  redirect(url_for('login'))
socketio.on_event('get_script_info', get_script_info)


@socketio.on('modify_script_info_commit')
def modify_script_info_commit(msg):
	if 'username' in session:
		username = session['username']
		evt_name = str(msg['evt_name'])
		script_id = int(msg['script_id'])
		script_name = str(msg['script_name'])
		script_object = str(msg['script_object'])
		script_type = str(msg['script_type'])
		script_path = str(msg['script_path'])
		script_version = str(msg['script_version'])
		script_describe = str(msg['script_describe'])
		script_des_dir = str(msg['script_des_dir'])
		script_md5 = str(msg['script_md5'])
		script_status = int(msg['script_status'])
		update_sql = "update ei_script set script_name='{script_name}',script_object='{script_object}',script_type='{script_type}', script_path='{script_path}', script_version='{script_version}', script_describe='{script_describe}', script_des_dir='{script_des_dir}', script_md5='{script_md5}', script_status={script_status} where script_id='{script_id}';".format(script_id=script_id, script_name=script_name, script_object=script_object, script_type=script_type, script_path=script_path, script_version=script_version, script_describe=script_describe, script_des_dir=script_des_dir, script_md5=script_md5, script_status=script_status)
		try:
			db.session.execute(update_sql)
			db.session.commit()
			rmsg = str(script_id) + " 更新成功!"
		except Exception as es:
			rmsg = str(script_id) + " 更新失败, 报错为: " + str(es)
		socketio.emit(evt_name,rmsg)
	else:
		return  redirect(url_for('login'))

@socketio.on('modify_pack_info_commit')
def modify_pack_info_commit(msg):
	if 'username' in session:
		username = session['username']
		evt_name = str(msg['evt_name'])
		pack_id = int(msg['pack_id'])
		pack_name = str(msg['pack_name'])
		pack_type = str(msg['pack_type'])
		pack_path = str(msg['pack_path'])
		pack_version = str(msg['pack_version'])
		pack_describe = str(msg['pack_describe'])
		pack_des_dir = str(msg['pack_des_dir'])
		pack_md5 = str(msg['pack_md5'])
		pack_status = int(msg['pack_status'])
		update_sql = "update ei_pack set pack_name='{pack_name}',pack_type='{pack_type}', pack_path='{pack_path}', pack_version='{pack_version}', pack_describe='{pack_describe}', pack_des_dir='{pack_des_dir}', pack_md5='{pack_md5}', pack_status={pack_status} where pack_id='{pack_id}';".format(pack_id=pack_id, pack_name=pack_name, pack_type=pack_type, pack_path=pack_path, pack_version=pack_version, pack_describe=pack_describe, pack_des_dir=pack_des_dir, pack_md5=pack_md5, pack_status=pack_status)
		try:
			db.session.execute(update_sql)
			db.session.commit()
			rmsg = str(pack_id) + " 更新成功!"
		except Exception as es:
			rmsg = str(pack_id) + " 更新失败, 报错为: " + str(es)
		socketio.emit(evt_name,rmsg)
	else:
		return  redirect(url_for('login'))

@socketio.on('del_script')
def del_script(msg):
	if 'username' in session:
		current_time = time.localtime()
		username = session['username']
		evt_name = str(msg['evt_name'])
		script_id = int(msg['script_id'])
		select_sql = "select script_path from ei_script where script_id={script_id}".format(script_id=script_id)
		delete_sql = "delete from ei_script where script_id={script_id}".format(script_id=script_id)
		try:
			file_path = list(db.session.execute(select_sql))
			file_name_old = str(file_path[0][0])
			file_name_new = file_name_old + "_WILL_NEED_AUTO_"  + str(time.strftime('%Y%m%d_%H%M%S',current_time))
			os.rename(file_name_old,file_name_new)
			db.session.execute(delete_sql)
			db.session.commit()
			rmsg = str(script_id) + " 删除成功!"
		except Exception as es:
			rmsg = str(script_id) + " 删除失败, 报错为: " + str(es)
		socketio.emit(evt_name,rmsg)
	else:
		return  redirect(url_for('login'))

@socketio.on('del_pack')
def del_pack(msg):
	if 'username' in session:
		current_time = time.localtime()
		username = session['username']
		evt_name = str(msg['evt_name'])
		pack_id = int(msg['pack_id'])
		select_sql = "select pack_path from ei_pack where pack_id={pack_id}".format(pack_id=pack_id)
		delete_sql = "delete from ei_pack where pack_id={pack_id}".format(pack_id=pack_id)
		try:
			file_path = list(db.session.execute(select_sql))
			file_name_old = str(file_path[0][0])
			file_name_new = file_name_old + "_WILL_NEED_AUTO_"  + str(time.strftime('%Y%m%d_%H%M%S',current_time))
			os.rename(file_name_old,file_name_new)
			db.session.execute(delete_sql)
			db.session.commit()
			rmsg = str(pack_id) + " 删除成功!"
		except Exception as es:
			rmsg = str(pack_id) + " 删除失败, 报错为: " + str(es)
		socketio.emit(evt_name,rmsg)
	else:
		return  redirect(url_for('login'))


#@socketio.on('get_pack_info')
def get_pack_info(msg):
	if 'username' in session:
		username = session['username']
		evt_name = str(msg['evt_name'])
		sql = "select pack_id,pack_name,pack_path,pack_type,pack_version,pack_describe,pack_des_dir,pack_md5,pack_status from ei_pack;"
		try:
			sql_result = list(db.session.execute(sql))
			if str(len(sql_result)) == "0":
				socketio.emit(evt_name,{"ROWS":0})
				return None
			addtype = 0
			for rows in sql_result:
				socketio.emit(evt_name,{"data":list(rows),"add":addtype})
				addtype = 1
				#socketio.sleep(0.5)
		except Exception as e:
			socketio.emit(evt_name,str(e))
	else:
		return  redirect(url_for('login'))
socketio.on_event('get_pack_info', get_pack_info)

#@socketio.on('once1')
def install_mysql_single(msg):
	if 'username' in session:
		username = session['username']
		current_time = time.localtime() 
		app.logger.info(username, "开始安装单机MYSQL了..")
		task_name = "INSTALL_MYSQL_SINGLE_" + str(time.strftime('%Y%m%d_%H%M%S',current_time)) + str(random.randint(0,10000))
		task_file = "../data/tasks/" + username + "_" + task_name + ".log"
		host = str(msg['mysql_host'])
		port = int(msg['mysql_host_port'])
		host_user = str(msg['mysql_host_username'])
		host_password = str(msg['mysql_host_password'])
		mysql_port = int(msg['mysql_port'])
		mysql_password = str(msg['mysql_root_password'])
		evt_name = str(msg['evt_name'])
		evt_name_err = str(msg['evt_name_err'])
		script_sql =  "select script_path,script_pack_path,script_target_path from ei_script where script_share=0 and script_name='install_mysql_single'"
		scrtpt_sql_result = list(db.session.execute(script_sql))
		script_name = scrtpt_sql_result[0][0].split('/')[-1]
		script_local_path = str(scrtpt_sql_result[0][0])
		pack_name = scrtpt_sql_result[0][1].split('/')[-1]
		pack_local_path = str(scrtpt_sql_result[0][1])
		remote_dir = str(scrtpt_sql_result[0][2])
		shell_command = "/usr/bin/sh {remote_dir}/{script_name} MYSQL_ROOT_PASSWORD={mysql_password} MYSQL_PORT={mysql_port} MYSQL_TAR='{remote_dir}/{pack_name}'".format(remote_dir=remote_dir,script_name=script_name,mysql_password=mysql_password,mysql_port=mysql_port,pack_name=pack_name)

		#task_sql ei_task表的   sql_0 成功则执行的sql   sql_2 失败则执行的sql  主要是修改状态
		task_sql = '''insert into ei_task(task_author,task_name,task_object,task_describe,task_shell,task_detail_path) values("{username}","{task_name}","{host}:{port}","安装mysql单机","{shell_command}","{task_file}")'''.format(username=username, task_name=task_name, host=host,port=port, host_password=host_password, shell_command=shell_command, task_file=task_file)
		try:
			res = db.session.execute(task_sql)
			res = db.session.commit()
		except Exception as et:
			app.logger.error(str(et))
			err_task = "配置任务失败" + task_name + task_file + "sql:  " + task_sql
			socketio.emit(evt_name_err,err_task)
		sql_0 = '''update ei_task set task_status = 0 where task_name="{task_name}" and task_author="{task_author}" and task_detail_path="{task_detail_path}"'''.format(task_name=task_name, task_author=username, task_detail_path=task_file)
		sql_2 = '''update ei_task set task_status = 2 where task_name="{task_name}" and task_author="{task_author}" and task_detail_path="{task_detail_path}"'''.format(task_name=task_name, task_author=username, task_detail_path=task_file)
		bgtsk = socketio.start_background_task(target=background_thread(host,port,host_user,host_password,shell_command,script_local_path,pack_local_path,remote_dir,evt_name,evt_name_err,task_file,task_name,sql_0,sql_2))
		log_info = "USERNAME:{username}  任务:{task_name}已执行完. 日志文件: {task_file} ".format(username=username, task_name=task_name, task_file=task_file)
		app.logger.info(log_info)
	return  redirect(url_for('login'))
socketio.on_event('install_mysql_single', install_mysql_single) #@socketio.on('once1') 没得用...

@socketio.on('message')
def handle_message(data):
	app.logger.info('received message: ' + str(data))
	emit('my_response',str(time.asctime(time.localtime(time.time()))))
	#emit('once_resp',str(time.asctime(time.localtime(time.time()))))
	#emit('my_response',get_top_info())
	#shell_command = "/usr/bin/sh /tmp/getrand.sh"
	#socketio.start_background_task(target=background_thread(shell_command))


def background_thread(host,port,host_user,host_password,shell_command,script_local_path,pack_local_path,remote_dir,evt_name,evt_name_err,task_file,task_name,sql_success,sql_fail):
	ssh_client = paramiko.SSHClient()
	ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	with open(task_file,'w',1) as f:
		msg_begin_1 = '开始上传脚本\n'
		socketio.emit(evt_name,msg_begin_1)
		f.write(msg_begin_1)
		try:
			ts = paramiko.Transport(str(host),int(port))
			ts.connect(username=str(host_user),password=str(host_password))
			sftp = paramiko.SFTPClient.from_transport(ts)
			try:
				script_remote_path = remote_dir + "/" + script_local_path.split('/')[-1]
				sftp.put(script_local_path, script_remote_path)
				msg_begin_2 = '上传脚本成功 本地脚本:' + script_local_path + "    远端脚本: " + script_remote_path + " \n"
				socketio.emit(evt_name,msg_begin_2)
				f.write(msg_begin_2)
			except Exception as  es:
				err_msg = "上传脚本失败 \n" + script_local_path + script_remote_path + "\n报错如下:\n" + str(es)
				f.write(err_msg)
				socketio.emit(evt_name_err,err_msg)
				db.session.execute(sql_fail)
				db.session.commit()
				return None
			msg_begin_3 = '开始上传软件包\n'
			socketio.emit(evt_name,msg_begin_3)
			f.write(msg_begin_3)
			try:
				for pack in pack_local_path.split(','):
					pack_remote_path = remote_dir + "/" + pack.split('/')[-1]
					sftp.put(pack,pack_remote_path)
				msg_begin_4 = '上传软件包成功     本地软件包:' + pack_local_path + "     远端目录: "  + remote_dir + ' \n'
				socketio.emit(evt_name, msg_begin_4)
				f.write(msg_begin_4)
			except Exception as  ep:
				err_msg = "上传软件包失败 \n" + pack_local_path  + remote_dir + "\n报错如下\n" + str(ep)
				f.write(err_msg)
				socketio.emit(evt_name_err,err_msg)
				db.session.execute(sql_fail)
				db.session.commit()
				return None
			finally:
				ts.close()
		except Exception as  e:
			err_msg = "上传软件失败, 连接sftp失败\n" + str(e)
			f.write(err_msg)
			socketio.emit(evt_name_err,err_msg)
			ts.close()
			db.session.execute(sql_fail)
			db.session.commit()
			return None
		finally:
			ts.close()

		msg_install_1 = '\n\n开始连接远程服务器执行脚本\n'
		socketio.emit(evt_name,msg_install_1)
		f.write(msg_install_1)
		try:
			ssh_client.connect(hostname=host, port=port, username=host_user, password=host_password)
		except:
			msg_install_2 = "连接失败,无法执行脚本\n"
			socketio.emit(evt_name_err,msg_install_2)
			f.write(msg_install_2)
			db.session.execute(sql_fail)
			db.session.commit()
			return None
		sshSession = ssh_client.get_transport().open_session()
		#app.logger.info(shell_command)
		sshSession.exec_command(shell_command)
		msg_install_3 = "\n\n开始执行(以下消息为脚本的标准输出, 错误输出将会弹窗)" + shell_command + "\n"
		socketio.emit(evt_name,msg_begin)
		while True:
			if sshSession.recv_ready():
				res_std_1 = bytes.decode(sshSession.recv(1024))
				f.write(res_std_1)
				socketio.emit(evt_name,res_std_1)
			if sshSession.recv_stderr_ready():
				res_std_2 = bytes.decode(sshSession.recv_stderr(1024))
				f.write(res_std_2)
				socketio.emit(evt_name_err,res_std_2)
			if sshSession.exit_status_ready():
				break
			socketio.sleep(0.5)
		last_std = bytes.decode(sshSession.recv(1024))
		last_std  += bytes.decode(sshSession.recv_stderr(1024))
		f.write(last_std)
	socketio.emit(evt_name,last_std)
	msg_end_1 = "\n\n脚本执行完毕, 可以关闭此页面, 任务列表中的 {task_name} 为本次任务\n".format(task_name=task_name)
	socketio.emit(evt_name,msg_end_1)
	sshSession.close()
	ssh_client.close()
	db.session.execute(sql_success)
	db.session.commit()
	return None
	

#	while True:
#		if sshSession.recv_ready():
#			res_std = bytes.decode(sshSession.recv(8))
#			app.logger.info(res_std)
#			socketio.sleep(0.1)
#			#socketio.emit('my_responce',res_std.replace('\n','%OA"'))
#			responce_evt = 'my_responce' + username
#			socketio.emit(responce_evt,res_std)
#			stdout_data.write(res_std)
#			os.fsync(stdout_data)
#		if sshSession.recv_stderr_ready():
#			res_std_err = bytes.decode(sshSession.recv_stderr(8))
#			app.logger.info(res_std_err)
#			socketio.sleep(0.1)
#			responce_evt = 'my_responce' + username
#			socketio.emit(responce_evt,res_std_err)
#		if sshSession.exit_status_ready():
#			res_std = bytes.decode(sshSession.recv(8))
#			app.logger.info(res_std)
#			responce_evt = 'my_responce' + username
#			socketio.emit(responce_evt,res_std)
#			break
#	responce_evt = 'my_responce' + username
#	#socketio.emit(responce_evt,bytes.decode(sshSession.recv(8)))
#	socketio.emit(responce_evt,"finished")
#	stdout_data.close()
#	stderr_data.close()
	
#	#stdin, stdout, stderr = ssh_client.exec_command(shell_command, get_pty=True)
#	while not stdout.channel.exit_status_ready():
#		result = stdout.readline()
#		socketio.sleep(1)
#		socketio.emit('once_resp',result)
#		if stdout.channel.exit_status_ready():
#			a = stdout.readlines()
#			socketio.emit('once_resp',a)
#			break


#	while True:
#		emit('my_response',str(time.asctime(time.localtime(time.time()))))
#		time.sleep(1)
#	
#
#@socketio.on('json')
#def handle_json(json):
#	app.logger.info('received json2: ' + str(json))
#
#@socketio.on('my event')
#def handle_my_custom_event(json):
#	app.logger.info('received json3: ' + str(json))
#	send(" i know")
#
#@socketio.on('my event', namespace='/testsio')
#def handle_my_custom_namespace_event(json):
#	app.logger.info('received json4: ' + str(json))
#	send("test 4")
#
#@socketio.on('evt1')
#def evt1(message):
#	app.logger.info('evt1:    ',str(message))
	#emit('my_response','aaaaaaaa')


	


@app.route('/install')
def install_byshell():
	if 'username' in session:
		username = session['username']
		html = 'db/' + request.args.get('html')
		return render_template(html,username = username)
	return  redirect(url_for('login'))

@app.route('/task_detail')
def return_task_detail():
	if 'username' in session:
		username = session['username']
		task_name = request.args.get('task_name')
		task_file = request.args.get('task_file')
		return render_template('task_detail.html',task_name = task_name, task_file=task_file, username=username)
	return redirect(url_for('login'))


@app.route('/download')
def download():
	if 'username' in session:
		username = session['username']
		file_name = request.args.get('task_file')
		if username == file_name.split('_INSTALL_MYSQL_SINGLE_')[0].split('/')[-1] :
			return send_file(file_name,as_attachment=True)
		else:
			return "没得权限或者用户名不对, 或者这个文件不是你的"
	return redirect(url_for('login'))

#这个路由没有使用了, 找个机会删掉
@app.route('/install_mysql_single',methods = ['POST','GET'])
def install_mysql_single():
	if 'username' in session:
		username = session['username']
		mysql_host = request.form['mysql_host']
		mysql_host_port = request.form['mysql_host_port']
		mysql_host_username = request.form['mysql_host_username']
		mysql_host_password = request.form['mysql_host_password']
		mysql_port = request.form['mysql_port']
		mysql_root_password = request.form['mysql_root_password']
		shell_command = "/usr/bin/sh /tmp/MysqlInstallerByDDCW_ei_1.0.sh MYSQL_ROOT_PASSWORD={mysql_root_password} MYSQL_PORT={mysql_port} MYSQL_TAR='/tmp'".format(mysql_root_password=mysql_root_password, mysql_port=mysql_port)
		straa = username + mysql_host + mysql_host_port + mysql_host_password
		socketio.start_background_task(target=background_thread(shell_command,username,mysql_host,mysql_host_port,mysql_host_username,mysql_host_password))
		return "aa"
	else:
		return "aaaaaaaa"
		return  redirect(url_for('login'))

@app.route('/newterminal')
def newterminnal():
	return app.send_static_file('newterminal.html')

@app.route('/testsio')
def testsio():
	#shell_command = "/usr/bin/sh /tmp/testshell.sh"
	#socketio.start_background_task(target=background_thread(shell_command))
	return render_template('testso.html')

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
		sql_db_instance = 'select db_instance_name, db_type, db_host, db_port, status,db_version,db_instance_id from ei_db where db_author = "' + username + '"'
		sql_host_instance = 'select host_instance_name,host_type,host_version,host_ssh_ip,host_ssh_port,status,host_instance_id from ei_host where host_author = "' + username + '"'
		sql_task = 'select task_name,task_object,task_describe,task_start,task_stop,task_detail_path,task_status,task_id from ei_task where task_author="' + username + '" order by task_start desc limit 15;'
		try:
			items_db = db.session.execute(sql_db_instance)
			items_host = db.session.execute(sql_host_instance)
			items_task = db.session.execute(sql_task)
			db_norm = list(db.session.execute('select count(db_instance_name) from ei_db where db_author = "' + username + '" and status = 0'))[0][0]
			db_warn = list(db.session.execute('select count(db_instance_name) from ei_db where db_author = "' + username + '" and status = 1'))[0][0]
			db_error = list(db.session.execute('select count(db_instance_name) from ei_db where db_author = "' + username + '" and status = 2'))[0][0]
			db_un = list(db.session.execute('select count(db_instance_name) from ei_db where db_author = "' + username + '" and status not in (0,1,2)'))[0][0]
			host_norm = list(db.session.execute('select count(host_instance_name) from ei_host where host_author = "' + username + '" and status = 0'))[0][0]
			host_warn = list(db.session.execute('select count(host_instance_name) from ei_host where host_author = "' + username + '" and status = 1'))[0][0]
			host_error = list(db.session.execute('select count(host_instance_name) from ei_host where host_author = "' + username + '" and status = 2'))[0][0]
			host_un = list(db.session.execute('select count(host_instance_name) from ei_host where host_author = "' + username + '" and status not in (0,1,2)'))[0][0]
		except:
			db_norm=0
			db_warn=0
			db_error=0
			db_un=0
			host_norm=0
			host_warn=0
			host_error=0
			host_un=0
			items_db="NO DB CONFIG, you can add db"
			items_host="NO HOST, you can add host"
			items_task="NO task"
		return render_template('index.html',username=username, db_list=list(items_db), host_list=list(items_host), task_list=list(items_task), db_norm = db_norm, db_warn = db_warn, db_error = db_error, db_un = db_un, host_norm = host_norm, host_warn = host_warn, host_error = host_error, host_un = host_un)
	else:
		return  redirect(url_for('login'))

@app.route('/')
def default_index():
	#return	app.send_static_file('index.html')
	#return render_template('index.html',username=username)
	return redirect(url_for('index'))



@app.route('/upload', methods=['GET', 'POST'])
def upload():
	if 'username' in session:
		evt_name = request.form['evt_name']
		type_table = request.form['type_table']
		if type_table == "script":
			script_name = request.form['script_name']
			script_object = request.form['script_object']
			exist_file = request.form['exist_file'] #等于0表示 存在文件则跳过
			script_file = request.files['myfilebyei']
			script_file_name = secure_filename(script_file.filename)
			script_dir = "../script"
			script_file_name_and_path = script_dir + "/" + script_file_name
			script_sql = 'insert into ei_script(script_name,script_object,script_path) values("{script_name}","{script_object}","{script_file_name_and_path}")'.format(script_name=script_name, script_object=script_object, script_file_name_and_path=script_file_name_and_path)
			if os.path.isfile(script_file_name_and_path) and str(exist_file) == "0":
				msg = str(script_file_name_and_path) + " 文件存在, 将自动跳过"
				app.logger.warning(msg)
				
			else:
				try:
					script_file.save(script_file_name_and_path)
					db.session.execute(script_sql)
					db.session.commit()
					msg = script_file_name + " 脚本上传成功."
				except Exception as e:
					msg = script_file_name + " 脚本上传失败" + str(e)
		elif type_table == "pack":
			pack_name = request.form['pack_name']
			pack_file = request.files['myfilebyei2']
			exist_file = request.form['exist_file'] #等于0表示 存在文件则跳过
			pack_version = request.form['pack_version']
			pack_file_name = secure_filename(pack_file.filename)
			if pack_version is None:
				pack_version = pack_file_name
			pack_dir = "../pack"
			pack_file_name_and_path = pack_dir + "/" + pack_file_name
			pack_sql = 'insert into ei_pack(pack_name,pack_path,pack_version) values("{pack_name}","{pack_file_name_and_path}","{pack_version}")'.format(pack_name=pack_name, pack_file_name_and_path=pack_file_name_and_path, pack_version=pack_version)
			if os.path.isfile(pack_file_name_and_path) and str(exist_file) == "0":
				msg = str(pack_file_name_and_path) + "文件存在, 将自动跳过"
				app.logger.warning(msg)
			else:
				try:
					pack_file.save(pack_file_name_and_path)
					db.session.execute(pack_sql)
					db.session.commit()
					msg = pack_file_name + "  软件包上传成功"
				except Exception as ep:
					msg = pack_file_name + " 软件包上传失败 " + str(ep)
			
		else:
			return "暂不支持上传其它类型的文件"
		r_msg = '''
<script type="text/javascript">
function returnIndex(){
//location.href="/index"
window.history.go(-1)
}
setTimeout("returnIndex()",5000)
</script>
<div align="center"><h2>''' + msg + '''</h2><p id="timereturn">5 秒后自动跳回首页<a href="/index">(点此返回)</a></p></div>'''
		return r_msg
	else:
		return  redirect(url_for('login'))


#@scheduler.task('interval', id='set_db_instacne_status', seconds=30, misfire_grace_time=4)
@scheduler.task('interval', id='set_db_instacne_status', seconds=int(EI_DB_INTERVALS_SECOND))
def set_db_instacne_status():
	conn = sqlite3.connect(DATABASE)
	c = conn.cursor()
	localtime = time.asctime(time.localtime(time.time()))
	sql_db_instacne = 'select db_instance_name,db_host,db_port,db_user,db_password, db_instance_id from ei_db where db_type = "mysql"'
	#items_db = db.session.execute(sql_db_instacne)
	items_db = c.execute(sql_db_instacne)
	items_db = items_db.fetchall()
	for instance_db in items_db:
		db_instance_name = instance_db[0]
		db_host = instance_db[1]
		db_port = instance_db[2]
		db_user = instance_db[3]
		db_password = instance_db[4]
		db_instance_id = instance_db[5]
		try:
			conn_mysql = pymysql.connect(host=db_host, port=db_port, user=db_user, passwd=db_password)
			cursor_mysql = conn_mysql.cursor()
			cursor_mysql.execute("select version()")
			db_version = cursor_mysql.fetchall()
			cursor_mysql.close()
			conn_mysql.close()
			sql_update = 'update ei_db set db_version = "{db_version}",status={status} where db_instance_id={db_instance_id};'.format(db_version=db_version[0][0],status=0,db_instance_id=db_instance_id)
		except Exception as emysql:
			warnning_msg = "mysql实例连接失败. 实例ID:{db_instance_id}  实例名:{db_instance_name}  实例主机地址:{db_host}  实例端口:{db_port} 异常信息为: {emysql}\n".format(db_instance_id=db_instance_id, db_instance_name=db_instance_name, db_host=db_host, db_port=db_port, emysql=str(emysql))
			app.logger.warning(warnning_msg)
			sql_update = 'update ei_db set status={status} where db_instance_id={db_instance_id};'.format(status=2,db_instance_id=db_instance_id)
		#update_db_result = db.session.execute(sql_update)
		#db.session.execute('commit;')
		c.execute(sql_update)
		conn.commit()
	conn.close()


#@scheduler.task('interval', id='set_host_instacne_status', seconds=20, misfire_grace_time=4)
@scheduler.task('interval', id='set_host_instacne_status', seconds=int(EI_HOST_INTERVALS_SECOND))
def set_host_instacne_status():
	localtime = time.asctime(time.localtime(time.time()))
	sql_host_instance = 'select host_instance_name,host_ssh_ip,host_ssh_port,host_ssh_username,host_ssh_password,host_instance_id from ei_host ;'
	items_host = db.session.execute(sql_host_instance)
	items_host = items_host.fetchall()
	for instance_host in items_host:
		host_instance_name = instance_host[0]
		host_ssh_ip = instance_host[1]
		host_ssh_port = instance_host[2]
		host_ssh_username = instance_host[3]
		host_ssh_password = instance_host[4]
		host_instance_id = instance_host[5]
		try:
			ssh = paramiko.SSHClient()
			ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
			ssh.connect(hostname=host_ssh_ip, port=host_ssh_port, username=host_ssh_username, password=host_ssh_password)
			stdin, stdout, stderr = ssh.exec_command("/usr/bin/grep NAME= /etc/os-release | /usr/bin/head -1")
			os_name = str(stdout.read().rstrip()).split('"')[1]
			stdin, stdout, stderr = ssh.exec_command("/usr/bin/grep VERSION= /etc/os-release | /usr/bin/head -1")
			os_version = str(stdout.read().rstrip()).split('"')[1]
			ssh.close()
			sql_update = 'update ei_host set host_type="{host_type}",host_version="{host_version}",status={status} where host_instance_id={host_instance_id}'.format(host_type=os_name, host_version=os_version, status=0, host_instance_id=host_instance_id)
		except Exception as ehost:
			log_warning = "主机SSH连接失败, 实例ID: {host_instance_id}   实例名字:{host_instance_name}  实例IP地址: {host_ssh_ip}  实例端口:{host_ssh_port} 报错信息为: {ehost}\n".format(host_instance_id=host_instance_id,host_instance_name=host_instance_name, host_ssh_ip=host_ssh_ip, host_ssh_port=host_ssh_port, ehost=str(ehost))
			app.logger.warning(log_warning)
			sql_update = 'update ei_host set status={status} where host_instance_id={host_instance_id};'.format(status=2, host_instance_id=host_instance_id)
		db.session.execute(sql_update)
		db.session.execute('commit;')

#@scheduler.task('interval', id='set_db_instacne_status', seconds=30, misfire_grace_time=4)
#def set_db_instacne_status():
#	localtime = time.asctime(time.localtime(time.time()))
#	sql_db_instacne = 'select db_instance_name,db_host,db_port,db_user,db_password,db_instance_id from ei_db where db_type = "mysql"'
#	try:
#		items_db = db.session.execute(sql_db_instacne)
#		for instance_db in items_db:
#			try:
#				db_instance_name = instance_db[0]
#				db_host = instance_db[1]
#				db_port = instance_db[2]
#				db_user = instance_db[3]
#				db_password = instance_db[4]
#				db_instance_id = instance_db[5]
#
#				conn_mysql = pymysql.connect(host=db_host, port=db_port, user=db_user, passwd=db_password)
#				cursor_mysql = conn_mysql.cursor()
#				cursor_mysql.execute("select version()")
#				db_version = cursor_mysql.fetchall()
#				cursor_mysql.close()
#				conn_mysql.close()
#				sql_update = 'update ei_db set db_version = "{db_version}",status={status} where db_instance_id={db_instance_id};'.format(db_version=db_version[0][0],status=0,db_instance_id=db_instance_id)
#				db.session.execute(sql_update)
#				db.session.commit()
#
#			except Exception as ed1:
#				app.logger.info("DB实例连接失败 ",db_instance_name,db_host,db_port,db_user,db1)
#				sql_update = 'update ei_db set status={status} where where db_instance_id={db_instance_id};'.format(status=2,db_instance_id=db_instance_id)
#				db.session.execute(sql_update)
#				db.session.commit()
#			#finally:
#			#	db.session.execute(sql_update)
#			#	db.session.commit()
#	except Exception as edb:
#		app.logger.info("执行任务set_db_instacne_status失败, (部分失败或者全部失败)",localtime,edb)
#
#
#@scheduler.task('interval', id='set_host_instacne_status', seconds=20, misfire_grace_time=4)
#def set_host_instacne_status():
#	localtime = time.asctime(time.localtime(time.time()))
#	sql_host_instance = 'select host_instance_name,host_ssh_ip,host_ssh_port,host_ssh_username,host_ssh_password from ei_host ;'
#	try:
#		items_host = db.session.execute(sql_host_instance)
#		for instance_host in items_host:
#			try:
#				host_instance_name = instance_host[0]
#				host_ssh_ip = instance_host[1]
#				host_ssh_port = instance_host[2]
#				host_ssh_username = instance_host[3]
#				host_ssh_password = instance_host[4]
#				ssh = paramiko.SSHClient()
#				ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#				ssh.connect(hostname=host_ssh_ip, port=host_ssh_port, username=host_ssh_username, password=host_ssh_password)
#				stdin, stdout, stderr = ssh.exec_command("/usr/bin/grep NAME= /etc/os-release | /usr/bin/head -1")
#				os_name = str(stdout.read().rstrip()).split('"')[1]
#				stdin, stdout, stderr = ssh.exec_command("/usr/bin/grep VERSION= /etc/os-release | /usr/bin/head -1")
#				os_version = str(stdout.read().rstrip()).split('"')[1]
#				ssh.close()
#				sql_update = 'update ei_host set host_type="{host_type}",host_version="{host_version}",status={status} where host_instance_name="{host_instance_name}" and host_ssh_ip="{host_ssh_ip}" and host_ssh_port={host_ssh_port} and host_ssh_username="{host_ssh_username}";'.format(host_type=os_name, host_version=os_version, status=0, host_instance_name=host_instance_name, host_ssh_ip=host_ssh_ip, host_ssh_port=host_ssh_port, host_ssh_username=host_ssh_username)
#				db.session.execute(sql_update)
#				db.session.commit()
#			except Exception as eh1:
#				app.logger.info("连接失败 host : ", host_instance_name, eh1)
#				sql_update = 'update ei_host set status={status} where host_instance_name="{host_instance_name}" and host_ssh_ip="{host_ssh_ip}" and host_ssh_port={host_ssh_port} and host_ssh_username="{host_ssh_username}";'.format(status=2, host_instance_name=host_instance_name, host_ssh_ip=host_ssh_ip, host_ssh_port=host_ssh_port, host_ssh_username=host_ssh_username)
#				db.session.execute(sql_update)
#				db.session.commit()
#			#finally:
#			#	db.session.execute(sql_update)
#			#	db.session.commit()
#	except Exception as ehost:
#		app.logger.info("JOB set_host_instacne_status 失败, 原因:部分主机信息不对,或者本地sqlite库有问题",ehost)
#	#app.logger.info("Time:", localtime)
#

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
					db.session.commit()
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
				db.session.commit()
				message = "添加成功:" + instance_name
				return redirect('/index')
				return render_template('index.html', username = username, message = message)
			except:
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
			db.session.commit()
			message = "添加成功:" + instance_name
			return redirect('/index')
			return render_template('index.html', username = username, message = message)
		except Exception as e:
			#db.session.execute("rollback")
			error = "添加失败:" + instance_name
			return str(e)
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
				db.session.commit()
				message = "删除成功" + ','.join(db_instance_list)
				return redirect('/index')
				return render_template('index.html', username = username, message = message)
			except:
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
				db.session.commit()
				message = "删除成功" + ','.join(host_instance_list)
				return redirect('/index')
				return render_template('index.html', username = username, message = message)
			except:
				error = "删除失败" + ','.join(host_instance_list)
		else:
			return "不能选择空"
	return redirect('/login')

@app.route('/deltask', methods = ['POST','GET'])
def del_task():
	error = None
	if 'username' in session:
		username = session['username']
		task_list = request.form.getlist('del_task_1')
		if len(task_list):
			task_name_str = '","'.join(task_list)
			sql_del = 'delete from ei_task where task_author = "' + username + '" and task_name in ("' + task_name_str + '")'
			try:
				db.session.execute(sql_del)
				db.session.commit()
				message = "删除成功" + ','.join(task_list)
				return redirect('/index')
				return render_template('index.html', username = username, message = message)
			except:
				error = "删除失败" + ','.join(task_list)
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
			sql_mysql_user = 'select user,host,plugin,password_last_changed,password_expired from mysql.user;'
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
			stdin, stdout, stderr = ssh.exec_command("/usr/bin/df -PT / | /usr/bin/tail -n +2 | /usr/bin/awk '{print $2}'")
			root_dir_type = str(stdout.read().rstrip())

			stdin, stdout, stderr = ssh.exec_command("/usr/bin/awk '{print $1,$2,$3}' /proc/loadavg")
			loadavg = stdout.readlines()[0].rstrip()


			stdin, stdout, stderr = ssh.exec_command("/usr/bin/wc -l /proc/net/tcp | /usr/bin/awk '{print $1-1}'")
			tcp4_sockets = int(stdout.read())
			stdin, stdout, stderr = ssh.exec_command("/usr/bin/wc -l /proc/net/tcp6 | /usr/bin/awk '{print $1-1}'")
			tcp6_sockets = int(stdout.read())

			stdin, stdout, stderr = ssh.exec_command("/usr/bin/cat /proc/uptime")
			uptime_res = stdout.read()
			uptime = round(float(uptime_res.split()[0])/60/60/24,2)
			#cpu_p_total = round((float(uptime_res.split()[0])  - float(uptime_res.split()[1]))/float(uptime_res.split()[0])*100,3)

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
			cpu_p_total = round((float(uptime_res.split()[0]) * cpu_count  - float(uptime_res.split()[1]))/float(uptime_res.split()[0])*100*cpu_count,3)
			mem_total_MB = round( int(mem_total) / 1024 , 1 )
			stdin, stdout, stderr = ssh.exec_command("/usr/bin/grep SwapTotal /proc/meminfo | /usr/bin/awk '{print $2}'")
			swap_total = int(stdout.read())
			swap_total_MB = round( swap_total / 1024 , 1 ) 
			stdin, stdout, stderr = ssh.exec_command("/usr/bin/cat /proc/sys/vm/swappiness")
			swappiness = int(stdout.read())

			#查询端口和进程的对应关系需要root权限, 或者用其它命令
			if host_ssh_username == "root":
				command_process_port = '''for procnum in /proc/[0-9]* ; do for inodes in $(/usr/bin/ls -l ${procnum}/fd 2>/dev/null | /usr/bin/grep socket: | /usr/bin/awk -F [ '{print $2}' | /usr/bin/awk -F ] '{print $1}'); do PORT=$(/usr/bin/awk -v inode2="${inodes}" '{if ($10 == inode2) print $2}' /proc/net/tcp | /usr/bin/awk -F : '{print $2}'); PORT=$((0x${PORT})); if [[ ${PORT} -gt 0 ]];then /usr/bin/echo -e "${procnum##*/} ${PORT} $(/usr/bin/ls ${procnum}/fd | /usr/bin/wc -l) $(/usr/bin/cat ${procnum}/cmdline)"; fi; done; done; '''
				stdin, stdout, stderr = ssh.exec_command(command_process_port)
				process_port = stdout.read()
				process_port_2 = stderr.read()
			else:
				process_port = None

			ssh.close()

			return render_template('host.html',username=username, instance_name=instance_name, cpu_p = cpu_p, cpu_p100 = cpu_p100, mem_p = mem_p, mem_p100 = mem_p100, root_dir_p = root_dir_p, root_dir_p100 = root_dir_p100, loadavg = loadavg, tcp4_sockets = tcp4_sockets, tcp6_sockets = tcp6_sockets, uptime = uptime, cpu_p_total = cpu_p_total, online_users = online_users , mysql_server = mysql_server, redis_server = redis_server, oracle_server = oracle_server, nginx_server = nginx_server, php_server = php_server, haproxy_server = haproxy_server, sysctl_parameter = sysctl_parameter, firewalld_status = firewalld_status, selinux_status = selinux_status, yum_repo_count = yum_repo_count, host_platform = host_platform, kernel_version = kernel_version, host_name = host_name1, os_version = os_version, cpu_sock = cpu_sock, cpu_core = cpu_core, cpu_thread = cpu_thread, cpu_count = cpu_count, mem_total_MB = mem_total_MB, swap_total_MB = swap_total_MB, swappiness = swappiness, root_dir_type = root_dir_type, process_port = process_port)
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
	except Exception as e:
		log_error = "上传文件失败: "
		app.logger.error(e)



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
	#app.run(app, host=EI_WEB_ADDRESS, debug=EI_WEB_DEBUG, port=EI_WEB_PORT)
	handler = logging.FileHandler(filename=str(EI_LOG), encoding='UTF-8')
	handler.setFormatter(logging.Formatter(EI_LOG_FORMAT))
	app.logger.addHandler(handler)
	#socketio.run(app, host=str(EI_WEB_ADDRESS), debug=bool(EI_WEB_DEBUG), port=int(EI_WEB_PORT))
	socketio.run(app, host=str(EI_WEB_ADDRESS), debug=EI_WEB_DEBUG, port=int(EI_WEB_PORT))
#if __name__ == "__main__":
#	from gevent import pywsgi
#	from geventwebsocket.handler import WebSocketHandler
#	server = pywsgi.WSGIServer(('', 6121), app, handler_class=WebSocketHandler)
#	app.logger.info('server start')
#	server.serve_forever()
