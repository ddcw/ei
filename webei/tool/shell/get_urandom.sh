#!/usr/bin/env bash
head -10 /dev/urandom | md5sum | awk '{print $1}' || echo "暂不支持  head -10 /dev/urandom | md5sum | awk '{print \$1}'"
