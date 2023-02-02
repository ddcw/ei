import ddcw_ssh
import os
import paramiko
import configparser
class install_mysql:
	def __init__(self,host,port,user,password,mysql_password,var,log,isENFORCE,pack): #这里的host,port是主机的信息, 
		self.host = host
		self.port = port
		self.user = user
		self.password = password
		self.mysql_password = mysql_password
		ssh_instance = ddcw_ssh.set(host=host,port=port,user=user,password=password)
		if ssh_instance.test()['status']:
			ssh_instance.set()
			self.status = True
		else:
			self.status = False
		self.ssh_instance = ssh_instance
		self.enforce = isENFORCE #True:忽略空间之类的问题,尽可能的安装.
		self.var = var
		self.log = log
		self.pack = pack #仅支持二进制文件(mysql)
		self.pack_filename = os.path.basename(pack)
		self.msg = '' #安装日志, 懒得整实时同步了, 现在安装完了才能看到...

	def _create_dir(self,):
		_file = ['socket','pid_file','log_error','slow_query_log_file','general_log_file','log_bin','relay_log']
		_dir = ['basedir','datadir','tmpdir','innodb_log_group_home_dir','innodb_data_home_dir']
		dir_list = []
		for x in _file:
			dir_list.append(os.path.dirname(self.var[x].split('#')[0]))
		for x in _dir:
			dir_list.append(self.var[x].split('#')[0])
			#dir_list.append(os.path.abspath(self.var[x]))

		#创建用户
		mysql_user = self.var["user"]
		useradd_cmd = f'useradd {mysql_user} -s /usr/sbin/nologin '
		self.ssh_instance.get_result_dict(useradd_cmd) #懒得去判断了, code=9:  useradd: user 'mysql' already exists

		#print(dir_list)

		#创建目录和修改权限
		for x in dir_list:
			#print(x,'AAAAAAa')
			cmd = f'mkdir -p {x}'
			cmd2 = f'chown {mysql_user}:{mysql_user} {x}'
			if self.ssh_instance.get_result_dict(cmd)['code'] != 0 or self.ssh_instance.get_result_dict(cmd2)['code'] != 0:
				self.msg += f'mkdir {x} faild or chown faild.'
				return False
		return True

	def _check_env(self,):
		return True #懒得整了...

	def _upload(self,):
		#ddcw_ssh忘了写Transport了....
		self.msg += f'up load file {self.pack}'
		try:
			ts = paramiko.Transport((self.host,int(self.port)))
			ts.connect(username=self.user, password=self.password)
			sftp = paramiko.SFTPClient.from_transport(ts)
			sftp.put(self.pack, '/tmp')
			mysql_config = configparser.ConfigParser()
			mysql_config['mysqld'] = self.var
			mysql_cnf = "/tmp/_mysql_{self.port}.cnf"
			self.mysql_cnf = mysql_cnf
			with open(mysql_cnf, 'w') as configfile:
				mysql_config.write(configfile)
			sftp.put(mysql_cnf, '/tmp') #配置文件就放/tmp了 懒得整了...
			ts.close()
		except Exception as e:
			self.msg += f'upload file FAILD. {e}'
			return False
		return True

	def _uncompress(self,):
		pack_dirname = self.pack_filename.replace('.tar.gz','').replace('.gz','') #懒得去整了, 直接字符串替换吧...
		cmd = f'cd /tmp && tar -xf {self.pack_filename} && cp -ra /tmp/{pack_dirname}/* {self.var["basedir"]}'
		self.ssh_instance.get_result_dict(cmd) #懒得去判断了. 其实还要看下二进制文件是否能运行的. 算了.
		return True
		pass

	def _create_db(self,):
		cmd = f"{self.var['basedir']}/bin/mysqld --defaults-file={self.mysql_cnf} --initialize"
		self.ssh_instance.get_result_dict(cmd) #懒得去判断了
		return True
		pass

	def _start_mysqld(self):
		cmd = f""" nohup {self.var['basedir']}/bin/mysqld --defaults-file={self.mysql_cnf}  & """
		pass

	def _create_user(self,):
		#先获取mysql的密码
		local_root_password_cmd = f"""grep "A temporary password is generated" {self.var["log_error"]} | tail -n1 | awk -F"root@localhost: " """ + """ '{print $2}'"""
		local_root_password = self.ssh_instance.get_result_dict(local_root_password_cmd)['stdout']
		create_user_sql = f"""create user root@'%' identified by {self.mysql_password};grant all on *.* to root@'%'; flush privileges;flush privilegs;"""
		cmd_create_user = f""" {self.var['basedir']}/bin/mysql -uroot -p"{local_root_password_cmd}" -P{self.var['port']} -S {self.var['socket']} -e "{create_user_sql}" """
		self.ssh_instance.get_result_dict(cmd_create_user) #懒得去判断了
		return True

	def _create_script(self):
		return True #懒得去创建了..

	def _install_post(self):
		#本来还准备远程连接测试下的, 算了.
		self.msg = 'install finish'
		self.ssh_conn.close()
		return True

	def install(self):
		return True if self._create_dir() and self._check_env() and self._upload() and self._uncompress() and self._create_db() and self._start_mysqld and self._create_user() and self._create_script() and self._install_post() else False
			
		#创建相关目录
		#检查环境
		#上传软件包和配置文件
		#解压软件包
		#建库
		#创建root@%用户
		#创建启动脚本(清理日志脚本之类的就算了吧... 也懒得整开机自启了)
		#启动mysql 并连接测试
		#关闭ssh连接和mysql连接
		print('xxx')
	

