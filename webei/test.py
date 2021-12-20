#!/usr/bin/python

import sqlite3

conn = sqlite3.connect('ei.db')

c = conn.cursor()
print(list(c.execute("select host_instance_id,host_instance_name from ei_host where host_author='ddcw'")))
conn.commit()
conn.close()
