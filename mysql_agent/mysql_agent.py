import argparse
import sys
import trans_client
import monitor_client
import yaml
import os
import signal

def _argparse():
	EXIT_FLAG = False
	parser = argparse.ArgumentParser(add_help=False, description='ei client')
	parser.add_argument('--help', '-H',  action='store_true', dest='HELPS', default=False, help='show this help message and exit')
	parser.add_argument('--version', '-v', '-V', action='store_true', dest="VERSION", default=False,  help='show version')
	parser.add_argument('--print', action='store_true', dest="PRINT", default=False,  help='show args')
	parser.add_argument('--config', '-c', action='store', dest="CONFIG", default='mysql_agent.yaml')

	parser.add_argument('ACTION', nargs='?', default='status', choices=['start','stop','status'], action='store', )
	parser.add_argument('SERVICE', nargs='?', default='all', choices=['monitor','transclient','all'], action='store', )

	if parser.parse_args().VERSION:
		print("VERSION: v1.1")
		EXIT_FLAG = True

	if parser.parse_args().PRINT:
		print('todo.... 有空了再去写. 反正就是打印 CONF[] , 优先位置参数,然后配置文件. 参数太多了, 目前就只要配置文件了吧...')
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

	#只适合unix,  暂不考虑win兼容
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
	
	#格式化一些路径问题
	conf['BASEDIR'] = f"{os.path.abspath(conf['BASEDIR'])}"
	conf['PID1'] = f"{conf['BASEDIR']}/{conf['MYSQL_HOST']}_{conf['MYSQL_PORT']}_monitor.pid" #monitor pid
	conf['PID2'] = f"{conf['BASEDIR']}/{conf['MYSQL_HOST']}_{conf['MYSQL_PORT']}_transclient.pid" #trans pid
	conf['LOG'] = f"{conf['BASEDIR']}/{conf['MYSQL_HOST']}_{conf['MYSQL_PORT']}.log"
	conf['TRANS_STATUS'] = f"{conf['BASEDIR']}/.{conf['MYSQL_HOST']}_{conf['MYSQL_PORT']}_trans.status"
	#然后解析命令行参数 去覆盖conf中的部分值. 但是我懒得很, 就不写了. TODO
	#for x in 

	#创建对应的目录
	os.makedirs(conf['BASEDIR'],exist_ok=True)

	#workdir 入口文件的路径
	conf['_WORKDIR'] = os.path.dirname(os.path.abspath(sys.argv[0]))


	#初始化authkey
	authkey_length = len(conf['MONITOR_SERVER_AUTHKEY'].encode('utf-8'))
	if authkey_length > 1021:
		print(f'AUTHKEY MUST BE LESS THAN 1021. {con["AUTHKEY"]}')
		sys.exit(3)
	elif authkey_length < 1021:
		conf['MONITOR_SERVER_AUTHKEY'] = conf['MONITOR_SERVER_AUTHKEY'].encode('utf-8') + int(0).to_bytes(1021-authkey_length,'big')
	else:
		conf['MONITOR_SERVER_AUTHKEY'] = conf['MONITOR_SERVER_AUTHKEY'].encode('utf-8')

	if parser.ACTION == 'status':
		monitor_client_pid = exist2(conf['PID1'])
		trans_client_pid = exist2(conf['PID2'])
		if monitor_client_pid:
			print(f'monitor client running({monitor_client_pid}).')
		else:
			print('monitor maybe closed.')
		if trans_client_pid:
			print(f'transclient running({trans_client_pid}).')
		else:
			print('transclient maybe closed.')

	elif parser.ACTION == 'start':
		if (parser.SERVICE == 'monitor' or parser.SERVICE == 'all') and exist_process_from_pidfile(conf['PID1']):
			monitor_instance = monitor_client.monitor_client(conf,conf['PID1'])
			monitor_instance.start()
			print('monitor start.')
		if (parser.SERVICE == 'transclient' or parser.SERVICE == 'all') and exist_process_from_pidfile(conf['PID2']):
			trans_instance = trans_client.transclient(conf,conf['PID2'])
			trans_instance.start()
			print('transclient start.')

	elif parser.ACTION == 'stop':
		#signal.signal(signalnum, handler)  #signalnum信号量, handler处理函数,一般就是sync,close
		if (parser.SERVICE == 'monitor' or parser.SERVICE == 'all'):
			try:
				os.kill(get_data(conf['PID1']), signal.SIGUSR1) #kill -10 pid
				print('closed monitor client')
			except:
				pass
		if (parser.SERVICE == 'transclient' or parser.SERVICE == 'all'):
			try:
				os.kill(get_data(conf['PID2']), signal.SIGUSR1) #kill -10 pid
				print('closed transclient')
			except:
				pass

	else:
		print(f'unknown {parser.ACTION}')


	
	
