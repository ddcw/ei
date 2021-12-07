DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS ei_db;
DROP TABLE IF EXISTS ei_host;

create table user(
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	username varchar(32), 
	password varchar(200), 
	create_time date,
	status int
	);

create table ei_db(
	db_instance_id INTEGER PRIMARY KEY AUTOINCREMENT,
	db_instance_name varchar(200),
	db_type varchar(15),
	db_version varchar(20),
	db_host varchar(32),
	db_port int,
	db_user varchar(32),
	db_password varchar(200)
	status int
);

create table ei_host(
	host_instance_id INTEGER PRIMARY KEY AUTOINCREMENT,
	host_instance_name varchar(200),
	host_type varchar(20),
	host_version varchar(20),
	host_ssh_ip varchar(32),
	host_ssh_port int,
	host_ssh_username varchar(32),
	host_ssh_password varchar(200),
	status int
);
