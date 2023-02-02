from COMMAND import *
import binascii
PACK_MAX_SIZE = 32*1024 #32KB #单个包最大限制


def senddataforserver(conn,bdata)->bool:
	LENGTH = len(bdata)
	ROWS = int(LENGTH / PACK_MAX_SIZE)
	LASTPACK_SIZE = LENGTH % PACK_MAX_SIZE
	actionpack = EI_OK.to_bytes(1,'big') +\
		PACK_MAX_SIZE.to_bytes(4,'big') +\
		ROWS.to_bytes(4,'big') +\
		LENGTH.to_bytes(4,'big') +\
		LASTPACK_SIZE.to_bytes(4,'big') +\
		int(0).to_bytes(15,'big')
	FAILED_PACK = 0
	if conn.send(actionpack) == len(actionpack):
		for x in range(ROWS):
			if conn.send(bdata[x*PACK_MAX_SIZE:x*PACK_MAX_SIZE+PACK_MAX_SIZE]) != PACK_MAX_SIZE:
				FAILED_PACK += 1
		if LASTPACK_SIZE > 0:
			if conn.send(bdata[-LASTPACK_SIZE:]) != LASTPACK_SIZE:
				FAILED_PACK += 1
		return True if int.from_bytes(conn.recv(1)[0:1],'big') == EI_OK and FAILED_PACK == 0 else False
	else:
		return False

def senddata(conn,bdata)->bool:
	LENGTH = len(bdata)
	ROWS = int(LENGTH / PACK_MAX_SIZE)
	LASTPACK_SIZE = LENGTH % PACK_MAX_SIZE
	actionpack = EI_DATA.to_bytes(1,'big') +\
		EI_MONITOR_DATA.to_bytes(1,'big') +\
		PACK_MAX_SIZE.to_bytes(4,'big') +\
		ROWS.to_bytes(4,'big') +\
		LENGTH.to_bytes(4,'big') +\
		LASTPACK_SIZE.to_bytes(4,'big') +\
		int(0).to_bytes(14,'big')
	FAILED_PACK = 0
	if conn.send(actionpack) == len(actionpack):
		for x in range(ROWS):
			if conn.send(bdata[x*PACK_MAX_SIZE:x*PACK_MAX_SIZE+PACK_MAX_SIZE]) != PACK_MAX_SIZE:
				FAILED_PACK += 1
		if LASTPACK_SIZE > 0:
			if conn.send(bdata[-LASTPACK_SIZE:]) != LASTPACK_SIZE:
				FAILED_PACK += 1
		return True if int.from_bytes(conn.recv(1)[0:1],'big') == EI_OK and FAILED_PACK == 0 else False
	else:
		return False

def sendfile(conn,bdata,date)->bool:
	LENGTH = len(bdata)
	ROWS = int(LENGTH / PACK_MAX_SIZE)
	LASTPACK_SIZE = LENGTH % PACK_MAX_SIZE
	actionpack = EI_DATA.to_bytes(1,'big') +\
		EI_MONITOR_FILEGZ.to_bytes(1,'big') +\
		PACK_MAX_SIZE.to_bytes(4,'big') +\
		ROWS.to_bytes(4,'big') +\
		LENGTH.to_bytes(4,'big') +\
		LASTPACK_SIZE.to_bytes(4,'big') +\
		int(date.timestamp()).to_bytes(4,'big') +\
		binascii.crc32(bdata).to_bytes(4,'big') +\
		int(0).to_bytes(6,'big')
	FAILED_PACK = 0
	if conn.send(actionpack) == len(actionpack):
		for x in range(ROWS):
			if conn.send(bdata[x*PACK_MAX_SIZE:x*PACK_MAX_SIZE+PACK_MAX_SIZE]) != PACK_MAX_SIZE:
				FAILED_PACK += 1
		if LASTPACK_SIZE > 0:
			if conn.send(bdata[-LASTPACK_SIZE:]) != LASTPACK_SIZE:
				FAILED_PACK += 1
		return True if int.from_bytes(conn.recv(1)[0:1],'big') == EI_OK and FAILED_PACK == 0 else False
	
	else:
		return False
	

def actionpack(conn,)->dict: #server端用的, 返回dict.只解析常用的字段.
	errormsg = ''
	try:
		pack = conn.recv(1024)
		status = True
	except Exception as e:
		status = False
		errormsg = e
		return {'STATUS':status,'MSG':errormsg}
	ACTION = int.from_bytes(pack[0:1],'big')
	PACK_MAX_SIZE = int.from_bytes(pack[1:5],'big')
	ROWS = int.from_bytes(pack[5:9],'big')
	LENGTH = int.from_bytes(pack[9:13],'big')
	LASTPACK_SIZE = int.from_bytes(pack[13:17],'big')
	DATE = datetime.datetime.fromtimestamp(int.from_bytes(pack[17:21],'big'))
	conn.send(EI_OK.to_bytes(1,'big'))
	return {'ACTION':ACTION,'PACK_MAX_SIZE':PACK_MAX_SIZE,'ROWS':ROWS,'LENGTH':LENGTH,'LASTPACK_SIZE':LASTPACK_SIZE,'DATE':DATE,'DATA':pack,'STATUS':status}
