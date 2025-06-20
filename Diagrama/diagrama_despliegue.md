subgraph "DMZ (Demilitarized Zone)"
    LB[🔄 Load Balancer<br/>nginx/HAProxy]
    WAF[🛡️ Web Application Firewall]
    CDN[🌐 CDN<br/>CloudFlare/AWS CloudFront]
end

subgraph "Web Tier"
    WS1[🖥️ Web Server 1<br/>Apache/nginx<br/>Port: 80, 443]
    WS2[🖥️ Web Server 2<br/>Apache/nginx<br/>Port: 80, 443]
    WS3[🖥️ Web Server 3<br/>Apache/nginx<br/>Port: 80, 443]
end

subgraph "Application Tier"
    AS1[⚙️ App Server 1<br/>Tomcat/Node.js<br/>Port: 8080]
    AS2[⚙️ App Server 2<br/>Tomcat/Node.js<br/>Port: 8080]
    AS3[⚙️ App Server 3<br/>Tomcat/Node.js<br/>Port: 8080]
end

subgraph "Database Tier"
    DB_Master[🗄️ Database Master<br/>MySQL/PostgreSQL<br/>Port: 3306/5432]
    DB_Slave1[🗄️ Database Slave 1<br/>MySQL/PostgreSQL<br/>Port: 3306/5432]
    DB_Slave2[🗄️ Database Slave 2<br/>MySQL/PostgreSQL<br/>Port: 3306/5432]
end

subgraph "Cache Layer"
    Redis[🚀 Redis Cache<br/>Port: 6379]
    Memcached[📦 Memcached<br/>Port: 11211]
end

subgraph "File Storage"
    FileServer[📁 File Server<br/>NFS/AWS S3]
end

subgraph "Monitoring & Logging"
    Monitor[📊 Monitoring<br/>Prometheus/Grafana]
    LogServer[📝 Log Server<br/>ELK Stack]
end

subgraph "Backup & Recovery"
    BackupServer[💾 Backup Server<br/>Scheduled Backups]
end

%% Connections
Users --> CDN
CDN --> WAF
WAF --> LB

LB --> WS1
LB --> WS2
LB --> WS3

WS1 --> AS1
WS2 --> AS2
WS3 --> AS3

AS1 --> DB_Master
AS2 --> DB_Master
AS3 --> DB_Master

AS1 --> DB_Slave1
AS2 --> DB_Slave1
AS3 --> DB_Slave2

AS1 --> Redis
AS2 --> Redis
AS3 --> Memcached

AS1 --> FileServer
AS2 --> FileServer
AS3 --> FileServer

DB_Master --> DB_Slave1
DB_Master --> DB_Slave2

%% Monitoring connections
WS1 -.-> Monitor
WS2 -.-> Monitor
WS3 -.-> Monitor
AS1 -.-> Monitor
AS2 -.-> Monitor
AS3 -.-> Monitor
DB_Master -.-> Monitor

%% Logging connections
WS1 -.-> LogServer
AS1 -.-> LogServer
DB_Master -.-> LogServer

%% Backup connections
DB_Master -.-> BackupServer
FileServer -.-> BackupServer

%% Styling
classDef webTier fill:#e1f5fe
classDef appTier fill:#f3e5f5
classDef dbTier fill:#e8f5e8
classDef cacheTier fill:#fff3e0
classDef dmzTier fill:#ffebee
classDef monitorTier fill:#f1f8e9

class WS1,WS2,WS3 webTier
class AS1,AS2,AS3 appTier
class DB_Master,DB_Slave1,DB_Slave2 dbTier
class Redis,Memcached cacheTier
class LB,WAF,CDN dmzTier
class Monitor,LogServer,BackupServer monitorTier</content>
