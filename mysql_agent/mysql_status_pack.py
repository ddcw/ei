#负责打包和解包mysql status 固定大小为1KB (虽然5.7基本上都是ulong类型L, 但为了兼容8.x 就全部使用ulonglong类型Q)
#https://dev.mysql.com/doc/refman/8.0/en/server-status-variables.html
import struct
def mysql_status_pack(data):
	#17*4+4*8 = 100
	bother = struct.pack('>17L4Q',
int(data["itime"]), #L
int(data["Aborted_clients"]),#L
int(data["Aborted_connects"]), #L m_aborted_connects
int(data["Connections"]), #L 连接次数(成功+失败)
int(data["Flush_commands"]), #L
int(data["Locked_connects"]), #L
int(data["Max_used_connections"]), #L 自服务器启动以来最大的连接数(业务峰值)
int(data["Ongoing_anonymous_transaction_count"]), #L  int32  匿名事务(gtid相关)
int(data["Open_files"]), #L ulong
int(data["Opened_files"]), #L ulong
int(data["Open_streams"]), #L ulong
int(data["Open_table_definitions"]), #L uint
int(data["Open_tables"]), #L uint
int(data["Opened_tables"]), #L ull
int(data["Prepared_stmt_count"]), #L ulong
int(data["Innodb_num_open_files"]), #L ulint
int(data["Uptime"]), #L 虽然是ll 但 uint就够了(136年)
int(data["Queries"]), #Q ull
int(data["Questions"]), #Q ull
int(data["Slow_queries"]), #Q ull
int(data["Opened_table_definitions"]), #Q ull
	)

	#4*4 = 16
	bbinlog = struct.pack('>4L',
int(data["Binlog_cache_disk_use"]),
int(data["Binlog_cache_use"]),
int(data["Binlog_stmt_cache_disk_use"]),
int(data["Binlog_stmt_cache_use"]),
	)

	#2*8 = 16
	bnet = struct.pack('>2Q',
int(data["Bytes_received"]),
int(data["Bytes_sent"]),
	)

	#93*8 = 744
	bcom = struct.pack('>26Q',
int(data["Com_call_procedure"]),
int(data["Com_delete"]),
int(data["Com_delete_multi"]),
int(data["Com_drop_table"]),
int(data["Com_drop_view"]),
int(data["Com_empty_query"]),
int(data["Com_execute_sql"]),
int(data["Com_explain_other"]),
int(data["Com_flush"]),
int(data["Com_insert"]),
int(data["Com_insert_select"]),
int(data["Com_lock_tables"]),
int(data["Com_prepare_sql"]),
int(data["Com_replace"]),
int(data["Com_replace_select"]),
int(data["Com_select"]),
int(data["Com_set_option"]),
int(data["Com_stmt_execute"]),
int(data["Com_stmt_close"]),
int(data["Com_stmt_fetch"]),
int(data["Com_stmt_prepare"]),
int(data["Com_stmt_reset"]),
int(data["Com_stmt_send_long_data"]),
int(data["Com_update"]),
int(data["Com_update_multi"]),
int(data["Com_stmt_reprepare"]),
	)

	#6*4 = 24
	bconnection_errors = struct.pack('>6L',
int(data["Connection_errors_accept"]),
int(data["Connection_errors_internal"]),
int(data["Connection_errors_max_connections"]),
int(data["Connection_errors_peer_address"]),
int(data["Connection_errors_select"]),
int(data["Connection_errors_tcpwrap"]),
	)

	#18*8 = 144
	bhandler = struct.pack('>18Q',
int(data["Handler_commit"]),
int(data["Handler_delete"]),
int(data["Handler_discover"]),
int(data["Handler_external_lock"]),
int(data["Handler_mrr_init"]),
int(data["Handler_prepare"]),
int(data["Handler_read_first"]),
int(data["Handler_read_key"]),
int(data["Handler_read_last"]),
int(data["Handler_read_next"]),
int(data["Handler_read_prev"]),
int(data["Handler_read_rnd"]),
int(data["Handler_read_rnd_next"]),
int(data["Handler_rollback"]),
int(data["Handler_savepoint"]),
int(data["Handler_savepoint_rollback"]),
int(data["Handler_update"]),
int(data["Handler_write"]),
	)

	#2*8+4 = 20
	btmp = struct.pack('>2Q1L',
int(data["Created_tmp_disk_tables"]),
int(data["Created_tmp_tables"]),
int(data["Created_tmp_files"]),
	)

	#15*8 = 120
	binnodb_buffer_pool = struct.pack('>15Q',
int(data["Innodb_buffer_pool_pages_data"]),
int(data["Innodb_buffer_pool_bytes_data"]),
int(data["Innodb_buffer_pool_pages_dirty"]),
int(data["Innodb_buffer_pool_bytes_dirty"]),
int(data["Innodb_buffer_pool_pages_flushed"]),
int(data["Innodb_buffer_pool_pages_free"]),
int(data["Innodb_buffer_pool_pages_misc"]),
int(data["Innodb_buffer_pool_pages_total"]),
int(data["Innodb_buffer_pool_read_ahead_rnd"]),
int(data["Innodb_buffer_pool_read_ahead"]),
int(data["Innodb_buffer_pool_read_ahead_evicted"]),
int(data["Innodb_buffer_pool_read_requests"]),
int(data["Innodb_buffer_pool_reads"]),
int(data["Innodb_buffer_pool_wait_free"]),
int(data["Innodb_buffer_pool_write_requests"]),
	)

#typedef unsigned long int ulint
	#8*8 = 64
	binnodb_data = struct.pack('>8Q',
int(data["Innodb_data_fsyncs"]),
int(data["Innodb_data_pending_fsyncs"]),
int(data["Innodb_data_pending_reads"]),
int(data["Innodb_data_pending_writes"]),
int(data["Innodb_data_read"]),
int(data["Innodb_data_reads"]),
int(data["Innodb_data_writes"]),
int(data["Innodb_data_written"]),
	)

	#2*8 = 16
	bdblwr = struct.pack('>2Q',
int(data["Innodb_dblwr_pages_written"]),
int(data["Innodb_dblwr_writes"]),
	)

	#7*8 = 56
	binnodb_log = struct.pack('>7Q',
int(data["Innodb_log_waits"]),
int(data["Innodb_log_write_requests"]),
int(data["Innodb_log_writes"]),
int(data["Innodb_os_log_fsyncs"]),
int(data["Innodb_os_log_pending_fsyncs"]),
int(data["Innodb_os_log_pending_writes"]),
int(data["Innodb_os_log_written"]),
	)

	#4*8 = 32
	binnodb_page = struct.pack('>4Q',
int(data["Innodb_page_size"]),
int(data["Innodb_pages_created"]),
int(data["Innodb_pages_read"]),
int(data["Innodb_pages_written"]),
	)

	#5*8 = 40
	binnodb_row_lock = struct.pack('>5Q',
int(data["Innodb_row_lock_current_waits"]),
int(data["Innodb_row_lock_time"]),
int(data["Innodb_row_lock_time_avg"]),
int(data["Innodb_row_lock_time_max"]),
int(data["Innodb_row_lock_waits"]),
	)

	#4*8 = 32
	binnodb_row_op = struct.pack('>4Q',
int(data["Innodb_rows_deleted"]),
int(data["Innodb_rows_inserted"]),
int(data["Innodb_rows_read"]),
int(data["Innodb_rows_updated"]),
	)

#int(data["Innodb_truncated_status_writes"]), show engine innodb status被截断的次数


	#5*8 = 40
	bselect = struct.pack('>5Q',
int(data["Select_full_join"]),
int(data["Select_full_range_join"]),
int(data["Select_range"]),
int(data["Select_range_check"]),
int(data["Select_scan"]),
	)

	#4*8 = 32
	bsort = struct.pack('>4Q',
int(data["Sort_merge_passes"]), #ulonglong filesort_merge_passes
int(data["Sort_range"]),
int(data["Sort_rows"]),
int(data["Sort_scan"]),
	)

	#2*4 = 8
	btable_lock = struct.pack('>2L',
int(data["Table_locks_immediate"]),
int(data["Table_locks_waited"]),
	)

	#3*8 = 24
	btable_open_cache = struct.pack('>3Q',
int(data["Table_open_cache_hits"]),
int(data["Table_open_cache_misses"]),
int(data["Table_open_cache_overflows"]),
	)
	
	#4*4 = 16
	bthreads = struct.pack('>4L',
int(data["Threads_cached"]),
int(data["Threads_connected"]),
int(data["Threads_created"]),
int(data["Threads_running"]),
	)

	#2*8  填充数据, 前面的加起来1008 了, 差个 16字节
	bcreate_db_table = struct.pack('>2Q',
int(data["Com_create_table"]),
int(data["Com_create_db"]),
	)

	bdata = bother + bbinlog + bnet + bcom + bconnection_errors + bhandler + btmp + binnodb_buffer_pool + binnodb_data + bdblwr + binnodb_log + binnodb_page + binnodb_row_lock + binnodb_row_op + bselect + bsort + btable_lock + btable_open_cache + bthreads + bcreate_db_table
	return bdata

def mysql_status_unpack(bdata):
	data = {}
	#grep 'int(data\[' mysql_status_pack.py | awk -F '(' '{print $2}' | awk -F ')' '{print $1","}' | tr '\n' ' '
	data["itime"], data["Aborted_clients"], data["Aborted_connects"], data["Connections"], data["Flush_commands"], data["Locked_connects"], data["Max_used_connections"], data["Ongoing_anonymous_transaction_count"], data["Open_files"], data["Opened_files"], data["Open_streams"], data["Open_table_definitions"], data["Open_tables"], data["Opened_tables"], data["Prepared_stmt_count"], data["Innodb_num_open_files"], data["Uptime"], data["Queries"], data["Questions"], data["Slow_queries"], data["Opened_table_definitions"], data["Binlog_cache_disk_use"], data["Binlog_cache_use"], data["Binlog_stmt_cache_disk_use"], data["Binlog_stmt_cache_use"], data["Bytes_received"], data["Bytes_sent"], data["Com_call_procedure"], data["Com_delete"], data["Com_delete_multi"], data["Com_drop_table"], data["Com_drop_view"], data["Com_empty_query"], data["Com_execute_sql"], data["Com_explain_other"], data["Com_flush"], data["Com_insert"], data["Com_insert_select"], data["Com_lock_tables"], data["Com_prepare_sql"], data["Com_replace"], data["Com_replace_select"], data["Com_select"], data["Com_set_option"], data["Com_stmt_execute"], data["Com_stmt_close"], data["Com_stmt_fetch"], data["Com_stmt_prepare"], data["Com_stmt_reset"], data["Com_stmt_send_long_data"], data["Com_update"], data["Com_update_multi"], data["Com_stmt_reprepare"], data["Connection_errors_accept"], data["Connection_errors_internal"], data["Connection_errors_max_connections"], data["Connection_errors_peer_address"], data["Connection_errors_select"], data["Connection_errors_tcpwrap"], data["Handler_commit"], data["Handler_delete"], data["Handler_discover"], data["Handler_external_lock"], data["Handler_mrr_init"], data["Handler_prepare"], data["Handler_read_first"], data["Handler_read_key"], data["Handler_read_last"], data["Handler_read_next"], data["Handler_read_prev"], data["Handler_read_rnd"], data["Handler_read_rnd_next"], data["Handler_rollback"], data["Handler_savepoint"], data["Handler_savepoint_rollback"], data["Handler_update"], data["Handler_write"], data["Created_tmp_disk_tables"], data["Created_tmp_tables"], data["Created_tmp_files"], data["Innodb_buffer_pool_pages_data"], data["Innodb_buffer_pool_bytes_data"], data["Innodb_buffer_pool_pages_dirty"], data["Innodb_buffer_pool_bytes_dirty"], data["Innodb_buffer_pool_pages_flushed"], data["Innodb_buffer_pool_pages_free"], data["Innodb_buffer_pool_pages_misc"], data["Innodb_buffer_pool_pages_total"], data["Innodb_buffer_pool_read_ahead_rnd"], data["Innodb_buffer_pool_read_ahead"], data["Innodb_buffer_pool_read_ahead_evicted"], data["Innodb_buffer_pool_read_requests"], data["Innodb_buffer_pool_reads"], data["Innodb_buffer_pool_wait_free"], data["Innodb_buffer_pool_write_requests"], data["Innodb_data_fsyncs"], data["Innodb_data_pending_fsyncs"], data["Innodb_data_pending_reads"], data["Innodb_data_pending_writes"], data["Innodb_data_read"], data["Innodb_data_reads"], data["Innodb_data_writes"], data["Innodb_data_written"], data["Innodb_dblwr_pages_written"], data["Innodb_dblwr_writes"], data["Innodb_log_waits"], data["Innodb_log_write_requests"], data["Innodb_log_writes"], data["Innodb_os_log_fsyncs"], data["Innodb_os_log_pending_fsyncs"], data["Innodb_os_log_pending_writes"], data["Innodb_os_log_written"], data["Innodb_page_size"], data["Innodb_pages_created"], data["Innodb_pages_read"], data["Innodb_pages_written"], data["Innodb_row_lock_current_waits"], data["Innodb_row_lock_time"], data["Innodb_row_lock_time_avg"], data["Innodb_row_lock_time_max"], data["Innodb_row_lock_waits"], data["Innodb_rows_deleted"], data["Innodb_rows_inserted"], data["Innodb_rows_read"], data["Innodb_rows_updated"], data["Select_full_join"], data["Select_full_range_join"], data["Select_range"], data["Select_range_check"], data["Select_scan"], data["Sort_merge_passes"], data["Sort_range"], data["Sort_rows"], data["Sort_scan"], data["Table_locks_immediate"], data["Table_locks_waited"], data["Table_open_cache_hits"], data["Table_open_cache_misses"], data["Table_open_cache_overflows"], data["Threads_cached"], data["Threads_connected"], data["Threads_created"], data["Threads_running"], data["Com_create_table"], data["Com_create_db"]  = struct.unpack(">17L4Q4L2Q26Q6L18Q2Q1L15Q8Q2Q7Q4Q5Q4Q5Q4Q2L3Q4L2Q",bdata)
	return data
