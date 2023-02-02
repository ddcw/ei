import argparse
import sys
import yaml
import os
import signal
import eiserver
import eiweb

def _argparse():
	EXIT_FLAG = False
	parser = argparse.ArgumentParser(add_help=False, description='ddcw ei server and web')
	parser.add_argument('--help', '-H',  action='store_true', dest='HELPS', default=False, help='show this help message and exit')
	parser.add_argument('--version', '-v', '-V', action='store_true', dest="VERSION", default=False,  help='show version')
	parser.add_argument('--print', action='store_true', dest="PRINT", default=False,  help='show args')
	parser.add_argument('--config', '-c', action='store', dest="CONFIG", default='ei.yaml')

	parser.add_argument('ACTION', nargs='?', default='status', choices=['start','stop','status','restart'], action='store', )
	parser.add_argument('SERVICE', nargs='?', default='all', choices=['server','web','all'], action='store', )

	if parser.parse_args().VERSION:
		print("VERSION: v1.1")
		EXIT_FLAG = True
	
	if parser.parse_args().PRINT:
		print('.....')
		EXIT_FLAG = True

	if parser.parse_args().HELPS:
		parser.print_help()
		EXIT_FLAG = True

	if EXIT_FLAG:
		sys.exit(0)

	return parser.parse_args()


#存在则返回 False  不存在或者文件不存在则为True
def exist_process_from_pidfile(pidfile):
	pid = 0
	try:
		with open(pidfile,'r',encoding="utf-8") as f:
			pid = f.read()
	except Exception as e:
		return True
	piddir = f'/proc/{pid}'
	return False if os.path.exists(piddir) else True


#存在则返回True
def exist2(pidfile):
	pid = 0
	try:
		with open(pidfile,'r',encoding="utf-8") as f:
			pid = f.read()
	except Exception as e:
		return False
	piddir = f'/proc/{pid}'
	return pid if os.path.exists(piddir) else 0

def get_data(pidfile):
	try:
		with open(pidfile,'r',encoding="utf-8") as f:
			pid = int(f.read())
	except Exception as e:
		pid = 0
	return pid


if __name__ == '__main__':
	parser = _argparse()
	conf_file = parser.CONFIG
	try:
		with open(conf_file, 'r', encoding="utf-8") as f:
			inf_data =  f.read()
		conf = yaml.load(inf_data,Loader=yaml.Loader)
	except Exception as e:
		print(e)
		sys.exit(1)


	#初始化配置信息
	conf['BASEDIR'] = f"{os.path.abspath(conf['BASEDIR'])}"
	conf['TMP'] = f"{os.path.abspath(conf['TMP'])}"
	conf["RUNDIR"] = f"{conf['BASEDIR']}/run"
	conf["LOGDIR"] = f"{conf['BASEDIR']}/log"
	conf["MONITORDIR"] = f"{conf['BASEDIR']}/monitor" #放监控数据的目录
	conf["DATADIR"] = f"{conf['BASEDIR']}/data" #server存储信息的目录

	conf['WEB_PID'] = f"{conf['RUNDIR']}/web.pid"
	conf['WEB_LOG'] = f"{conf['LOGDIR']}/web.log"
	conf['SERVER_PID'] = f"{conf['RUNDIR']}/server.pid"
	conf['SERVER_SOCKET'] = f"conf['RUNDIR']/server.sock"
	conf['SERVER_LOG'] = f"{conf['LOGDIR']}/server.log"

	conf['LOG'] = conf['SERVER_LOG'] #daemon.Daemon需要LOG


	#初始化 BASEDIR TMP目录之类的
	os.makedirs(conf['BASEDIR'],exist_ok=True)
	os.makedirs(conf['RUNDIR'],exist_ok=True)
	os.makedirs(conf['LOGDIR'],exist_ok=True)
	os.makedirs(conf['MONITORDIR'],exist_ok=True)
	os.makedirs(conf['DATADIR'],exist_ok=True)
	os.makedirs(conf['TMP'],exist_ok=True)

	#workdir 入口文件的路径
	conf['_WORKDIR'] = os.path.dirname(os.path.abspath(sys.argv[0]))


	#初始化authkey (1021字节, 不够的结尾补0, 多的去掉)
	authkey_length = len(conf['AUTHKEY'].encode('utf-8'))
	if authkey_length > 1021:
		print(f'AUTHKEY MUST BE LESS THAN 1021. {con["AUTHKEY"]}')
		sys.exit(3)
	elif authkey_length < 1021:
		conf['AUTHKEY'] = conf['AUTHKEY'].encode('utf-8') + int(0).to_bytes(1021-authkey_length,'big')
	else:
		conf['AUTHKEY'] = conf['AUTHKEY'].encode('utf-8')

	if parser.ACTION == 'status':
		webei_pid = exist2(conf['WEB_PID'])
		server_pid = exist2(conf['SERVER_PID'])
		if server_pid:
			print(f'server is running(port:{conf["PORT"]} pid:{server_pid})')
		else:
			print('server is closed')

		if webei_pid:
			print(f'web is running(port:{conf["WEB_PORT"]} pid:{webei_pid})')
		else:
			print('web is closed')

	elif parser.ACTION == 'start':
		if (parser.SERVICE == 'server' or parser.SERVICE == 'all') and exist_process_from_pidfile(conf['SERVER_PID']):
			server_instance = eiserver.server(conf,conf['SERVER_PID'])
			server_instance.start()
			print('start server.')

		if (parser.SERVICE == 'web' or parser.SERVICE == 'all') and exist_process_from_pidfile(conf['WEB_PID']):
			web_instance = eiweb.web(conf,conf['WEB_PID'])
			web_instance.start()
			print('start web')

	elif parser.ACTION == 'stop':
		if (parser.SERVICE == 'server' or parser.SERVICE == 'all'):
			try:
				os.kill(get_data(conf['SERVER_PID']), signal.SIGKILL)
				print('closed ei server')
			except:
				pass
		if (parser.SERVICE == 'web' or parser.SERVICE == 'all'):
			try:
				os.kill(get_data(conf['WEB_PID']), signal.SIGKILL)
				print('closed ei web')
			except:
				pass
	elif parser.ACTION == 'restart':
		pass


	else:
		print(f'unknown {parser.ACTION}')

