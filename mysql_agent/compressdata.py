import gzip
import shutil
import time
#不判断文件是否存在, 由上层去判断.
#要使用其它压缩算法的,自己改.
#gzip.open() 打开的文件, 读写都自带压缩功能

#压缩文件,然后返回二进制数据
def compress_f2d(filename):
	with open(filename,'rb') as f:
		bdata = f.read()
	return gzip.compress(bdata)
	
#压缩文件, 返回压缩后的文件名
def compress_f2f(filename,newfilename = None):
	newfilename = f'{filename}.gz' if newfilename is None else newfilename
	with open(filename, 'rb') as f_in:
		with gzip.open(newfilename, 'wb') as f_out:
			shutil.copyfileobj(f_in, f_out)
	return newfilename

#压缩数据, 返回压缩后的数据
def compress_d2d(data):
	return gzip.compress(data)

#压缩数据, 返回压缩后的文件
def compress_d2f(data,filename=None):
	filename = f'tmpfile_{time.time()}.gz' if filename is None else filename
	with gzip.open(filename, 'wb') as f:
		f.write(data)
	return filename


#解压数据文件, 返回数据
def decompress_f2d(filename):
	with gzip.open(filename,'rb') as f:
		return f.read()

#解压数据文件, 返回解压后的数据文件名
def decompress_f2f(filename,newfilename=None):
	newfilename = f'{filename}.decompress' if newfilename is None else newfilename
	with gzip.open(filename, 'rb') as f_in:
		with open(newfilename, 'wb') as f_out:
			shutil.copyfileobj(f_in, f_out)
	return newfilename
		


#解压数据, 返回解压后的数据
def decompress_d2d(data):
	return gzip.decompress(data)

#解压数据, 返回解压后的数据文件
def decompress_d2f(data,filename=None):
	filename = f'tmpfile_{time.time()}.decompress' if filename is None else filename
	with gzip.open(filename,'wb') as f:
		f.write(data)
	return filename
