import psycopg2
conn = psycopg2.connect('postgresql://postgres.deafrefldvesvbpungjo:6cUxq1HLqJ8CMjxy@aws-1-ap-northeast-2.pooler.supabase.com:6543/postgres')
conn.autocommit = True
cur = conn.cursor()
cur.execute("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE pid != pg_backend_pid() AND state in ('idle', 'idle in transaction', 'idle in transaction (aborted)', 'disabled')")
print('Terminated idle connections!')
conn.close()
