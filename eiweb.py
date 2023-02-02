import flask
import time
from mysql_agent import daemon
import webapp
from gevent import pywsgi
class web(daemon.Daemon):
	def close(self,):
		print('closed')
	def start(self,):
		host = self.conf['WEB_HOST']
		port = self.conf['WEB_PORT']
		self.set_daemon()
		#print('start web')
		test = webapp.testweb(self.conf)
		if test.connect():
			print(f'start web with {host}:{port}')
		else:
			print('connect faild....')
			return
		app = test.run()
		server = pywsgi.WSGIServer((host, port), app)
		server.serve_forever()
