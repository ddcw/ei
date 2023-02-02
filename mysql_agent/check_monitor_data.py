import argparse
import sys
import os
import datetime
import mysql_status_pack

ROWSIZE = 1024
def _argparse():
	parser = argparse.ArgumentParser(add_help=True, description='ddcw ei monitor data check')
	parser.add_argument('FILENAME', nargs='?', action='store', )
	return parser.parse_args()

def fdate(timest):
	date = datetime.datetime.fromtimestamp(timest)
	return f'{date.year}.{date.month:02}.{date.day:02}_{date.hour:02}:{date.minute:02}:{date.second:02}'

if __name__ == '__main__':
	parser = _argparse()
	filename = parser.FILENAME
	if not os.path.exists(filename):
		print(f'unknown file {filename}')
		sys.exit(0)
	filesize = os.path.getsize(filename)
	rows = int(filesize/ROWSIZE)
	f = open(filename,'rb')
	timestamp_list = []
	while rows > 0:
		rows -= 1
		bdata = f.read(1024)
		try:
			data = mysql_status_pack.mysql_status_unpack(bdata)
			if data['itime'] > 0:
				timestamp_list.append(data['itime'])
		except Exception as e:
			#print(e)
			#break
			pass
	if len(timestamp_list) > 0:
		print('begin\t\t\tend\t\t\tsecond')
		starttimestamp = timestamp_list[0]
		print(fdate(starttimestamp),'\t',end='')
		lasttimestamp = 4294967294
		for x in timestamp_list:
			if x - lasttimestamp > 1:
				print(fdate(lasttimestamp),'\t',lasttimestamp-starttimestamp)
				starttimestamp = x
				print(fdate(x),'\t',end='')
			lasttimestamp = x
		print(fdate(timestamp_list[len(timestamp_list)-1]),'\t',lasttimestamp-starttimestamp)
	else:
		print('no data.')

	f.close()
