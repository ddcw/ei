import os
import time
import re
import datetime
import threading

import gzip
import shutil

ROW_SIZE = 1024
class write_data:
	def __init__(self,conf,log):
		self.flush_method = int(conf['FLUSH_SYNC'])
		self.flushs = 1 #刷新次数
		self.basedir = conf['BASEDIR']
		self.log = log
		self.host = conf['MYSQL_HOST']
		self.port = conf['MYSQL_PORT']

			
		

	def open(self,date = datetime.datetime.now()):
		#self.today = date.day
		self.today = datetime.datetime(date.year, date.month, date.day, 0, 0)
		filename = f'{os.path.abspath(self.basedir)}/{self.host}_{self.port}_{date.year}_{date.month:02}_{date.day:02}.data'
		msg = f'will write data to FILENAME: {filename}'
		self.log.info(msg)
		self.f = os.open(filename, os.O_RDWR|os.O_CREAT, 0o644)
		return True

	def write(self,data):
		t = datetime.datetime.fromtimestamp(int.from_bytes(data[0:4],'big'))
		time_diff = t - self.today
		if time_diff.days != 0: #不是today的了, 该修改today了, 然后调用next_day(), 后台线程去跑吧...
			self.today = t.day
			os.close(self.f)
			date = t
			filename = f'{os.path.abspath(self.basedir)}/{self.host}_{self.port}_{date.year}_{date.month:02}_{date.day:02}.data'
			msg = f'will write data to FILENAME: {filename}'
			log.info(msg)
			self.f = os.open(filename, os.O_RDWR|os.O_CREAT, 0o644)
			time_diff = t - self.today
			p = threading.Thread(target=self.next_day, )
			p.start()
			#p.join() #不需要去堵着...
		offset = int(time_diff.total_seconds()) * ROW_SIZE
		os.lseek(self.f, offset, 0)
		os.write(self.f, data)
		if self.flush_method == self.flushs:
			os.fsync(self.f)
			self.flushs = 1
		else:
			self.flushs += 1
		return 0
			

	#清除过期数据, 归档, 切换文件(write做,这里就不做了)
	def next_day(self,):
		log.info('开始归档')
		basedir = os.path.abspath(self.basedir)
		if os.path.isdir(basedir):
			files = os.listdir(basedir)
			pattern = re.compile('.*_,*\d{4}_\d{2}_\d{2}\.data')
			for x in files:
				if pattern.match(x):
					filename = f'{basedir}/{x}'
					new_filename = f'{basedir}/{x}.gz'
					with open(filename, 'rb') as f_in:
						with gzip.open(new_filename, 'wb') as f_out:
							shutil.copyfileobj(f_in, f_out)
					if self.conf["COMPRESS_REMOVED"]:
						os.remove(filename)
			
		log.info('归档完成')
		log.info('开始清理过期数据')
		if os.path.isdir(basedir):
			files = os.listdir(basedir)
			for x in files:
				if x[-4] != '.pid':
					filename = f'{basedir}/{x}'
					mtime = datetime.datetime.fromtimestamp(os.path.getmtime(filename))
					time_diff = datetime.datetime.now() - mtime
					if time_diff.days > conf['EXPIRED_DAYS']:
						try:
							os.remove(filename)
							msg = f'清除过期文件 {filename}'
							log.info(msg)
						except Exception as e:
							msg = f'清除过期文件 {filename} 失败'
							log.warning(msg)

		log.info('清理过期数据完成')
		
	def close(self,):
		os.fsync(self.f)
		return os.close(self.f)
