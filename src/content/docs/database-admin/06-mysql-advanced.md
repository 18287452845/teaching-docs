---
title: "06.项目六 MySQL数据库高级安全维护"
---

# 06.项目六 MySQL数据库高级安全维护

# 任务一 使用Navicat进行MySQL数据库的维护

## 🧠 理论知识

### Navicat for MySQL 功能概述

Navicat for MySQL 是广泛使用的 MySQL 图形化管理工具，主要功能模块：

| 功能模块 | 说明 |
| --- | --- |
| **连接管理** | 同时管理多个MySQL服务器，支持SSH隧道加密连接 |
| **数据库/表管理** | 图形化创建、修改、删除数据库对象 |
| **数据编辑** | 表格形式查看和编辑数据，类似Excel操作 |
| **查询编辑器** | SQL编写和执行，代码高亮和自动补全 |
| **导入/导出** | 支持Excel、CSV、SQL、XML、JSON等多种格式 |
| **数据传输** | 在不同服务器/数据库间迁移数据 |
| **数据同步** | 比较并同步两个数据库的结构和数据差异 |
| **备份/还原** | 数据库备份和还原，支持计划任务 |
| **用户权限管理** | 图形化管理账户和权限 |
| **ER图** | 可视化显示表结构和关系 |

---

### 数据库备份策略

**逻辑备份 vs 物理备份**：

| 类型 | 工具 | 优点 | 缺点 | 适用场景 |
| --- | --- | --- | --- | --- |
| **逻辑备份** | mysqldump、Navicat | 可读性好，跨版本/跨平台 | 数据量大时慢 | 中小型数据库迁移 |
| **物理备份** | Percona XtraBackup | 速度快，支持热备份 | 只能在同版本/同平台还原 | 大型生产数据库 |

---

### Navicat 安全和维护工具

Navicat 内置维护功能（工具菜单或右键表）：

- **分析表**：分析并存储表的关键字分布
- **检查表**：检查表是否有错误
- **优化表**：整理碎片，回收磁盘空间（等价于`OPTIMIZE TABLE`）
- **修复表**：修复损坏的MyISAM表（等价于`REPAIR TABLE`）

---

## 🛠️ 实践操作

### 导入 employees 案例数据库

```bash
# 下载 employees 测试数据库（约170MB，约300万条记录）
git clone https://github.com/datacharmer/test_db.git
cd test_db

# 导入（大约需要几分钟）
mysql -u root -p < employees.sql

# 验证导入
mysql -u root -p -e "USE employees; SELECT COUNT(*) AS '员工总数' FROM employees;"
```

### 使用 Navicat 进行用户权限管理

1. 连接MySQL服务器
2. 点击顶部”用户”图标（或菜单：工具 → 用户）
3. 点击”新建用户” → 填写用户名、主机、密码
4. 切换到”服务器权限”选项卡 → 分配全局权限
5. 切换到”权限”选项卡 → 选择数据库/表 → 分配具体权限
6. 保存

### 使用 Navicat 备份数据库

**方式1：数据库转储（生成SQL文件）** ：

1. 右键数据库名 → **转储SQL文件** → **结构和数据**
2. 选择保存路径，生成 `.sql` 文件

**方式2：Navicat备份模块（推荐）** ：

1. 点击顶部”备份”图标
2. 点击”新建备份” → 选择备份数据库
3. 点击”开始” → 生成 `.nb3` 格式备份文件（Navicat专有格式）
4. 还原：右键备份文件 → 还原备份

### 设置自动运行的计划任务

1. Navicat 顶部工具栏 → **自动运行**
2. 点击”新建批处理作业” → 添加要执行的查询或备份任务
3. 点击”设置任务计划” → 配置执行时间（每日/每周等）
4. 保存并启用

---

# 任务二 MySQL 的权限管理

## 🧠 理论知识

### MySQL 权限系统

MySQL 权限验证分为两步：

```
第一步：连接验证 → 检查 用户名@主机名 是否存在 + 密码是否正确
第二步：操作验证 → 检查该用户是否有权执行当前操作（数据库级、表级、列级）
```

权限存储在 `mysql` 系统数据库的以下表中：

| 表名 | 存储内容 |
| --- | --- |
| `mysql.user` | 全局权限（所有数据库） |
| `mysql.db` | 数据库级权限 |
| `mysql.tables_priv` | 表级权限 |
| `mysql.columns_priv` | 列级权限 |

---

### MySQL 用户权限分类

| 权限分类 | 权限名称 | 说明 |
| --- | --- | --- |
| **数据权限** | SELECT、INSERT、UPDATE、DELETE | 增删改查数据 |
| **结构权限** | CREATE、ALTER、DROP、INDEX | 管理表结构 |
| **管理权限** | SUPER、PROCESS、RELOAD | 管理服务器 |
| **复制权限** | REPLICATION SLAVE、REPLICATION CLIENT | 主从复制 |
| **程序权限** | CREATE ROUTINE、EXECUTE | 存储过程/函数 |

---

### GRANT 命令详解

```sql
GRANT privilege_list
ON database.table
TO 'user'@'host' [IDENTIFIED BY 'password']
[WITH GRANT OPTION];
```

---

### MySQL 数据库攻防与加固

**常见MySQL攻击方式**：

| 攻击方式 | 说明 | 防御措施 |
| --- | --- | --- |
| SQL注入 | 在输入中插入恶意SQL代码 | 参数化查询、WAF |
| 弱密码暴力破解 | 遍历常见密码登录MySQL | 强密码策略、账户锁定 |
| 权限滥用 | 高权限账户被盗用 | 最小权限原则 |
| 未授权访问 | root允许远程连接 | 禁止root远程，限制来源IP |
| UDF提权 | 通过MySQL执行系统命令 | 禁用`secure_file_priv`滥用 |

---

## 🛠️ 实践操作

### 账号管理完整演练

```sql
-- === 创建账号 ===
CREATE USER 'webapp'@'192.168.100.%' IDENTIFIED BY 'WebApp@Pass123!';

-- === 授予权限（最小权限原则：只授予必要权限）===
-- 只读账号
GRANT SELECT ON employees.* TO 'webapp'@'192.168.100.%';

-- 读写账号（不含DROP）
GRANT SELECT, INSERT, UPDATE, DELETE ON employees.* TO 'webapp'@'192.168.100.%';

-- 撤销SELECT权限
REVOKE SELECT ON employees.* FROM 'webapp'@'192.168.100.%';

-- === 修改账号密码 ===
-- 方式1：SET PASSWORD
SET PASSWORD FOR 'webapp'@'192.168.100.%' = PASSWORD('NewWebApp@789!');

-- 方式2：mysqladmin（命令行）
-- mysqladmin -u webapp -p password 'NewWebApp@789!'

-- 方式3：ALTER USER（MySQL 5.7+）
ALTER USER 'webapp'@'192.168.100.%' IDENTIFIED BY 'NewWebApp@789!';

-- 方式4：UPDATE（5.7以前，需FLUSH）
UPDATE mysql.user SET Password=PASSWORD('NewWebApp@789!') WHERE User='webapp';
FLUSH PRIVILEGES;

-- === 删除账号 ===
DROP USER 'webapp'@'192.168.100.%';

-- === 限制账号资源（防止滥用）===
GRANT ALL ON employees.* TO 'limited_user'@'%'
WITH MAX_QUERIES_PER_HOUR 1000        -- 每小时最多1000次查询
     MAX_UPDATES_PER_HOUR 100         -- 每小时最多100次更新
     MAX_CONNECTIONS_PER_HOUR 50      -- 每小时最多50次连接
     MAX_USER_CONNECTIONS 5;          -- 同时最多5个并发连接

-- === 查看用户权限 ===
SHOW GRANTS FOR 'webapp'@'192.168.100.%';
```

---

# 任务三 MySQL 数据库的复制

## 🧠 理论知识

### MySQL 复制原理

MySQL 复制（Replication）是将数据从一台服务器（主服务器 Master）自动同步到一台或多台服务器（从服务器 Slave）的技术。

**复制流程**：

```
主服务器（Master）                    从服务器（Slave）
   ↓ 写操作产生                          ↓
Binary Log（二进制日志）  →  IO线程读取  →  Relay Log（中继日志）
                                               ↓ SQL线程重放
                                         从服务器数据库
```

**三个关键线程**：

1. **Binary Log Dump Thread**（主服务器）：向从服务器发送binlog
2. **IO Thread**（从服务器）：接收binlog，写入Relay Log
3. **SQL Thread**（从服务器）：读取Relay Log，执行SQL，更新从库数据

---

### 复制类型

| 类型 | 拓扑 | 适用场景 |
| --- | --- | --- |
| **主从复制（Master-Slave）** | 一主多从 | 读写分离，备份，报表查询 |
| **主主复制（Master-Master）** | 双向同步 | 双活高可用（需注意写冲突） |
| **级联复制（Chain）** | 主→中继→从 | 减少主库复制压力 |
| **多源复制（Multi-Source）** | 多主一从 | 数据汇聚分析 |

---

### 主从复制的应用场景

- **读写分离**：写操作发送到主库，读操作分发到从库，提升整体吞吐量
- **数据备份**：从库作为热备，主库故障时快速切换
- **数据分析**：在从库执行耗时的统计查询，不影响主库性能
- **地理分布**：不同地区部署从库，就近提供服务

---

### server-id 配置

每台MySQL实例必须有唯一的 `server-id`（1~2^32-1的正整数）：

- 主服务器：如 `server-id = 1`
- 从服务器：如 `server-id = 2`（不能与主库相同）

---

## 🛠️ 实践操作

### 配置主从复制完整步骤

**主服务器配置（Master：192.168.100.20）** ：

```bash
# Ubuntu 默认配置文件：/etc/mysql/mysql.conf.d/mysqld.cnf
# 在 [mysqld] 段添加（如不存在则自行补充）
[mysqld]
server-id = 1                           # 唯一ID
log-bin = /var/lib/mysql/mysql-bin      # 开启二进制日志
binlog_format = ROW
log-bin-index = /var/lib/mysql/mysql-bin.index
binlog_do_db = employees                # 只复制employees库（可选）

# 重启MySQL
sudo systemctl restart mysql
```

```sql
-- 登录主服务器创建复制账号
CREATE USER 'repl'@'192.168.100.%' IDENTIFIED BY 'Repl@Pass123!';
GRANT REPLICATION SLAVE ON *.* TO 'repl'@'192.168.100.%';
FLUSH PRIVILEGES;

-- 锁定主库，查看当前binlog位置（记录文件名和Position）
FLUSH TABLES WITH READ LOCK;
SHOW MASTER STATUS;
-- 记录输出中的 File 和 Position 值，如：mysql-bin.000003, 154

-- 解锁（若需要先导出数据则稍后解锁）
UNLOCK TABLES;
```

**从服务器配置（Slave：192.168.100.21）** ：

```bash
# Ubuntu 默认配置文件：/etc/mysql/mysql.conf.d/mysqld.cnf
[mysqld]
server-id = 2                           # 与主库不同的唯一ID
relay-log = /var/lib/mysql/relay-bin    # 中继日志路径
read_only = 1                           # 从库设为只读（推荐）

# 重启MySQL
sudo systemctl restart mysql
```

```sql
-- 配置从库连接参数（使用从主库记录的File和Position）
CHANGE MASTER TO
    MASTER_HOST = '192.168.100.20',
    MASTER_USER = 'repl',
    MASTER_PASSWORD = 'Repl@Pass123!',
    MASTER_PORT = 3306,
    MASTER_LOG_FILE = 'mysql-bin.000003',   -- 主库SHOW MASTER STATUS的File值
    MASTER_LOG_POS = 154;                    -- 主库SHOW MASTER STATUS的Position值

-- 启动从服务
START SLAVE;

-- 查看从库同步状态（关键字段）
SHOW SLAVE STATUS\G
-- 检查以下两项均为 Yes 表示正常：
-- Slave_IO_Running: Yes
-- Slave_SQL_Running: Yes
-- Seconds_Behind_Master: 0  （延迟秒数）
```

### 验证主从同步

```sql
-- 在主库执行写操作
USE employees;
CREATE TABLE repl_test (id INT, msg VARCHAR(50));
INSERT INTO repl_test VALUES(1, '主库写入测试');
COMMIT;

-- 在从库验证是否同步
USE employees;
SELECT * FROM repl_test;
-- 应能看到主库写入的数据
```

### 常见错误处理

```sql
-- 跳过一个复制错误（谨慎使用）
STOP SLAVE;
SET GLOBAL sql_slave_skip_counter = 1;
START SLAVE;

-- 重置从库（清空所有复制信息，重新配置）
STOP SLAVE;
RESET SLAVE ALL;
```

> 🆕 **补充：MySQL 8.0 复制术语变化（以 8.0 为主）**：
> 

> - 8.0 起逐步将 `MASTER/SLAVE` 命令替换为 `SOURCE/REPLICA`（兼容模式下旧命令仍可用）
> 

> - 推荐优先使用 GTID（降低 File/Position 人工出错概率）
> 

> **基于 GTID 的复制（MySQL 5.6+，MySQL 8.0 强烈推荐）**：
> 

```bash
# 主从均在 mysqld.cnf 的 [mysqld] 中添加
gtid_mode = ON
enforce_gtid_consistency = ON
```

```sql
-- GTID 模式下配置从库（不需要指定 File 和 Position）
CHANGE MASTER TO
  MASTER_HOST = '192.168.100.20',
  MASTER_USER = 'repl',
  MASTER_PASSWORD = 'Repl@Pass123!',
  MASTER_AUTO_POSITION = 1;

START SLAVE;

-- MySQL 8.0 推荐查看方式（如环境启用新命令）
-- SHOW REPLICA STATUS\G
```

> **MySQL InnoDB Cluster（MySQL 8.0 官方高可用方案）** ：
> 

> • 基于 Group Replication 技术
> 

> • 支持自动故障转移（主库宕机后从库自动提升）
> 

> • 通过 MySQL Shell + MySQL Router 实现读写分离
> 

> • 适合取代传统主从复制方案
> 

> 实践操作
> 

> **Percona XtraDB Cluster（PXC）** ：
> 

> • 同步复制（写入所有节点），无主从延迟
> 

> • 任意节点都可写入（多主模式）
> 

> • 适合要求强一致性的金融/电商场景
>