#!/usr/bin/env bash
echo $* | base64  || echo "不支持base64 命令!"
