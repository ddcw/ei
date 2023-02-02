#负责加密和解密的. 后面再说, 先用base64吧.....

import base64
def encrypt(k,salt=None)->bytes:
	'''
	k: str, 需要加密的字符串
	salt: 盐
	'''
	return base64.b64encode(k.encode('utf-8'))

def decrypt(k,salt=None)->str:
	return base64.b64decode(k).decode('utf-8')
	
