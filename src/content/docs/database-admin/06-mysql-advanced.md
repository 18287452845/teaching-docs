---
title: "06.项目六 MySQL数据库高级安全维护"
---

# 06 项目六 MySQL 数据库高级安全维护

🎯 **本项目学习目标**

- 能结合命令行和 Navicat 完成权限精细化管理和资源限制配置
- 能理解 MySQL 账号生命周期管理（创建、授权、锁定、过期、删除）
- 能识别常见攻击面，并给出对应的安全加固措施
- 能理解 MySQL 高可用方案的基本原理

<aside>
🧭

**主线地图**：权限精细化 → 密码策略与账号生命周期 → 安全加固 → 高可用方案。

</aside>

<aside>
🖥️

**前置条件**

- 已完成项目五：MySQL 已安装，Navicat 能远程连接，binlog 已开启
- 已有数据库 `stusta` 和 `employees`，账号 `app@192.168.100.%`

**课堂产出**

- 能创建多角色账号并验证权限边界
- 能管理账号的锁定、过期、资源限制
- 能列出常见攻击与对应防御措施
- 能理解高可用方案与主从复制的关系

</aside>

---

## 第 1 课 权限精细化管理：管得住人

### 1.1 本课要解决的问题

> 项目五中，我们用 `app` 账号做了所有操作——建库建表、读写数据、导入导出。但在真实场景中，一个账号干所有事，安全吗？

- 能在 Navicat 中管理用户权限
- 能用命令行完成完整的权限管理流程
- 能理解权限排查的基本思路

### 1.2 为什么需要多角色账号？

#### 场景分析

假设你是一家互联网公司的 DBA，公司有一套 `employees` 员工管理系统数据库。现在有四类人需要访问这个数据库：

| 角色 | 他是谁 | 他要做什么 | 他不应该做什么 |
| --- | --- | --- | --- |
| **数据分析师** | 运营/财务人员，用 BI 工具出报表 | 查询员工数据 | 修改、删除数据 |
| **应用系统** | 后端程序，通过代码读写数据库 | 增删改查员工数据 | 建表、删表、改结构 |
| **开发者** | 开发人员，需要调试和建新功能 | 读写数据 + 修改表结构 | 删库、管理其他账号 |
| **DBA（你）** | 数据库管理员 | 所有操作 | — |

> **核心问题**：如果给所有人都是 `app` 账号（全权限），会出现什么问题？
>
> 1. 数据分析师误操作 `DELETE`，数据没了
> 2. 开发者不小心 `DROP TABLE`，业务中断
> 3. 应用系统被黑客注入后，可以 `DROP DATABASE`
>
> **结论**：每个角色必须只能做他该做的事——**最小权限原则**。

### 1.3 权限验证流程

客户端发起连接后，MySQL 先做身份验证，再做权限验证：

```text
连接请求
  ↓
认证：用户名 + 主机 + 密码
  ↓
授权：全局 → 数据库 → 表 → 列
  ↓
允许或拒绝操作
```

<aside>
💬

**排查权限问题的顺序**

1. 看当前连接身份：`SELECT USER(), CURRENT_USER();`
2. 看账号拥有哪些权限：`SHOW GRANTS;`
3. 看账号是否被锁定：`SELECT user, host, account_locked FROM mysql.user;`
4. 看密码是否过期：`SELECT user, host, password_expired FROM mysql.user;`

</aside>

### 1.4 权限存储表

| 表名 | 存储内容 | 查看方式 |
| --- | --- | --- |
| `mysql.user` | 全局权限 + 账号信息 | `SELECT * FROM mysql.user WHERE user='app'\G` |
| `mysql.db` | 数据库级权限 | `SELECT * FROM mysql.db WHERE user='app'\G` |
| `mysql.tables_priv` | 表级权限 | `SELECT * FROM mysql.tables_priv WHERE user='app'\G` |
| `mysql.columns_priv` | 列级权限 | `SELECT * FROM mysql.columns_priv WHERE user='app'\G` |

### 1.5 权限速查表

| 分类 | 权限 | 说明 | 常见场景 |
| --- | --- | --- | --- |
| **数据操作** | `SELECT` | 读取数据 | 只读报表账号 |
| | `INSERT` | 插入数据 | 应用写入 |
| | `UPDATE` | 修改数据 | 应用更新 |
| | `DELETE` | 删除数据 | 应用删除 |
| **结构管理** | `CREATE` | 创建数据库/表 | 开发者 |
| | `ALTER` | 修改表结构 | 开发者 |
| | `DROP` | 删除数据库/表 | **生产环境慎给** |
| | `INDEX` | 创建/删除索引 | 性能优化 |
| **管理权限** | `GRANT OPTION` | 允许该用户授权给别人 | 仅限管理员 |
| | `SUPER` | 管理服务器级操作 | 仅限 DBA |
| | `PROCESS` | 查看所有连接 | 排查问题 |
| | `FILE` | 读写服务器文件 | **高危，不建议给** |

<aside>
⚠️

**高危权限黑名单**：以下权限在教学环境可以了解，但**生产环境绝不应该授予业务账号**：

- `SUPER`：可以修改全局变量、杀死任何连接
- `FILE`：可以读写服务器文件系统
- `GRANT OPTION`：可以把权限再授予别人，导致权限失控
- `ALL PRIVILEGES`：包含以上所有危险权限

</aside>

### 1.6 权限变更何时生效：FLUSH PRIVILEGES 要不要执行？

<aside>
💬

**记忆口诀**：用标准语句，不用 flush；直接改表，必须 flush。

</aside>

| 操作方式 | 是否需要 `FLUSH PRIVILEGES` | 原因 |
| --- | --- | --- |
| `CREATE USER` / `ALTER USER` / `DROP USER` | 不需要 | MySQL 自动刷新权限缓存 |
| `GRANT` / `REVOKE` | 不需要 | MySQL 自动刷新权限缓存 |
| `UPDATE mysql.user` / `DELETE FROM mysql.user` | 需要 | 直接改系统表，需手动让 MySQL 重新加载 |

<aside>
⚠️

**课堂建议**：不要直接 `UPDATE mysql.user`。账号和权限管理优先使用 `CREATE USER`、`ALTER USER`、`GRANT`、`REVOKE`、`DROP USER`。这样语义清晰、风险更低，也通常不需要手动 `FLUSH PRIVILEGES`。

</aside>

### 1.7 动手：创建四个角色账号

回到 1.2 的场景分析，我们现在把四类角色变成四个 MySQL 账号。

#### 第一步：分析每个账号的设计

在写任何 SQL 之前，先想清楚三个问题：

| 账号 | 来源 IP | 密码 | 需要什么权限 | 为什么 |
| --- | --- | --- | --- | --- |
| `reader` | `192.168.100.%` | `123456` | `SELECT` | 只需要查数据出报表，不能改 |
| `writer` | `192.168.100.%` | `123456` | `SELECT, INSERT, UPDATE, DELETE` | 应用需要增删改查，但不能改表结构 |
| `developer` | `192.168.100.%` | `123456` | `SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX` | 开发需要建表改结构，但不能删库或授权 |
| `app` | `192.168.100.%` | `123456` | 已有 | 项目五创建的全权限账号，本课不再使用 |

> **为什么 `writer` 也要有 `SELECT`？** 因为大多数应用在更新/删除前都需要先查询。比如"修改工号 1001 的薪资"，要先 `SELECT` 找到这条记录，再 `UPDATE`。
>
> **为什么 `developer` 不给 `DROP`？** `DROP TABLE` 是不可逆操作。开发者如果需要重建表，可以 `ALTER` 或者找 DBA 处理。

#### 第二步：先降低密码策略

> 项目五中已安装 `validate_password` 组件，MEDIUM 策略会拒绝 `123456`。创建账号前先降低策略（生产环境恢复为 MEDIUM）：

```sql
-- 检查密码策略组件是否已安装
SELECT COMPONENT_ID, COMPONENT_URN FROM mysql.component
  WHERE COMPONENT_URN LIKE '%validate_password%';

-- 如果已安装，降低策略
SET GLOBAL validate_password.policy = LOW;
SET GLOBAL validate_password.length = 6;
```

#### 第三步：创建账号并授权

```sql
-- 只读账号（数据分析师用）
CREATE USER 'reader'@'192.168.100.%' IDENTIFIED WITH mysql_native_password BY '123456';
GRANT SELECT ON employees.* TO 'reader'@'192.168.100.%';

-- 读写账号（应用系统用）
CREATE USER 'writer'@'192.168.100.%' IDENTIFIED WITH mysql_native_password BY '123456';
GRANT SELECT, INSERT, UPDATE, DELETE ON employees.* TO 'writer'@'192.168.100.%';

-- 开发者账号（开发人员用）
CREATE USER 'developer'@'192.168.100.%' IDENTIFIED WITH mysql_native_password BY '123456';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX, CREATE TEMPORARY TABLES
  ON employees.*
  TO 'developer'@'192.168.100.%';
```

#### 第四步：验证权限边界

> 创建完不是终点，**验证才是**。用每个账号登录后，测试他能做什么、不能做什么。

```sql
-- 在 root 账号下查看各账号的权限
SHOW GRANTS FOR 'reader'@'192.168.100.%';
SHOW GRANTS FOR 'writer'@'192.168.100.%';
SHOW GRANTS FOR 'developer'@'192.168.100.%';
```

验证测试表：

| 测试操作 | reader 应该 | writer 应该 | developer 应该 |
| --- | --- | --- | --- |
| `SELECT * FROM employees.employees LIMIT 1;` | ✅ 成功 | ✅ 成功 | ✅ 成功 |
| `INSERT INTO employees.dept_emp VALUES (1, 'd001', '2024-01-01', '9999-01-01');` | ❌ 拒绝 | ✅ 成功 | ✅ 成功 |
| `CREATE TABLE test_tbl (id INT);` | ❌ 拒绝 | ❌ 拒绝 | ✅ 成功 |
| `DROP TABLE test_tbl;` | ❌ 拒绝 | ❌ 拒绝 | ❌ 拒绝 |

> **小技巧**：在 Navicat 中也可以验证——用不同账号建连接，尝试执行上述操作，观察哪些成功、哪些报 `ACCESS DENIED`。

### 1.8 权限修改：授权 + 撤权

> **场景**：项目需求变了。writer 账号需要临时建一个测试表；developer 不应该再改表结构了（有专门的 DBA 了）。怎么办？

```sql
-- 给 writer 添加 CREATE 权限（临时需要建表）
GRANT CREATE ON employees.* TO 'writer'@'192.168.100.%';

-- 撤销 developer 的 ALTER 权限（不再允许改结构）
REVOKE ALTER ON employees.* FROM 'developer'@'192.168.100.%';

-- 需求结束，撤销 writer 的 CREATE（收回临时权限）
REVOKE CREATE ON employees.* FROM 'writer'@'192.168.100.%';

-- 撤销所有权限但不删除账号（账号还在，但什么也做不了）
REVOKE ALL PRIVILEGES, GRANT OPTION FROM 'reader'@'192.168.100.%';
```

<aside>
⚠️

**注意：MySQL 权限没有"显式 DENY"语法。** 如果数据库级授予了某表的 `SELECT`，不能再通过表级权限"拒绝"同一张表。要实现更细粒度控制，应从一开始就只授予需要的表级或列级权限。

</aside>

<aside>
✅

**第 1 课小结**

- 权限管理主线是查、改、锁、删
- 创建账号前先想清楚：谁用、从哪连、要做什么、不能做什么
- 多角色账号应遵循最小权限原则
- 标准权限语句会自动生效；直接改 `mysql.user` 等系统表后才需要 `FLUSH PRIVILEGES`

</aside>

---

## 第 2 课 账号生命周期与密码策略

### 2.1 与上一课的衔接

> 上一课创建了多角色账号。但账号不是创建完就不管了——**员工入职要开通账号，离职要关闭账号，密码泄露要强制改密码**。这就是账号生命周期管理。

### 2.2 本课要解决的问题

- 掌握账号的锁定、过期、删除等生命周期操作
- 理解密码策略参数，能区分课堂和生产环境配置
- 能配置资源限制，防止账号滥用

### 2.3 账号生命周期全景

> 一个账号从"出生"到"死亡"，经历哪些阶段？每个阶段对应什么操作？什么场景触发？

```text
创建账号（入职 / 新项目）
  ↓
授权（分配权限）
  ↓
日常使用
  ↓  ┌──────────────────────────────┐
  ├──│ 员工离职 → 锁定或删除账号    │
  ├──│ 密码泄露 → 强制改密码        │
  ├──│ 试用期转正 → 解锁账号        │
  ├──│ 定期安全审计 → 密码过期      │
  └──│ 业务下线 → 删除账号          │
     └──────────────────────────────┘
```

### 2.4 查看现有账号

> 操作之前先看清现状：系统里有哪些账号？用什么认证方式？有没有被锁定的？

```sql
-- 查看所有账号
SELECT user, host, plugin, account_locked FROM mysql.user;

-- 只看有密码的账号（排除 auth_socket）
SELECT user, host, plugin FROM mysql.user WHERE plugin != 'auth_socket';
```

### 2.5 修改密码

> **场景一**：员工忘记密码了，需要重置。
> **场景二**：定期安全巡检，需要批量修改密码。

```sql
-- 修改其他用户的密码（管理员操作，MySQL 8.0 推荐）
ALTER USER 'app'@'192.168.100.%' IDENTIFIED BY '123456';

-- 修改自己的密码（用户自行操作）
ALTER USER USER() IDENTIFIED BY '123456';
```

### 2.6 撤销权限

> **场景**：writer 账号之前有 DELETE 权限，但业务调整后不再需要删除数据了。

```sql
-- 撤销 DELETE 权限（只保留 SELECT, INSERT, UPDATE）
REVOKE DELETE ON stusta.* FROM 'app'@'192.168.100.%';

-- 验证
SHOW GRANTS FOR 'app'@'192.168.100.%';
```

### 2.7 锁定与解锁账号

> **场景**：员工离职了，但不确定他的账号是否还被其他系统引用。直接删怕出问题，先锁住。

```sql
-- 临时锁定账号（禁止登录，但不删除，数据权限都还在）
ALTER USER 'app'@'192.168.100.%' ACCOUNT LOCK;

-- 验证：用 app 账号登录会报 "Access denied for user ... ACCOUNT IS LOCKED"

-- 员工回来了或者确认要恢复
ALTER USER 'app'@'192.168.100.%' ACCOUNT UNLOCK;
```

> **锁定 vs 删除的区别**：
>
> | 操作 | 账号还在吗 | 权限还在吗 | 能恢复吗 | 适用场景 |
> | --- | --- | --- | --- | --- |
> | 锁定 | ✅ | ✅ | ✅ 解锁即可 | 员工离职，暂时禁用 |
> | 删除 | ❌ | ❌ | ❌ 不可逆 | 确认不再需要 |

### 2.8 设置密码过期

> **场景一**：发现某个账号的密码可能泄露了，强制下次登录必须改密码。
> **场景二**：公司安全策略要求每 90 天必须改密码。

```sql
-- 让账号密码立即过期（下次登录必须改密码）
ALTER USER 'writer'@'192.168.100.%' PASSWORD EXPIRE;

-- 设置密码 90 天后过期（生产环境推荐）
ALTER USER 'writer'@'192.168.100.%' PASSWORD EXPIRE INTERVAL 90 DAY;

-- 密码永不过期（课堂环境使用，避免学生被强制改密码卡住）
ALTER USER 'writer'@'192.168.100.%' PASSWORD EXPIRE NEVER;
```

> **课堂注意**：本课所有账号密码设为永不过期，避免操作中途被强制改密码。

### 2.9 删除账号

> **场景**：确认某个账号已经没有任何业务在使用了，可以彻底删除。

```sql
-- 删除前先查：有没有视图、存储过程依赖这个账号
SELECT * FROM information_schema.VIEWS WHERE DEFINER LIKE '%app%';

-- 确认安全后删除（不可逆）
DROP USER 'app'@'192.168.100.%';
```

<aside>
⚠️

**删除前先查依赖**：在删除账号前，检查是否有视图、存储过程或定时任务引用了该账号，避免删除后导致业务报错。

</aside>

### 2.10 一张表记住生命周期

| 场景 | 操作 | 命令 |
| --- | --- | --- |
| 员工入职 | 创建账号 | `CREATE USER ...` |
| 分配权限 | 授权 | `GRANT ... ON ... TO ...` |
| 权限调整 | 撤权 | `REVOKE ... ON ... FROM ...` |
| 员工离职 | 锁定账号 | `ALTER USER ... ACCOUNT LOCK;` |
| 员工回来 | 解锁账号 | `ALTER USER ... ACCOUNT UNLOCK;` |
| 密码泄露 | 强制改密码 | `ALTER USER ... PASSWORD EXPIRE;` |
| 定期安全 | 90 天过期 | `ALTER USER ... PASSWORD EXPIRE INTERVAL 90 DAY;` |
| 业务下线 | 删除账号 | `DROP USER ...;` |

### 2.11 密码策略详解

> **问题**：前面我们一直用 `123456` 作为密码，这在课堂没问题，但在生产环境呢？
>
> - 2019 年，某公司数据库被拖库，原因就是 admin 账号密码是 `123456`
> - 2021 年，勒索软件攻击 MySQL 服务器，专门扫描弱密码账号
>
> MySQL 8.0 提供了 `validate_password` 组件来强制密码复杂度。

#### 密码策略参数说明

```sql
-- 查看当前策略
SHOW VARIABLES LIKE 'validate_password%';
```

| 参数 | 含义 | 默认值 | 课堂值 | 生产建议值 |
| --- | --- | --- | --- | --- |
| `validate_password.policy` | 策略等级 | MEDIUM | LOW | MEDIUM |
| `validate_password.length` | 密码最短长度 | 8 | 6 | 8+ |
| `validate_password.mixed_case_count` | 大小写字母最少各几个 | 1 | 0（LOW 模式不检查） | 1 |
| `validate_password.number_count` | 数字最少几个 | 1 | 0（LOW 模式不检查） | 1 |
| `validate_password.special_char_count` | 特殊字符最少几个 | 1 | 0（LOW 模式不检查） | 1 |

策略等级说明：
- `LOW`：只检查长度（课堂环境使用）
- `MEDIUM`：长度 + 大小写 + 数字 + 特殊字符（生产环境推荐）
- `STRONG`：MEDIUM + 字典检查（高安全要求场景）

<aside>
💡

**课堂 vs 生产**

- **课堂**：`policy = LOW`，`length = 6`，密码统一 `123456`，专注学习操作流程
- **生产**：`policy = MEDIUM` 或 `STRONG`，`length ≥ 8`，必须使用强密码

策略的修改是临时生效的（`SET GLOBAL`），重启后恢复默认。如果需要永久生效，在配置文件中添加：

```ini
[mysqld]
validate_password.policy = LOW
validate_password.length = 6
```

</aside>

### 2.12 资源限制

> **场景**：你发现某个 API 账号每小时执行了 10 万次查询，把数据库拖慢了。或者某个开发者同时开了 50 个连接做测试。
>
> **问题**：能不能限制一个账号的使用量？

```sql
CREATE USER 'limited_app'@'192.168.100.%' IDENTIFIED WITH mysql_native_password BY '123456';
GRANT SELECT, INSERT, UPDATE, DELETE ON employees.* TO 'limited_app'@'192.168.100.%'
WITH MAX_QUERIES_PER_HOUR 1000
     MAX_UPDATES_PER_HOUR 100
     MAX_CONNECTIONS_PER_HOUR 50
     MAX_USER_CONNECTIONS 5;
```

每个参数的含义和应用场景：

| 参数 | 含义 | 典型场景 |
| --- | --- | --- |
| `MAX_QUERIES_PER_HOUR 1000` | 每小时最多 1000 次查询 | 限制外部 API 调用频率 |
| `MAX_UPDATES_PER_HOUR 100` | 每小时最多 100 次写操作 | 防止批量刷数据 |
| `MAX_CONNECTIONS_PER_HOUR 50` | 每小时最多连接 50 次 | 防止连接风暴 |
| `MAX_USER_CONNECTIONS 5` | 同时最多 5 个连接 | 防止一个账号占满连接池 |

> **什么时候需要资源限制？**
>
> - 面向外部系统的 API 账号 → 限制查询频率，防止被滥用
> - 第三方合作伙伴的只读账号 → 限制连接数，防止占满资源
> - 测试环境中的公共账号 → 限制写操作频率，防止误操作刷数据

<aside>
✅

**第 2 课小结**

- 账号有完整生命周期：创建 → 授权 → 验证 → 修改 → 锁定 → 删除
- 每个生命周期操作都有对应的场景：离职锁定、泄露过期、下线删除
- 课堂密码统一 `123456`，创建账号前需先降低 `validate_password` 策略为 LOW
- 生产环境使用 MEDIUM/STRONG 策略，强制密码复杂度
- 资源限制可用于防止账号滥用

</aside>

---

## 第 3 课 日志与排错：出事能查

### 3.1 与上一课的衔接

> 前两课解决了"管得住人"的问题。但数据库运维中，**出了问题能快速定位**同样重要。
>
> 想象一下：
> - 早上 9 点，用户说"系统好慢" → 你怎么查？
> - 凌晨 3 点，数据库挂了 → 你看什么？
> - 有人怀疑数据被篡改了 → 你怎么追溯？

### 3.2 本课要解决的问题

- 知道四类日志分别在什么场景用
- 能查看错误日志、能开启/查看慢查询日志
- 理解通用查询日志的适用场景

### 3.3 四种主要日志——先知道看什么

> 遇到不同问题，要看不同的日志。先记住这个对应关系：

| 你遇到的问题 | 应该看的日志 | 为什么 |
| --- | --- | --- |
| 数据库启动不了 / 崩溃了 | **错误日志** | 记录了所有启动、运行、关闭时的错误 |
| 系统变慢，不知道哪条 SQL 慢 | **慢查询日志** | 专门记录超过阈值的 SQL |
| 需要追溯"谁在什么时候执行了什么" | **通用查询日志** | 记录每一条 SQL（但代价大） |
| 需要恢复数据或做主从复制 | **二进制日志（binlog）** | 记录所有写操作事件（项目五已学） |

### 3.4 错误日志：数据库挂了先看这里

> **场景**：你到公司发现 MySQL 服务挂了，`systemctl start mysql` 也启动失败。第一件事看什么？错误日志。

```bash
# 查看最近 100 行错误日志
tail -100 /var/log/mysql/error.log

# 实时跟踪（排查启动问题时特别有用）
sudo tail -f /var/log/mysql/error.log
```

```sql
-- 在 MySQL 内查看错误日志路径
SHOW VARIABLES LIKE 'log_error';
```

#### 常见错误日志场景

| 日志关键字 | 含义 | 排查方向 |
| --- | --- | --- |
| `[ERROR] Can't start server` | 服务启动失败 | 检查端口冲突、配置文件语法、磁盘空间 |
| `[ERROR] Access denied` | 认证失败 | 检查用户名/密码/主机权限 |
| `[ERROR] Disk full` | 磁盘满 | 清理日志、扩展磁盘 |
| `[Warning] IP address 'x.x.x.x' could not be resolved` | DNS 反解失败 | 设置 `skip_name_resolve` |

<aside>
🔧

**快速排错步骤**：

1. 先看 `tail -50 /var/log/mysql/error.log`
2. 找到最近的 `[ERROR]` 行
3. 复制错误信息搜索解决方案
4. 如果服务完全启动不了：`sudo systemctl status mysql` 查看 systemd 层面的报错

</aside>

### 3.5 慢查询日志：系统慢了怎么找 SQL

> **场景**：用户反馈"页面加载很慢"，但不知道是哪条 SQL 慢。怎么定位？
>
> **思路**：开启慢查询日志 → 让 MySQL 自动记录超过阈值的 SQL → 用工具分析 → 找到最慢的几条 → 优化它们。

#### 开启与配置

```sql
-- 查看当前状态
SHOW VARIABLES LIKE 'slow_query%';
SHOW VARIABLES LIKE 'long_query_time';

-- 开启慢查询日志（临时生效，重启后失效）
SET GLOBAL slow_query_log = 1;
SET GLOBAL long_query_time = 1;   -- 超过 1 秒的 SQL 记录到慢查询日志
SET GLOBAL log_queries_not_using_indexes = 1;  -- 没用索引的也记录
```

在配置文件中永久生效：

```ini
[mysqld]
slow_query_log = 1
slow_query_log_file = /var/log/mysql/slow.log
long_query_time = 1
log_queries_not_using_indexes = 1
```

#### 查看慢查询日志

```bash
# 查看慢查询日志
sudo tail -50 /var/log/mysql/slow.log
```

```sql
-- 统计慢查询数量
SHOW GLOBAL STATUS LIKE 'Slow_queries';
```

#### 用 mysqldumpslow 分析

> 慢查询日志可能很长，手动看效率低。`mysqldumpslow` 工具可以帮你汇总分析。

```bash
# 按执行次数排序，显示前 10 条
sudo mysqldumpslow -s c -t 10 /var/log/mysql/slow.log

# 按平均执行时间排序
sudo mysqldumpslow -s at -t 10 /var/log/mysql/slow.log

# 按锁定时间排序
sudo mysqldumpslow -s t -t 10 /var/log/mysql/slow.log
```

| 参数 | 含义 |
| --- | --- |
| `-s c` | 按查询次数（count）排序 |
| `-s at` | 按平均查询时间（avg time）排序 |
| `-s t` | 按总锁定时间排序 |
| `-t N` | 只显示前 N 条 |

### 3.6 通用查询日志：临时排错利器

> **场景**：某条数据被莫名修改了，你需要追溯"到底是谁、在什么时候执行了什么 SQL"。错误日志和慢查询日志都看不到。
>
> **问题**：通用查询日志能记录每一条 SQL，但为什么不能一直开着？

通用查询日志记录**每一条**到达 MySQL 的 SQL，包括连接、断开、查询。由于日志量巨大，**只在排错时临时开启**。

```sql
-- 查看当前状态
SHOW VARIABLES LIKE 'general_log%';

-- 临时开启（排错时使用）
SET GLOBAL general_log = 1;
SET GLOBAL general_log_file = '/var/log/mysql/general.log';

-- ... 执行需要排查的操作 ...

-- 排查完毕，立即关闭
SET GLOBAL general_log = 0;
```

> **算一笔账**：假设系统每秒执行 1000 条 SQL，通用查询日志每条 SQL 约 200 字节，那么每秒产生 200KB，每天约 17GB。这就是为什么不能长期开启。

<aside>
⚠️

**通用查询日志是性能杀手**

在生产环境长期开启通用查询日志，每秒可能产生数 MB 日志，迅速填满磁盘。只用于临时排错，用完即关。

</aside>

<aside>
✅

**第 3 课小结**

- **错误日志**：服务异常第一入口，`tail -f /var/log/mysql/error.log`
- **慢查询日志**：会开、会看、会用 `mysqldumpslow` 定位慢 SQL
- **通用查询日志**：临时排错利器，用完即关
- **binlog**：项目五已学，用途是复制 + PITR 恢复

</aside>

---

## 第 4 课 安全加固与高可用：防得住攻击

### 4.1 与上一课的衔接

> 前三课解决了权限管理、账号生命周期和日志排错。最后一课从**攻防视角**看 MySQL 安全——如果你是黑客，你会怎么攻击？如果你是 DBA，你怎么防御？

### 4.2 本课要解决的问题

- 能识别 MySQL 常见攻击方式，并给出对应防御措施
- 了解 MySQL 高可用方案的基本原理

### 4.3 攻击场景分析

> 先站在攻击者角度思考：MySQL 数据库暴露在网络上，攻击者有哪些入手点？

```text
攻击者的思路：
  ① 能不能直接连上？ → 弱密码 / 默认账号 / 匿名用户
  ② 连上后能做什么？ → 权限过大 → 读取敏感数据 / 修改数据
  ③ 能不能提权？ → FILE 权限 → UDF 提权 → 控制操作系统
  ④ 应用层面有没有漏洞？ → SQL 注入 → 绕过认证 / 拖库
```

### 4.4 SQL 注入

> **场景**：一个登录页面的后端代码这样写：
>
> ```python
> # 危险写法：直接拼接 SQL
> sql = "SELECT * FROM users WHERE username='" + username + "' AND password='" + password + "'"
> ```
>
> 攻击者在用户名输入 `' OR '1'='1`，SQL 变成了：
>
> ```sql
> SELECT * FROM users WHERE username='' OR '1'='1' AND password='xxx'
> ```
>
> `'1'='1'` 永远为真，攻击者无需密码就登录了。

**防御措施**：

- 使用参数化查询（预编译语句），不要拼接 SQL
- 输入验证和过滤
- 部署 WAF（Web 应用防火墙）
- 数据库账号遵循最小权限原则（即使注入成功，也只能操作授权范围内的数据）

### 4.5 弱密码暴力破解

> **场景**：攻击者用脚本尝试常见密码：root/123456、root/admin、root/password……每秒尝试几百次，24 小时不间断。
>
> **问题**：如果 root 允许远程登录且密码是 `123456`，多快会被破解？答案是几秒。

**防御措施**：

- 启用 `validate_password` 组件，强制密码复杂度
- 限制账号来源 IP（`'user'@'192.168.100.%'` 而非 `'user'@'%'`）
- 禁止 root 远程登录
- 部署防火墙，限制 3306 端口的访问来源

### 4.6 未授权访问

> **场景**：MySQL 的 3306 端口直接暴露在公网上，且存在匿名用户或 test 数据库。攻击者可以直接连上来探索。

**防御措施**：

- 限制 `bind-address`，只开放内网访问
- 配合防火墙或安全组
- 删除匿名用户和 test 数据库
- 使用 SSH 隧道而非直接暴露 3306 端口

### 4.7 UDF 提权

> **场景**：攻击者拿到了一个普通账号的权限，但这个账号有 `FILE` 权限。他上传了一个自定义函数（UDF），通过 UDF 执行操作系统命令——从数据库权限升级到了操作系统权限。

**防御措施**：

- 不授予业务账号 `FILE` 权限
- 限制文件读写路径（`secure_file_priv`）
- 定期审计账号和权限

### 4.8 安全加固清单

> 把以上所有防御措施汇总成一份清单，逐项检查：

| 加固措施 | 命令 / 操作 | 防御什么 |
| --- | --- | --- |
| 禁止 root 远程登录 | `mysql_secure_installation` | 远程暴力破解 |
| 限制账号来源 IP | `'user'@'192.168.100.%'` | 未知网络连接 |
| 启用密码验证组件 | `INSTALL COMPONENT 'file://component_validate_password'` | 弱密码 |
| 定期轮换密码 | `ALTER USER ... IDENTIFIED BY ...` | 密码泄露后的窗口期 |
| 锁定不用的账号 | `ALTER USER ... ACCOUNT LOCK` | 废弃账号被利用 |
| 最小权限原则 | 只授予业务所需权限 | 权限滥用 / 提权 |
| 删除匿名用户 | `DROP USER ''@'localhost'` | 匿名访问 |
| 删除 test 数据库 | `DROP DATABASE test` | 测试库被利用 |
| 限制 FILE 权限 | 不授予业务账号 FILE 权限 | UDF 提权 |
| 开启 binlog | 项目五已配置 | 数据恢复 / 审计追溯 |

### 4.9 MySQL 高可用方案

> **问题**：主从复制（项目五已学）解决了"数据备份"和"读写分离"的问题，但主库挂了怎么办？
>
> **答案**：需要**自动故障转移**——当主库不可用时，自动把一个从库提升为新主库。这就是高可用方案要解决的事。

| 方案 | 原理 | 适用场景 |
| --- | --- | --- |
| InnoDB Cluster | 基于 Group Replication 的自动故障转移 | 官方推荐的高可用方案 |
| PXC | 同步多主复制 | 强一致性要求场景 |
| MHA | 自动主从切换 | 传统主从复制升级 |
| ProxySQL / MySQL Router | 读写分离中间件 | 配合主从复制使用 |

<aside>
💬

**初学者掌握重点**

当前阶段重点是理解主从复制（项目五已学）和基本加固思路即可，高可用方案了解名称和用途就够了。

**从主从复制到高可用的演进路径**：

1. 单机 → 主从复制（读写分离 + 热备）
2. 主从复制 + MHA（自动故障切换）
3. InnoDB Cluster（官方推荐，自动选主 + 数据一致性保证）

</aside>

<aside>
✅

**第 4 课小结**

- 安全加固是持续工作，不是一劳永逸
- 先站在攻击者角度想"能怎么攻"，再想"怎么防"
- 常见攻击：SQL 注入、弱密码、未授权访问、UDF 提权
- 防御核心：最小权限 + 强密码 + 网络隔离 + 审计日志
- 高可用方案建立在主从复制基础上，当前了解即可

</aside>

---

## 📝 项目总结（一张表复盘）

| 课时 | 核心能力 | 验收点（可检查） |
| --- | --- | --- |
| 第 1 课：权限管理 | 管得住人 | 能创建多角色账号并验证权限边界 |
| 第 2 课：账号生命周期 | 全流程管理 | 能完成锁定/过期/资源限制/删除操作 |
| 第 3 课：日志排错 | 出事能查 | 能查看错误/慢查询日志，能用 mysqldumpslow 分析 |
| 第 4 课：安全加固 | 防得住攻击 | 能列出常见攻击与对应防御措施 |

---

## 附录

### 附录 A：密码管理多方式（旧系统兼容，课堂不作为主线）

- MySQL 8.0 推荐：`ALTER USER ... IDENTIFIED BY ...;`
- `SET PASSWORD ... = PASSWORD()` 为旧语法（8.0 已弃用 PASSWORD()）
- `mysqladmin` 适用于脚本化，但注意密码泄露风险（命令历史/进程列表）

### 附录 B：InnoDB 与 MyISAM 的差异

| 维度 | InnoDB | MyISAM |
| --- | --- | --- |
| 事务支持 | 支持（ACID） | 不支持 |
| 崩溃恢复 | 自动恢复 | 需手动 REPAIR |
| 锁粒度 | 行级锁 | 表级锁 |
| 外键 | 支持 | 不支持 |
| 全文索引 | 支持（5.6+） | 支持 |
| MySQL 8.0 默认 | 是 | 否 |

MySQL 8.0 默认使用 InnoDB，支持事务和崩溃恢复，一般不需要手工修复；MyISAM 是旧引擎，已不适合作为新项目默认选择。
