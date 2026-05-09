---
title: 项目六 MySQL 数据库高级安全维护
sidebar:
  order: 6
---

# 项目六 MySQL 数据库高级安全维护

> **前置知识**：本项目是 **项目五** 的延伸。项目五你已经学会了用 Navicat 管理数据库、创建账号并分配权限、用 mysqldump 做备份还原，以及理解了主从复制的基本原理。项目六将在此基础上，带你进入**生产级安全运维**——你将面对项目五没有覆盖的真实安全场景：审计与合规、入侵检测与响应、数据脱敏与加密、高级备份恢复策略、以及完整的加固 Checklist。

---

## 🎯 项目目标

完成本项目后，你能够：

- 开启并分析 MySQL 审计日志，追踪异常操作
- 检测并响应 SQL 注入、暴力破解、UDF 提权等真实攻击
- 对敏感数据做脱敏和透明加密（TDE），满足合规要求
- 设计增量备份 + binlog 时间点恢复（PITR）策略，确保 RPO 接近零
- 从零搭建半同步复制 + 自动故障切换，保障高可用
- 执行一份完整的生产环境加固 Checklist

---

## 第 1 课：审计与合规——谁动了数据库？

### 1.1 为什么需要审计？

在项目五中，你学会了用 `SHOW GRANTS` 查看权限，但这只能看到"谁有什么权限"，看不到"谁在什么时候做了什么"。一旦发生数据泄露或误操作，没有审计日志就等于"黑箱"。

**审计的核心问题**：

| 问题 | 没有审计 | 有审计 |
| --- | --- | --- |
| 谁删了数据？ | 不知道 | 精确到用户、时间、SQL |
| 什么时候发生的？ | 不知道 | 秒级时间戳 |
| 是误操作还是恶意？ | 无法判断 | 结合操作上下文可判定 |
| 如何满足合规要求？ | 无法通过审计 | 可导出审计报告 |

### 1.2 MySQL 审计方案对比

| 方案 | 原理 | 优点 | 缺点 |
| --- | --- | --- | --- |
| **通用日志 (general_log)** | 记录所有 SQL | 无需插件、开箱即用 | 性能影响大、日志量大 |
| **慢查询日志 + 错误日志** | 只记录慢/错误 SQL | 性能影响小 | 覆盖不全 |
| **企业级审计插件** | MySQL Enterprise 自带 | 功能最完整 | 需要企业版授权 |
| **MariaDB Audit Plugin** | 第三方插件 | 免费、兼容社区版 | 需额外安装 |
| **binlog** | 记录所有写操作 | 默认开启、可用于恢复 | 只记录写、不记录读 |

<aside>
💡

**项目五衔接**：你在项目五中已经用 binlog 做过主从复制的数据同步，但 binlog 只记录写操作。如果需要审计 `SELECT` 读取敏感数据的行为，必须开启通用日志或审计插件。

</aside>

### 1.3 实操：开启通用日志做快速审计

```sql
-- 查看当前通用日志状态
SHOW VARIABLES LIKE 'general_log%';

-- 开启通用日志（临时生效，重启后失效）
SET GLOBAL general_log = ON;
SET GLOBAL general_log_file = '/var/log/mysql/general.log';

-- 测试：执行一条查询，然后查看日志
SELECT * FROM mysql.user WHERE user = 'root';
```

查看日志输出：

```bash
# 在服务器上查看
tail -f /var/log/mysql/general.log

# 输出示例：
# 2025-01-15T10:30:45.123456Z  12 Query  SELECT * FROM mysql.user WHERE user = 'root'
```

**通用日志字段解析**：

| 字段 | 含义 |
| --- | --- |
| 时间戳 | 操作发生时间（精确到微秒） |
| 连接 ID | 哪个会话执行的 |
| 命令类型 | Query / Connect / Quit 等 |
| SQL 内容 | 完整的 SQL 语句 |

> **生产注意**：通用日志会记录所有 SQL，包括密码哈希等敏感信息。生产环境不建议长期开启，仅用于排查问题时短期启用。

### 1.4 实操：安装 MariaDB Audit Plugin（社区版推荐）

```sql
-- 检查是否已安装
SELECT PLUGIN_NAME, PLUGIN_STATUS FROM INFORMATION_SCHEMA.PLUGINS
  WHERE PLUGIN_NAME LIKE '%audit%';

-- 安装审计插件
INSTALL PLUGIN server_audit SONAME 'server_audit.so';

-- 配置审计行为
SET GLOBAL server_audit_events = 'CONNECT,QUERY,TABLE';
SET GLOBAL server_audit_logging = ON;
SET GLOBAL server_audit_file_path = '/var/log/mysql/audit.log';

-- 查看配置
SHOW VARIABLES LIKE 'server_audit%';
```

**审计事件类型说明**：

| 事件类型 | 记录内容 | 典型场景 |
| --- | --- | --- |
| `CONNECT` | 连接/断开、用户、IP | 检测异常来源 IP |
| `QUERY` | 所有 SQL 语句 | 追踪 DDL/DML 操作 |
| `TABLE` | 表访问记录 | 追踪敏感表读取 |
| `QUERY_DDL` | 仅 DDL（CREATE/ALTER/DROP） | 追踪结构变更 |
| `QUERY_DML` | 仅 DML（INSERT/UPDATE/DELETE） | 追踪数据修改 |

### 1.5 实操：分析审计日志发现异常

**场景**：某天发现数据被删除，需要追查责任人。

```bash
# 查找所有 DELETE 操作
grep "DELETE" /var/log/mysql/audit.log | tail -20

# 查找特定表的访问记录
grep "salary" /var/log/mysql/audit.log

# 查找非工作时间的操作（晚上 22:00 - 次日 06:00）
grep -E "20[0-9]{2}-[0-9]{2}-[0-9]{2}T(2[2-3]|0[0-5]):" /var/log/mysql/audit.log
```

**审计日志关键字段**：

```
20250115 10:30:45,db_user,172.16.1.100,12,QUERY,testdb,'DROP TABLE users',0
```

| 字段 | 示例值 | 含义 |
| --- | --- | --- |
| 时间戳 | `20250115 10:30:45` | 操作时间 |
| 用户名 | `db_user` | 执行操作的账号 |
| 来源 IP | `172.16.1.100` | 客户端地址 |
| 连接 ID | `12` | 会话标识 |
| 事件类型 | `QUERY` | 操作类型 |
| 数据库 | `testdb` | 目标数据库 |
| SQL 内容 | `DROP TABLE users` | 完整语句 |
| 返回码 | `0` | 0=成功，非0=失败 |

<aside>
✅

**第 1 课小结**

- 理解审计的价值：从"谁有什么权限"到"谁做了什么"
- 掌握通用日志的开启与分析（排查用，不要长期开）
- 掌握 MariaDB Audit Plugin 的安装与配置（生产推荐）
- 能通过审计日志定位异常操作（异常时间、敏感表、危险 SQL）

</aside>

---

## 第 2 课：入侵检测与响应——数据库被攻击了怎么办？

### 2.1 常见攻击方式与项目五知识的延伸

在项目五中，你了解了暴力破解、未授权访问、UDF 提权的防御措施。本课将带你**深入原理**并**实操检测与响应**。

| 攻击方式 | 项目五认知 | 项目六延伸 |
| --- | --- | --- |
| 暴力破解 | 知道要设强密码 | 学会检测暴力破解、配置账户锁定策略 |
| 未授权访问 | 知道要限制 bind-address | 学会网络层+数据库层双重防御 |
| SQL 注入 | 未涉及 | 项目六重点：检测、防御、应急响应 |
| UDF 提权 | 知道要限制 FILE 权限 | 学会检测是否已被提权、如何清理 |

### 2.2 SQL 注入：最危险的数据库攻击

**SQL 注入原理**：攻击者通过前端输入拼接到 SQL 中，改变原 SQL 语义。

**示例——一个危险的登录接口**：

```php
// 危险写法：直接拼接
$sql = "SELECT * FROM users WHERE username='" . $_POST['username'] . "' AND password='" . $_POST['password'] . "'";

// 攻击者输入：username = admin' -- 
// 实际执行：SELECT * FROM users WHERE username='admin' --' AND password='xxx'
// 结果：密码验证被注释掉，直接以 admin 登录
```

**SQL 注入分类**：

| 类型 | 特征 | 危害等级 |
| --- | --- | --- |
| 联合查询注入 (UNION) | 可直接读取其他表数据 | 高 |
| 盲注 (Boolean/Time) | 无法直接看结果，通过条件推断 | 高 |
| 报错注入 | 利用数据库报错信息泄露数据 | 中 |
| 堆叠注入 | 一次注入执行多条 SQL（如 DROP TABLE） | 极高 |

### 2.3 实操：检测 SQL 注入攻击

**方法一：通过审计日志检测**

```bash
# 查找疑似注入的 SQL 模式
grep -iE "(UNION SELECT|OR\s+1=1|;\s*DROP|;\s*DELETE|'\s*--\s|'\s*#\s|SLEEP\(|BENCHMARK\()" /var/log/mysql/audit.log
```

**方法二：通过慢查询日志检测盲注**

盲注通常使用 `SLEEP()` 或 `BENCHMARK()` 函数，导致查询时间异常：

```sql
-- 检查是否有 SLEEP 调用
SELECT * FROM mysql.slow_log
  WHERE sql_text LIKE '%SLEEP%'
  OR sql_text LIKE '%BENCHMARK%';
```

**方法三：通过 performance_schema 监控异常查询**

```sql
-- 查找执行次数异常多的语句（可能正在被注入扫描）
SELECT DIGEST_TEXT, COUNT_STAR, SUM_TIMER_WAIT/1000000000 AS total_sec
FROM performance_schema.events_statements_summary_by_digest
ORDER BY COUNT_STAR DESC
LIMIT 10;

-- 查找返回行数异常多的查询（可能正在拖库）
SELECT DIGEST_TEXT, SUM_ROWS_EXAMINED, SUM_ROWS_SENT
FROM performance_schema.events_statements_summary_by_digest
WHERE SUM_ROWS_SENT > 10000
ORDER BY SUM_ROWS_SENT DESC
LIMIT 10;
```

### 2.4 实操：暴力破解检测与防御

**检测暴力破解**：

```bash
# 从审计日志统计失败连接
grep "CONNECT" /var/log/mysql/audit.log | grep "FAILED" | \
  awk '{print $3}' | sort | uniq -c | sort -rn | head -10

# 输出示例：
#   1523 192.168.1.200    ← 异常！1500+ 次失败连接
#      2 10.0.0.5          ← 正常，偶尔输错密码
```

**防御措施一：账户锁定策略（MySQL 8.0+）**

```sql
-- 项目五中你创建过用户，现在加上登录失败锁定策略
-- 连续失败 3 次锁定 1 天
CREATE USER 'app_user'@'10.0.%'
  IDENTIFIED BY 'StrongP@ss123!'
  FAILED_LOGIN_ATTEMPTS 3
  PASSWORD_LOCK_TIME 1;

-- 修改已有用户的锁定策略
ALTER USER 'app_user'@'10.0.%'
  FAILED_LOGIN_ATTEMPTS 3
  PASSWORD_LOCK_TIME 1;

-- 手动解锁被锁定的账户
ALTER USER 'app_user'@'10.0.%' ACCOUNT UNLOCK;
```

**防御措施二：密码复杂度策略（项目五延伸）**

项目五中你只是设置了密码，现在要确保密码足够强：

```sql
-- 安装密码验证插件（MySQL 8.0 默认已安装）
-- 查看当前策略
SHOW VARIABLES LIKE 'validate_password%';

-- 设置密码策略（MEDIUM = 中等强度）
SET GLOBAL validate_password.policy = 'MEDIUM';
SET GLOBAL validate_password.length = 12;
SET GLOBAL validate_password.mixed_case_count = 1;
SET GLOBAL validate_password.number_count = 1;
SET GLOBAL validate_password.special_char_count = 1;
```

**密码策略等级对比**：

| 策略等级 | 要求 |
| --- | --- |
| LOW | 仅检查长度 |
| MEDIUM | 长度 + 大小写 + 数字 + 特殊字符 |
| STRONG | MEDIUM + 字典词检查 |

### 2.5 实操：UDF 提权检测与清理

**项目五衔接**：项目五告诉你"不授予 FILE 权限"就能防 UDF 提权，但如果你接手了一台已经运行多年的服务器，怎么知道是否已经被提权？

**检测步骤**：

```sql
-- 1. 检查是否有可疑的自定义函数
SELECT * FROM mysql.func;

-- 正常情况下应该为空或只有业务需要的函数
-- 如果出现 cmdshell、exec、system 等函数名，极可能已被 UDF 提权

-- 2. 检查插件目录中的可疑文件
SHOW VARIABLES LIKE 'plugin_dir';

-- 3. 检查哪些用户有 FILE 权限（UDF 提权的前提）
SELECT User, Host FROM mysql.user WHERE File_priv = 'Y';

-- 4. 检查是否有不正常的 SUPER 权限用户
SELECT User, Host FROM mysql.user WHERE Super_priv = 'Y';
```

**清理步骤**：

```sql
-- 删除恶意 UDF 函数
DROP FUNCTION IF EXISTS cmdshell;

-- 收回不必要的 FILE 权限
REVOKE FILE ON *.* FROM 'suspicious_user'@'%';

-- 删除恶意用户
DROP USER 'suspicious_user'@'%';

-- 检查插件目录，删除恶意 so/dll 文件
-- 需要在服务器上操作：
-- ls -la /usr/lib/mysql/plugin/
-- 删除不明文件后重启 MySQL
```

### 2.6 入侵应急响应流程

当确认数据库被入侵后，按以下流程操作：

```
1. 隔离 → 立即断开数据库外网访问（防火墙/安全组）
2. 保全 → 导出审计日志、binlog、错误日志（不要重启，保留现场）
3. 排查 → 确认入侵方式（SQL注入？暴力破解？UDF提权？）
4. 止损 → 删除恶意账号/函数、修复注入漏洞、重置被泄露的密码
5. 恢复 → 从最近的干净备份恢复数据（项目五的备份技能用上了）
6. 加固 → 按第 5 课 Checklist 全面加固
7. 复盘 → 记录事件时间线、根因、改进措施
```

<aside>
💡

**项目五衔接**：步骤 5 中的"从备份恢复"，正是你在项目五第 3 课练过的 mysqldump 备份还原技能。但现在你知道，如果只做了全量备份，可能丢失几个小时的数据——第 3 课将教你如何做到近零丢失。

</aside>

<aside>
✅

**第 2 课小结**

- SQL 注入：理解原理，掌握通过审计日志和 performance_schema 检测
- 暴力破解：掌握 `FAILED_LOGIN_ATTEMPTS` 账户锁定策略
- UDF 提权：掌握检测（查 mysql.func、查 FILE 权限）和清理方法
- 入侵响应：隔离 → 保全 → 排查 → 止损 → 恢复 → 加固 → 复盘

</aside>

---

## 第 3 课：数据脱敏与加密——保护敏感数据

### 3.1 为什么需要脱敏和加密？

项目五中你学会了用权限控制"谁能访问"数据，但有些场景权限控制不够：

- **开发/测试环境**需要用真实数据量测试，但不能看到真实敏感信息
- **合规要求**（如等保、GDPR）要求敏感数据必须加密存储
- **数据泄露兜底**：即使数据库被拖库，加密后的数据也无法直接使用

### 3.2 数据脱敏：让测试数据安全可用

**脱敏原则**：保持数据格式和统计特征，替换敏感内容。

| 数据类型 | 原始值 | 脱敏后 | 脱敏方式 |
| --- | --- | --- | --- |
| 手机号 | 13812345678 | 138****5678 | 保留前3后4 |
| 身份证 | 110101199001011234 | 110101****1234 | 保留前6后4 |
| 姓名 | 张三丰 | 张** | 保留姓 |
| 邮箱 | user@example.com | u***@example.com | 保留首字母和域名 |
| 银行卡 | 6222021234567890 | 6222********7890 | 保留前4后4 |
| 密码哈希 | $2b$12$xxx... | $2b$12$随机值 | 重新生成 |

**实操：MySQL 视图脱敏**

```sql
-- 假设有一个用户表（项目五中你可能创建过类似的表）
CREATE TABLE IF NOT EXISTS employees (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(50),
  phone VARCHAR(20),
  id_card VARCHAR(20),
  salary DECIMAL(10,2),
  department VARCHAR(50)
);

-- 创建脱敏视图（开发/测试环境使用）
CREATE VIEW v_employees_masked AS
SELECT
  id,
  CONCAT(LEFT(name, 1), '**') AS name,
  CONCAT(LEFT(phone, 3), '****', RIGHT(phone, 4)) AS phone,
  CONCAT(LEFT(id_card, 6), '****', RIGHT(id_card, 4)) AS id_card,
  salary,  -- 薪资视需求决定是否脱敏
  department
FROM employees;

-- 对比
SELECT * FROM employees WHERE id = 1;
-- | 1 | 张三丰 | 13812345678 | 110101199001011234 | 15000.00 | 技术部 |

SELECT * FROM v_employees_masked WHERE id = 1;
-- | 1 | 张** | 138****5678 | 110101****1234 | 15000.00 | 技术部 |
```

**实操：数据导出时脱敏**

```bash
# 导出脱敏后的数据到新表，供测试环境使用
mysqldump -u root -p testdb employees \
  --no-create-info \
  --skip-add-locks \
  --where="1=1" | \
  sed "s/[0-9]\{11\}/&/g" > /tmp/masked_data.sql
# 实际生产中建议用脚本程序做更精确的脱敏
```

### 3.3 透明数据加密（TDE）：存储层加密

**TDE 原理**：数据在写入磁盘前自动加密，读取时自动解密。应用层无感知，但磁盘文件是加密的。

| 对比项 | 无 TDE | 有 TDE |
| --- | --- | --- |
| 磁盘文件 | 明文存储 | 加密存储 |
| 应用改动 | — | 无需改动 |
| 拖库风险 | 拿走磁盘文件即泄露 | 文件无法直接读取 |
| 性能影响 | 无 | 约 5%~15% |

**实操：MySQL 8.0 开启 TDE**

```sql
-- 1. 查看当前加密状态
SELECT * FROM performance_schema.file_summary_by_instance
  WHERE FILE_NAME LIKE '%ibd%' LIMIT 5;

-- 2. 创建加密密钥
-- MySQL 8.0 使用 keyring 插件管理密钥
-- 先安装 keyring 插件（需在 my.cnf 中配置）
-- my.cnf 添加：
-- [mysqld]
-- early-plugin-load=keyring_file.so
-- keyring_file_data=/var/lib/mysql-keyring/keyring

-- 3. 重启 MySQL 后，创建加密表空间
CREATE TABLESPACE encrypted_ts
  ADD DATAFILE 'encrypted_ts.ibd'
  ENCRYPTION = 'Y';

-- 4. 在加密表空间中创建表
CREATE TABLE sensitive_data (
  id INT PRIMARY KEY AUTO_INCREMENT,
  credit_card VARCHAR(50),
  secret_key VARCHAR(100)
) TABLESPACE = encrypted_ts ENCRYPTION = 'Y';

-- 5. 也可以直接对已有表开启加密
ALTER TABLE employees ENCRYPTION = 'Y';

-- 6. 验证加密状态
SELECT TABLE_SCHEMA, TABLE_NAME, ENCRYPTION
  FROM INFORMATION_SCHEMA.TABLES
  WHERE ENCRYPTION = 'YES';
```

### 3.4 连接加密：SSL/TLS

项目五中你用 Navicat 连接数据库时，数据是明文传输的。在生产环境中，必须加密传输通道。

```sql
-- 检查当前 SSL 状态
SHOW VARIABLES LIKE '%ssl%';

-- 查看当前连接是否使用 SSL
SELECT user, host, ssl_type, ssl_cipher
  FROM performance_schema.threads
  WHERE type = 'FOREGROUND';
```

**强制特定用户必须使用 SSL 连接**：

```sql
-- 项目五中创建的用户，现在强制 SSL
ALTER USER 'app_user'@'10.0.%' REQUIRE SSL;

-- 更严格：要求客户端提供证书
ALTER USER 'admin'@'10.0.%' REQUIRE X509;

-- 验证
SHOW GRANTS FOR 'app_user'@'10.0.%';
-- 输出中会包含: REQUIRE SSL
```

<aside>
✅

**第 3 课小结**

- 数据脱敏：视图脱敏让测试环境安全可用，脱敏原则是保留格式替换内容
- TDE 加密：磁盘层加密，拖库也无法读取，性能影响约 5%~15%
- 连接加密：SSL/TLS 加密传输，可强制特定用户必须使用 SSL
- 三层防护体系：权限控制（项目五）+ 脱敏 + 加密 = 纵深防御

</aside>

---

## 第 4 课：高级备份与恢复——从"能备份"到"不丢数据"

### 4.1 项目五回顾与局限

项目五中你学会了用 `mysqldump` 做全量备份和还原。但全量备份有一个致命问题：

**场景**：每天凌晨 2:00 做一次全量备份，周三上午 10:00 误删了一张表。

- 如果只做全量备份 → 恢复到周二凌晨 2:00 → **丢失 8 小时数据**
- 如果做了全量 + binlog → 恢复到周三 9:59:59 → **只丢失 1 秒数据**

| 策略 | RPO（最大丢失量） | 存储成本 | 恢复复杂度 |
| --- | --- | --- | --- |
| 仅全量备份（项目五） | 最大 24 小时 | 低 | 简单 |
| 全量 + 增量备份 | 最大 24 小时 | 中 | 中等 |
| 全量 + binlog（PITR） | 接近 0 | 中 | 较高 |
| 全量 + 增量 + binlog | 接近 0 | 较高 | 高 |

> **RPO**（Recovery Point Objective）：恢复点目标，即允许丢失的最大数据量。

### 4.2 实操：增量备份（基于 mysqldump）

增量备份不是 MySQL 原生支持的概念，但可以通过 `--flush-logs` 切换 binlog 实现：

```bash
# 周日：全量备份 + 刷新 binlog
mysqldump -u root -p --single-transaction \
  --flush-logs --source-data=2 \
  --all-databases > /backup/full_sun.sql

# 周一至周六：只需要备份新的 binlog 文件
# --flush-logs 会在备份后生成新的 binlog 文件
# 之后每天备份自上次 flush 以来新生成的 binlog 即可
mysqladmin -u root -p flush-logs
cp /var/lib/mysql/mysql-bin.* /backup/binlog/
```

### 4.3 实操：基于 binlog 的时间点恢复（PITR）

这是**生产环境必须掌握**的恢复能力。

**场景**：周三上午 10:05:00 有人误执行了 `DROP TABLE employees`，需要恢复到 10:04:59。

**步骤一：恢复最近的全量备份**

```bash
mysql -u root -p < /backup/full_sun.sql
```

**步骤二：用 binlog 重放到误操作之前**

```bash
# 1. 确定全量备份时的 binlog 位置
head -50 /backup/full_sun.sql | grep "CHANGE MASTER"
# 输出：CHANGE MASTER TO MASTER_LOG_FILE='mysql-bin.000015', MASTER_LOG_POS=154;

# 2. 查看所有 binlog 文件
ls -la /var/lib/mysql/mysql-bin.*

# 3. 用 mysqlbinlog 重放 binlog，截止到误操作前
# 方法一：按时间截止
mysqlbinlog --start-position=154 \
  --stop-datetime="2025-01-15 10:04:59" \
  /var/lib/mysql/mysql-bin.000015 \
  /var/lib/mysql/mysql-bin.000016 | mysql -u root -p

# 方法二：按位置截止（更精确）
# 先查看 binlog 找到 DROP TABLE 的位置
mysqlbinlog /var/lib/mysql/mysql-bin.000016 | grep -n "DROP TABLE"
# 假设发现 DROP TABLE 在 position 3456

mysqlbinlog --start-position=154 \
  --stop-position=3455 \
  /var/lib/mysql/mysql-bin.000015 \
  /var/lib/mysql/mysql-bin.000016 | mysql -u root -p
```

**关键 mysqlbinlog 参数**：

| 参数 | 作用 |
| --- | --- |
| `--start-datetime` | 从指定时间开始重放 |
| `--stop-datetime` | 重放到指定时间停止 |
| `--start-position` | 从指定 binlog 位置开始 |
| `--stop-position` | 重放到指定位置停止 |
| `--database=db` | 只重放指定数据库的操作 |
| `--base64-output=DECODE-ROWS` | 以可读格式显示 ROW 模式的 binlog |
| `-v` | 显示伪 SQL（将 ROW 事件还原为 SQL 语句） |

### 4.4 实操：跳过误操作继续重放

如果误操作后面还有正常操作，需要跳过误操作继续重放：

```bash
# 假设 binlog 内容：
# position 154: 正常 INSERT
# position 3456: 误操作 DROP TABLE  ← 跳过
# position 3520: 正常 UPDATE        ← 继续

# 分段重放
mysqlbinlog --start-position=154 --stop-position=3455 \
  /var/lib/mysql/mysql-bin.000016 | mysql -u root -p

mysqlbinlog --start-position=3520 \
  /var/lib/mysql/mysql-bin.000016 | mysql -u root -p
```

### 4.5 实操：XtraBackup 热备份（进阶）

`mysqldump` 是逻辑备份（导出 SQL），`XtraBackup` 是物理备份（直接复制数据文件），速度更快，对大库更友好。

```bash
# 安装 XtraBackup（Percona 提供）
# Ubuntu/Debian
apt install percona-xtrabackup-80

# 全量备份（在线热备，不锁表）
xtrabackup --backup --target-dir=/backup/full/ -u root -p

# 准备备份（使备份一致）
xtrabackup --prepare --target-dir=/backup/full/

# 恢复备份（需要先停止 MySQL）
systemctl stop mysql
xtrabackup --copy-back --target-dir=/backup/full/
chown -R mysql:mysql /var/lib/mysql
systemctl start mysql

# 增量备份
xtrabackup --backup --target-dir=/backup/inc1/ \
  --incremental-basedir=/backup/full/ -u root -p

# 恢复增量备份
xtrabackup --prepare --apply-log-only --target-dir=/backup/full/
xtrabackup --prepare --target-dir=/backup/full/ \
  --incremental-dir=/backup/inc1/
xtrabackup --copy-back --target-dir=/backup/full/
```

| 对比项 | mysqldump | XtraBackup |
| --- | --- | --- |
| 类型 | 逻辑备份（SQL） | 物理备份（数据文件） |
| 锁表 | `--single-transaction` 不锁 InnoDB | 不锁表（热备） |
| 速度 | 慢（需要执行 SQL） | 快（直接复制文件） |
| 恢复方式 | `mysql < backup.sql` | `--copy-back` |
| 增量支持 | 间接（通过 binlog） | 原生支持 |
| 适用场景 | 小中型数据库 | 大型数据库 |

<aside>
💡

**项目五衔接**：项目五第 3 课学的 `mysqldump` 是入门必备，现在你学会了 PITR 和 XtraBackup，从"能备份"升级到"不丢数据"。

</aside>

<aside>
✅

**第 4 课小结**

- 理解 RPO 概念：全量备份 RPO 最大 24h，加 binlog 可接近 0
- 掌握 PITR：全量恢复 + binlog 重放到误操作前
- 掌握跳过误操作继续重放：分段 `--stop-position` / `--start-position`
- 了解 XtraBackup：物理热备，大库首选

</aside>

---

## 第 5 课：高可用架构与生产加固——让数据库"永远在线"

### 5.1 从项目五的主从复制到高可用

项目五第 4 课你学会了主从复制的原理和配置，但主从复制本身**不是高可用**——主库挂了，从库不会自动切换。本课带你实现真正的**自动故障转移**。

**从主从复制到高可用的演进路线**：

```
主从复制（项目五）         →    半同步复制（本项目）     →    自动故障转移（本项目）
主库挂了=手动切            主库挂了=数据不丢           主库挂了=自动切、业务不停
RPO可能丢数据              RPO=0                      RPO=0 + RTO<30秒
```

### 5.2 实操：半同步复制

项目五用的是异步复制（主库不等从库确认），如果主库崩溃，从库可能没收到最后的变更。

**半同步复制**：主库提交事务后，至少等待一个从库确认收到才返回成功。

```sql
-- 主库配置
INSTALL PLUGIN rpl_semi_sync_master SONAME 'semisync_master.so';
SET GLOBAL rpl_semi_sync_master_enabled = ON;
SET GLOBAL rpl_semi_sync_master_timeout = 5000;  -- 等待从库5秒，超时降级为异步

-- 从库配置
INSTALL PLUGIN rpl_semi_sync_slave SONAME 'semisync_slave.so';
SET GLOBAL rpl_semi_sync_slave_enabled = ON;

-- 从库重启 IO 线程使半同步生效
STOP SLAVE IO_THREAD;
START SLAVE IO_THREAD;

-- 主库验证
SHOW STATUS LIKE 'Rpl_semi_sync_master_status';
-- Value: ON 表示半同步正常

SHOW STATUS LIKE 'Rpl_semi_sync_master_clients';
-- Value: 1 表示有1个从库在半同步模式

-- 查看超时降级情况
SHOW STATUS LIKE 'Rpl_semi_sync_master_no_times';
-- 如果此值不断增长，说明从库跟不上，频繁降级为异步
```

**半同步 vs 异步对比**：

| 对比项 | 异步复制（项目五） | 半同步复制 |
| --- | --- | --- |
| 主库提交后 | 立即返回 | 等待至少1个从库确认 |
| 主库崩溃时数据丢失 | 可能丢失 | 不丢失（已确认的） |
| 性能影响 | 无 | 略有延迟（超时时间内） |
| 降级机制 | — | 超时后自动降级为异步 |

### 5.3 实操：MHA 自动主从切换

MHA（Master High Availability）是最成熟的开源 MySQL 故障切换方案。

**架构**：

```
              MHA Manager
                  |
    +-------------+-------------+
    |             |             |
  主库         从库1         从库2
(Master)     (Slave1)      (Slave2)
    |             |             |
    +------复制-----+------复制-----+
```

**安装与配置**：

```bash
# 1. 所有节点安装 MHA Node
apt install mha4mysql-node

# 2. 管理节点安装 MHA Manager
apt install mha4mysql-manager

# 3. 配置 SSH 免密登录（所有节点之间）
ssh-keygen -t rsa
ssh-copy-id root@slave1
ssh-copy-id root@slave2

# 4. 创建 MHA 配置文件
cat > /etc/mha/app1.cnf << 'EOF'
[server default]
manager_workdir=/var/log/mha/app1
manager_log=/var/log/mha/app1/manager.log
user=mha_monitor
password=MhaMonitor123!
repl_user=repl
repl_password=Repl123!
ssh_user=root

[server1]
hostname=192.168.1.10
port=3306
candidate_master=1

[server2]
hostname=192.168.1.11
port=3306
candidate_master=1

[server3]
hostname=192.168.1.12
port=3306
no_master=1
EOF

# 5. 检查配置
masterha_check_ssh --conf=/etc/mha/app1.cnf
masterha_check_repl --conf=/etc/mha/app1.cnf

# 6. 启动 MHA Monitor
nohup masterha_manager --conf=/etc/mha/app1.cnf &

# 7. 模拟主库故障
# 在主库上：systemctl stop mysql
# MHA 会在 30 秒内自动将某个从库提升为新主库
```

**MHA 故障切换过程**：

```
1. 检测主库不可用（连续 ping 失败）
2. 尝试从主库保存 binlog（如果 SSH 可达）
3. 从最新的从库中找出 relaylog 最完整的
4. 将差异 relaylog 应用到其他从库
5. 提升最完整的从库为新主库
6. 其他从库指向新主库
7. 发送故障通知
```

### 5.4 生产环境加固 Checklist

结合项目五和项目六所有知识，整理一份完整的生产加固 Checklist：

#### 网络层

| 检查项 | 加固措施 | 验证命令 |
| --- | --- | --- |
| 监听地址 | 只监听内网 | `SHOW VARIABLES LIKE 'bind_address'` |
| 防火墙 | 只开放必要 IP | `iptables -L -n \| grep 3306` |
| SSL 连接 | 强制 SSL | `SHOW VARIABLES LIKE 'require_secure_transport'` |

#### 账户层

| 检查项 | 加固措施 | 验证命令 |
| --- | --- | --- |
| root 远程登录 | 禁止 root 远程 | `SELECT * FROM mysql.user WHERE user='root' AND host!='localhost'` |
| 匿名账号 | 删除匿名用户 | `SELECT * FROM mysql.user WHERE user=''` |
| 空密码 | 禁止空密码 | `SELECT user,host FROM mysql.user WHERE authentication_string=''` |
| 密码策略 | 启用 validate_password | `SHOW VARIABLES LIKE 'validate_password%'` |
| 账户锁定 | 配置失败锁定 | `SELECT user,host,FAILED_LOGIN_ATTEMPTS FROM mysql.user` |
| 闲置账号 | 定期清理 | `SELECT user,host,password_last_changed FROM mysql.user` |
| 权限最小化 | 按需授权 | `SELECT * FROM mysql.user WHERE Super_priv='Y'` |
| FILE 权限 | 严格控制 | `SELECT user,host FROM mysql.user WHERE File_priv='Y'` |

#### 数据层

| 检查项 | 加固措施 | 验证命令 |
| --- | --- | --- |
| 敏感数据加密 | TDE 加密表 | `SELECT TABLE_NAME,ENCRYPTION FROM INFORMATION_SCHEMA.TABLES WHERE ENCRYPTION='YES'` |
| 测试数据脱敏 | 视图脱敏 | 检查脱敏视图是否存在 |
| 审计日志 | 开启审计插件 | `SHOW VARIABLES LIKE 'server_audit%'` |

#### 备份层

| 检查项 | 加固措施 | 验证命令 |
| --- | --- | --- |
| 定期全量备份 | 每日全量 | 检查 crontab 和备份文件 |
| binlog 保留 | 保留 7 天以上 | `SHOW VARIABLES LIKE 'binlog_expire_logs_seconds'` |
| 备份验证 | 定期恢复测试 | 在测试环境恢复验证 |
| 异地备份 | 备份文件传异地 | 检查同步脚本 |

#### 高可用层

| 检查项 | 加固措施 | 验证命令 |
| --- | --- | --- |
| 复制模式 | 半同步复制 | `SHOW STATUS LIKE 'Rpl_semi_sync%'` |
| 故障切换 | MHA 或 InnoDB Cluster | `masterha_check_status --conf=/etc/mha/app1.cnf` |
| 监控告警 | 复制延迟告警 | `SHOW SLAVE STATUS` 的 Seconds_Behind_Master |

<aside>
✅

**第 5 课小结**

- 从主从复制（项目五）→ 半同步复制 → 自动故障转移，实现真正高可用
- 半同步复制确保已提交事务不丢失，超时自动降级
- MHA 实现主库故障后自动切换，RTO < 30 秒
- 生产加固 Checklist 覆盖网络、账户、数据、备份、高可用五大层面

</aside>

---

## 📝 项目总结（与项目五对比复盘）

| 能力维度 | 项目五（基础安全维护） | 项目六（高级安全维护） |
| --- | --- | --- |
| **审计** | 用 `SHOW GRANTS` 看权限 | 用审计日志追踪"谁做了什么" |
| **防注入** | 未涉及 | 检测 SQL 注入、分析攻击模式 |
| **防暴力破解** | 设强密码 | 账户锁定策略 + 密码复杂度策略 |
| **UDF 提权** | 知道要限制 FILE 权限 | 能检测是否已被提权、能清理 |
| **数据保护** | 权限控制"谁能访问" | 脱敏 + TDE + SSL 纵深防御 |
| **备份恢复** | mysqldump 全量备份还原 | PITR 时间点恢复 + XtraBackup 热备 |
| **高可用** | 主从复制（手动切） | 半同步复制 + MHA 自动切换 |
| **加固** | 知道基本措施 | 完整 Checklist 五大层面 |

---

## 附录

### 附录 A：审计日志关键字段速查

| 字段 | 含义 | 排查场景 |
| --- | --- | --- |
| 时间戳 | 操作发生时间 | 查找非工作时间操作 |
| 用户名 | 执行账号 | 确认操作者身份 |
| 来源 IP | 客户端地址 | 检测异常来源 |
| 命令类型 | Query/Connect/Quit | 过滤关注的事件类型 |
| SQL 内容 | 完整语句 | 搜索危险操作（DROP/DELETE/GRANT） |
| 返回码 | 0=成功 | 过滤失败操作 |

### 附录 B：PITR 恢复流程速查

```
1. 停止应用写入
2. 恢复最近全量备份: mysql < full_backup.sql
3. 找到全量备份的 binlog 位置
4. 查找误操作位置: mysqlbinlog binlog_file | grep -n "危险SQL"
5. 重放 binlog 到误操作前: mysqlbinlog --stop-position=XXX | mysql
6. 跳过误操作，继续重放: mysqlbinlog --start-position=YYY | mysql
7. 验证数据完整性
8. 恢复应用写入
```

### 附录 C：MHA 常用命令速查

| 命令 | 用途 |
| --- | --- |
| `masterha_check_ssh` | 检查 SSH 连通性 |
| `masterha_check_repl` | 检查复制状态 |
| `masterha_manager` | 启动 MHA 监控 |
| `masterha_check_status` | 查看监控状态 |
| `masterha_master_switch` | 手动切换主库 |
| `masterha_conf_host` | 修改配置 |
