#!/usr/bin/env bash
for i in {1..65536}; do if echo &>/dev/null > /dev/tcp/${1}/${i} ;then echo -e "${1}:${i} is open"; fi; done
