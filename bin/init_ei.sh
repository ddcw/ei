#!/usr/bin/env bash
#write by ddcw at 2021.12.14
#初始化脚本, 设置venv环境, 初始化sqlite库, 配置启停脚本
INSTALL_SCRIPT_DIR=$(realpath $0 )
BASE_DIR=${INSTALL_SCRIPT_DIR%/bin/init_ei.sh*} #全局路径
PID_FILE=${BASE_DIR}/run/ei.pid
LOG_FILE=${BASE_DIR}/log/ei.log

exits(){
  echo -e "[`date +%Y%m%d-%H:%M:%S`] \033[31;40m$1\033[0m"
  [ -z $2 ] || exit $2
  exit 1
}
echo_color() {
  detaillog1=$3
  [[ -z ${detaillog1} ]] && detaillog1=${details}
  case $1 in
    green)
      echo -e "\033[32;40m$2\033[0m"
      ;;
    red)
      echo -e "\033[31;40m$2\033[0m"
      ;;
    error|err|erro|ERROR|E|e)
      echo -e "[\033[1;5;41;33mERROR\033[0m `date +%Y%m%d-%H:%M:%S`] \033[1;41;33m$2\033[0m"
      ;;
    redflicker)
      echo -e "\033[1;5;41;33m$2\033[0m"
      ;;
    info|INFO|IF|I|i)
      echo -e "[\033[32;40mINFO\033[0m `date +%Y%m%d-%H:%M:%S`] \033[32;40m$2\033[0m"
      ;;
    highlightbold)
      echo -e "\033[1;41;33m$2\033[0m"
      ;;
    warn|w|W|WARN|warning)
      echo -e "[\033[31;40mWARNNING\033[0m `date +%Y%m%d-%H:%M:%S`] \033[31;40m$2\033[0m"
      ;;
    detail|d|det)
      echo -e "[\033[32;40mINFO\033[0m `date +%Y%m%d-%H:%M:%S`] \033[32;40m$2\033[0m"
      echo "[`date +%Y%m%d-%H:%M:%S`] $2" >> ${detaillog1}
      ;;
    n|null)
      echo -e "$2"
      ;;
    *)
      echo "INTERNAL ERROR: echo_color KEY VALUE"
      ;;
  esac
}

get_python_msg(){
	export PYTHON3_VERSION=$(python3 --version 2>/dev/null | awk '{print $NF}')
	export PYTHON3_DIR=$(which python3)
}


if which python3 >/dev/null 2>&1; then
	get_python_msg
else
	if which yum >/dev/null 2>&1; then
		echo "正在安装python3"
		yum -y install python3 >/dev/null 2>&1 && get_python_msg
	elif which apt >/dev/null 2>&1; then
		echo "正在安装python3"
		apt -y install python3 >/dev/null 2>&1 && get_python_msg
	else
		exits "NO PYTHON3 ,  you must install python3 first."
	fi

	if ! which python3 >/dev/null 2>&1; then
		echo "[ERROR] 请先安装python3"
		exit 1
	fi
fi

#config venv 建议是重新设置个venv, 但是ei的目的是简单轻量化, 就没必要了
if [ -d ${BASE_DIR}/webei/venv ] 2>/dev/null; then
	sed -i "/version/cversion = ${PYTHON3_VERSION}" ${BASE_DIR}/webei/venv/pyvenv.cfg

	sed -i "/webei/csetenv VIRTUAL_ENV \"${BASE_DIR}/webei/venv\"" ${BASE_DIR}/webei/venv/bin/activate.csh
	sed -i "/webei/cset -gx VIRTUAL_ENV \"${BASE_DIR}/webei/venv\"" ${BASE_DIR}/webei/venv/bin/activate.fish
	sed -i "/webei/cVIRTUAL_ENV=\"${BASE_DIR}/webei/venv\"" ${BASE_DIR}/webei/venv/bin/activate

	sed -i "/webei/c#!${BASE_DIR}/webei/venv/bin/python3" ${BASE_DIR}/webei/venv/bin/easy_install
	sed -i "/webei/c#!${BASE_DIR}/webei/venv/bin/python3" ${BASE_DIR}/webei/venv/bin/easy_install-3.6
	sed -i "/webei/c#!${BASE_DIR}/webei/venv/bin/python3" ${BASE_DIR}/webei/venv/bin/pip
	sed -i "/webei/c#!${BASE_DIR}/webei/venv/bin/python3" ${BASE_DIR}/webei/venv/bin/pip3
	sed -i "/webei/c#!${BASE_DIR}/webei/venv/bin/python3" ${BASE_DIR}/webei/venv/bin/pip3
	sed -i "/webei/c#!${BASE_DIR}/webei/venv/bin/python3" ${BASE_DIR}/webei/venv/bin/pip3.6
	sed -i "/webei/c#!${BASE_DIR}/webei/venv/bin/python3" ${BASE_DIR}/webei/venv/bin/flask
	
fi

#init-db
if [ -f ${BASE_DIR}/webei/ei.db  ] 2>/dev/null; then
	echo_color info "${BASE_DIR}/webei/ei.db 已存在,不会初始化ei.db. (初始化方法: python3 ${BASE_DIR}/webei/initdb.py)"	
else
	python3 ${BASE_DIR}/webei/initdb.py
fi

#mkdir tasks
mkdir -p ${BASE_DIR}/data/tasks

#touch ei.pid
touch ${BASE_DIR}/run/ei.pid

#mkdir pack
mkdir -p ${BASE_DIR}/pack/bin
mkdir -p ${BASE_DIR}/pack/customize
mkdir -p "${BASE_DIR}/pack/source"
mkdir -p ${BASE_DIR}/pack/other

#mkdir script
mkdir -p ${BASE_DIR}/script/bin
mkdir -p ${BASE_DIR}/script/customize
mkdir -p "${BASE_DIR}/script/source"
mkdir -p ${BASE_DIR}/script/other


#set webei/conf/ei.conf
sed -i "/log=/clog=${LOG_FILE}" ${BASE_DIR}/webei/conf/ei.conf

#set start and stop script
sed -i "/BASE_DIR_/cBASE_DIR=${BASE_DIR}" ${BASE_DIR}/bin/start.sh
sed -i "/PID_FILE_/cPID_FILE=${PID_FILE}" ${BASE_DIR}/bin/start.sh
sed -i "/LOG_FILE_/cLOG_FILE=${LOG_FILE}" ${BASE_DIR}/bin/start.sh

sed -i "/BASE_DIR_/cBASE_DIR=${BASE_DIR}" ${BASE_DIR}/bin/stop.sh
sed -i "/PID_FILE_/cPID_FILE=${PID_FILE}" ${BASE_DIR}/bin/stop.sh
sed -i "/LOG_FILE_/cLOG_FILE=${LOG_FILE}" ${BASE_DIR}/bin/stop.sh

echo "初始化完成."
