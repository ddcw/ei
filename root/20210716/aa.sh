#!/bin/env bash
#write by ddcw at 2021.07.20

hostinfo_file="${i}"
mysqlinfo_file="${i}"

for i in mysql*/*; 
do

if echo $i | grep hostinfo >/dev/null 2>&1; then
echo "======================系统信息  $(echo $i | awk -F / '{print $2}' | awk -F _ '{print $1}')================================="
echo -n "CPU:  "
grep -C 1 "==cpu version======" ${i}  | tail -1
echo -n "内存大小(M)  "
grep  "Mem:" ${i}   | awk '{print $2}'
	
if echo $i | awk -F / '{print $2}' | awk -F _ '{print $1}' | grep -E "10.80.88.62|10.80.88.63|10.100.8.192|10.80.88.35|10.80.88.59|10.100.8.188"; then
echo -n "磁盘空间(/app):     "
	grep  "% /app" ${i}   | awk '{print $3}'
else
echo -n "磁盘空间(/data):   "
	grep  "% /data" ${i}   | awk '{print $3}'
fi
grep -C 1 "=====hostname=======" ${i}  | tail -1

echo -n "系统负载(1,5,15)    "
grep -C 1 "==uptime================" ${i}  | tail -1 | awk '{print $(NF-2)" "$(NF-1)" "$NF}'
echo -n "cpu使用率(usr+sys)    "
grep -C 1 "avg-cpu:  %user   %nice" ${i}  | tail -1 | awk '{print $1"+"$3}' | bc
echo -n "内存使用率       "
grep -C 2 "=====memory&swap========" ${i}  | tail -1 | awk '{print $3"*100/"$2}' | bc
echo -n "swap使用率      "
grep -C 3 "=====memory&swap========" ${i}  | tail -1 | awk '{print $3"*100/"$2}' | bc
echo -n "vm.swappiness    "
grep -C 1 "===numa mount====" ${i}  | tail -1
#if echo $i | awk -F / '{print $2}' | awk -F _ '{print $1}' | grep -E "10.80.88.62|10.80.88.63|10.100.8.192|10.80.88.35|10.80.88.59|10.100.8.188"; then
echo -n "磁盘使用率(/app):     "
grep "% /app" ${i}  | tail -1 | awk '{print $(NF-1)"(剩余"$(NF-2)")"}'
#else
echo -n "磁盘使用率(/data):    "
#	grep  "% /data" ${i}   | awk '{print $3}'
grep "% /data" ${i}  | tail -1 | awk '{print $(NF-1)"(剩余"$(NF-2)")"}'
#fi
echo -n "IO利用率      "
testaaa=""
testaaa=$(grep sda $i | grep -v dev | head -1 | awk '{print $13}' >/dev/null 2>&1)
if [[ -z ${testaaa} ]]; then
grep sda ${i} | grep -v dev | head -1 | awk '{print $(NF-2)" "$(NF-1)" "$NF}'
else
grep sda ${i} | grep -v dev | head -1 | awk '{print $(10)" "$(13)" "$(14)}'
fi
echo ""
echo ""
echo ""
echo ""
echo ""
echo ""
echo ""
echo ""
echo ""
echo ""
echo ""
echo ""
echo ""


else
echo "=================================mysql info $(echo $i | awk -F / '{print $2}' | awk -F _ '{print $1}')=================="
echo -n "数据库版本:    "
grep "Server version:" ${i}  | awk -F : '{print $2}'
echo -n "端口:   "
grep "TCP port:" ${i}  | awk -F : '{print $2}'
echo -n "程序目录   "
grep "basedir :" ${i}  | awk -F : '{print $2}'
echo -n "数据目录   "
grep "datadir :" ${i}  | awk -F : '{print $2}'
echo -n "buffer_pool   "
grep "innodb_buffer_pool_size" ${i}  | awk  '{print $2"/1024/1024/1024"}' | bc
echo -n "库(表个数)"
grep "Tables counts :" ${i}  | awk -F : '{print $2}'
echo "字符集   "
grep " characterset:" ${i}
echo -n "sql_mode    "
grep "sql_mode" ${i}  | awk  '{print $2}'
echo -n "Query cache"
grep "query_cache_type" ${i}  | awk  '{print $2}'
echo -n "skip_name_resolve      "
grep "skip_name_resolve" ${i}  | awk  '{print $2}'
echo -n "log_warnings    "
grep "log_warnings" ${i}  | awk  '{print $2}'
echo -n "binlog格式    "
grep "binlog_format" ${i}  | awk  '{print $2}'
grep "binlog_row_image" ${i}  | awk  '{print $2}'
echo -n "server-id    "
grep "server_id" ${i}  | awk  '{print $2}' | tail -2 | head -1
grep "InnoDB buffer read" ${i}
grep "Thread cache" ${i}


grep "master_info_repository" ${i}  | awk  '{print $2}'
grep "relay_log_info_repository" ${i}  | awk  '{print $2}'


fi
done


























