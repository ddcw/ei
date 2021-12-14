#!/usr/bin/env bash
#write by ddcw at 2021.12.14
BASE_DIR="BASE_DIR_"
PID_FILE="PID_FILE_"
LOG_FILE="LOG_FILE_"
FLAGS="THIS_IS_FLAG_NO_ANYTHING_ABCDEFGHIJKLMNOPQRSTUVWXYZ_BY_DDCW_FOR_EI"

dt=$(date +%Y%m%d-%H:%M:%S)

current_ei_pid=$(ps -ef | grep python | grep flag=${FLAGS} | grep ei | awk '{print $2}')

if [ ! -z ${current_ei_pid} ];then
	pidfile_pid=$(cat ${PID_FILE})
	if [ ${pidfile_pid} -eq ${current_ei_pid} ]; then
		echo "ei的PID为: ${current_ei_pid} , 即将停掉"
		echo "[ ${dt} ] 人工kill了 ${current_ei_pid}" >> ${LOG_FILE}
		kill -9 ${current_ei_pid}
		cat /dev/null > ${PID_FILE}
		echo "已停止."
		exit 0
	else
		echo "[warning] 当前的PID${current_ei_pid} 和 记录的PID(${pidfile_pid}) 不一致"
		echo "[ ${dt} ] 人工kill了 ${current_ei_pid}" >> ${LOG_FILE}
		kill -9 ${current_ei_pid}
		cat /dev/null > ${PID_FILE}
		echo "已停止."
		exit 2
	fi
else
	echo "ei未运行."
	exit 0
fi

