PACK_MAX_SIZE = 32*1024
from mysql_agent import COMMAND

def senddataforserver(conn,bdata)->bool:
	LENGTH = len(bdata)
	ROWS = int(LENGTH / PACK_MAX_SIZE)
	LASTPACK_SIZE = LENGTH % PACK_MAX_SIZE
	actionpack = COMMAND.EI_OK.to_bytes(1,'big') +\
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
		return True if int.from_bytes(conn.recv(1)[0:1],'big') == COMMAND.EI_OK and FAILED_PACK == 0 else False
	else:
		return False

def getataforserver(conn,bdata):
	_recv_data = _conn.recv(32)
	if COMMAND.EI_OK.to_bytes(1,'big') == _recv_data[0:1]:
		PACK_MAX_SIZE = int.from_bytes(_recv_data[1:5],'big')
		ROWS = int.from_bytes(_recv_data[5:9],'big')
		LENGTH = int.from_bytes(_recv_data[9:13],'big')
		LASTPACK_SIZE = int.from_bytes(_recv_data[13:17],'big')
