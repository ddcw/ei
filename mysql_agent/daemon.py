import sys
import time
import signal
import atexit
import os

class Daemon:
	def __init__(self,conf,pidfile,stdin='/dev/null',stdout='/dev/null',stderr='/dev/null'):
		self.pidfile = pidfile
		self.conf = conf
		self.stdin = stdin
		self.stdout = conf['LOG'] if 'LOG' in conf else stdout #优先写日志.
		self.stderr = conf['LOG'] if 'LOG' in conf else stderr
		self.state = 'prepare' #进程状态

	def set_daemon(self,):
		if os.fork() > 0:
			sys.exit(1)
		#os.chdir('/') 
		os.chdir(self.conf['_WORKDIR']) 
		os.setsid()
		os.umask(0) #0o644

		#可选
		if os.fork() > 0:
			sys.exit(1)

		#flush
		sys.stdout.flush()
		sys.stderr.flush()

		#set stdin stdout stderr
		with open(self.stdin, 'r') as fread, open(self.stdout, 'a') as fwrite:
			os.dup2(fread.fileno(), sys.stdin.fileno())
			os.dup2(fwrite.fileno(), sys.stdout.fileno())
			os.dup2(fwrite.fileno(), sys.stderr.fileno())

		#pid
		with open(self.pidfile, 'w') as f:
			f.write(str(os.getpid()))

		#atexit
		atexit.register(os.remove, self.pidfile)

		#regiter signal
		signal.signal(signal.SIGTERM, self.stop)
		#signal.signal(signal.SIGKILL, self.stop)
		signal.signal(signal.SIGUSR1, self.stop)
		signal.signal(signal.SIGUSR2, self.stop)

	def start(self):
		pass


	def close(self,):
		pass

	def stop(self,*args,**kwargs):
		self.close()
	#	if os.path.exists(self.pidfile):
	#		with open(self.pidfile, 'r') as f:
	#			os.kill(int(f.read()), signal.SIGTERM)
	#		os.remove(self.pidfile)

