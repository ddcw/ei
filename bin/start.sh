#!/usr/bin/env bash
#write by ddcw at 2021.12.14
BASE_DIR="BASE_DIR_"
PID_FILE="PID_FILE_"
LOG_FILE="LOG_FILE_"
FLAGS="THIS_IS_FLAG_NO_ANYTHING_ABCDEFGHIJKLMNOPQRSTUVWXYZ_BY_DDCW_FOR_EI"

dt=$(date +%Y%m%d-%H:%M:%S)
current_ei_pid=$(ps -ef | grep python | grep flag=${FLAGS} | grep ei | awk '{print $2}')

if [ ! -z ${current_ei_pid} ];then
	pidfile_pid=(cat ${PID_FILE})
	if [ ${pidfile_pid} -eq ${current_ei_pid} ]; then
		echo "ei正在运行, PID: ${current_ei_pid}"
		exit 0
	else
		echo ${current_ei_pid} > ${PID_FILE} && echo "ei正在运行, 但是当前PID(current_ei_pid)与记录的PID(pidfile_pid)不符, 已重新记录(${PID_FILE})"
	fi
else
	cd ${BASE_DIR}/webei
	. ${BASE_DIR}/webei/venv/bin/activate
	echo "[ ${dt} ] 人工启动中.." >> ${LOG_FILE}
	nohup python app.py flag=${FLAGS} >> ${LOG_FILE} 2>&1 &
	echo -n "启动中."
	sleep 1
	echo -n "."
	sleep 1
	echo -n "."
	sleep 1
	echo  "."
	current_ei_pid_2=$(ps -ef | grep python | grep flag=${FLAGS} | grep ei | awk '{print $2}')
	if [ ! -z ${current_ei_pid_2} ]; then
		echo ${current_ei_pid_2} > ${PID_FILE}
		echo "启动完成. 进程号: ${current_ei_pid_2}"
	fi
fi


