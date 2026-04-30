---
title: "05.项目五 MySQL数据库安全基础"
---

# 05.项目五 MySQL数据库安全基础

🎯**本项目学习目标**

- 能够在 Ubuntu 24.04 LTS 环境下完成 MySQL 的安装与验证（以 MySQL 8.0 为主）
- 掌握 MySQL 服务的启动/停止，并完成初始密码修改 / 认证方式理解
- 能够创建受限账户并配置**内网远程访问**权限（两台 VM 互连）
- 了解 MySQL 四种主要日志的用途及基本操作，重点掌握 binlog 的开启与基础恢复思路（PITR）

<aside>
🧭

**主线地图（先记这一句）**：装得起来 → 配得安全（边界/基线）→ 管得住人（最小权限）→ 出事能追溯/能恢复（日志）。

</aside>

<aside>
🖥️

**实验拓扑（同一内网两台虚拟机互连）**

- VM-A：MySQL Server（示例 IP：`192.168.100.20`）
- 两台 VM 需能互相 ping 通；后续远程连接走 TCP/3306
</aside>

---

# 第 1 课 安装与验证：让 MySQL “能跑起来”

## 1.1 本课要解决的问题

把 MySQL 在 Ubuntu 24.04 上装起来，并能验证：**服务在跑、能登录、能看到版本与数据库列表**。

## 1.2 本课交付物（学生可检查）

- `mysql --version` 输出
- `sudo systemctl status mysql --no-pager` 显示 active(running)
- MySQL 内执行成功：
    - `SELECT VERSION();`
    - `SHOW DATABASES;`

## 1.3 MySQL 简介

MySQL 是世界上最流行的**开源关系型数据库管理系统（RDBMS）**，大量 Web 系统使用它作为核心数据存储。安全运维从安装开始：**安装 ≠ 安全，安装只是第一步**。

<aside>
💬

**一句话理解**：如果把 Web 应用比作餐厅，MySQL 就是后厨的“仓库管理系统”——所有数据的存、取、改、删都由它负责。

</aside>

## 1.4 安装前准备：拍快照 + 换源（Ubuntu 24.04）

### 第 1 步：拍摄 VMware 快照（安全网）

<aside>
📸

**为什么先拍快照？** 安装或配置出错时可一键恢复。
**操作**：VMware 菜单 → 虚拟机 → 快照 → 拍摄快照 → 命名为“安装MySQL前”

</aside>

### 第 2 步：换源加速

- Ubuntu 24.04 LTS 换源（DEB822 格式）
    
    Ubuntu 24.04 使用 `/etc/apt/sources.list.d/ubuntu.sources`（DEB822 格式）。
    
    ```bash
    # 1) 备份原文件
    sudo cp /etc/apt/sources.list.d/ubuntu.sources /etc/apt/sources.list.d/ubuntu.sources.bak
    
    # 2) 编辑配置文件
    sudo nano /etc/apt/sources.list.d/ubuntu.sources
    ```
    
    将文件内容**全部替换**为以下内容（阿里云镜像示例）：
    
    ```
    Types: deb
    URIs: https://mirrors.aliyun.com/ubuntu
    Suites: noble noble-updates noble-backports
    Components: main restricted universe multiverse
    Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg
    
    Types: deb
    URIs: https://mirrors.aliyun.com/ubuntu
    Suites: noble-security
    Components: main restricted universe multiverse
    Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg
    ```
    
    保存退出后更新索引：
    
    ```bash
    sudo apt update
    ```
    
- Ubuntu 22.04 LTS 换源（传统 sources.list 格式）
    
    Ubuntu 22.04 使用传统的 `/etc/apt/sources.list` 文件。
    
    ```bash
    # 1) 备份原文件
    sudo cp /etc/apt/sources.list /etc/apt/sources.list.bak
    
    # 2) 编辑配置文件
    sudo nano /etc/apt/sources.list
    ```
    
    将文件内容**全部替换**为以下内容（阿里云镜像示例）：
    
    ```
    deb https://mirrors.aliyun.com/ubuntu/ jammy main restricted universe multiverse
    deb https://mirrors.aliyun.com/ubuntu/ jammy-updates main restricted universe multiverse
    deb https://mirrors.aliyun.com/ubuntu/ jammy-backports main restricted universe multiverse
    deb https://mirrors.aliyun.com/ubuntu/ jammy-security main restricted universe multiverse
    ```
    
    保存退出后更新索引：
    
    ```bash
    sudo apt update
    ```
    

## 1.5 安装与验证（关键四步）

```bash
# 0) 更新索引
sudo apt update

# 1) 安装 MySQL Server
sudo apt install -y mysql-server

# 2) 启动并设置开机自启
sudo systemctl enable --now mysql

# 3) 验证版本与服务状态
mysql --version
sudo systemctl status mysql --no-pager
```

### 第 4 步：运行安全加固向导

```bash
sudo mysql_secure_installation
```

<aside>
✅

**向导建议选项（零基础按这个选）**

1. 设置 / 修改 root 密码 → 设置强口令（或后续用 ALTER USER 设置）
2. 删除匿名用户 → Yes
3. 禁止 root 远程登录 → Yes
4. 删除 test 数据库 → Yes
5. 刷新权限表 → Yes
</aside>

### 第 5 步：首次登录验证

```bash
# Ubuntu apt 安装后 root 常见为 auth_socket：sudo 即可进入
sudo mysql
```

```sql
SELECT VERSION();
SHOW DATABASES;
exit;
```

<aside>
✅

**第 1 课小结**

- 安装的目标不是“看懂所有概念”，而是完成：安装→启动→加固→验证
- `sudo mysql` 能进是因为 Ubuntu 默认 auth_socket（不是“没设密码”）
</aside>

---

# 第 2 课 配置文件与安全基线：把“边界”和“默认坑”补齐

## 2.1 与上一课的衔接（过渡）

我们已经让 MySQL **能跑起来**。下一步要让它**在正确的边界内运行**：远程访问是否允许、字符集是否正确、时间是否一致。否则会出现：**远程连不上、乱码、时间错位**等常见问题。

## 2.2 本课要解决的问题

- 找到 Ubuntu 24.04 的主配置文件位置
- 完成三件“必改且可验证”的基线配置：**bind-address / utf8mb4 / time_zone**
- 修改后能重启并验证变量生效

## 2.3 配置文件入口与结构

MySQL 配置文件采用 INI 格式，Ubuntu 24.04 主要编辑：

<aside>
📍

`/etc/mysql/mysql.conf.d/mysqld.cnf`（服务端 mysqld 配置）

</aside>

配置段示例：

```
[mysqld]
port = 3306
bind-address = 127.0.0.1

[client]
port = 3306
```

## 2.4 三件必改

### A. 远程访问边界：bind-address

- `127.0.0.1`：只允许本机连接（安全但 VM-B 连不上）
- **内网互连实验建议**：改为 `0.0.0.0`，但必须配合：内网网段账号 + 防火墙限制

```
[mysqld]
bind-address = 0.0.0.0
port = 3306
```

<aside>
⚠️

**安全提示**：`bind-address = 0.0.0.0` 会监听所有网卡。只用于内网实验环境；真实生产必须结合防火墙/安全组，并禁用公网暴露。

</aside>

### B. 字符集：utf8mb4（避免乱码/Emoji问题）

```
[mysqld]
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci

[client]
default-character-set = utf8mb4
```

### C. 时区：+08:00（避免时间错 8 小时）

```
[mysqld]
default-time-zone = '+08:00'
```

## 2.5 重启与验证

```bash
sudo systemctl restart mysql
sudo systemctl status mysql --no-pager
```

```sql
SHOW VARIABLES LIKE 'bind_address';
SHOW VARIABLES LIKE 'character_set_server';
SHOW VARIABLES LIKE 'time_zone';
SELECT NOW();
```

<aside>
✅

**第 2 课小结**

- 三件必改：bind-address（边界）、utf8mb4（编码）、time_zone（时间一致）
- 修改配置后：重启服务 + SHOW VARIABLES 验证生效
</aside>

---

# 第 3 课 账号与权限：远程能连，但不用 root（最小权限）

## 3.1 与上一课的衔接（过渡）

我们已经允许 MySQL 监听内网（bind-address），接下来要让 VM-B **能连接**，同时遵循数据库安全核心：**不用 root，按最小权限创建业务账号**。

## 3.2 本课要解决的问题

- 理解 MySQL 账户识别方式：`'用户名'@'主机'`
- 创建一个只允许内网网段连接的用户
- 给用户授予某个数据库范围内的最小权限
- 从 VM-B 远程登录验证

## 3.3 远程连接三要素（排错顺序）

<aside>
🔧

**从 VM-B 连不上？按这个顺序查：**

1) MySQL 是否监听 0.0.0.0:3306

2) 防火墙是否放通（`sudo ufw status`）

3) 账号 host 是否匹配来源 IP（MySQL：`SELECT user, host, plugin FROM mysql.user;`）

</aside>

## 3.4 创建数据库与远程账号

> 下面以数据库 `stusta` 为例，账号只允许 `192.168.100.%` 网段连接。
> 

在 VM-A（服务器）登录 MySQL：

```bash
sudo mysql
```

```sql
-- 1) 准备示例库
CREATE DATABASE stusta;

-- 2) 创建远程账号（网段限制）
CREATE USER 'app'@'192.168.100.%' IDENTIFIED BY 'App@Pass123!';

-- 3) 最小权限授权（只对 stusta.*）
GRANT SELECT, INSERT, UPDATE, DELETE ON stusta.* TO 'app'@'192.168.100.%';

-- 4) 验证权限
SHOW GRANTS FOR 'app'@'192.168.100.%';
```

## 3.5 防火墙（内网实验环境建议）

若启用了 ufw，可在 VM-A 放通 3306（仅内网）：

```bash
sudo ufw allow 3306/tcp
sudo ufw status
```

## 3.6 从 VM-B 远程登录验证

在 VM-B：

```bash
mysql -h 192.168.100.20 -u app -p
```

登录后验证：

```sql
SELECT USER(), CURRENT_USER();
SHOW DATABASES;
USE stusta;
SHOW TABLES;
exit;
```

<aside>
✅

**第 3 课小结**

- 账户身份 = `'user'@'host'`，host 约束“从哪里来”
- 远程访问建议：网段限制 + 最小权限授权 + 不使用 root
</aside>

---

# 第 4 课 日志：会排错、会定位慢、会恢复（重点：binlog）

## 4.1

我们已经实现“远程可用 + 最小权限”。最后要补上安全运维闭环：**出了问题能查、误操作能追溯、必要时能恢复**——这就靠日志。

## 4.2 本课要解决的问题

- 知道四类日志分别在什么场景用
- 能查看错误日志、能开启/查看慢查询日志
- 能开启 binlog，并理解“全量备份 + binlog 回放”的时间点恢复（PITR）思路

## 4.3 四种主要日志（先会选，再会做）

| 日志类型 | 记录内容 | 主要用途 | 建议 |
| --- | --- | --- | --- |
| 错误日志（Error Log） | 启动/关闭/运行错误 | 故障排查第一入口 | 默认开启，必须会看 |
| 查询日志（General Log） | 所有 SQL | 审计/调试 | 仅排错时临时开 |
| 二进制日志（binlog） | 所有写操作事件 | 复制 + PITR 恢复 | 建议开启（重点） |
| 慢查询日志（Slow Log） | 超过阈值的 SQL | 性能定位 | 建议开启（会用即可） |

## 4.4 错误日志：服务异常先看这里

```bash
tail -100 /var/log/mysql/error.log
```

## 4.5 慢查询日志：系统慢了怎么找 SQL

```sql
SHOW VARIABLES LIKE 'slow_query%';
SHOW VARIABLES LIKE 'long_query_time';

SET GLOBAL slow_query_log = 1;
SET GLOBAL long_query_time = 1;

SHOW GLOBAL STATUS LIKE 'Slow_queries';
```

```bash
tail -50 /var/log/mysql/slow.log
```

---

## 4.6 Binlog（重点）：开启 + 验证 + PITR 思路

### 4.6.1 开启 binlog（VM-A 修改配置文件）

编辑：

```bash
sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf
```

在 `[mysqld]` 段添加（或确认存在）：

```
[mysqld]
log_bin = /var/lib/mysql/mysql-bin
binlog_format = ROW
server_id = 1
```

重启并验证：

```bash
sudo systemctl restart mysql
```

```sql
SHOW VARIABLES LIKE 'log_bin';
SHOW VARIABLES LIKE 'binlog_format';
SHOW BINARY LOGS;
SHOW MASTER STATUS;
```

### 4.6.2 解析与按时间筛选（了解 + 会用命令）

```bash
sudo mysqlbinlog --base64-output=DECODE-ROWS -v /var/lib/mysql/mysql-bin.000001 | less
```

按时间范围：

```bash
sudo mysqlbinlog \
  --start-datetime="2026-04-21 08:00:00" \
  --stop-datetime="2026-04-21 10:00:00" \
  /var/lib/mysql/mysql-bin.000001 | less
```

### 4.6.3 时间点恢复（PITR）三步走

<aside>
🛡️

**PITR（Point-In-Time Recovery）核心流程**：

1) 先恢复全量备份（如 mysqldump）

2) 确定误操作时间点（从 binlog 找到）

3) 回放 binlog 到误操作前一刻（`--stop-datetime`）

</aside>

示例（思路演示）：

```bash
# 1) 恢复全量备份
mysql -u root -p < full_backup.sql

# 2) 回放 binlog 到误操作前
sudo mysqlbinlog \
  --stop-datetime="2026-04-21 09:59:59" \
  /var/lib/mysql/mysql-bin.000001 \
  /var/lib/mysql/mysql-bin.000002 | mysql -u root -p
```

<aside>
✅

**第 4 课小结**

- 错误日志：服务异常第一入口
- 慢查询：会开、会看、会定位慢 SQL
- binlog：能开启、能验证、能讲清 PITR 三步走
</aside>

---

# 📝 项目总结（一张表复盘）

| 课时 | 核心能力 | 验收点（可检查） |
| --- | --- | --- |
| 第 1 课：安装验证 | 装得起来 | 服务 active + `SELECT VERSION()` |
| 第 2 课：配置基线 | 配得安全 | bind-address/utf8mb4/time_zone 生效 |
| 第 3 课：账号权限 | 管得住人 | VM-B 能用最小权限账号远程登录 |
| 第 4 课：日志与恢复 | 能追溯/能恢复 | 能查看错误/慢查询；binlog 开启并能解释 PITR |

---

# 附录

- 附录 A：MySQL 与 SQL Server 主要差异（对比表）
    
    
    | 特性 | MySQL | SQL Server |
    | --- | --- | --- |
    | 许可证 | 开源（GPL）/ 商业双轨 | 商业（微软授权） |
    | 运行平台 | Linux、Windows、macOS | 主要 Windows（2017+ 支持 Linux） |
    | 主要生态 | LAMP、Web 应用、云原生 | 企业级 Windows 应用 |
    | 存储引擎 | 多引擎（InnoDB / MyISAM 等） | 单一引擎 |
    | SQL 方言 | 标准 SQL + MySQL 扩展 | T-SQL（Transact-SQL） |
    | 价格 | 免费（社区版） | 收费（企业版较贵） |
- 附录 B：安装场景与方法对比（课堂不展开）
    
    
    | 场景 | 说明 | 推荐安装方式 |
    | --- | --- | --- |
    | 课程实验 / 个人学习 | VMware 虚拟机中练习 | apt 安装（本项目推荐） |
    | Web 项目开发 | 本地或测试服务器 | apt 安装 或 Docker |
    | 生产环境部署 | 正式线上服务 | apt / 二进制包 + 加固脚本 |
    | 快速验证 / CI 流水线 | 一次性测试环境 | Docker 容器（秒级启停） |
    | 高性能调优 | 需要自定义编译参数 | 源码编译安装 |
- 附录 C：MySQL 安装后的目录结构与系统库（速查）
    
    
    | 路径 | 说明 | 使用场景 |
    | --- | --- | --- |
    | `/usr/bin/` | 客户端工具（mysql、mysqladmin、mysqldump 等） | 日常操作、备份 |
    | `/usr/sbin/mysqld` | MySQL 服务器进程 | 排查进程问题 |
    | `/var/lib/mysql/` | 数据目录 | 备份、迁移、磁盘空间排查 |
    | `/var/log/mysql/` | 日志目录（错误日志等） | 故障排查 |
    | `/etc/mysql/mysql.conf.d/mysqld.cnf` | 主配置文件 | 修改端口、绑定地址、日志等 |
    
    | 数据库 | 说明 | 使用场景 |
    | --- | --- | --- |
    | mysql | 用户账户、权限、插件配置 | 管理用户权限、排查认证问题 |
    | information_schema | 元数据库（只读虚拟库） | 查询表结构、索引信息 |
    | performance_schema | 性能监控数据 | 性能调优、慢查询分析 |
    | sys | 高级视图 | 快速获取性能摘要 |
- 附录 D：密码管理多方式（旧系统兼容，课堂不作为主线）
    - MySQL 8.0 推荐：`ALTER USER ... IDENTIFIED BY ...;`
    - `SET PASSWORD ... = PASSWORD()` 为旧语法（8.0 已弃用 PASSWORD()）
    - `mysqladmin` 适用于脚本化，但注意密码泄露风险（命令历史/进程列表）
- 附录 E：Navicat 远程连接与 8.0 认证插件兼容性
    
    MySQL 8.0 默认使用 `caching_sha2_password`，旧版 Navicat 可能不支持。可升级客户端，或对该账号临时降级：
    
    ```sql
    ALTER USER 'app'@'192.168.100.%'
      IDENTIFIED WITH mysql_native_password BY 'App@Pass123!';
    ```