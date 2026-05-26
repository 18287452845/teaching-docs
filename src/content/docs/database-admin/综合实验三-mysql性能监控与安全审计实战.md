---
title: "综合实验三 MySQL 性能监控与安全审计综合实战"
---

# 综合实验三 MySQL 性能监控与安全审计综合实战

🎯 **本实验学习目标**

- 能使用 MySQL 内置工具和 Navicat 完成数据库性能监控
- 能通过慢查询日志定位和优化性能瓶颈
- 能使用 `EXPLAIN` 分析 SQL 执行计划
- 能编写安全审计脚本并生成审计报告
- 能模拟安全事件并完成应急响应流程

<aside>
🧭

**实验主线**：性能基线采集 → 慢查询定位与优化 → 索引优化实战 → 安全事件模拟与审计 → 应急响应

本实验将项目五中的日志知识和项目六中的监控排错融合，通过真实场景掌握数据库运维中的"监控 → 发现 → 分析 → 优化 → 审计"完整闭环。

</aside>

<aside>
🖥️

**前置条件**

- 已完成综合实验一（MySQL 已安装加固、数据库和账号已创建）
- 虚拟机 Ubuntu 24.04 + MySQL 8.0（IP：`192.168.100.20`）
- 宿主机 Windows + Navicat，已能远程连接
- `ecommerce` 数据库中已有 `users`、`products`、`orders` 表

**课堂产出**

- 一份性能基线报告
- 至少 1 条慢查询的优化记录
- 一份安全审计脚本和审计报告
- 一次安全事件应急响应演练

</aside>

---

## 实验背景

公司电商系统上线后，用户量逐渐增长。近期收到用户反馈："查询订单历史越来越慢"。同时，安全团队发现数据库服务器上出现了可疑的登录尝试。你需要同时处理两个问题：**性能优化**和**安全审计**。

---

## 任务一 性能基线采集

### 1.1 了解当前服务器状态

```sql
sudo mysql

-- ========== 服务器基本信息 ==========
SELECT VERSION() AS 'MySQL版本';

-- ========== 运行时间 ==========
SHOW GLOBAL STATUS LIKE 'Uptime';

-- ========== 连接相关 ==========
SHOW GLOBAL STATUS LIKE 'Threads_connected';    -- 当前连接数
SHOW GLOBAL STATUS LIKE 'Threads_running';       -- 正在执行的线程
SHOW GLOBAL STATUS LIKE 'Connections';           -- 历史总连接数
SHOW GLOBAL STATUS LIKE 'Max_used_connections';  -- 历史最大并发
SHOW GLOBAL STATUS LIKE 'Aborted_connects';      -- 中断的连接（可能有异常访问）

-- ========== 查询相关 ==========
SHOW GLOBAL STATUS LIKE 'Questions';             -- 总查询数
SHOW GLOBAL STATUS LIKE 'Slow_queries';          -- 慢查询总数
SHOW GLOBAL STATUS LIKE 'Com_select';            -- SELECT 次数
SHOW GLOBAL STATUS LIKE 'Com_insert';            -- INSERT 次数
SHOW GLOBAL STATUS LIKE 'Com_update';            -- UPDATE 次数
SHOW GLOBAL STATUS LIKE 'Com_delete';            -- DELETE 次数

-- ========== 缓冲池命中率（InnoDB） ==========
SHOW GLOBAL STATUS LIKE 'Innodb_buffer_pool_read_requests';  -- 逻辑读
SHOW GLOBAL STATUS LIKE 'Innodb_buffer_pool_reads';          -- 物理读（未命中）

-- ========== 表锁情况 ==========
SHOW GLOBAL STATUS LIKE 'Table_locks_waited';   -- 等待表锁次数
SHOW GLOBAL STATUS LIKE 'Table_locks_immediate'; -- 立即获得表锁次数
```

### 1.2 缓冲池命中率计算

```
缓冲池命中率 = 1 - (Innodb_buffer_pool_reads / Innodb_buffer_pool_read_requests) × 100%
```

<aside>
💬

**缓冲池命中率怎么看？**

- **99% 以上**：优秀，大部分数据从内存读取
- **95% ~ 99%**：正常，偶尔需要从磁盘读取
- **低于 95%**：可能需要增大 `innodb_buffer_pool_size`

</aside>

### 1.3 查看当前连接与进程

```sql
-- 查看所有连接
SHOW PROCESSLIST;

-- 查看更详细的信息
SELECT
    id AS '连接ID',
    user AS '用户',
    host AS '来源主机',
    db AS '当前数据库',
    command AS '命令类型',
    time AS '持续时间(秒)',
    state AS '状态',
    LEFT(info, 80) AS '执行的SQL'
FROM information_schema.processlist
WHERE user != 'system user'
ORDER BY time DESC;
```

### 1.4 用 Navicat 辅助监控

在 Navicat 中：

1. 菜单 → **工具** → **服务器监控**
2. 查看 **进程列表**：关注 `Time` 列（持续时间长的可能有问题）
3. 查看 **变量**：搜索关键变量如 `buffer_pool_size`、`max_connections`
4. 查看 **状态**：关注 `Slow_queries`、`Threads_connected` 等指标

<aside>
✅

**检查点 1**：完成性能基线采集，记录关键指标数值。

</aside>

---

## 任务二 慢查询定位与优化

### 2.1 准备测试数据

先给 `ecommerce` 库插入大量测试数据，模拟真实业务量：

```sql
sudo mysql
USE ecommerce;

-- 创建一个大批量数据生成的存储过程
DELIMITER //
CREATE PROCEDURE generate_test_data(IN num_rows INT)
BEGIN
    DECLARE i INT DEFAULT 0;
    DECLARE prod_count INT;

    SELECT COUNT(*) INTO prod_count FROM products;

    -- 禁用自动提交，提升插入速度
    SET autocommit = 0;

    WHILE i < num_rows DO
        INSERT INTO orders (user_id, product_id, quantity, total_amount, order_status)
        VALUES (
            FLOOR(1 + RAND() * 3),                        -- 随机用户 1~3
            FLOOR(1 + RAND() * prod_count),                -- 随机商品
            FLOOR(1 + RAND() * 5),                         -- 数量 1~5
            ROUND(50 + RAND() * 2000, 2),                  -- 金额 50~2050
            FLOOR(RAND() * 4)                              -- 状态 0~3
        );
        SET i = i + 1;

        -- 每 1000 条提交一次
        IF i % 1000 = 0 THEN
            COMMIT;
        END IF;
    END WHILE;

    COMMIT;
    SET autocommit = 1;
END //
DELIMITER ;

-- 生成 10000 条测试订单
CALL generate_test_data(10000);

-- 验证数据量
SELECT COUNT(*) AS '订单总数' FROM orders;

-- 清理存储过程
DROP PROCEDURE generate_test_data;
```

### 2.2 开启慢查询日志

```sql
-- 查看当前慢查询日志配置
SHOW VARIABLES LIKE 'slow_query%';
SHOW VARIABLES LIKE 'long_query_time';

-- 设置为 1 秒阈值（临时生效）
SET GLOBAL slow_query_log = 1;
SET GLOBAL long_query_time = 1;
SET GLOBAL log_queries_not_using_indexes = 1;
```

### 2.3 制造慢查询

```sql
-- 慢查询 1：全表扫描 + 排序（无索引优化）
SELECT o.order_id, u.username, p.name, o.total_amount, o.created_at
FROM orders o
JOIN users u ON o.user_id = u.user_id
JOIN products p ON o.product_id = p.product_id
WHERE o.created_at >= '2026-01-01'
ORDER BY o.total_amount DESC
LIMIT 100;

-- 慢查询 2：聚合统计（无合适索引）
SELECT
    u.username,
    COUNT(o.order_id) AS '订单数',
    SUM(o.total_amount) AS '总金额',
    AVG(o.total_amount) AS '平均金额'
FROM orders o
JOIN users u ON o.user_id = u.user_id
WHERE o.order_status = 1
GROUP BY u.username
ORDER BY 总金额 DESC;

-- 慢查询 3：子查询（性能隐患）
SELECT * FROM orders
WHERE user_id IN (
    SELECT user_id FROM users WHERE username LIKE 'zhang%'
)
AND total_amount > 100;

-- 慢查询 4：无索引条件查询
SELECT * FROM orders
WHERE total_amount BETWEEN 500 AND 1000
AND created_at >= '2026-01-01';
```

### 2.4 分析慢查询日志

```bash
# 查看慢查询日志
sudo tail -50 /var/log/mysql/slow.log

# 使用 mysqldumpslow 分析
# 按执行次数排序
sudo mysqldumpslow -s c -t 10 /var/log/mysql/slow.log

# 按平均执行时间排序
sudo mysqldumpslow -s at -t 10 /var/log/mysql/slow.log

# 按扫描行数排序
sudo mysqldumpslow -s r -t 10 /var/log/mysql/slow.log
```

```sql
-- 查看慢查询计数
SHOW GLOBAL STATUS LIKE 'Slow_queries';
```

<aside>
💬

**mysqldumpslow 输出中的关键字段**

| 字段 | 含义 |
| --- | --- |
| `Count` | 该类型 SQL 执行了多少次 |
| `Time` | 总执行时间 / 平均执行时间 / 最大执行时间 |
| `Lock` | 锁等待时间 |
| `Rows` | 扫描行数 / 发送行数 |

将相同模式但参数不同的 SQL 归为一类统计，方便找到最需要优化的 SQL 模式。

</aside>

### 2.5 使用 EXPLAIN 分析执行计划

对每条慢查询加上 `EXPLAIN` 分析：

```sql
-- 分析慢查询 1 的执行计划
EXPLAIN
SELECT o.order_id, u.username, p.name, o.total_amount, o.created_at
FROM orders o
JOIN users u ON o.user_id = u.user_id
JOIN products p ON o.product_id = p.product_id
WHERE o.created_at >= '2026-01-01'
ORDER BY o.total_amount DESC
LIMIT 100;
```

重点关注的 EXPLAIN 字段：

| 字段 | 关注点 | 优化方向 |
| --- | --- | --- |
| `type` | `ALL`（全表扫描）最差，`const` 最好 | 至少达到 `ref` 或 `range` |
| `key` | 是否使用了索引 | `NULL` 表示没有使用索引 |
| `rows` | 预估扫描行数 | 越少越好 |
| `Extra` | `Using filesort`（额外排序）| 考虑添加排序字段索引 |
| `Extra` | `Using temporary`（临时表）| 考虑优化 GROUP BY |
| `Extra` | `Using where` | 正常，但如果 rows 大则需优化 |

EXPLAIN type 访问类型从好到差排序：

```
system > const > eq_ref > ref > range > index > ALL
```

### 2.6 创建索引优化慢查询

```sql
-- 查看 orders 表当前索引
SHOW INDEX FROM orders;

-- ========== 优化 1：为 created_at 添加索引 ==========
-- 解决慢查询 1 和 4 的 WHERE 条件过滤
ALTER TABLE orders ADD INDEX idx_created_at (created_at);

-- ========== 优化 2：为 order_status + user_id 添加复合索引 ==========
-- 解决慢查询 2 的 WHERE + GROUP BY
ALTER TABLE orders ADD INDEX idx_status_user (order_status, user_id);

-- ========== 优化 3：为 total_amount 添加索引 ==========
-- 解决慢查询 4 的范围查询
ALTER TABLE orders ADD INDEX idx_total_amount (total_amount);

-- 查看索引创建结果
SHOW INDEX FROM orders;
```

### 2.7 对比优化前后的执行计划

```sql
-- 优化后的执行计划
EXPLAIN
SELECT o.order_id, u.username, p.name, o.total_amount, o.created_at
FROM orders o
JOIN users u ON o.user_id = u.user_id
JOIN products p ON o.product_id = p.product_id
WHERE o.created_at >= '2026-01-01'
ORDER BY o.total_amount DESC
LIMIT 100;

EXPLAIN
SELECT * FROM orders
WHERE total_amount BETWEEN 500 AND 1000
AND created_at >= '2026-01-01';
```

对比优化前后：

| 指标 | 优化前 | 优化后 |
| --- | --- | --- |
| `type` | `ALL`（全表扫描） | `range`（索引范围扫描） |
| `key` | `NULL`（无索引） | `idx_created_at` 等 |
| `rows` | ~10000 | 大幅减少 |
| `Extra` | `Using filesort` | 消除或减少 |

<aside>
💬

**索引不是越多越好**

每个索引都会占用存储空间，并且会降低 INSERT/UPDATE/DELETE 的速度（因为每次写操作都需要更新索引）。只对查询频繁且区分度高的字段建索引。

**口诀**：WHERE 常用 → 建索引；区分度高 → 放前面；频繁更新 → 慎重建。

</aside>

<aside>
✅

**检查点 2**：至少 2 条慢查询的 EXPLAIN 中 `type` 从 `ALL` 提升为 `range` 或 `ref`。

</aside>

---

## 任务三 MySQL 状态变量监控

### 3.1 关键健康指标监控脚本

```sql
-- ========== 连接健康 ==========
SELECT
    '连接使用率' AS 指标,
    CONCAT(
        (SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Threads_connected'),
        ' / ',
        (SELECT VARIABLE_VALUE FROM performance_schema.global_variables WHERE VARIABLE_NAME = 'max_connections')
    ) AS 当前值,
    CASE
        WHEN (SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Threads_connected')
             / (SELECT VARIABLE_VALUE FROM performance_schema.global_variables WHERE VARIABLE_NAME = 'max_connections') > 0.8
        THEN '警告：连接数超过 80%'
        ELSE '正常'
    END AS 状态;

-- ========== 慢查询增长 ==========
SELECT
    '慢查询数' AS 指标,
    VARIABLE_VALUE AS 当前值,
    CASE
        WHEN VARIABLE_VALUE > 100 THEN '警告：慢查询过多，需优化'
        ELSE '正常'
    END AS 状态
FROM performance_schema.global_status
WHERE VARIABLE_NAME = 'Slow_queries';

-- ========== 缓冲池命中率 ==========
SELECT
    '缓冲池命中率' AS 指标,
    CONCAT(
        ROUND(
            (1 - (
                (SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Innodb_buffer_pool_reads')
                /
                (SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Innodb_buffer_pool_read_requests')
            )) * 100, 2
        ),
        '%'
    ) AS 当前值,
    CASE
        WHEN (1 - (
            (SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Innodb_buffer_pool_reads')
            /
            (SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Innodb_buffer_pool_read_requests')
        )) < 0.95
        THEN '警告：命中率低于 95%'
        ELSE '正常'
    END AS 状态;

-- ========== 表锁等待 ==========
SELECT
    '表锁等待次数' AS 指标,
    VARIABLE_VALUE AS 当前值,
    CASE
        WHEN VARIABLE_VALUE > 0 THEN '注意：存在表锁等待'
        ELSE '正常'
    END AS 状态
FROM performance_schema.global_status
WHERE VARIABLE_NAME = 'Table_locks_waited';

-- ========== 异常连接 ==========
SELECT
    '中断连接数' AS 指标,
    VARIABLE_VALUE AS 当前值,
    CASE
        WHEN VARIABLE_VALUE > 10 THEN '警告：中断连接过多，检查网络或暴力破解'
        ELSE '正常'
    END AS 状态
FROM performance_schema.global_status
WHERE VARIABLE_NAME = 'Aborted_connects';
```

### 3.2 查看数据库大小和表统计

```sql
-- 查看 ecommerce 库中各表的大小
SELECT
    table_name AS '表名',
    table_rows AS '估算行数',
    ROUND(data_length / 1024 / 1024, 2) AS '数据大小(MB)',
    ROUND(index_length / 1024 / 1024, 2) AS '索引大小(MB)',
    ROUND((data_length + index_length) / 1024 / 1024, 2) AS '总大小(MB)',
    engine AS '存储引擎'
FROM information_schema.tables
WHERE table_schema = 'ecommerce'
ORDER BY data_length DESC;

-- 查看所有数据库的大小
SELECT
    table_schema AS '数据库',
    COUNT(*) AS '表数量',
    ROUND(SUM(data_length) / 1024 / 1024, 2) AS '数据大小(MB)',
    ROUND(SUM(index_length) / 1024 / 1024, 2) AS '索引大小(MB)',
    ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS '总大小(MB)'
FROM information_schema.tables
WHERE table_schema NOT IN ('information_schema', 'performance_schema', 'sys', 'mysql')
GROUP BY table_schema
ORDER BY SUM(data_length + index_length) DESC;
```

### 3.3 用 Navicat 辅助查看

在 Navicat 中可以图形化查看以上信息：

1. 右键连接 → **服务器监控** → 查看进程列表、变量和状态
2. 右键数据库 → **转储 SQL 文件**（备份前查看对象列表）
3. 右键表 → **设计表** → 查看索引列表
4. 查询窗口中执行 `EXPLAIN` 并查看执行计划表

<aside>
✅

**检查点 3**：完成 5 项健康指标监控，表大小统计已生成。

</aside>

---

## 任务四 安全事件模拟与审计

### 4.1 模拟安全事件

#### 事件 1：暴力破解尝试

```bash
# 模拟暴力破解：使用错误密码反复尝试连接
# 在虚拟机终端中执行（故意使用错误密码）
for i in $(seq 1 5); do
    mysql -u root -pwrong_password 2>/dev/null
done

# 使用一个不存在的用户尝试连接
mysql -u hacker -p123456 -h 192.168.100.20 2>/dev/null
```

#### 事件 2：可疑的 SQL 操作

```sql
# 用 dev_user 账号（在 Navicat 中打开 dev_user 连接）执行一些越权尝试
# 这些操作应该被拒绝，但仍会被记录

-- 尝试访问系统表
SELECT * FROM mysql.user;

-- 尝试读取服务器文件
SELECT LOAD_FILE('/etc/passwd');

-- 尝试创建新数据库
CREATE DATABASE hacked_db;
```

#### 事件 3：可疑的数据访问模式

```sql
# 用 analyst 账号（在 Navicat 中打开 analyst 连接）尝试写操作
INSERT INTO ecommerce.users (username, email, phone, password_hash)
VALUES ('injected', 'evil@hack.com', '000', 'hacked');
```

### 4.2 安全事件检测

#### 检测 1：查看错误日志中的认证失败

```bash
# 查看最近的认证失败记录
sudo grep "Access denied" /var/log/mysql/error.log | tail -20
```

#### 检测 2：查看当前可疑连接

```sql
sudo mysql

-- 查看所有当前连接
SELECT
    id AS '连接ID',
    user AS '用户名',
    host AS '来源主机',
    db AS '数据库',
    command AS '命令',
    time AS '持续秒数',
    LEFT(info, 100) AS 'SQL语句'
FROM information_schema.processlist
WHERE user NOT IN ('system user', 'event_scheduler')
ORDER BY time DESC;

-- 查看异常连接（长时间 Sleep 可能是连接泄漏或扫描器）
SELECT
    user, host, db, time, command
FROM information_schema.processlist
WHERE command = 'Sleep' AND time > 300;
```

#### 检测 3：查看账号权限异常

```sql
-- 查看哪些非 root 账号拥有危险权限
SELECT
    grantee,
    privilege_type
FROM information_schema.schema_privileges
WHERE privilege_type IN ('ALL PRIVILEGES', 'GRANT OPTION')
    AND grantee NOT LIKE '%root%'
    AND grantee NOT LIKE '%mysql%';

-- 查看全局权限中的高危权限
SELECT
    CONCAT('''', user, '''@''', host, '''') AS 账号,
    CASE WHEN Super_priv = 'Y' THEN '是' ELSE '否' END AS SUPER,
    CASE WHEN File_priv = 'Y' THEN '是' ELSE '否' END AS FILE,
    CASE WHEN Grant_priv = 'Y' THEN '是' ELSE '否' END AS GRANT_OPTION,
    CASE WHEN Shutdown_priv = 'Y' THEN '是' ELSE '否' END AS SHUTDOWN
FROM mysql.user
WHERE (Super_priv = 'Y' OR File_priv = 'Y' OR Grant_priv = 'Y')
    AND user NOT IN ('root', 'mysql.sys', 'mysql.session', 'debian-sys-maint');
```

### 4.3 综合安全审计脚本

将以上检查整合为一个完整的审计脚本：

```sql
-- ========== MySQL 安全审计脚本 ==========
-- 执行方式：mysql -u root -p123456 < security_audit.sql

-- 输出审计标题
SELECT '========== MySQL 安全审计报告 ==========' AS '';
SELECT CONCAT('审计时间：', NOW()) AS '';
SELECT CONCAT('MySQL 版本：', VERSION()) AS '';
SELECT '' AS '';

-- 1. 账号清单
SELECT '【1】账号清单' AS '审计项';
SELECT
    user AS '用户名',
    host AS '来源主机',
    plugin AS '认证插件',
    CASE account_locked WHEN 'Y' THEN '已锁定' ELSE '正常' END AS '锁定状态',
    CASE WHEN authentication_string = '' OR authentication_string IS NULL
         THEN '空密码！' ELSE '有密码' END AS '密码状态',
    password_expired AS '密码过期'
FROM mysql.user
WHERE user NOT IN ('mysql.sys', 'mysql.session', 'debian-sys-maint')
ORDER BY user;

-- 2. 匿名用户检查
SELECT '【2】匿名用户检查' AS '审计项';
SELECT
    CASE WHEN COUNT(*) = 0 THEN '通过：无匿名用户'
         ELSE CONCAT('风险：发现 ', COUNT(*), ' 个匿名用户')
    END AS '结果'
FROM mysql.user WHERE user = '';

-- 3. root 远程访问检查
SELECT '【3】root 远程访问检查' AS '审计项';
SELECT
    CASE WHEN COUNT(*) = 0 THEN '通过：root 仅限本地'
         ELSE CONCAT('风险：root 可从以下主机远程登录：', GROUP_CONCAT(host))
    END AS '结果'
FROM mysql.user WHERE user = 'root' AND host != 'localhost';

-- 4. 空密码检查
SELECT '【4】空密码检查' AS '审计项';
SELECT
    CASE WHEN COUNT(*) = 0 THEN '通过：无空密码账号'
         ELSE CONCAT('风险：发现 ', COUNT(*), ' 个空密码账号')
    END AS '结果'
FROM mysql.user
WHERE (authentication_string = '' OR authentication_string IS NULL)
    AND user NOT IN ('mysql.sys', 'mysql.session');

-- 5. 高危权限检查
SELECT '【5】高危权限检查' AS '审计项';
SELECT
    CONCAT('''', user, '''@''', host, '''') AS '拥有高危权限的账号',
    CASE WHEN Super_priv = 'Y' THEN 'SUPER ' ELSE '' END,
    CASE WHEN File_priv = 'Y' THEN 'FILE ' ELSE '' END,
    CASE WHEN Grant_priv = 'Y' THEN 'GRANT_OPTION' ELSE '' END
FROM mysql.user
WHERE (Super_priv = 'Y' OR File_priv = 'Y')
    AND user NOT IN ('root', 'mysql.sys', 'mysql.session', 'debian-sys-maint');

-- 6. 认证失败统计
SELECT '【6】连接异常统计' AS '审计项';
SELECT
    VARIABLE_VALUE AS '中断连接总数',
    CASE WHEN VARIABLE_VALUE > 10 THEN '警告：可能存在暴力破解'
         ELSE '正常' END AS '评估'
FROM performance_schema.global_status
WHERE VARIABLE_NAME = 'Aborted_connects';

-- 7. 安全配置检查
SELECT '【7】安全配置检查' AS '审计项';
SELECT
    'bind_address' AS '配置项',
    VARIABLE_VALUE AS '当前值',
    CASE WHEN VARIABLE_VALUE = '0.0.0.0' THEN '需配合防火墙'
         ELSE 'OK' END AS '评估'
FROM performance_schema.global_variables WHERE VARIABLE_NAME = 'bind_address'
UNION ALL
SELECT 'log_bin', VARIABLE_VALUE,
    CASE WHEN VARIABLE_VALUE = 'ON' THEN 'OK' ELSE '风险：未开启' END
FROM performance_schema.global_variables WHERE VARIABLE_NAME = 'log_bin'
UNION ALL
SELECT 'local_infile', VARIABLE_VALUE,
    CASE WHEN VARIABLE_VALUE = 'OFF' THEN 'OK' ELSE '风险：允许本地文件导入' END
FROM performance_schema.global_variables WHERE VARIABLE_NAME = 'local_infile'
UNION ALL
SELECT 'skip_name_resolve', VARIABLE_VALUE,
    CASE WHEN VARIABLE_VALUE = 'ON' THEN 'OK' ELSE '建议开启' END
FROM performance_schema.global_variables WHERE VARIABLE_NAME = 'skip_name_resolve';

-- 8. 权限摘要
SELECT '【8】各账号权限摘要' AS '审计项';
SELECT
    grantee AS '账号',
    GROUP_CONCAT(DISTINCT privilege_type ORDER BY privilege_type SEPARATOR ', ') AS '权限列表'
FROM information_schema.schema_privileges
WHERE grantee NOT LIKE '%root%'
    AND grantee NOT LIKE '%mysql.%'
    AND grantee NOT LIKE '%sys%'
    AND grantee NOT LIKE '%session%'
GROUP BY grantee
ORDER BY grantee;

SELECT '========== 审计完成 ==========' AS '';
```

<aside>
✅

**检查点 4**：安全审计脚本执行成功，各项检查结果已记录。

</aside>

---

## 任务五 应急响应演练

### 5.1 应急响应流程

<aside>
🛡️

**发现安全事件时的标准响应流程**

1. **确认**：确认是否真的是安全事件（排除误报）
2. **止损**：立即采取措施阻止损害扩大
3. **取证**：保留证据用于后续分析
4. **修复**：消除安全隐患
5. **复盘**：总结经验，完善防护

</aside>

### 5.2 模拟应急场景：发现可疑账号

#### 第 1 步：确认——发现异常账号

```sql
-- 发现了一个未知账号
SELECT user, host, plugin, account_locked
FROM mysql.user
WHERE user NOT IN (
    'root', 'mysql.sys', 'mysql.session',
    'debian-sys-maint', 'dba_admin', 'dev_user',
    'analyst', 'app_ecom'
);
```

假设发现了一个可疑账号 `'backdoor'@'%'`。

#### 第 2 步：止损——锁定可疑账号

```sql
-- 立即锁定账号（不删除，保留证据）
ALTER USER 'backdoor'@'%' ACCOUNT LOCK;

-- 确认已锁定
SELECT user, host, account_locked
FROM mysql.user WHERE user = 'backdoor';
```

#### 第 3 步：取证——查看该账号权限和操作

```sql
-- 查看可疑账号的权限
SHOW GRANTS FOR 'backdoor'@'%';

-- 查看该账号是否有活动连接
SELECT * FROM information_schema.processlist WHERE user = 'backdoor';

-- 如果有活动连接，结束它
-- KILL <连接ID>;

-- 检查错误日志中该账号的登录记录
-- 在终端中执行：
-- sudo grep "backdoor" /var/log/mysql/error.log
```

#### 第 4 步：修复——删除可疑账号

```sql
-- 确认没有业务依赖后删除
DROP USER 'backdoor'@'%';

-- 确认已删除
SELECT user, host FROM mysql.user WHERE user = 'backdoor';
```

#### 第 5 步：复盘——检查其他账号安全性

```sql
-- 检查是否有其他账号密码过于简单
SELECT user, host, plugin FROM mysql.user
WHERE authentication_string IN (
    -- 常见弱密码的哈希（课堂演示用，实际应使用密码审计工具）
    SELECT authentication_string FROM mysql.user
    WHERE authentication_string = ''
);

-- 检查是否有账号权限过大
SELECT user, host FROM mysql.user
WHERE Super_priv = 'Y' AND user NOT IN ('root');

-- 确认防火墙规则
-- sudo ufw status
```

### 5.3 撰写应急响应报告

<aside>
📝

**课堂任务**：根据演练过程，填写应急响应报告模板。

</aside>

| 项目 | 内容 |
| --- | --- |
| **事件编号** | SEC-001 |
| **发现时间** | （填写） |
| **事件类型** | 可疑账号入侵 |
| **影响范围** | （填写） |
| **发现方式** | 安全审计脚本检查 |
| **止损措施** | 锁定可疑账号 |
| **取证结果** | （填写账号权限、活动连接等） |
| **修复措施** | 删除可疑账号 + 全面安全检查 |
| **改进建议** | （填写） |

---

## 实验总结

| 任务 | 核心能力 | 关键验证点 |
| --- | --- | --- |
| 任务一：性能基线 | 服务器状态采集 | 能解读 5+ 项关键指标 |
| 任务二：慢查询优化 | EXPLAIN 分析 + 索引优化 | 至少 2 条查询执行计划改善 |
| 任务三：状态监控 | 健康指标监控脚本 | 5 项指标监控完成 |
| 任务四：安全审计 | 审计脚本编写与执行 | 8 项审计检查全部完成 |
| 任务五：应急响应 | 安全事件响应流程 | 完成完整 5 步应急演练 |

<aside>
💬

**本实验核心收获**

1. **性能优化闭环**：监控基线 → 发现瓶颈 → EXPLAIN 分析 → 索引优化 → 验证效果
2. **EXPLAIN 是 SQL 优化的核心工具**：关注 `type`、`key`、`rows`、`Extra` 四个字段
3. **安全审计要定期执行**：不是出了事才审计，而是定期主动检查
4. **应急响应五步法**：确认 → 止损 → 取证 → 修复 → 复盘
5. **监控和审计是运维的"眼睛"**：没有监控就看不到问题，没有审计就防不住风险

</aside>
