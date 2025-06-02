Direct connection

Ideal for applications with persistent, long-lived connections, such as those running on virtual machines or long-standing containers.

postgresql://postgres:[YOUR-PASSWORD]@db.ryfkuilvlbuzaxniqxwx.supabase.co:5432/postgres

View parameters

host:
db.ryfkuilvlbuzaxniqxwx.supabase.co

port:
5432

database:
postgres

user:
postgres


---
Transaction pooler
Shared Pooler
Ideal for stateless applications like serverless functions where each interaction with Postgres is brief and isolated.

postgresql://postgres.ryfkuilvlbuzaxniqxwx:[YOUR-PASSWORD]@aws-0-sa-east-1.pooler.supabase.com:6543/postgres

host:
aws-0-sa-east-1.pooler.supabase.com

port:
6543

database:
postgres

user:
postgres.ryfkuilvlbuzaxniqxwx

pool_mode:
transaction
---
Session pooler

Shared Pooler

Only recommended as an alternative to Direct Connection, when connecting via an IPv4 network.

postgresql://postgres.ryfkuilvlbuzaxniqxwx:[YOUR-PASSWORD]@aws-0-sa-east-1.pooler.supabase.com:5432/postgres

host:
aws-0-sa-east-1.pooler.supabase.com

port:
5432

database:
postgres

user:
postgres.ryfkuilvlbuzaxniqxwx

pool_mode:
session
---