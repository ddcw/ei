#AUTH_PACK 为1024字节
#ACTION_PACK均为32字节.
EI_OK = 0x01 #成功
EI_FAILED = 0x02 #失败
EI_AUTH = 0x03 #认证包
EI_CLOSE = 0x04 #关闭连接 当接收到这个包的时候就发送EI_CLOSE并关闭连接.
EI_DATA = 0x05 #监控数据, 文件之类的都走这个 ACTION  TYPE(data/file/filegz) 
EI_GET = 0x06 #获取数据
EI_UNKNOWN = 0x07 #未知命令
EI_TODO = 0x08 #未实现的功能...
EI_TASK = 0x09 #task数据
EI_ADD = 0x0a #添加主机,数据库,CLUSTER信息
EI_MODIFY_PASSWORD = 0x0b #修改admin账号密码

#下面这三不属于上面的ACTION
EI_MONITOR_DATA = 0x09 #monitor data
EI_MONITOR_FILE = 0x0a #monitor file #未使用
EI_MONITOR_FILEGZ = 0x0b #monitor file gz
