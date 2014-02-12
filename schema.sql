drop table if exists user;
create table user (
	id INTEGER primary key autoincrement,
	login TEXT,
	pass TEXT
);
drop table if exists weights;
create table weights (
	id INTEGER primary key autoincrement,
	user_id INTEGER,
	timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	weight REAL
);