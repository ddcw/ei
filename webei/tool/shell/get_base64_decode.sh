#!/usr/bin/env bash
echo $* | base64 -d || echo "不支持base64 命令!"
