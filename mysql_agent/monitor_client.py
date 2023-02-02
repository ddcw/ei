import daemon
import signal
import sys
import time
import datetime
from mysql_status_pack import mysql_status_pack
import logging
import pymysql
import ddcw_ei_data


def get_datab(conn):
	cursor = conn.cursor()
	cursor.execute('show global status')
	data = cursor.fetchall()
	datadict = dict((k,v) for k,v in data)
	datadict['itime'] = int(time.time())
	return mysql_status_pack(datadict)



class monitor_client(daemon.Daemon):
	def close(self):
		try:
			self.conn.close()
		except Exception as e:
			pass
		try:
			self.eiw.close()
		except Exception as e:
			pass
		try:
			self.log.info('monitor closed.')
		except Exception as e:
			pass
		sys.exit(0)

	def _stop(self,):
		self.close()
		self.log.info('closed')
		sys.exit(0)
			

	def start(self,):
		self.set_daemon() #设置为后台


		#设置log
		logfilename = self.conf['LOG']
		fmt = '%(asctime)s %(levelname)s %(message)s'
		logging.basicConfig(level=logging.INFO,format=fmt,filename=logfilename)
		log = logging.getLogger('eidatalog')

		self.log = log


		while True:
			while True:
				try:
					conn = pymysql.connect(
					host = self.conf['MYSQL_HOST'],
					port = self.conf['MYSQL_PORT'],
					user = self.conf['MYSQL_USER'],
					password = self.conf['MYSQL_PASSWORD'],
					unix_socket = self.conf['MYSQL_SOCKET']
					)
					self.conn = conn
					log.info('connect mysql success.')
					break
				except Exception as e:
					log.error(e)
					time.sleep(10)



			
			#设置eiw 负责写数据, 归档, 清除过期数据, 数据文件切换. 挺多事情的...  不过判断 days != current_day 才做
			eiw = ddcw_ei_data.write_data(self.conf,log)
			if eiw.open():
				self.eiw = eiw
			else:
				log.error('gg')
				sys.exit(3)


			#开始监控
			while True:
				begin_time = time.time()
				try:
					bdata = get_datab(conn)
				except Exception as e:
					msg = f'pack error, {e}'
					log.error(msg)
					break
				if eiw.write(bdata,) != 0:
					msg = f'write data error. {begin_time}'
					log.error(msg)
				try:
					#time.sleep(1-(time.time()-begin_time))
					time.sleep(1)
				except:
					pass
			self.close()
