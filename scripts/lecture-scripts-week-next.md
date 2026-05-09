---
title: "下周授课逐字稿"
---

# 下周授课逐字稿（4 课时 × 40 分钟）

---

## 第 1 课时：权限管理——最小权限原则

> 承接上周「创建账号 + Navicat 连接」，本课延伸「这个账号能干什么」

---

### 开场（0-3 分钟）

好，同学们，上周我们做了几件事：装了 MySQL，改了配置文件，建了账号，然后用 Navicat 连上了数据库。现在大家都能在 Navicat 里看到 stusta 库里的学生表了对吧？

但是我想问大家一个问题——上周我们建的那个 app 账号，它能做什么？有同学记得吗？

对，我们给了它 SELECT、INSERT、UPDATE、DELETE 四个权限，范围是 stusta 这个库。那我问大家，如果我现在想让 app 账号去建一个新数据库，它能做到吗？

试一下就知道了。来，打开 Navicat，在查询窗口里敲：

```sql
CREATE DATABASE hackdb;
```

执行——报错了对吧？`ERROR 1044: Access denied`。这就对了，说明我们的 app 账号没有建库的权限。

今天这节课，我们就来系统地学习 MySQL 的权限管理。核心原则就四个字——**最小权限**。给你的账号刚好够用的权限，不多给。

---

### GRANT 和 REVOKE 基础语法（3-10 分钟）

首先来看授权语法。MySQL 授权用的是 GRANT 语句，基本格式：

```sql
GRANT 权限列表 ON 数据库.表 TO '用户'@'主机';
```

我给大家写几个例子，大家跟着在虚拟机上敲：

**例子 1：只给查询权限**

```sql
-- 先创建一个只读用户
CREATE USER 'reader'@'192.168.100.%' IDENTIFIED WITH mysql_native_password BY '123456';

-- 只授予 SELECT 权限
GRANT SELECT ON stusta.* TO 'reader'@'192.168.100.%';
```

这里 `stusta.*` 里的星号代表 stusta 库下的所有表。这就是**库级授权**。

**例子 2：给增删改查四个权限**

```sql
-- 创建一个开发用户
CREATE USER 'dev'@'192.168.100.%' IDENTIFIED WITH mysql_native_password BY '123456';

GRANT SELECT, INSERT, UPDATE, DELETE ON stusta.* TO 'dev'@'192.168.100.%';
```

注意，这四个权限就是我们上周给 app 用户的那些。开发用户通常需要这四个。

**例子 3：加上建表的权限**

```sql
GRANT CREATE ON stusta.* TO 'dev'@'192.168.100.%';
```

这样 dev 用户就能在 stusta 库下创建新表了。

那如果我想把某个权限收回来呢？用 REVOKE：

```sql
-- 收回 DELETE 权限
REVOKE DELETE ON stusta.* FROM 'dev'@'192.168.100.%';
```

收回之后，dev 用户就不能执行 DELETE 了。

大家注意，GRANT 和 REVOKE 是配对的。给了什么就能收什么。关键是你要清楚你给了什么。

---

### 实操：按岗位分配权限（10-25 分钟）

好，现在我们来做一个完整场景。假设你是一个公司的 DBA，公司有三个岗位需要访问数据库：

- **运维人员**：只需要看数据，不能改
- **开发人员**：需要增删改查，还能建表
- **DBA 助手**：什么都能做

大家跟着我一起操作。先登到虚拟机：

```bash
sudo mysql
```

**第一步：创建运维账号**

```sql
CREATE USER 'ops'@'192.168.100.%' IDENTIFIED WITH mysql_native_password BY '123456';
GRANT SELECT ON stusta.* TO 'ops'@'192.168.100.%';
```

运维只给了 SELECT，只能看，不能改。

**第二步：创建开发账号**

```sql
CREATE USER 'dev'@'192.168.100.%' IDENTIFIED WITH mysql_native_password BY '123456';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE ON stusta.* TO 'dev'@'192.168.100.%';
```

开发有增删改查加建表，但没有 DROP（删表太危险）。

**第三步：创建 DBA 助手账号**

```sql
CREATE USER 'dba_assist'@'192.168.100.%' IDENTIFIED WITH mysql_native_password BY '123456';
GRANT ALL PRIVILEGES ON stusta.* TO 'dba_assist'@'192.168.100.%';
```

`ALL PRIVILEGES` 是所有权限的意思。但注意，我这里给的范围是 `stusta.*`，不是 `*.*`。`*.*` 代表所有库的所有表，那是超级管理员的权限，绝对不能随便给。

现在大家来验证一下。打开 Navicat，分别用这三个账号登录，试试看：

**ops 账号：**
```sql
SELECT * FROM stusta.students;          -- 成功
INSERT INTO stusta.students (name, score) VALUES ('测试', 60);  -- 失败
```

SELECT 成功，INSERT 报错 `ERROR 1142`，这就对了。

**dev 账号：**
```sql
INSERT INTO stusta.students (name, score) VALUES ('测试', 60);  -- 成功
DROP TABLE stusta.students;             -- 失败
```

INSERT 成功，DROP 报错。因为没给 DROP 权限。

**dba_assist 账号：**
```sql
DROP TABLE stusta.students;             -- 成功（小心！）
```

这个会成功，因为给了 ALL。所以——

等一下，我刚才说了什么？DROP TABLE 会成功？那表就没了啊！所以大家看，ALL PRIVILEGES 包含了 DROP，这在生产环境是非常危险的。

我们赶紧把表恢复回来：

```sql
-- 用 sudo mysql 登录
CREATE TABLE stusta.students (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL,
    score DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO stusta.students (name, score) VALUES
    ('张三', 88.5), ('李四', 92.0), ('王五', 76.0);
```

这就是为什么我说——**ALL PRIVILEGES 能不给就不给**。你给了 ALL，就意味着别人可以删你的表。

---

### 查看权限与 FLUSH PRIVILEGES（25-35 分钟）

好，现在我们已经有好几个账号了，怎么查看一个账号有哪些权限呢？

```sql
SHOW GRANTS FOR 'ops'@'192.168.100.%';
SHOW GRANTS FOR 'dev'@'192.168.100.%';
SHOW GRANTS FOR 'dba_assist'@'192.168.100.%';
```

`SHOW GRANTS` 会列出这个账号被授予的所有权限。大家看一下输出，`dba_assist` 那行会显示 `GRANT ALL PRIVILEGES`，而 `ops` 那行只有 `GRANT SELECT`。

现在讲一个大家经常会困惑的问题——**权限修改后要不要执行 `FLUSH PRIVILEGES`？**

答案是：**大多数情况下不需要**。

当你用 `GRANT`、`REVOKE`、`CREATE USER`、`ALTER USER`、`DROP USER` 这些标准语句的时候，MySQL 会自动刷新内存中的权限缓存，不需要手动 FLUSH。

什么时候才需要 FLUSH？只有你直接去改 `mysql.user` 这个系统表的时候，比如：

```sql
UPDATE mysql.user SET Host = '%' WHERE User = 'app';
```

这种直接 UPDATE 系统表的操作，MySQL 不知道你改了，所以需要 FLUSH。

但是，**我们课堂上永远不要去直接 UPDATE 系统表**。记住口诀：用标准语句，不用 FLUSH；直接改表，必须 FLUSH。

---

### 小结（35-40 分钟）

好，我们来总结一下今天学的内容：

1. **GRANT 语法**：`GRANT 权限 ON 库.表 TO '用户'@'主机'`
2. **REVOKE 语法**：`REVOKE 权限 ON 库.表 FROM '用户'@'主机'`
3. **最小权限原则**：只给够用的权限，不多给。运维给 SELECT，开发给 CRUD+CREATE，DBA 才给 ALL
4. **SHOW GRANTS**：查看权限，养成"授权后验证"的习惯
5. **FLUSH PRIVILEGES**：用标准语句不用 flush，直接改表才需要

大家记住一个原则——**能少给就少给，给多了收回来很难**。这在真实工作中非常重要。你给了一个开发人员 ALL 权限，他不小心删了生产表，那是你的责任，不是他的。

好，下节课我们学日志。权限管的是"谁能干什么"，日志管的是"谁干了什么"。下节课见。

---

## 第 2 课时：日志管理——出事能追溯

> 承接上节课的权限管理，本课从"谁能干什么"延伸到"谁干了什么"

---

### 开场回顾（0-5 分钟）

上节课我们学了权限管理，知道了怎么控制"谁能干什么"。但是光控制还不够——万一有人越权了呢？万一有人用合法账号做了坏事呢？你怎么知道谁在什么时候干了什么？

答案就是——**日志**。

大家回忆一下上周的配置文件修改。我们改的是 `/etc/mysql/mysql.conf.d/mysqld.cnf` 这个文件对吧？今天我们要在同一个文件里加日志配置，所以上次的经验直接用得上。

---

### 四种日志对比（5-10 分钟）

MySQL 有四种主要日志，我先给大家一个表格，大家先会选，再会做：

| 日志类型 | 记录什么 | 什么时候用 | 性能影响 |
|----------|---------|-----------|---------|
| 错误日志 | 启动/运行错误 | 故障排查第一步 | 无 |
| 通用查询日志 | 所有 SQL 语句 | 临时排错 | 高 |
| 慢查询日志 | 执行慢的 SQL | 找性能问题 | 低 |
| 二进制日志 binlog | 所有写操作 | 复制 + 数据恢复 | 低-中 |

我打个比方大家就好理解了：

- **错误日志**就像医院的急诊记录——出了大事才记
- **通用查询日志**就像商场的监控录像——所有进出都拍，但存起来很占空间
- **慢查询日志**就像考勤异常记录——只记迟到的，不管正常的
- **binlog**就像银行流水——只记钱的变动，不记你看了几次余额

生产环境中，错误日志默认开着，通用查询日志基本不开，慢查询日志建议开，binlog 必须开。我们重点学 binlog，因为它是数据恢复的基石。

---

### 错误日志（10-13 分钟）

错误日志是排查问题的第一入口。MySQL 启动失败了？看错误日志。连接报错了？看错误日志。

```bash
# 查看错误日志路径
sudo mysql -e "SHOW VARIABLES LIKE 'log_error';"

# 查看最近的内容
sudo tail -50 /var/log/mysql/error.log
```

大家现在敲一下，看看输出。你会看到一些启动信息、关闭信息，如果有 [ERROR] 开头的行就是报错了。

错误日志不需要配置，MySQL 默认就开着的。大家只需要记住——**出问题先看这里**。

---

### 慢查询日志（13-20 分钟）

接下来看慢查询日志。这个在生产中非常实用——用户反馈"系统好卡"，你怎么查？就是靠它。

**配置慢查询日志：**

```bash
sudo mysql << 'EOF'
-- 开启慢查询日志
SET GLOBAL slow_query_log = 1;
SET GLOBAL long_query_time = 1;
SET GLOBAL log_queries_not_using_indexes = 1;
EOF
```

`long_query_time = 1` 意思是超过 1 秒的 SQL 才记录。`log_queries_not_using_indexes = 1` 是没用索引的查询也记录，即使没超过 1 秒。

现在我们来故意制造一条慢查询：

```sql
-- 在 MySQL 中执行
SELECT SLEEP(2);
```

`SLEEP(2)` 会让 MySQL 等待 2 秒，这肯定超过 1 秒了，会被记录到慢查询日志。

然后查看：

```bash
sudo tail -20 /var/log/mysql/slow.log
```

你应该能看到刚才那条 SELECT SLEEP(2) 的记录。

MySQL 还自带了一个分析工具叫 `mysqldumpslow`，可以对慢查询日志做统计：

```bash
# 按查询次数排序，看前 10 条
sudo mysqldumpslow -s c -t 10 /var/log/mysql/slow.log
```

这个工具会把相似的 SQL 归为一类，帮你快速找到"哪些 SQL 最慢"或者"哪些 SQL 执行次数最多"。

---

### binlog 详解（20-35 分钟）

好，现在到了今天的重点——**binlog**。

为什么说它最重要？因为它有两个关键用途：
1. **主从复制**——从库通过读主库的 binlog 来同步数据
2. **数据恢复**——配合全量备份，可以恢复到任意秒

**第一步：开启 binlog**

编辑配置文件：

```bash
sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf
```

在 `[mysqld]` 段添加：

```ini
log_bin = /var/lib/mysql/mysql-bin
binlog_format = ROW
server_id = 1
binlog_expire_logs_seconds = 604800
max_binlog_size = 100M
```

这些参数什么意思？

- `log_bin`：指定 binlog 文件的前缀，实际文件名会是 `mysql-bin.000001`、`mysql-bin.000002` 这样递增
- `binlog_format = ROW`：记录格式，ROW 是最精确的，记录每一行数据变更前后的值。生产环境就用 ROW，不用纠结
- `server_id = 1`：服务器标识，单机随便写，但做主从的时候每台机器必须不同
- `binlog_expire_logs_seconds = 604800`：7 天自动清理旧 binlog
- `max_binlog_size = 100M`：单个文件超过 100M 就切换到下一个文件

保存退出，重启：

```bash
sudo systemctl restart mysql
```

**第二步：验证 binlog 已开启**

```sql
SHOW VARIABLES LIKE 'log_bin';        -- 应该是 ON
SHOW VARIABLES LIKE 'binlog_format';  -- 应该是 ROW
SHOW BINARY LOGS;                     -- 列出所有 binlog 文件
```

大家看一下 `SHOW BINARY LOGS` 的输出，应该能看到一个或多个 binlog 文件，文件大小从 100 多字节开始。

**第三步：产生一些写操作**

binlog 只记录写操作，SELECT 不记录。我们来做一些写操作：

```sql
USE stusta;
INSERT INTO students (name, score) VALUES ('赵六', 85.0);
UPDATE students SET score = 90.0 WHERE name = '王五';
DELETE FROM students WHERE name = '赵六';
```

这三条是写操作，会被记录到 binlog 中。

**第四步：查看 binlog 内容**

binlog 是二进制文件，不能直接 cat。MySQL 提供了 `mysqlbinlog` 工具来解码：

```bash
sudo mysqlbinlog --base64-output=DECODE-ROWS -v /var/lib/mysql/mysql-bin.000001 | less
```

`--base64-output=DECODE-ROWS` 是把编码过的内容解码成可读格式，`-v` 是显示详细信息。less 可以翻页查看，按 q 退出。

大家找一找，能看到刚才的 INSERT、UPDATE、DELETE 吗？

如果内容太多，可以按时间过滤：

```bash
sudo mysqlbinlog \
  --start-datetime="2025-01-01 00:00:00" \
  --stop-datetime="2025-12-31 23:59:59" \
  /var/lib/mysql/mysql-bin.000001 | grep -A 5 "INSERT"
```

**第五步：PITR 恢复思路**

现在讲一个最重要的概念——**PITR，Point-In-Time Recovery，时间点恢复**。

场景：假设今天上午 10:00，有人不小心执行了 `DELETE FROM students;`，把整张表清空了。你有一个昨晚的全量备份。如果只恢复备份，今天上午所有正常的数据操作就丢了。

PITR 的思路是：先恢复昨晚的备份 → 然后用 binlog 重放从备份到误操作之前的所有正常操作 → 数据恢复到误操作前一刻。

```
昨晚备份 → 重放 binlog（00:00-09:59）→ 跳过误操作 → 继续重放后续正常操作
```

上周我们学的 `mysqldump` 做全量备份，加上今天学的 binlog 做增量恢复，就构成了完整的恢复方案。

这就是为什么 binlog 必须开——没有 binlog，你就无法做时间点恢复。

---

### 小结 + 项目五收尾（35-40 分钟）

好，我们来回顾一下项目五的完整脉络：

```
装得起来 → 配得安全 → 管得住人 → 出事能追溯
   第1课       第2课       第3课       第4课
```

- 第 1 课：安装 MySQL，让它跑起来
- 第 2 课：改配置，把边界和默认坑补齐
- 第 3 课：建账号、授权、Navicat 远程连接
- 第 4 课（今天）：日志——错误日志、慢查询、binlog

这四步形成了一个闭环：**装起来→配安全→管住人→出事能查**。

从下节课开始，我们进入项目六——MySQL 高级安全维护。项目五解决的是"基本能用和安全"，项目六解决的是"更安全、更精细、更可靠"。下次课我们会从密码策略和认证插件开始，让大家知道怎么让 MySQL "进不来"。

---

## 第 3 课时：密码策略 + 认证插件 + SSL/TLS

> 进入项目六，从项目五的"建账号"延伸到"建更安全的账号"

---

### 项目六总览（0-8 分钟）

好，同学们，从今天开始我们进入项目六——MySQL 高级安全维护。

项目五我们学的是基础：装起来、配安全、管住人、出事能查。项目六要在这个基础上做得更深。

我给大家一个主线地图，就四句话：

```
进不来 → 留痕迹 → 拿走读不了 → 出事能恢复
```

- **进不来**：密码策略、认证插件、SSL 加密——这是今天要学的
- **留痕迹**：审计插件——谁在什么时间做了什么操作都有记录
- **拿走读不了**：数据加密——就算有人把数据文件拷走了，也看不了
- **出事能恢复**：物理热备、时间点恢复、主从复制——比 mysqldump 强大得多

今天我们先解决"进不来"这个问题。

---

### 密码策略：validate_password（8-18 分钟）

上周我们建账号的时候用的密码是什么？`123456`。上课的时候我还让大家先把密码策略降成 LOW 才能创建这个密码，对吧？

为什么？因为 MySQL 的密码验证组件默认要求密码至少 8 位，包含大小写字母、数字和特殊字符。`123456` 这种密码根本过不了。

但是——在生产环境，你绝对不应该降低密码策略，而是应该使用强密码。今天我们就来正式配置密码策略。

**第一步：安装密码验证组件**

```sql
sudo mysql

INSTALL COMPONENT 'file://component_validate_password';

SHOW VARIABLES LIKE 'validate_password%';
```

大家看输出，默认策略是 MEDIUM，最短 8 位。这个策略已经比课堂用的 LOW 强多了。

**第二步：设置为强策略**

```sql
SET GLOBAL validate_password.policy = 'STRONG';
SET GLOBAL validate_password.length = 12;
SET GLOBAL validate_password.mixed_case_count = 2;
SET GLOBAL validate_password.number_count = 2;
SET GLOBAL validate_password.special_char_count = 2;
```

STRONG 策略在 MEDIUM 的基础上还增加了字典检查，不允许使用常见单词做密码。我把长度改成了 12 位，要求至少 2 个大写、2 个小写、2 个数字、2 个特殊字符。

**第三步：验证弱密码被拒绝**

现在我们来试，创建一个弱密码用户：

```sql
CREATE USER 'test_weak'@'localhost' IDENTIFIED BY '123456';
```

报错了对吧？`ERROR 1819: Your password does not satisfy the current policy requirements`。密码不满足策略要求。

换一个合规密码：

```sql
CREATE USER 'test_weak'@'localhost' IDENTIFIED BY 'Str0ng!Pass#2025';
```

成功了。大家注意这个密码：大写 S、小写字母、数字 0 和 2025、感叹号和井号——12 位，满足所有要求。

```sql
-- 清理测试用户
DROP USER 'test_weak'@'localhost';
```

这就是密码策略的作用——**从制度上杜绝弱密码**。就算开发人员想偷懒用 123456，系统也不让他创建。

---

### 认证插件：caching_sha2_password（18-30 分钟）

好，密码策略是"密码要多强"，接下来看"密码怎么验证"——这就是认证插件。

上周我们建账号的时候，用的是 `mysql_native_password` 这个认证插件。为什么？因为 Navicat 旧版本不兼容新的插件。但 MySQL 8.0 默认的认证插件已经不是它了。

MySQL 8.0 默认用的是 `caching_sha2_password`。这两个有什么区别？

| 对比项 | mysql_native_password | caching_sha2_password |
|--------|----------------------|----------------------|
| 哈希算法 | SHA-1 | SHA-256 + 盐值 |
| 安全性 | 低（SHA-1 已被攻破） | 高 |
| 缓存 | 无 | 内存缓存已认证哈希 |
| 兼容性 | 所有客户端 | 需 MySQL 8.0+ 连接器 |

简单说，`caching_sha2_password` 更安全，SHA-1 在密码学界已经被认为不安全了。所以 MySQL 8.0 把默认插件改了。

**查看当前用户的认证插件：**

```sql
SELECT User, Host, plugin FROM mysql.user ORDER BY User;
```

大家看输出，root 用的还是 `auth_socket`（Ubuntu 默认），我们上周建的 app 用的是 `mysql_native_password`（因为我们建的时候手动指定了）。

**把 root 改为密码认证：**

在生产环境中，root 用 auth_socket 是不够的——你只能在本机用 sudo 登录，远程管理不了。应该改为密码认证：

```sql
ALTER USER 'root'@'localhost' IDENTIFIED WITH caching_sha2_password BY 'R00t!Secure#2025';
FLUSH PRIVILEGES;
```

改完之后，就不能用 `sudo mysql` 了，要用密码登录：

```bash
mysql -u root -p'R00t!Secure#2025' -e "SELECT 'password auth OK' AS status;"
```

能登录就说明改成功了。

再查看一下插件：

```sql
SELECT User, Host, plugin FROM mysql.user WHERE User='root';
```

应该显示 `caching_sha2_password` 了。

**那 app 用户呢？** 上周我们为了兼容 Navicat 用了 `mysql_native_password`。如果你的 Navicat 版本是 16 以上，其实已经支持新插件了，可以改过来：

```sql
ALTER USER 'app'@'192.168.100.%' IDENTIFIED WITH caching_sha2_password BY 'App!Secure#2025';
FLUSH PRIVILEGES;
```

改完后在 Navicat 里重新连接试试，如果能连上，说明你的 Navicat 版本支持新插件。

**总结一下认证插件的选择原则：**
- 新建用户：默认用 `caching_sha2_password`，更安全
- 只有旧客户端连不上时，才对那个特定用户降级为 `mysql_native_password`
- root 必须改为密码认证，不能用 auth_socket

---

### SSL/TLS 加密连接（30-40 分钟）

最后一个话题——SSL/TLS 加密连接。

大家想一个问题：你用 Navicat 连 MySQL 的时候，用户名和密码在网络上是明文传输的。如果有人在你的网络上抓包，他就能看到你的密码。这就像你在公共场合大声说出银行卡密码一样危险。

SSL/TLS 就是来解决这个问题的——它把网络传输的数据加密，抓包了也看不懂。

**第一步：检查 MySQL SSL 状态**

```sql
SHOW VARIABLES LIKE '%ssl%';
```

看 `have_ssl` 这一行。如果是 `YES`，说明 SSL 已经启用。MySQL 安装时会自动生成自签名证书，所以大部分情况下这个已经是 YES 了。

**第二步：验证当前连接是否加密**

```sql
SHOW STATUS LIKE 'Ssl_cipher';
```

如果你看到 `Value` 是空的，说明当前连接没走 SSL。如果是通过 `sudo mysql` 本机连接的，走的是 Unix socket，不需要 SSL，所以是空的是正常的。

**第三步：用 SSL 连接**

```bash
mysql -u root -p'R00t!Secure#2025' --ssl-mode=REQUIRED -e "SHOW STATUS LIKE 'Ssl_cipher';"
```

加上 `--ssl-mode=REQUIRED`，强制使用 SSL。看输出，`Ssl_cipher` 应该有值了，比如 `TLS_AES_256_GCM_SHA384`。有值就说明连接是加密的。

**第四步：Navicat 开启 SSL**

在 Navicat 的连接属性里，有个 SSL 选项卡。勾选"使用 SSL"，SSL 模式选 `REQUIRED`，然后重新连接。

连接成功后，执行：

```sql
SHOW STATUS LIKE 'Ssl_cipher';
```

有值就说明 Navicat 也是加密连接了。

这样，即使有人在你的网络上抓包，也看不到你的密码和查询内容了。

**最后总结一下今天的内容：**

| 安全层面 | 做了什么 | 效果 |
|----------|---------|------|
| 密码策略 | STRONG + 12位 | 弱密码创建不了 |
| 认证插件 | caching_sha2_password | 更安全的哈希算法 |
| SSL/TLS | REQUIRED | 网络传输加密 |

这三层加在一起，就是让 MySQL "进不来"：密码猜不到、哈希破不了、传输抓不到。下节课我们学"留痕迹"和"管得更细"——审计和细粒度权限控制。

---

## 第 4 课时：列级权限 + RBAC + 数据脱敏

> 承接第 1 课时的表级权限，延伸到列级权限和角色管理

---

### 开场回顾（0-3 分钟）

上节课我们学了密码策略、认证插件和 SSL 加密，解决的是"进不来"的问题。今天我们回到权限管理这个话题。

第 1 课时我们学的是库级和表级权限——`GRANT SELECT ON stusta.*`。但是大家想一个场景：如果有一个员工表，里面有姓名、部门、薪资、身份证号这些字段。HR 只能看姓名和部门，不能看薪资；财务能看薪资但不能看身份证号。表级权限能做到吗？

做不到。因为 `GRANT SELECT ON salary_db.employees` 是对整张表的 SELECT，HR 要是有了这个权限，就能看到所有人的薪资。

这就是为什么我们需要**列级权限**。

---

### 准备实验数据（3-5 分钟）

先建一个模拟的员工薪资表：

```sql
sudo mysql

CREATE DATABASE IF NOT EXISTS salary_db;
USE salary_db;

CREATE TABLE employees (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL,
    department VARCHAR(30) NOT NULL,
    position VARCHAR(50),
    salary DECIMAL(10,2) NOT NULL,
    id_card VARCHAR(18) NOT NULL COMMENT '身份证号',
    phone VARCHAR(20) NOT NULL COMMENT '手机号',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

INSERT INTO employees (name, department, position, salary, id_card, phone) VALUES
('张三', '技术部', '高级工程师', 28000.00, '110101199001011234', '13800138001'),
('李四', '财务部', '财务主管', 25000.00, '110101198512052345', '13800138002'),
('王五', '技术部', '初级工程师', 15000.00, '110101199503033456', '13800138003'),
('赵六', '人事部', '招聘专员', 12000.00, '110101199807074567', '13800138004'),
('钱七', '技术部', '架构师', 35000.00, '110101198709095678', '13800138005');
```

好，现在我们有了一个包含敏感信息（薪资、身份证号、手机号）的员工表。

---

### 列级权限实战（5-12 分钟）

**场景**：HR 专员只能看姓名、部门、职位和手机号，不能看薪资和身份证号。

**第一步：创建 HR 用户**

```sql
CREATE USER 'hr_user'@'192.168.100.%' IDENTIFIED WITH mysql_native_password BY '123456';
```

**第二步：授予列级权限**

注意看，SELECT 后面跟的是列名，不是星号：

```sql
GRANT SELECT (id, name, department, position, phone) 
  ON salary_db.employees TO 'hr_user'@'192.168.100.%';
```

这就意味着 hr_user 只能查这五个字段。

**第三步：验证**

打开 Navicat，用 hr_user 登录，执行：

```sql
-- 允许的字段（应成功）
SELECT id, name, department, position, phone FROM salary_db.employees;

-- 尝试查看薪资（应失败）
SELECT name, salary FROM salary_db.employees;
```

看到没有？查薪资报了 `ERROR 1143: SELECT command denied for column 'salary'`。列级权限生效了！

再看身份证号：

```sql
SELECT name, id_card FROM salary_db.employees;
```

同样报错，id_card 也不在授权范围内。

这就是列级权限的威力——**表里有很多列，但你只能看你被授权的那几列**。

同样，我们可以给财务用户不同的列级权限：

```sql
CREATE USER 'finance_user'@'192.168.100.%' IDENTIFIED WITH mysql_native_password BY '123456';
GRANT SELECT (id, name, department, salary) 
  ON salary_db.employees TO 'finance_user'@'192.168.100.%';
```

财务能看薪资，但看不到身份证号和手机号。两个用户看同一张表，看到的字段不一样。

---

### RBAC 角色管理（12-25 分钟）

刚才我们给每个用户单独授权。但如果公司有 10 个 HR 人员呢？你要把同样的 GRANT 语句执行 10 次？如果哪天权限要调整，又要改 10 个用户？

这就引出了 **RBAC——基于角色的访问控制**。

思路很简单：先创建角色，给角色授权，然后把角色分配给用户。改权限只需要改角色，所有拥有这个角色的用户自动生效。

**第一步：创建角色**

```sql
CREATE ROLE 'role_hr';
CREATE ROLE 'role_finance';
CREATE ROLE 'role_dev';
```

注意，角色和用户的区别：角色不能登录，它只是一个权限的"容器"。

**第二步：给角色授权**

```sql
-- HR 角色：看基本信息
GRANT SELECT (id, name, department, position, phone) 
  ON salary_db.employees TO 'role_hr';

-- 财务角色：看薪资
GRANT SELECT (id, name, department, salary) 
  ON salary_db.employees TO 'role_finance';

-- 开发角色：只看基础信息
GRANT SELECT (id, name, department, position)
  ON salary_db.employees TO 'role_dev';
```

**第三步：把角色分配给用户**

```sql
GRANT 'role_hr' TO 'hr_user'@'192.168.100.%';
GRANT 'role_finance' TO 'finance_user'@'192.168.100.%';
```

**第四步：设置默认角色**

用户登录后，需要激活角色才能使用。设置默认角色后，登录时自动激活：

```sql
ALTER USER 'hr_user'@'192.168.100.%' DEFAULT ROLE 'role_hr';
ALTER USER 'finance_user'@'192.168.100.%' DEFAULT ROLE 'role_finance';
```

**第五步：验证**

用 hr_user 登录 Navicat，执行：

```sql
SELECT CURRENT_ROLE();
```

应该返回 `role_hr@%`，说明当前激活的角色是 role_hr。

```sql
SHOW GRANTS FOR CURRENT_USER();
```

能看到这个用户通过 role_hr 角色获得的权限。

**RBAC 的好处是什么呢？**

假设公司新增了 5 个 HR 人员。你不需要给每个人单独授权，只需要：

```sql
CREATE USER 'hr2'@'192.168.100.%' IDENTIFIED WITH mysql_native_password BY '123456';
GRANT 'role_hr' TO 'hr2'@'192.168.100.%';
ALTER USER 'hr2'@'192.168.100.%' DEFAULT ROLE 'role_hr';
```

三行搞定。如果哪天 HR 部门需要多看一个字段，改 role_hr 的权限就行，所有 HR 人员自动生效。

---

### 数据脱敏（25-33 分钟）

好，现在还有一个问题。HR 能看手机号，但如果手机号是 `13800138001`，全号显示出来也有隐私风险。能不能显示成 `138****8001`？这就是**数据脱敏**。

MySQL 没有内置的动态脱敏功能（那是企业版的功能），但我们可以用**视图**来实现。

**创建脱敏视图：**

```sql
USE salary_db;

CREATE OR REPLACE VIEW v_employees_masked AS
SELECT 
    id,
    name,
    department,
    position,
    -- 手机号脱敏：保留前3位和后4位
    CONCAT(LEFT(phone, 3), '****', RIGHT(phone, 4)) AS phone_masked,
    -- 身份证号脱敏：保留前6位和后4位
    CONCAT(LEFT(id_card, 6), '****', RIGHT(id_card, 4)) AS id_card_masked,
    -- 薪资脱敏：只显示范围
    CASE 
        WHEN salary >= 30000 THEN '高'
        WHEN salary >= 20000 THEN '中'
        ELSE '低'
    END AS salary_level
FROM employees;
```

**查看脱敏效果：**

```sql
SELECT id, name, phone_masked, id_card_masked, salary_level 
FROM v_employees_masked;
```

输出类似：

```
+----+------+---------------+-------------------+-------------+
| id | name | phone_masked  | id_card_masked    | salary_level |
+----+------+---------------+-------------------+-------------+
|  1 | 张三 | 138****8001   | 110101****1234    | 中          |
|  2 | 李四 | 138****8002   | 110101****2345    | 中          |
|  5 | 钱七 | 138****8005   | 110101****5678    | 高          |
+----+------+---------------+-------------------+-------------+
```

手机号、身份证号变成了掩码，薪资只显示高中低——敏感信息被保护了。

**给 HR 分配脱敏视图权限：**

```sql
-- HR 只能查脱敏视图，不能查原表
GRANT SELECT ON salary_db.v_employees_masked TO 'hr_user'@'192.168.100.%';
```

这样 HR 查的是脱敏后的数据，敏感字段不会暴露。

---

### 本周总结（33-40 分钟）

好，这四节课我们学了很多内容，来做一个完整回顾：

**第 1 课时：权限管理**
- GRANT / REVOKE 语法
- 按岗位分配权限（ops 只读、dev 增删改查、DBA 全权限）
- 最小权限原则：能少给就少给
- SHOW GRANTS 验证，FLUSH PRIVILEGES 使用时机

**第 2 课时：日志管理**
- 四种日志：错误日志、通用查询日志、慢查询日志、binlog
- binlog 是重点：开启、查看、PITR 恢复思路
- 项目五完整闭环：装起来→配安全→管住人→出事能查

**第 3 课时：认证安全**
- 密码策略：STRONG + 12 位，弱密码被拒绝
- 认证插件：caching_sha2_password 比 mysql_native_password 更安全
- SSL/TLS：加密网络传输，防止抓包

**第 4 课时：细粒度控制**
- 列级权限：控制到字段级别
- RBAC：角色管理，批量授权
- 数据脱敏：视图 + 掩码，保护敏感信息

把四节课串起来，我们完成了从项目五收尾到项目六前半部分的学习：

```
项目五收尾：权限管理 → 日志管理
项目六切入：认证安全 → 细粒度控制
```

下个周我们会继续项目六的后半部分：审计插件（留痕迹）、数据加密（拿走读不了）、备份容灾（出事能恢复）。到时候我们需要两台虚拟机做主从复制，所以大家可以提前把第二台虚拟机准备好。

好，下课。
