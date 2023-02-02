import daemon
import signal
import sys
import time
import datetime
import socket
import COMMAND
import compressdata
import binascii
import logging
import os
import logging
import transdata
#import math


class transclient(daemon.Daemon):
	def close(self):
		try:
			self.f.close()
		except Exception as e:
			pass
		try:
			self.conn.close() #发包clsoe. TODO
		except:
			pass
		self.log.info('transclient Closed.')
		sys.exit(0)

	def connect(self):
		HOST = self.conf['MONITOR_SERVER_HOST']
		PORT = self.conf['MONITOR_SERVER_PORT']
		conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			conn.connect((HOST,PORT))
			if conn.send(COMMAND.EI_AUTH.to_bytes(1,'big') + self.conf["MYSQL_PORT"].to_bytes(2,'big') + self.conf["MONITOR_SERVER_AUTHKEY"]) == 1024:
				if int.from_bytes(conn.recv(1),'big') == COMMAND.EI_OK:
					self.log.info('Login Succeeded.')
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
	
	def start(self,):
		self.set_daemon() #设置为后台

		BASEDIR = self.conf['BASEDIR']
		HOST = self.conf['MYSQL_HOST']
		PORT = self.conf['MYSQL_PORT']
		conf = self.conf
		#信号注册
		#signal.signal(signal.SIGTERM, self.close())
		#signal.signal(signal.SIGINT, self.close()) 

		#连接失败, sleep(60) 然后重连

		#设置log
		logfilename = self.conf['LOG']
		fmt = '%(asctime)s %(levelname)s %(message)s'
		logging.basicConfig(level=logging.INFO,format=fmt,filename=logfilename)
		log = logging.getLogger('eidatalog')
		self.log = log

		#year_month_day_hour_minute_second (取第一行 自动去掉首尾的空格) #为了减少写IO, 只有切换文件的时候, 才flush TRANS_STATUS
		transdata_date = datetime.datetime.now()
		if os.path.exists(self.conf['TRANS_STATUS']) and os.path.getsize(self.conf['TRANS_STATUS']) > 0:
			with open(self.conf['TRANS_STATUS'],'r') as f:
				_tmp = f.readline()
			try:
				year,month,day,hour,minute,second = _tmp.strip().split('_')
				transdata_date = datetime.datetime(int(year),int(month),int(day),int(hour),int(minute),int(second)) #已经同步完了的
			except Exception as e:
				log.warning(e)
		else:
			with open(self.conf['TRANS_STATUS'],'w') as f:
				msg = f'{transdata_date.year}_{transdata_date.month}_{transdata_date.day}_{transdata_date.hour}_{transdata_date.minute}_{transdata_date.second}'
				f.write(msg)

		while True:
			while True:
				if self.connect():
					break
				else:
					time.sleep(10) #每10秒重试一次.
			
			#传输文件
			timediff = datetime.datetime.now() - transdata_date
			if timediff.days > 0:
				msg = f'Will Send File Count : {timediff.days}'
			else:
				msg = f'No File Need To Be Transferred'
			log.info(msg)
			for x in range(timediff.days):
				#时分秒 重置为0
				transdata_date = datetime.datetime(transdata_date.year, transdata_date.month, transdata_date.day, 0,0,0)
				transdata_date += datetime.timedelta(days=+1)
				filename = f'{BASEDIR}/{HOST}_{PORT}_{transdata_date.year}_{transdata_date.month:02}_{transdata_date.day:02}.data'
				filenamegz = f'{filename}.gz'
				if os.path.exists(filenamegz):
					with open(filenamegz,'rb') as f:
						bdata = f.read()
				elif os.path.exists(filename):
					bdata = compressdata.compress_f2d(filename)
				else:
					msg = f'No File {filename}. Ignore It And Continue'
					log.error(msg)
					continue
				#msg = f'Sending File: {filename}'
				#log.info(msg)
				if transdata.sendfile(self.conn, bdata, transdata_date):
					msg = f'Send File SUCCESS. FILENAME:{filename}'
					log.info(msg)
				else:
					msg = f"Send File FAILED. Will Not Retransmission. FILENAME:{filename}"
					log.warning(msg)

				with open(self.conf['TRANS_STATUS'],'w') as f:
					msg = f'{transdata_date.year}_{transdata_date.month}_{transdata_date.day}_{transdata_date.hour}_{transdata_date.minute}_{transdata_date.second}'
					f.write(msg)

			if timediff.days > 0:
				msg = f'Send File Finish. {self.conf["TRANS_STATUS"]}'
				log.info(msg)
			msg = f'Transfer data from {transdata_date}'
			log.info(msg)
			#传输数据(每隔5秒, 监控文件时间是否变化, 变了就传输变化的部分, 并把最新进度写入 status文件)
			filename = f'{BASEDIR}/{HOST}_{PORT}_{transdata_date.year}_{transdata_date.month:02}_{transdata_date.day:02}.data'
			try:
				f = open(filename,'rb')
				self.f = f
				msg = f'Open File Success FILENAME:{filename}'
				log.info(msg)
			except Exception as e:
				msg = f'Open File {filename} FAILED. {e}'
				log.warning(msg)
				break
			offset = (transdata_date.hour*3600 + transdata_date.minute*60 + transdata_date.second)*1024
			while True:
				offset_diff = os.stat(f.fileno()).st_size - offset
				if offset_diff > 0 and offset_diff % 1024 == 0:
					f.seek(offset,0)
					bdata = f.read(offset_diff)
					offset += offset_diff
					try:
						if not transdata.senddata(self.conn, bdata):
							if not transdata.senddata(self.conn, bdata):
								msg = f"FAILD TO TRANSFER DATA. {bdata[0:4]}"
								log.info(msg)
					except ConnectionResetError:
						msg = f'Connection reset by peer. Will auto reconnect.'
						log.warning(msg)
						break
					except BrokenPipeError:
						msg = f'BrokenPipeError Will auto reconnect.'
						log.warning(msg)
						break

				elif transdata_date.day != datetime.datetime.now().day: #不是今天了, 切换f和刷新statu
					offset = 0*1024
					transdata_date = datetime.datetime.now()
					filename = f'{BASEDIR}/{HOST}_{PORT}_{transdata_date.year}_{transdata_date.month:02}_{transdata_date.day:02}.data'
					with open(self.conf['TRANS_STATUS'],'w') as tf:
						msg = f'{transdata_date.year}_{transdata_date.month}_{transdata_date.day}_{transdata_date.hour}_{transdata_date.minute}_{transdata_date.second}'
						tf.write(msg)
					try:
						f = open(filename,'rb')
						self.f = f
						msg = f'Open File Success FILENAME:{filename}'
						log.info(msg)
					except Exception as e:
						msg = f'Open File {filename} Failed. {e}'
						log.warning(msg)
						continue
				else:
					time.sleep(5)
			with open(self.conf['TRANS_STATUS'],'w') as tf:
				_tdate = datetime.datetime(transdata_date.year, transdata_date.month, transdata_date.day, 0, 0, 0)
				_tmstamp = int(_tdate.timestamp() + offset/1024)
				transdata_date = datetime.datetime.fromtimestamp(_tmstamp)
				msg = f'{transdata_date.year}_{transdata_date.month}_{transdata_date.day}_{transdata_date.hour}_{transdata_date.minute}_{transdata_date.second}'
				tf.write(msg)
			time.sleep(60)
			#self.close() #不退出
		
