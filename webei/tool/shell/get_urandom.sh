#!/usr/bin/env bash
head -10 /dev/urandom | md5sum | awk '{print $1}' || echo "ζδΈζ―ζ  head -10 /dev/urandom | md5sum | awk '{print \$1}'"
