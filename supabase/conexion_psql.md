Connecting with PSQL

psql is a command-line tool that comes with Postgres.

Connecting with SSL#
You should connect to your database using SSL wherever possible, to prevent snooping and man-in-the-middle attacks.

You can obtain your connection info and Server root certificate from your application's dashboard:

Connection Info and Certificate.

Download your SSL certificate to /path/to/prod-supabase.cer.

#### El certificado esta en "C:\Users\zamor\UltiBotInversiones\supabase\prod-ca-2021.crt"

Find your connection settings. Go to your Database Settings and make sure Use connection pooling is checked. Change the connection mode to Session, and copy the parameters into the connection string:

< psql "sslmode=verify-full sslrootcert=/path/to/prod-supabase.cer host=[CLOUD_PROVIDER]-0-[REGION].pooler.supabase.com dbname=postgres user=postgres.[PROJECT_REF]"3 >


