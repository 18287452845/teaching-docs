---
title: "06.项目六 MySQL数据库高级安全维护"
---

# 06.项目六 MySQL数据库高级安全维护

🎯**本项目学习目标**

- 掌握 Navicat for MySQL 的核心操作：连接管理、数据导入导出、备份还原、权限管理
- 理解 MySQL 权限系统的完整运作机制，能在 Navicat 和命令行两种方式下完成权限管理
- 掌握 mysqldump 命令行备份与还原，理解逻辑备份的适用场景与局限
- 了解 MySQL 主从复制的原理与基本配置流程
- 能针对常见 MySQL 攻击方式提出加固措施

<aside>
🧭

**主线地图**：用得顺手（Navicat 图形化）→ 管得住人（权限精细化）→ 丢不了数据（备份还原）→ 扩得了容（主从复制）→ 防得住攻击（攻防加固）。

</aside>

<aside>
🖥️

**前置条件**

- VM-A 已安装 MySQL 8.0（上一章已完成）
- VM-A 已安装 Navicat for MySQL（或 Navicat Premium）
- 上一章已创建数据库 `stusta`、账号 `app@192.168.100.%`

</aside>

---

# 第 1 课 Navicat 图形化管理：用得顺手

## 1.1 与上一章的衔接

上一章我们全程用命令行操作 MySQL——创建账号、授予权限、查看日志。命令行的优势是精确可控，但日常维护中频繁敲 SQL 效率不高。Navicat 把常见的管理操作封装成了图形界面，让我们把精力集中在"要做什么"而不是"怎么敲命令"。

<aside>
💬

**为什么学了命令行还要学 Navicat？**

- 命令行适合精确操作和脚本自动化
- Navicat 适合日常浏览、批量操作、快速备份
- 两者互补，不是替代关系
- 面试/工作中，DBA 通常两者都用

</aside>

## 1.2 本课要解决的问题

- 能通过 Navicat 连接 MySQL 服务器
- 能用 Navicat 完成数据导入导出
- 能用 Navicat 完成备份还原
- 能用 Navicat 管理用户权限

## 1.3 Navicat for MySQL 功能全景

Navicat for MySQL 是广泛使用的 MySQL 图形化管理工具，主要功能模块：

| 功能模块 | 说明 | 使用频率 |
| --- | --- | --- |
| **连接管理** | 同时管理多个 MySQL 服务器，支持 SSH 隧道加密连接 | 每次使用 |
| **数据库/表管理** | 图形化创建、修改、删除数据库对象 | 高 |
| **数据编辑** | 表格形式查看和编辑数据，类似 Excel 操作 | 高 |
| **查询编辑器** | SQL 编写和执行，代码高亮和自动补全 | 高 |
| **导入/导出** | 支持 Excel、CSV、SQL、XML、JSON 等多种格式 | 中 |
| **数据传输** | 在不同服务器/数据库间迁移数据 | 中 |
| **数据同步** | 比较并同步两个数据库的结构和数据差异 | 低 |
| **备份/还原** | 数据库备份和还原，支持计划任务 | 高 |
| **用户权限管理** | 图形化管理账户和权限 | 中 |
| **ER 图** | 可视化显示表结构和关系 | 低 |

## 1.4 建立连接

### 连接 MySQL 服务器

1. 打开 Navicat → 点击左上角 **连接** → 选择 **MySQL**
2. 填写连接信息：

| 字段 | 值（示例） | 说明 |
| --- | --- | --- |
| 连接名 | VM-A-MySQL | 自定义，方便识别 |
| 主机 | 192.168.100.20 | MySQL 服务器 IP |
| 端口 | 3306 | 默认端口 |
| 用户名 | app | 上一章创建的账号 |
| 密码 | App@Pass123! | 对应密码 |

3. 点击 **测试连接** → 显示"连接成功" → 点击 **确定**

<aside>
🔧

**连接失败排查清单**

| 现象 | 可能原因 | 解决方法 |
| --- | --- | --- |
| Can't connect to MySQL server | MySQL 未启动或 bind-address 未开放 | `sudo systemctl status mysql` 检查 |
| Access denied for user | 用户名/密码/主机不匹配 | 在 MySQL 中 `SELECT user, host FROM mysql.user;` |
| Authentication plugin error | Navicat 版本不支持 `caching_sha2_password` | 升级 Navicat 或降级认证插件 |
| Host is not allowed | 账号的 host 限制不允许该 IP | 修改账号 host 或创建新账号 |

</aside>

### 使用 SSH 隧道连接（安全方式）

在生产环境中，不建议直接暴露 MySQL 端口。Navicat 支持通过 SSH 隧道连接：

1. 新建连接 → 切换到 **SSH** 选项卡
2. 勾选 **使用 SSH 通道**
3. 填写 SSH 信息：

| 字段 | 值（示例） |
| --- | --- |
| 主机 | 192.168.100.20 |
| 端口 | 22 |
| 用户名 | ubuntu |
| 认证方式 | 密码 / 密钥文件 |

4. 返回 **常规** 选项卡，主机改为 `127.0.0.1`（因为 SSH 隧道后是本地连接）

<aside>
💬

**SSH 隧道的优势**：MySQL 端口不需要对外开放，所有流量通过 SSH 加密传输。即使在公网环境下也是安全的。

</aside>

## 1.5 导入测试数据

在实际操作前，先导入一个真实的测试数据库。MySQL 官方提供了 `employees` 示例数据库（约 300 万条员工记录）：

```bash
# 在 VM-A 上下载并导入
git clone https://github.com/datacharmer/test_db.git
cd test_db

# 导入（大约需要几分钟）
mysql -u root -p < employees.sql

# 验证导入
mysql -u root -p -e "USE employees; SELECT COUNT(*) AS '员工总数' FROM employees;"
```

导入完成后，在 Navicat 中右键连接名 → **刷新**，即可看到 `employees` 数据库及其表结构。

### 数据导入（CSV / Excel → MySQL）

假设有一个 `students.csv` 文件需要导入 `stusta` 数据库：

1. 在 Navicat 中展开 `stusta` 数据库
2. 右键 `students` 表 → **导入向导**
3. 选择文件格式（CSV / Excel / JSON 等）
4. 选择源文件 → 预览数据
5. 字段映射：确认 CSV 列与表字段的对应关系
6. 选择导入模式：
   - **添加**：追加新记录
   - **更新**：根据主键更新已有记录
   - **添加或更新**：不存在则插入，存在则更新
7. 点击 **开始** → 查看导入结果

### 数据导出（MySQL → CSV / Excel / SQL）

1. 在 Navicat 中右键表名或数据库名
2. 选择 **导出向导**
3. 选择导出格式：
   - **SQL 文件**：生成可直接在 MySQL 中执行的 `.sql` 脚本
   - **CSV / Excel**：方便在电子表格中查看和分析
   - **JSON / XML**：方便应用程序读取
4. 配置选项（字段分隔符、是否含表头等）
5. 选择保存路径 → **开始**

<aside>
💬

**导出 SQL vs 导出 CSV 的选择**

- **导出 SQL**：适合数据迁移、备份、在其他 MySQL 实例恢复。保留了完整的表结构和数据类型。
- **导出 CSV**：适合数据分析、报表制作、与其他系统交换数据。但丢失了表结构和类型信息。

</aside>

## 1.6 备份与还原

### 方式一：数据库转储（生成 SQL 文件）

这是最通用的备份方式，生成的 `.sql` 文件可以在任何 MySQL 实例上恢复：

**备份**：

1. 右键数据库名 → **转储 SQL 文件** → **结构和数据**
2. 选择保存路径，生成 `.sql` 文件

**还原**：

1. 右键连接名 → **运行 SQL 文件**
2. 选择之前导出的 `.sql` 文件
3. 等待执行完成

### 方式二：Navicat 备份模块（推荐用于日常备份）

Navicat 内置的备份模块支持增量备份和计划任务，更适合日常运维：

**创建备份**：

1. 点击顶部 **备份** 图标
2. 点击 **新建备份** → 选择要备份的数据库
3. 点击 **开始** → 生成 `.nb3` 格式备份文件（Navicat 专有格式）

**还原备份**：

1. 点击 **备份** 图标 → 选择备份文件
2. 右键 → **还原备份**
3. 确认目标数据库 → **开始**

### 设置自动计划任务

手动备份容易遗忘，Navicat 支持设置定时自动备份：

1. Navicat 顶部工具栏 → **自动运行**
2. 点击 **新建批处理作业** → 添加备份任务
3. 点击 **设置任务计划** → 配置执行频率：
   - 每天凌晨 2:00（推荐，业务低峰期）
   - 每周日凌晨 3:00（全量备份）
4. 保存并启用

<aside>
⚠️

**备份文件的安全**

- 备份文件包含数据库中的所有数据，本身也是敏感资产
- 不要把备份文件放在数据库同一台服务器上（服务器故障时备份也没了）
- 定期验证备份是否能成功还原（没验证过的备份等于没有备份）

</aside>

## 1.7 数据库维护工具

Navicat 内置维护功能（右键表名 → **维护**）：

| 操作 | 等价 SQL 命令 | 作用 | 何时使用 |
| --- | --- | --- | --- |
| **分析表** | `ANALYZE TABLE` | 更新表的索引统计信息 | 查询突然变慢时 |
| **检查表** | `CHECK TABLE` | 检查表是否有损坏 | 异常断电/崩溃后 |
| **优化表** | `OPTIMIZE TABLE` | 整理碎片，回收空间 | 大量 DELETE 后 |
| **修复表** | `REPAIR TABLE` | 修复损坏的 MyISAM 表 | CHECK TABLE 报错时 |

<aside>
💬

**InnoDB vs MyISAM 的维护差异**

- InnoDB（MySQL 8.0 默认引擎）：支持事务，崩溃后可自动恢复，一般不需要 REPAIR
- MyISAM（旧引擎）：不支持事务，容易在异常断电后损坏，需要定期 CHECK + REPAIR

**建议**：新项目统一使用 InnoDB，不要选 MyISAM。

</aside>

<aside>
✅

**第 1 课小结**

- Navicat 连接：常规连接 + SSH 隧道连接（生产推荐）
- 数据导入导出：CSV/Excel/SQL 多格式互转
- 备份还原：SQL 转储（通用）vs Navicat 备份模块（支持计划任务）
- 维护工具：ANALYZE / CHECK / OPTIMIZE / REPAIR 的使用时机
</aside>

---

# 第 2 课 权限精细化管理：管得住人

## 2.1 与上一课的衔接

上一章我们在命令行中创建了 `app` 账号并授予了 CRUD 权限。这一课要做两件事：

1. 在 Navicat 中用图形界面完成相同操作（对比理解）
2. 深入学习权限系统的细节：多账号管理、权限排查、安全加固

## 2.2 本课要解决的问题

- 能在 Navicat 中管理用户权限
- 能用命令行完成完整的权限管理流程
- 理解权限排查的思路：查、改、收、锁、删
- 能说出至少 3 种 MySQL 常见攻击方式及对应防御措施

## 2.3 权限验证流程（深入理解）

上一章讲了权限的四层结构，这一课补充完整的验证流程：

```
客户端发起连接
    │
    ▼
第一步：连接验证（authentication）
    → mysql.user 表中查找匹配的 user + host 记录
    → 验证密码是否正确（检查认证插件）
    → 失败 → Access denied
    → 成功 → 进入第二步
    │
    ▼
第二步：权限验证（authorization）
    → 检查 mysql.user 全局权限（有 ALL PRIVILEGES 直接放行）
    → 检查 mysql.db 数据库级权限
    → 检查 mysql.tables_priv 表级权限
    → 检查 mysql.columns_priv 列级权限
    → 任意一层有匹配权限 → 放行
    → 所有层都没有 → Command denied
```

<aside>
💬

**实战中怎么排查"权限不足"报错？**

```sql
-- 1) 确认当前连接的身份
SELECT USER(), CURRENT_USER();

-- 2) 查看该账号的所有权限
SHOW GRANTS;

-- 3) 检查是否被锁定了
SELECT user, host, account_locked FROM mysql.user WHERE user = 'app';

-- 4) 检查密码是否过期
SELECT user, host, password_expired FROM mysql.user WHERE user = 'app';
```

</aside>

### 权限存储表详解

| 表名 | 存储内容 | 查看方式 |
| --- | --- | --- |
| `mysql.user` | 全局权限 + 账号信息 | `SELECT * FROM mysql.user WHERE user='app'\G` |
| `mysql.db` | 数据库级权限 | `SELECT * FROM mysql.db WHERE user='app'\G` |
| `mysql.tables_priv` | 表级权限 | `SELECT * FROM mysql.tables_priv WHERE user='app'\G` |
| `mysql.columns_priv` | 列级权限 | `SELECT * FROM mysql.columns_priv WHERE user='app'\G` |

## 2.4 在 Navicat 中管理用户权限

### 创建新用户

1. 在 Navicat 中点击顶部 **用户** 图标（或菜单：工具 → 用户）
2. 点击 **新建用户**
3. 填写账号信息：

| 字段 | 示例值 | 说明 |
| --- | --- | --- |
| 用户名 | `report` | 账号名 |
| 主机 | `192.168.100.%` | 允许连接的来源 |
| 密码 | `Report@Pass123!` | 密码 |
| 密码过期 | 90 天 | 强制定期更换密码 |

4. 切换到 **权限** 选项卡 → 选择数据库 → 勾选允许的权限（只勾选 SELECT）
5. 点击 **保存**

### 修改已有用户权限

1. **用户** 列表中双击目标用户
2. 切换到 **权限** 选项卡
3. 添加/移除数据库和对应权限
4. 保存

## 2.5 命令行完整权限管理演练

### 创建多角色账号

实际业务中，不同角色需要不同的权限：

```sql
-- ========================================
-- 只读账号：适合报表、数据分析人员
-- ========================================
CREATE USER 'reader'@'192.168.100.%' IDENTIFIED BY 'Read@Pass123!';
GRANT SELECT ON employees.* TO 'reader'@'192.168.100.%';

-- ========================================
-- 读写账号：适合应用服务器
-- ========================================
CREATE USER 'writer'@'192.168.100.%' IDENTIFIED BY 'Write@Pass123!';
GRANT SELECT, INSERT, UPDATE, DELETE ON employees.* TO 'writer'@'192.168.100.%';

-- ========================================
-- 开发者账号：可以改表结构但不能删库
-- ========================================
CREATE USER 'developer'@'192.168.100.%' IDENTIFIED BY 'Dev@Pass123!';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX, CREATE TEMPORARY TABLES
    ON employees.*
    TO 'developer'@'192.168.100.%';

-- ========================================
-- 验证每个账号的权限
-- ========================================
SHOW GRANTS FOR 'reader'@'192.168.100.%';
SHOW GRANTS FOR 'writer'@'192.168.100.%';
SHOW GRANTS FOR 'developer'@'192.168.100.%';
```

### 权限修改：授权 + 撤权

```sql
-- 给 writer 添加 CREATE 权限（比如需要创建临时表）
GRANT CREATE ON employees.* TO 'writer'@'192.168.100.%';

-- 撤销 developer 的 ALTER 权限（不再允许修改表结构）
REVOKE ALTER ON employees.* FROM 'developer'@'192.168.100.%';

-- 撤销所有权限（但不删除账号）
REVOKE ALL PRIVILEGES, GRANT OPTION FROM 'reader'@'192.168.100.%';
```

### 账号生命周期管理

```sql
-- 查看所有账号
SELECT user, host, account_locked, password_expired, password_lifetime
FROM mysql.user
WHERE plugin != 'auth_socket'
ORDER BY user;

-- 锁定账号（临时禁用，不删除）
ALTER USER 'developer'@'192.168.100.%' ACCOUNT LOCK;

-- 解锁账号
ALTER USER 'developer'@'192.168.100.%' ACCOUNT UNLOCK;

-- 设置密码过期（强制下次登录时修改密码）
ALTER USER 'writer'@'192.168.100.%' PASSWORD EXPIRE;

-- 删除账号（先确认没有业务依赖）
DROP USER 'reader'@'192.168.100.%';
```

### 资源限制（防止账号滥用）

MySQL 可以限制单个账号的资源消耗，防止单个应用拖垮整个数据库：

```sql
-- 创建有资源限制的账号
GRANT ALL ON employees.* TO 'limited_app'@'192.168.100.%'
WITH MAX_QUERIES_PER_HOUR 1000        -- 每小时最多 1000 次查询
     MAX_UPDATES_PER_HOUR 100         -- 每小时最多 100 次更新
     MAX_CONNECTIONS_PER_HOUR 50      -- 每小时最多 50 次连接
     MAX_USER_CONNECTIONS 5;          -- 同时最多 5 个并发连接
```

| 限制参数 | 作用 | 推荐场景 |
| --- | --- | --- |
| `MAX_QUERIES_PER_HOUR` | 限制每小时查询总数 | 防止脚本无限循环查询 |
| `MAX_UPDATES_PER_HOUR` | 限制每小时写操作总数 | 防止异常批量写入 |
| `MAX_CONNECTIONS_PER_HOUR` | 限制每小时连接总数 | 防止连接池泄漏 |
| `MAX_USER_CONNECTIONS` | 限制同时并发连接数 | 防止一个账号占满所有连接 |

<aside>
💬

**什么时候用资源限制？**

- 开放给外部系统的 API 账号（限制 QPS）
- 给第三方合作伙伴的只读账号
- 测试环境的公共账号

内部应用服务器一般不需要限制，因为应用本身有连接池管理。

</aside>

## 2.6 MySQL 安全加固清单

| 加固措施 | 命令 / 操作 | 防御什么 |
| --- | --- | --- |
| 禁止 root 远程登录 | `mysql_secure_installation` 中选择 Yes | 远程暴力破解 root |
| 限制账号来源 IP | `'user'@'192.168.100.%'` 而不是 `'user'@'%'` | 来自未知网络的连接 |
| 启用密码验证组件 | `INSTALL COMPONENT 'file://component_validate_password'` | 弱密码 |
| 定期轮换密码 | `ALTER USER ... IDENTIFIED BY ...` | 密码泄露后的窗口期 |
| 锁定不用的账号 | `ALTER USER ... ACCOUNT LOCK` | 废弃账号被利用 |
| 最小权限原则 | 只授予业务需要的权限 | 权限滥用 / 提权 |
| 删除匿名用户 | `DROP USER ''@'localhost'` | 匿名访问 |
| 删除 test 数据库 | `DROP DATABASE test` | 测试库被利用 |
| 限制 FILE 权限 | 不授予业务账号 FILE 权限 | 读写服务器文件系统 |
| 开启 binlog | 第五章已配置 | 数据恢复 / 审计追溯 |

<aside>
✅

**第 2 课小结**

- 权限管理四步走：查（SHOW GRANTS）→ 改（GRANT/REVOKE）→ 锁（ACCOUNT LOCK）→ 删（DROP USER）
- 多角色账号：reader / writer / developer 各有不同权限范围
- 资源限制是防止单账号拖垮数据库的最后一道防线
- 安全加固不是一次性操作，需要定期审计
</aside>

---

# 第 3 课 命令行备份与还原：丢不了数据

## 3.1 与上一课的衔接

上一课解决了"管人"的问题。这一课回到命令行，学习 MySQL 最重要的备份工具 `mysqldump`。为什么有了 Navicat 备份还要学命令行？因为**服务器上没有 GUI**，生产环境的备份一定是用脚本自动化执行的。

<aside>
💬

**备份策略对比**

| 方式 | 适合场景 | 是否需要 GUI |
| --- | --- | --- |
| Navicat 备份模块 | 本地快速备份、开发环境 | 需要 |
| mysqldump 命令行 | 服务器自动化备份、生产环境 | 不需要 |
| 物理备份（XtraBackup） | 大数据量、热备份 | 不需要 |

</aside>

## 3.2 本课要解决的问题

- 掌握 `mysqldump` 的常用备份语法
- 掌握备份还原的完整流程
- 理解逻辑备份的适用场景和局限性
- 能写出简单的定时备份脚本

## 3.3 mysqldump 备份详解

`mysqldump` 是 MySQL 自带的逻辑备份工具，将数据库导出为 SQL 脚本文件。

### 备份单个数据库

```bash
# 基本备份（结构 + 数据）
mysqldump -u root -p stusta > stusta_backup.sql

# 备份带时间戳（方便管理多个备份文件）
mysqldump -u root -p stusta > stusta_$(date +%Y%m%d_%H%M%S).sql
```

### 备份多个数据库

```bash
# 备份指定的多个数据库
mysqldump -u root -p --databases stusta employees > multi_db_backup.sql

# 备份所有数据库（系统库也包含在内）
mysqldump -u root -p --all-databases > all_db_backup.sql
```

### 常用参数

| 参数 | 作用 | 推荐使用 |
| --- | --- | --- |
| `--single-transaction` | InnoDB 一致性备份（不锁表） | InnoDB 必加 |
| `--routines` | 包含存储过程和函数 | 建议加上 |
| `--triggers` | 包含触发器 | 默认已包含 |
| `--events` | 包含定时事件 | 有事件时加上 |
| `--flush-logs` | 备份前切换 binlog | PITR 场景使用 |
| `--master-data=2` | 记录 binlog 位置（注释形式） | 主从复制场景使用 |
| `--where` | 只备份符合条件的数据 | 部分备份 |

<aside>
💬

**为什么 InnoDB 备份要加 `--single-transaction`？**

不加这个参数，`mysqldump` 会对每张表加 `LOCK TABLES`，备份期间其他会话无法写入这些表，相当于"暂停业务"。

加了 `--single-transaction`，mysqldump 会开启一个事务快照（类似数据库的"照片"），在不锁表的情况下获取一致性的数据。备份期间业务正常运行。

</aside>

### 推荐的备份命令

```bash
# 日常备份：InnoDB 不锁表 + 包含存储过程 + 包含事件
mysqldump -u root -p \
  --single-transaction \
  --routines \
  --triggers \
  --events \
  --flush-logs \
  stusta > stusta_daily_$(date +%Y%m%d).sql
```

## 3.4 备份还原

### 还原整个数据库

```bash
# 方式一：mysql 命令行还原
mysql -u root -p stusta < stusta_backup.sql

# 方式二：在 MySQL 内部还原
mysql -u root -p
> SOURCE /path/to/stusta_backup.sql;
```

### 还原到新数据库（不影响原数据）

```bash
# 先创建新数据库
mysql -u root -p -e "CREATE DATABASE stusta_restored;"

# 还原到新数据库
mysql -u root -p stusta_restored < stusta_backup.sql
```

<aside>
💬

**还原前注意事项**

1. 如果 `.sql` 文件中包含 `CREATE DATABASE` 和 `USE` 语句（`--databases` 导出的），会直接覆盖同名数据库
2. 如果 `.sql` 中不包含 `CREATE DATABASE`（单库导出的），需要先手动创建目标数据库
3. 还原大文件时可能需要调整 `max_allowed_packet`：`mysql --max_allowed_packet=512M -u root -p db < backup.sql`

</aside>

## 3.5 逻辑备份 vs 物理备份

| 维度 | 逻辑备份（mysqldump） | 物理备份（XtraBackup） |
| --- | --- | --- |
| 输出格式 | SQL 文本文件 | 数据文件的二进制副本 |
| 备份速度 | 慢（逐行导出） | 快（直接复制文件） |
| 还原速度 | 慢（逐行执行 SQL） | 快（直接替换文件） |
| 可读性 | 人类可读（可编辑） | 不可读 |
| 跨版本 | 支持（SQL 兼容性） | 不支持（必须同版本） |
| 适用规模 | 中小型（< 100GB） | 大型（100GB+） |
| 热备份 | 支持（`--single-transaction`） | 支持 |

<aside>
💬

**初学者用 mysqldump 就够了**

`mysqldump` 是入门必学的备份工具，简单可靠，适合课程实验和中小型数据库。等数据量增长到百 GB 级别，再考虑 XtraBackup 等物理备份方案。

</aside>

## 3.6 自动化备份脚本

手动备份容易遗忘，生产环境应该用 cron 定时任务自动执行：

```bash
#!/bin/bash
# /opt/mysql_backup.sh — MySQL 每日备份脚本

BACKUP_DIR="/var/backups/mysql"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="stusta"
KEEP_DAYS=7

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 执行备份
mysqldump -u root -p'YourRootPassword' \
  --single-transaction \
  --routines \
  --triggers \
  --events \
  --flush-logs \
  "$DB_NAME" > "$BACKUP_DIR/${DB_NAME}_${DATE}.sql"

# 检查备份是否成功
if [ $? -eq 0 ]; then
    echo "[$(date)] Backup OK: ${DB_NAME}_${DATE}.sql" >> "$BACKUP_DIR/backup.log"
else
    echo "[$(date)] Backup FAILED!" >> "$BACKUP_DIR/backup.log"
fi

# 删除 N 天前的备份
find "$BACKUP_DIR" -name "*.sql" -mtime +$KEEP_DAYS -delete
```

设置定时执行：

```bash
# 给脚本执行权限
chmod +x /opt/mysql_backup.sh

# 添加 cron 任务：每天凌晨 2 点执行
sudo crontab -e
# 添加以下行：
0 2 * * * /opt/mysql_backup.sh
```

<aside>
⚠️

**脚本中的密码安全**

示例中将密码写在脚本里只是为了演示。生产环境建议：

- 使用 MySQL 配置文件 `~/.my.cnf` 存储凭证
- 或使用 MySQL 的 `--defaults-extra-file` 参数指定凭证文件
- 确保凭证文件权限为 `600`（仅 owner 可读写）

</aside>

<aside>
✅

**第 3 课小结**

- `mysqldump` 是 MySQL 最基础的备份工具，必须掌握
- InnoDB 备份加 `--single-transaction`，不锁表
- 还原前先确认目标数据库的状态，避免误覆盖
- 生产环境用 cron + 脚本实现自动备份
- 中小型数据库用 mysqldump，大型数据库考虑 XtraBackup
</aside>

---

# 第 4 课 主从复制与攻防加固：扩得了容、防得住攻击

## 4.1 与上一课的衔接

前面三课解决了"用得顺手、管得住人、丢不了数据"。这一课解决两个高级话题：

1. **主从复制**：数据量增大后，单台 MySQL 扛不住所有读写压力，需要"分身"
2. **攻防加固**：知道 MySQL 面临哪些攻击，才能做好防御

## 4.2 本课要解决的问题

- 理解 MySQL 主从复制的原理（三个线程 + relay log）
- 能配置基于 binlog 的主从复制
- 了解常见的 MySQL 攻击方式和对应防御措施
- 了解 GTID 复制和 MySQL 高可用方案（拓展）

## 4.3 主从复制原理

MySQL 复制（Replication）是将数据从一台服务器（主服务器 Master）自动同步到一台或多台服务器（从服务器 Slave）的技术。

**复制流程图**：

```
主服务器（Master）                        从服务器（Slave）
┌──────────────┐                    ┌──────────────────┐
│              │                    │                  │
│  写操作产生   │                    │                  │
│      ↓       │                    │                  │
│  Binary Log  │ ─── 网络传输 ──→  │  IO Thread 接收   │
│  (binlog)    │                    │      ↓           │
│              │                    │  Relay Log       │
│              │                    │  (中继日志)       │
│              │                    │      ↓           │
│              │                    │  SQL Thread 重放  │
│              │                    │      ↓           │
│              │                    │  从库数据更新     │
└──────────────┘                    └──────────────────┘
```

**三个关键线程**：

| 线程 | 所在 | 作用 |
| --- | --- | --- |
| **Binlog Dump Thread** | 主服务器 | 读取 binlog 并发送给从服务器 |
| **IO Thread** | 从服务器 | 接收 binlog，写入本地 Relay Log |
| **SQL Thread** | 从服务器 | 读取 Relay Log，执行 SQL 更新数据 |

<aside>
💬

**类比理解**

把主从复制想象成"同步笔记"：

- 主库是"老师"，每次写板书（写操作）都记在一本流水账（binlog）里
- 从库是"学生"，通过 IO 线程抄写老师的流水账（写入 Relay Log）
- 然后通过 SQL 线程按照流水账的内容在自己的本子上重写一遍

这样老师的每一步操作，学生都能同步看到。

</aside>

### 复制的应用场景

| 场景 | 说明 |
| --- | --- |
| **读写分离** | 写操作发给主库，读操作发给从库，提升整体吞吐 |
| **数据备份** | 从库作为热备，主库故障时可快速切换 |
| **数据分析** | 在从库执行耗时的统计查询，不影响主库性能 |
| **地理分布** | 不同地区部署从库，就近提供服务 |

## 4.4 配置主从复制（完整步骤）

<aside>
🖥️

**实验拓扑**

- Master（主库）：192.168.100.20（VM-A）
- Slave（从库）：192.168.100.21（VM-B，需要在 VM-B 上也安装 MySQL）

</aside>

### 第一步：配置主服务器（Master）

编辑主库配置文件：

```bash
sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf
```

```ini
[mysqld]
server-id = 1                           # 唯一 ID，主从不能重复
log_bin = /var/lib/mysql/mysql-bin      # 开启 binlog
binlog_format = ROW                     # 推荐 ROW 格式
binlog_do_db = employees                # 只复制指定库（可选）
```

```bash
# 重启使配置生效
sudo systemctl restart mysql
```

在主库创建复制专用账号：

```sql
-- 创建复制账号（只需要 REPLICATION SLAVE 权限）
CREATE USER 'repl'@'192.168.100.%' IDENTIFIED BY 'Repl@Pass123!';
GRANT REPLICATION SLAVE ON *.* TO 'repl'@'192.168.100.%';
FLUSH PRIVILEGES;

-- 记录当前 binlog 文件名和位置（后面配置从库要用）
SHOW MASTER STATUS;
-- +------------------+----------+
-- | File             | Position |
-- +------------------+----------+
-- | mysql-bin.000003 | 154      |
-- +------------------+----------+
```

<aside>
💬

**为什么要单独创建复制账号？**

- 复制只需要 `REPLICATION SLAVE` 权限，不需要数据读写权限
- 使用独立账号，万一密码泄露，攻击者也只能做复制操作，不能改数据
- 符合最小权限原则

</aside>

### 第二步：配置从服务器（Slave）

编辑从库配置文件：

```bash
sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf
```

```ini
[mysqld]
server-id = 2                           # 与主库不同的唯一 ID
relay_log = /var/lib/mysql/relay-bin    # 中继日志路径
read_only = 1                           # 从库设为只读（防止误写）
```

```bash
# 重启
sudo systemctl restart mysql
```

在从库配置连接参数：

```sql
-- 配置从库连接主库的参数
CHANGE MASTER TO
    MASTER_HOST = '192.168.100.20',
    MASTER_USER = 'repl',
    MASTER_PASSWORD = 'Repl@Pass123!',
    MASTER_PORT = 3306,
    MASTER_LOG_FILE = 'mysql-bin.000003',   -- SHOW MASTER STATUS 的 File 值
    MASTER_LOG_POS = 154;                    -- SHOW MASTER STATUS 的 Position 值

-- 启动复制
START SLAVE;

-- 查看从库状态（关键检查项）
SHOW SLAVE STATUS\G
```

### 第三步：验证复制状态

```sql
-- 在 SHOW SLAVE STATUS 的输出中，确认以下两项：
-- Slave_IO_Running: Yes    ← IO 线程正在运行
-- Slave_SQL_Running: Yes   ← SQL 线程正在运行
-- Seconds_Behind_Master: 0 ← 无延迟
```

| 状态 | 含义 | 正常值 |
| --- | --- | --- |
| `Slave_IO_Running` | IO 线程是否在运行 | `Yes` |
| `Slave_SQL_Running` | SQL 线程是否在运行 | `Yes` |
| `Seconds_Behind_Master` | 从库落后主库的秒数 | `0`（无延迟） |
| `Last_IO_Error` | IO 线程的最近错误 | 空（无错误） |
| `Last_SQL_Error` | SQL 线程的最近错误 | 空（无错误） |

### 第四步：验证数据同步

```sql
-- 在主库执行写操作
USE employees;
CREATE TABLE repl_test (id INT, msg VARCHAR(50));
INSERT INTO repl_test VALUES(1, '主库写入测试');

-- 在从库验证是否同步
USE employees;
SELECT * FROM repl_test;
-- 应该能看到：1 | 主库写入测试
```

## 4.5 常见复制故障处理

| 故障现象 | 可能原因 | 处理方法 |
| --- | --- | --- |
| `Slave_IO_Running: No` | 网络不通、账号密码错误、binlog 文件不存在 | 检查 `Last_IO_Error` 字段 |
| `Slave_SQL_Running: No` | SQL 执行失败（如主键冲突） | 跳过错误或修复数据 |
| `Seconds_Behind_Master` 持续增大 | 从库性能不足或网络延迟 | 检查从库负载和网络 |

```sql
-- 跳过一个复制错误（谨慎使用，仅用于非关键数据）
STOP SLAVE;
SET GLOBAL sql_slave_skip_counter = 1;
START SLAVE;

-- 重置从库（清空所有复制信息，重新配置）
STOP SLAVE;
RESET SLAVE ALL;
```

## 4.6 GTID 复制（MySQL 8.0 推荐）

传统的复制需要手动记录 File 和 Position，容易出错。GTID（Global Transaction Identifier）为每个事务分配全局唯一 ID，从库自动定位，不需要人工记录位置。

```ini
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
```

<aside>
💬

**GTID vs 传统 File+Position**

| 维度 | File + Position | GTID |
| --- | --- | --- |
| 配置复杂度 | 需要手动记录位置 | 自动定位 |
| 故障切换 | 需要手动计算新位置 | 自动接管 |
| 数据一致性 | 可能遗漏事务 | 不会遗漏 |
| 推荐度 | 旧版本兼容 | **MySQL 8.0 强烈推荐** |

</aside>

## 4.7 复制拓扑类型（拓展了解）

| 类型 | 拓扑 | 适用场景 |
| --- | --- | --- |
| **主从复制**（Master-Slave） | 一主多从 | 读写分离、备份 |
| **主主复制**（Master-Master） | 双向同步 | 双活高可用（需注意写冲突） |
| **级联复制**（Chain） | 主→中继→从 | 减少主库复制压力 |
| **多源复制**（Multi-Source） | 多主一从 | 数据汇聚分析 |

## 4.8 MySQL 常见攻击与防御

了解攻击手段，才能做好防御。以下是 MySQL 面临的主要安全威胁：

### SQL 注入

**原理**：攻击者在用户输入中插入恶意 SQL 代码，让数据库执行非预期操作。

```sql
-- 正常查询
SELECT * FROM users WHERE name = '张三';

-- 注入攻击：输入 ' OR 1=1 --
SELECT * FROM users WHERE name = '' OR 1=1 --';
-- 结果：返回所有用户数据
```

**防御措施**：

| 措施 | 说明 |
| --- | --- |
| 参数化查询 / 预编译语句 | 用 `?` 占位符代替直接拼接 SQL |
| Web 应用防火墙（WAF） | 检测并拦截可疑 SQL |
| 输入验证 | 在应用层过滤非法字符 |
| 最小权限 | 应用账号没有 DROP / FILE 等高危权限 |

### 弱密码暴力破解

**原理**：攻击者遍历常见用户名密码组合，尝试登录 MySQL。

**防御措施**：

- 强密码策略（`validate_password` 组件）
- 限制连接来源 IP
- 账户锁定策略
- 修改默认端口 3306（仅增加发现难度，不是真正的安全措施）

### 未授权访问

**原理**：MySQL 监听 `0.0.0.0:3306`，且存在 `'root'@'%'` 或弱密码账号，攻击者可以直接连接。

**防御措施**：

- 禁止 root 远程登录
- `bind-address` 绑定内网 IP
- 配合防火墙只允许内网网段访问 3306

### UDF 提权

**原理**：攻击者通过 MySQL 的 `FILE` 权限上传恶意动态链接库（UDF），然后通过 MySQL 调用该库执行系统命令，获得操作系统级别的权限。

**防御措施**：

- 不授予业务账号 `FILE` 权限
- 设置 `secure_file_priv` 限制文件读写路径
- 定期审计 `mysql.func` 表

<aside>
⚠️

**UDF 提权的严重性**

UDF 提权可以将"数据库权限"升级为"操作系统权限"。如果 MySQL 以 root 身份运行（极不推荐），攻击者通过 UDF 可以获得服务器的 root 权限。

**关键防御**：MySQL 进程不要以 root 用户运行，应该用专用的 `mysql` 用户。

</aside>

## 4.9 MySQL 高可用方案（拓展了解）

| 方案 | 原理 | 适用场景 |
| --- | --- | --- |
| **MySQL InnoDB Cluster** | 基于 Group Replication，自动故障转移 | 官方推荐的高可用方案 |
| **Percona XtraDB Cluster** | 同步多主复制，强一致性 | 金融/电商等要求强一致性的场景 |
| **MHA**（Master High Availability） | 自动主从切换 | 传统主从复制的高可用升级 |
| **ProxySQL / MySQL Router** | 读写分离中间件 | 配合主从复制使用 |

<aside>
💬

**初学者不需要掌握所有方案**

当前阶段重点理解主从复制的原理和配置。InnoDB Cluster、PXC 等高级方案是后续深入学习的内容，了解即可。

</aside>

<aside>
✅

**第 4 课小结**

- 主从复制三个线程：Binlog Dump → IO Thread → SQL Thread
- 配置四步：主库配置 → 创建复制账号 → 从库配置 → 验证状态
- GTID 是 MySQL 8.0 推荐的复制方式，免去手动记录位置的麻烦
- 常见攻击：SQL 注入、暴力破解、未授权访问、UDF 提权
- 安全加固核心：最小权限 + 限制来源 + 不以 root 运行 MySQL
</aside>

---

# 📝 项目总结（一张表复盘）

| 课时 | 核心能力 | 验收点（可检查） |
| --- | --- | --- |
| 第 1 课：Navicat 管理 | 用得顺手 | 能用 Navicat 连接、导入数据、完成备份还原 |
| 第 2 课：权限管理 | 管得住人 | 能创建多角色账号并验证权限边界 |
| 第 3 课：命令行备份 | 丢不了数据 | 能用 mysqldump 完成备份还原，能写定时备份脚本 |
| 第 4 课：复制与加固 | 扩得了容、防得住攻击 | 能解释主从复制流程，能说出 3 种攻击及防御 |

---

# 附录

## 附录 A：Navicat 常用快捷键

| 操作 | 快捷键 |
| --- | --- |
| 新建查询 | `Ctrl + Q` |
| 执行查询 | `Ctrl + R` |
| 注释/取消注释 | `Ctrl + /` |
| 切换数据库 | `Ctrl + D` |
| 刷新对象列表 | `F5` |

## 附录 B：mysqldump 常用参数速查

| 参数 | 作用 |
| --- | --- |
| `--single-transaction` | InnoDB 一致性不锁表备份 |
| `--databases db1 db2` | 指定备份的数据库 |
| `--all-databases` | 备份所有数据库 |
| `--routines` | 包含存储过程和函数 |
| `--triggers` | 包含触发器（默认开启） |
| `--events` | 包含定时事件 |
| `--flush-logs` | 备份前切换 binlog |
| `--master-data=2` | 记录 binlog 位置（注释形式） |
| `--where="条件"` | 只备份符合条件的数据 |
| `--no-data` | 只备份表结构，不备份数据 |
| `--add-drop-database` | 在还原前先 DROP DATABASE |
