---
title: "06.项目六 MySQL数据库高级安全维护"
---

# 06 项目六 MySQL 数据库高级安全维护

🎯 **本项目学习目标**

- 能在项目五的基础上完成 MySQL 安全认证深度配置（密码策略、认证插件、SSL/TLS 加密连接）
- 能实施细粒度访问控制（列级权限、角色管理）和企业级审计（MariaDB Audit Plugin）
- 能配置透明数据加密（TDE）、应用层加密和数据脱敏方案
- 能使用 Percona XtraBackup 完成物理热备、时间点恢复（PITR）和自动化备份脚本
- 能设计并演练容灾策略（主从复制、MHA 高可用架构）

<aside>
🧭

**主线地图（先记这一句）**：认证加密（进不来）→ 访问控制+审计（留痕迹）→ 数据加密（拿走也读不了）→ 备份容灾（出事能恢复）。

</aside>

<aside>
🖥️

**实验拓扑（双虚拟机 + 宿主机）**

```
┌─────────────────────────────────────────────────────────────┐
│                        宿主机 (Windows)                      │
│                                                             │
│   ┌──────────┐         ┌──────────┐                         │
│   │  Navicat │         │  MySQL   │                         │
│   │  客户端   │────────│  Workbench│                        │
│   └────┬─────┘         └─────┬────┘                         │
│        │                     │                              │
└────────┼─────────────────────┼──────────────────────────────┘
         │ TCP/3306 (SSL)      │ TCP/3306
         │                     │
┌────────┼─────────────────────┼──────────────────────────────┐
│        ▼                     ▼                              │
│   ┌──────────────────────────────────┐                      │
│   │  VM-1: mysql-master (主服务器)     │                      │
│   │  IP: 192.168.100.20              │                      │
│   │  MySQL 8.0 + Percona XtraBackup  │                      │
│   │  MariaDB Audit Plugin            │                      │
│   │  SSL/TLS 证书服务端               │                      │
│   └──────────────┬───────────────────┘                      │
│                  │ TCP/3306 (复制通道)                       │
│                  │                                          │
│   ┌──────────────▼───────────────────┐                      │
│   │  VM-2: mysql-slave (从服务器)      │                      │
│   │  IP: 192.168.100.21              │                      │
│   │  MySQL 8.0 (只读副本)             │                      │
│   │  MHA Node                        │                      │
│   └──────────────────────────────────┘                      │
│                                                             │
│            虚拟机网络：NAT / 桥接均可                         │
│            两台 VM 互相 ping 通即可                          │
└─────────────────────────────────────────────────────────────┘
```

**环境清单**

| 角色 | 主机名 | IP | 系统 | 软件 |
|------|--------|-----|------|------|
| 主服务器 | mysql-master | 192.168.100.20 | Ubuntu 24.04 LTS | MySQL 8.0、Percona XtraBackup 8.0、MariaDB Audit Plugin、OpenSSL |
| 从服务器 | mysql-slave | 192.168.100.21 | Ubuntu 24.04 LTS | MySQL 8.0、MHA Node |
| 宿主机 | — | — | Windows | Navicat / MySQL Workbench |

**前置条件（项目五已完成的基线）**

- VM-1 已安装 MySQL 8.0 且 `sudo mysql` 可正常登录
- root 账号已设置密码、匿名用户已删除、test 库已移除
- 监听地址已改为 `0.0.0.0`（或指定内网 IP）、字符集 UTF8MB4
- binlog 已开启（`log_bin=ON`）
- 宿主机 Navicat 能通过 `app@192.168.100.%` 远程连接

**课堂产出**

- VM-1 启用 SSL 加密连接，宿主机通过 SSL 连接并验证加密生效
- VM-1 完成列级权限控制 + RBAC 角色分配，验证越权访问被拒绝
- VM-1 安装 MariaDB Audit Plugin，产生审计日志并完成一次安全事件溯源
- VM-1 对 `salary_db` 启用 TDE 加密，验证数据文件无法被直接读取
- VM-1 使用 XtraBackup 完成一次全量热备 + 增量备份 + PITR 恢复演练
- VM-1 + VM-2 完成主从复制搭建，手动切换验证数据同步

</aside>

---

## 第 0 课 实验环境准备

### 0.1 克隆项目五虚拟机

项目六基于项目五的 MySQL 环境延伸。如果项目五的 VM 还在，直接在其上操作；否则按以下步骤从零搭建。

**Step 1：克隆 VM-1（主服务器）**

在 VMware / VirtualBox 中，将项目五的虚拟机完整克隆一份，重命名为 `mysql-master`：

```bash
# 登录后确认 MySQL 状态
sudo systemctl status mysql --no-pager
# 输出应显示 active (running)

mysql --version
# 输出应类似：mysql  Ver 8.0.xx for Linux on x86_64 (Ubuntu)

# 确认 binlog 已开启
sudo mysql -e "SHOW VARIABLES LIKE 'log_bin';"
# +---------------+-------+
# | Variable_name | Value |
# +---------------+-------+
# | log_bin       | ON    |
# +---------------+-------+
```

**Step 2：创建 VM-2（从服务器）**

再次克隆项目五的虚拟机，重命名为 `mysql-slave`，修改 IP 为 `192.168.100.21`：

```bash
# 在 VM-2 上修改 IP（以 Netplan 为例）
sudo nano /etc/netplan/00-installer-config.yaml
```

```yaml
network:
  ethernets:
    ens33:
      addresses: [192.168.100.21/24]
      gateway4: 192.168.100.2
      nameservers:
        addresses: [8.8.8.8, 114.114.114.114]
  version: 2
```

```bash
sudo netplan apply

# 确认 IP
ip addr show ens33 | grep "inet "
# 输出应包含 192.168.100.21
```

**Step 3：验证双机互通**

```bash
# 在 VM-1 上
ping -c 3 192.168.100.21
# 应收到 3 个 reply

# 在 VM-2 上
ping -c 3 192.168.100.20
# 应收到 3 个 reply
```

✅ **验证点**：两台 VM 互相 ping 通，各自 MySQL 服务 running

### 0.2 在 VM-1 上安装项目六所需软件

```bash
# 1. 安装 OpenSSL（通常已预装）
openssl version
# 若未安装：sudo apt install -y openssl

# 2. 安装 Percona XtraBackup 8.0
sudo apt install -y wget gnupg2 lsb-release
wget https://repo.percona.com/apt/percona-release_latest.generic_all.deb
sudo dpkg -i percona-release_latest.generic_all.deb
sudo percona-release enable-only tools release
sudo apt update
sudo apt install -y percona-xtrabackup-80

# 验证安装
xtrabackup --version
# 输出应含：xtrabackup version 8.0.xx

# 3. 安装 MariaDB Audit Plugin 所需依赖
sudo apt install -y libmariadb3 mariadb-plugin-provider-socket 2>/dev/null || true
# 审计插件文件将在第 2 课中手动下载

# 4. 创建项目六专用目录
sudo mkdir -p /opt/mysql-lab06/{backup,ssl,audit,scripts}
sudo chown -R $USER:$USER /opt/mysql-lab06
```

✅ **验证点**：

```bash
xtrabackup --version   # 能输出版本号
ls -d /opt/mysql-lab06/{backup,ssl,audit,scripts}  # 四个目录均存在
```

### 0.3 准备实验数据库

在 VM-1 的 MySQL 中创建项目六所需的数据库和表：

```bash
sudo mysql << 'EOF'
-- 1. 员工薪资数据库（用于列级权限 + TDE 演示）
CREATE DATABASE IF NOT EXISTS salary_db;
USE salary_db;

CREATE TABLE employees (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL,
    department VARCHAR(30) NOT NULL,
    position VARCHAR(50),
    salary DECIMAL(10,2) NOT NULL,
    id_card VARCHAR(18) NOT NULL COMMENT '身份证号-脱敏字段',
    phone VARCHAR(20) NOT NULL COMMENT '手机号-脱敏字段',
    bank_account VARCHAR(30) NOT NULL COMMENT '银行卡号-加密字段',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

INSERT INTO employees (name, department, position, salary, id_card, phone, bank_account) VALUES
('张三', '技术部', '高级工程师', 28000.00, '110101199001011234', '13800138001', '6222021234567890001'),
('李四', '财务部', '财务主管', 25000.00, '110101198512052345', '13800138002', '6222021234567890002'),
('王五', '技术部', '初级工程师', 15000.00, '110101199503033456', '13800138003', '6222021234567890003'),
('赵六', '人事部', '招聘专员', 12000.00, '110101199807074567', '13800138004', '6222021234567890004'),
('钱七', '技术部', '架构师', 35000.00, '110101198709095678', '13800138005', '6222021234567890005'),
('孙八', '财务部', '会计', 13000.00, '110101199211116789', '13800138006', '6222021234567890006'),
('周九', '技术部', 'DBA', 30000.00, '110101198803037890', '13800138007', '6222021234567890007'),
('吴十', '人事部', '人事经理', 22000.00, '110101199405058901', '13800138008', '6222021234567890008');

-- 2. 系统操作日志表（用于审计演示）
CREATE DATABASE IF NOT EXISTS audit_db;
USE audit_db;

CREATE TABLE sys_operations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user VARCHAR(50) NOT NULL,
    action VARCHAR(20) NOT NULL,
    target_object VARCHAR(100),
    query_text TEXT,
    client_ip VARCHAR(45),
    event_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 3. 业务订单表（用于备份恢复演练）
CREATE DATABASE IF NOT EXISTS orders_db;
USE orders_db;

CREATE TABLE orders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    order_no VARCHAR(32) NOT NULL UNIQUE,
    customer_name VARCHAR(50),
    amount DECIMAL(12,2),
    status ENUM('pending','paid','shipped','completed','cancelled') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 插入一批初始订单
INSERT INTO orders (order_no, customer_name, amount, status) VALUES
('ORD-20250101-0001', '北京科技有限公司', 15600.00, 'completed'),
('ORD-20250101-0002', '上海贸易集团', 89300.50, 'shipped'),
('ORD-20250102-0003', '深圳电子科技', 23400.00, 'paid'),
('ORD-20250102-0004', '广州信息技术', 56700.00, 'pending'),
('ORD-20250103-0005', '杭州电商平台', 128000.00, 'completed');

-- 4. 验证
SELECT 'salary_db' AS db, COUNT(*) AS rows_count FROM salary_db.employees
UNION ALL
SELECT 'audit_db', COUNT(*) FROM audit_db.sys_operations
UNION ALL
SELECT 'orders_db', COUNT(*) FROM orders_db.orders;
EOF
```

✅ **验证点**：

```bash
sudo mysql -e "SHOW DATABASES;" | grep -E "salary_db|audit_db|orders_db"
# 应输出三个库名

sudo mysql -e "SELECT COUNT(*) FROM salary_db.employees;"
# 应输出 8
```

---

## 第 1 课 安全认证深度配置

### 1.1 本课要解决的问题

项目五完成了 MySQL 的基础安全加固（root 密码、匿名用户清理），但生产环境需要更深层的认证安全：**强密码策略、认证插件选择、SSL/TLS 加密连接**。

### 1.2 本课交付物

- 密码策略配置生效，弱密码被拒绝
- 宿主机 Navicat 通过 SSL 连接 MySQL，`Ssl_cipher` 非空
- 非加密连接被拒绝（可选加固）

### 1.3 密码策略深度配置

MySQL 8.0 内置 `validate_password` 组件，可强制密码复杂度。

**Step 1：安装并启用密码验证组件**

```bash
sudo mysql << 'EOF'
-- 安装密码验证组件
INSTALL COMPONENT 'file://component_validate_password';

-- 查看默认策略
SHOW VARIABLES LIKE 'validate_password%';
EOF
```

输出示例：

```
+--------------------------------------+--------+
| Variable_name                        | Value  |
+--------------------------------------+--------+
| validate_password.check_user_name    | ON     |
| validate_password.dictionary_file    |        |
| validate_password.length             | 8      |
| validate_password.mixed_case_count   | 1      |
| validate_password.number_count       | 1      |
| validate_password.policy             | MEDIUM |
| validate_password.special_char_count | 1      |
+--------------------------------------+--------+
```

**Step 2：调高密码策略为生产级别**

```bash
sudo mysql << 'EOF'
-- 设置为强策略
SET GLOBAL validate_password.policy = 'STRONG';
SET GLOBAL validate_password.length = 12;
SET GLOBAL validate_password.mixed_case_count = 2;
SET GLOBAL validate_password.number_count = 2;
SET GLOBAL validate_password.special_char_count = 2;

-- 持久化到配置文件
-- 注意：MySQL 8.0.28+ 支持 SET PERSIST
SET PERSIST validate_password.policy = 'STRONG';
SET PERSIST validate_password.length = 12;
SET PERSIST validate_password.mixed_case_count = 2;
SET PERSIST validate_password.number_count = 2;
SET PERSIST validate_password.special_char_count = 2;

-- 验证
SHOW VARIABLES LIKE 'validate_password%';
EOF
```

**Step 3：验证弱密码被拒绝**

```bash
sudo mysql << 'EOF'
-- 尝试创建弱密码用户（应失败）
CREATE USER 'weak_test'@'localhost' IDENTIFIED BY '123456';
EOF
```

预期报错：

```
ERROR 1819 (HY000): Your password does not satisfy the current policy requirements
```

```bash
sudo mysql << 'EOF'
-- 使用合规密码（应成功）
CREATE USER 'weak_test'@'localhost' IDENTIFIED BY 'Str0ng!Pass#2025';
SELECT User, Host FROM mysql.user WHERE User='weak_test';

-- 清理测试用户
DROP USER 'weak_test'@'localhost';
EOF
```

✅ **验证点**：弱密码创建失败，合规密码创建成功

⚠️ **注意**：`SET PERSIST` 会将配置写入 `/var/lib/mysql/mysqld-auto.cnf`，优先级高于 `mysqld.cnf`。如需回退，执行 `RESET PERSIST` 或手动删除该文件后重启。

### 1.4 认证插件对比与配置

MySQL 8.0 默认使用 `caching_sha2_password`，与旧版 `mysql_native_password` 有本质区别。

**背景知识**

| 特性 | mysql_native_password | caching_sha2_password |
|------|----------------------|----------------------|
| 哈希算法 | SHA-1 | SHA-256 + Salt |
| 安全性 | 低（SHA-1 已被攻破） | 高（抗彩虹表/碰撞） |
| 缓存 | 无 | 内存缓存已认证的哈希 |
| 连接要求 | 明文或 SSL 均可 | 首次必须 SSL 或 RSA 密钥交换 |
| 兼容性 | 旧客户端均可 | 需 MySQL 8.0+ 连接器 |

**Step 1：查看当前用户认证插件**

```bash
sudo mysql -e "SELECT User, Host, plugin FROM mysql.user ORDER BY User;"
```

输出示例：

```
+------------------+-----------+-----------------------+
| User             | Host      | plugin                |
+------------------+-----------+-----------------------+
| app              | 192.168.% | caching_sha2_password |
| mysql.sys        | localhost | mysql_native_password |
| root             | localhost | auth_socket           |
+------------------+-----------+-----------------------+
```

⚠️ Ubuntu 下 root 默认使用 `auth_socket`（仅允许系统 root 用户免密登录）。生产环境应改为密码认证。

**Step 2：为 root 设置密码认证**

```bash
sudo mysql << 'EOF'
-- 将 root 改为密码认证（使用强密码）
ALTER USER 'root'@'localhost' IDENTIFIED WITH caching_sha2_password BY 'R00t!Secure#2025';

-- 刷新权限
FLUSH PRIVILEGES;

-- 验证
SELECT User, Host, plugin FROM mysql.user WHERE User='root';
EOF
```

**Step 3：用密码登录验证**

```bash
mysql -u root -p'R00t!Secure#2025' -e "SELECT 'password auth OK' AS status;"
```

✅ **验证点**：root 的 plugin 变为 `caching_sha2_password`，密码方式登录成功

**Step 4：（可选）为旧应用兼容降级特定用户**

```bash
sudo mysql << 'EOF'
-- 仅对需要兼容的旧应用用户降级
CREATE USER 'legacy_app'@'192.168.100.%' IDENTIFIED WITH mysql_native_password BY 'Legacy!App#2025';
GRANT SELECT ON salary_db.employees TO 'legacy_app'@'192.168.100.%';
FLUSH PRIVILEGES;

-- 验证
SELECT User, Host, plugin FROM mysql.user WHERE User='legacy_app';
EOF
```

⚠️ **安全建议**：仅对必须兼容的旧应用使用 `mysql_native_password`，其他用户一律使用 `caching_sha2_password`。

### 1.5 SSL/TLS 加密连接配置

默认 MySQL 安装已自动生成 SSL 证书，但需要验证和强制使用。

**Step 1：检查 MySQL SSL 状态**

```bash
sudo mysql -e "SHOW VARIABLES LIKE '%ssl%';"
```

输出示例：

```
+--------------------+--------------------------------+
| Variable_name      | Value                          |
+--------------------+--------------------------------+
| have_ssl           | YES                            |
| ssl_ca             | /var/lib/mysql/ca.pem          |
| ssl_capath         |                                |
| ssl_cert           | /var/lib/mysql/server-cert.pem |
| ssl_cipher         |                                |
| ssl_crl            |                                |
| ssl_crlpath        |                                |
| ssl_key            | /var/lib/mysql/server-key.pem  |
+--------------------+--------------------------------+
```

`have_ssl = YES` 表示 SSL 已启用。

**Step 2：验证当前连接是否加密**

```bash
sudo mysql -e "SHOW STATUS LIKE 'Ssl_cipher';"
```

若通过 `sudo mysql`（auth_socket）连接，`Ssl_cipher` 可能为空（本地 socket 不走 SSL）。

**Step 3：使用 SSL 远程连接测试**

```bash
# 在 VM-1 上，用密码 + SSL 连接
mysql -u root -p'R00t!Secure#2025' \
  --ssl-mode=REQUIRED \
  -e "SHOW STATUS LIKE 'Ssl_cipher';"
```

预期输出：

```
+---------------+----------------------------------------+
| Variable_name | Value                                  |
+---------------+----------------------------------------+
| Ssl_cipher    | TLS_AES_256_GCM_SHA384                 |
+---------------+----------------------------------------+
```

`Ssl_cipher` 非空 = 连接已加密。

**Step 4：生成自定义 CA 证书（生产推荐）**

MySQL 自签证书安全性有限，生产环境应使用自建 CA 或商业证书：

```bash
cd /opt/mysql-lab06/ssl

# 1. 生成 CA 私钥和证书
openssl genrsa -out ca-key.pem 2048
openssl req -new -x509 -nodes -days 3650 \
  -key ca-key.pem \
  -out ca.pem \
  -subj "/CN=MySQL-CA/O=Lab06/C=CN"

# 2. 生成服务端私钥和证书
openssl genrsa -out server-key.pem 2048
openssl req -new -nodes \
  -key server-key.pem \
  -out server-req.pem \
  -subj "/CN=mysql-master/O=Lab06/C=CN"

openssl x509 -req -days 3650 \
  -CA ca.pem -CAkey ca-key.pem \
  -set_serial 01 \
  -in server-req.pem \
  -out server-cert.pem

# 3. 生成客户端私钥和证书
openssl genrsa -out client-key.pem 2048
openssl req -new -nodes \
  -key client-key.pem \
  -out client-req.pem \
  -subj "/CN=mysql-client/O=Lab06/C=CN"

openssl x509 -req -days 3650 \
  -CA ca.pem -CAkey ca-key.pem \
  -set_serial 02 \
  -in client-req.pem \
  -out client-cert.pem

# 4. 设置权限
chmod 600 *-key.pem
chmod 644 *.pem
ls -la /opt/mysql-lab06/ssl/
```

**Step 5：配置 MySQL 使用自定义证书**

```bash
sudo tee -a /etc/mysql/mysql.conf.d/mysqld.cnf << 'EOF'

# SSL Configuration (Lab06)
[mysqld]
ssl-ca=/opt/mysql-lab06/ssl/ca.pem
ssl-cert=/opt/mysql-lab06/ssl/server-cert.pem
ssl-key=/opt/mysql-lab06/ssl/server-key.pem
EOF

sudo systemctl restart mysql
```

验证：

```bash
sudo mysql -e "SHOW VARIABLES LIKE '%ssl%';"
# ssl_ca / ssl_cert / ssl_key 应指向 /opt/mysql-lab06/ssl/ 下的文件
```

**Step 6：宿主机 Navicat 通过 SSL 连接**

1. 将以下三个文件从 VM 复制到宿主机：
   - `/opt/mysql-lab06/ssl/ca.pem`
   - `/opt/mysql-lab06/ssl/client-cert.pem`
   - `/opt/mysql-lab06/ssl/client-key.pem`

2. 在 Navicat 连接属性中：
   - **SSL** 选项卡 → 勾选「使用 SSL」
   - CA 证书 → 选择 `ca.pem`
   - 客户端证书 → 选择 `client-cert.pem`
   - 客户端密钥 → 选择 `client-key.pem`
   - SSL 模式 → 选择 `REQUIRED` 或 `VERIFY_CA`

3. 连接后执行：

```sql
SHOW STATUS LIKE 'Ssl_cipher';
-- 应返回非空值，如 TLS_AES_256_GCM_SHA384

SHOW STATUS LIKE 'Ssl_version';
-- 应返回 TLSv1.3 或 TLSv1.2
```

✅ **验证点**：宿主机通过 SSL 连接成功，`Ssl_cipher` 和 `Ssl_version` 非空

**Step 7：（可选）强制所有远程连接必须使用 SSL**

```bash
sudo mysql << 'EOF'
-- 对已有用户强制 SSL
ALTER USER 'app'@'192.168.100.%' REQUIRE SSL;
ALTER USER 'root'@'localhost' REQUIRE SSL;

FLUSH PRIVILEGES;

-- 验证
SELECT User, Host, ssl_type FROM mysql.user WHERE User IN ('app','root');
EOF
```

⚠️ **注意**：`REQUIRE SSL` 后，非 SSL 连接将被拒绝。确保所有客户端都支持 SSL 再启用。

### 1.6 本课小结

| 认证层面 | 项目五（基础） | 项目六（高级） |
|----------|---------------|---------------|
| 密码策略 | 默认或无 | STRONG 策略 + 12 位长度 |
| 认证插件 | 默认不改 | root 改为 caching_sha2_password |
| 传输加密 | 无 | SSL/TLS + 自定义 CA 证书 |
| 连接控制 | 基本防火墙 | REQUIRE SSL 强制加密 |

---

## 第 2 课 数据库访问控制与审计

### 2.1 本课要解决的问题

项目五实现了「最小权限原则」的库级/表级授权，但生产环境需要更细粒度的控制：**列级权限、角色管理（RBAC）、以及完整的安全审计链路**。

### 2.2 本课交付物

- HR 用户只能看到员工的姓名和部门，无法查看薪资和身份证号
- 角色体系 `role_hr` / `role_finance` / `role_dev` 创建并分配完成
- MariaDB Audit Plugin 产生审计日志，完成一次安全事件溯源

### 2.3 列级权限控制

**场景**：salary_db.employees 表包含敏感字段（salary、id_card、phone、bank_account），不同岗位只能看到对应字段。

**Step 1：创建不同角色用户**

```bash
sudo mysql << 'EOF'
-- HR 专员：只能看姓名、部门、职位
CREATE USER 'hr_user'@'192.168.100.%' IDENTIFIED BY 'Hr!Secure#2025';

-- 财务人员：能看姓名、部门、薪资
CREATE USER 'finance_user'@'192.168.100.%' IDENTIFIED BY 'Fin!Secure#2025';

-- 开发人员：只能看非敏感字段
CREATE USER 'dev_user'@'192.168.100.%' IDENTIFIED BY 'Dev!Secure#2025';

FLUSH PRIVILEGES;
EOF
```

**Step 2：授予列级权限**

```bash
sudo mysql << 'EOF'
-- HR：只能查看姓名、部门、职位、手机号（脱敏后）
GRANT SELECT (id, name, department, position, phone) 
  ON salary_db.employees TO 'hr_user'@'192.168.100.%';

-- 财务：能查看薪资相关字段
GRANT SELECT (id, name, department, salary, bank_account)
  ON salary_db.employees TO 'finance_user'@'192.168.100.%';

-- 开发：只能查看基础信息
GRANT SELECT (id, name, department, position)
  ON salary_db.employees TO 'dev_user'@'192.168.100.%';

FLUSH PRIVILEGES;

-- 验证权限
SHOW GRANTS FOR 'hr_user'@'192.168.100.%';
SHOW GRANTS FOR 'finance_user'@'192.168.100.%';
SHOW GRANTS FOR 'dev_user'@'192.168.100.%';
EOF
```

**Step 3：验证列级权限生效**

```bash
# HR 用户尝试查看薪资（应失败）
mysql -u hr_user -p'Hr!Secure#2025' -h 192.168.100.20 \
  -e "SELECT name, salary FROM salary_db.employees;" 2>&1

# 预期报错：
# ERROR 1143 (42000): SELECT command denied to user 'hr_user'@'...' for column 'salary' in table 'employees'

# HR 用户查看允许的字段（应成功）
mysql -u hr_user -p'Hr!Secure#2025' -h 192.168.100.20 \
  -e "SELECT id, name, department, position FROM salary_db.employees;"

# 财务用户查看薪资（应成功）
mysql -u finance_user -p'Fin!Secure#2025' -h 192.168.100.20 \
  -e "SELECT name, salary FROM salary_db.employees;"

# 开发用户尝试查看身份证号（应失败）
mysql -u dev_user -p'Dev!Secure#2025' -h 192.168.100.20 \
  -e "SELECT name, id_card FROM salary_db.employees;" 2>&1
```

✅ **验证点**：各用户只能访问被授权的列，越权访问被拒绝

### 2.4 RBAC 角色管理实战

MySQL 8.0 原生支持角色（Role），可以批量管理权限。

**Step 1：创建角色**

```bash
sudo mysql << 'EOF'
-- 创建角色
CREATE ROLE 'role_hr';
CREATE ROLE 'role_finance';
CREATE ROLE 'role_dev';
CREATE ROLE 'role_dba';
EOF
```

**Step 2：为角色授权**

```bash
sudo mysql << 'EOF'
-- HR 角色：查看员工基本信息
GRANT SELECT (id, name, department, position, phone) 
  ON salary_db.employees TO 'role_hr';

-- 财务角色：查看薪资信息 + 订单信息
GRANT SELECT (id, name, department, salary, bank_account) 
  ON salary_db.employees TO 'role_finance';
GRANT SELECT ON orders_db.* TO 'role_finance';

-- 开发角色：查看基础信息 + 审计日志（只读）
GRANT SELECT (id, name, department, position)
  ON salary_db.employees TO 'role_dev';
GRANT SELECT ON audit_db.* TO 'role_dev';

-- DBA 角色：全部权限
GRANT ALL PRIVILEGES ON *.* TO 'role_dba' WITH GRANT OPTION;

FLUSH PRIVILEGES;
EOF
```

**Step 3：将角色分配给用户**

```bash
sudo mysql << 'EOF'
-- 将角色绑定到用户
GRANT 'role_hr' TO 'hr_user'@'192.168.100.%';
GRANT 'role_finance' TO 'finance_user'@'192.168.100.%';
GRANT 'role_dev' TO 'dev_user'@'192.168.100.%';

-- 设置用户默认激活的角色
ALTER USER 'hr_user'@'192.168.100.%' DEFAULT ROLE 'role_hr';
ALTER USER 'finance_user'@'192.168.100.%' DEFAULT ROLE 'role_finance';
ALTER USER 'dev_user'@'192.168.100.%' DEFAULT ROLE 'role_dev';

FLUSH PRIVILEGES;

-- 验证角色分配
SELECT User, Host, Role_from_user AS Assigned_Roles FROM mysql.role_edges;
EOF
```

**Step 4：验证角色生效**

```bash
# 登录 hr_user，查看当前激活的角色
mysql -u hr_user -p'Hr!Secure#2025' -h 192.168.100.20 \
  -e "SELECT CURRENT_ROLE();"
# 预期输出：role_hr@%

# 查看该角色下的权限
mysql -u hr_user -p'Hr!Secure#2025' -h 192.168.100.20 \
  -e "SHOW GRANTS FOR CURRENT_USER();"
```

💡 **实操：动态切换角色**

```bash
sudo mysql << 'EOF'
-- 给 dev_user 同时分配 dev 和 hr 角色
GRANT 'role_hr' TO 'dev_user'@'192.168.100.%';
ALTER USER 'dev_user'@'192.168.100.%' DEFAULT ROLE 'role_dev';
FLUSH PRIVILEGES;
EOF

# dev_user 登录后可手动激活 hr 角色
mysql -u dev_user -p'Dev!Secure#2025' -h 192.168.100.20 << 'EOF'
SELECT CURRENT_ROLE();
-- 默认只有 role_dev

SET ROLE 'role_hr';
SELECT CURRENT_ROLE();
-- 切换为 role_hr，拥有 HR 的列级权限

SET ROLE 'role_dev','role_hr';
SELECT CURRENT_ROLE();
-- 同时拥有两个角色的权限

SET ROLE NONE;
SELECT CURRENT_ROLE();
-- 临时取消所有角色
EOF
```

✅ **验证点**：角色权限正确分配，`CURRENT_ROLE()` 返回预期值，角色切换生效

### 2.5 企业级审计：MariaDB Audit Plugin

MySQL 社区版不自带审计插件，MariaDB Audit Plugin 兼容 MySQL 8.0，可记录所有 DDL/DML/DCL 操作。

**Step 1：下载审计插件**

```bash
# 从 MariaDB 仓库获取插件 .so 文件
cd /opt/mysql-lab06/audit

# 方法一：从 MariaDB 安装包中提取
sudo apt install -y mariadb-server-core-10.11 2>/dev/null || true

# 查找插件文件
find /usr/lib -name "server_audit.so" 2>/dev/null
find /usr/lib -name "ha_connect.so" 2>/dev/null

# 如果 apt 安装失败，手动下载
wget -q "https://deb.mariadb.org/10.11/ubuntu/pool/main/m/mariadb/mariadb-server-core-10.11_10.11.11-mariadb~noble_amd64.deb" -O mariadb-server-core.deb 2>/dev/null || true

# 提取 server_audit.so
if [ -f mariadb-server-core.deb ]; then
  dpkg-deb -x mariadb-server-core.deb /tmp/mariadb-extract/
  find /tmp/mariadb-extract/ -name "server_audit.so" -exec cp {} /opt/mysql-lab06/audit/ \;
fi

# 方法二（备选）：直接从 GitHub 获取
# 注意：需确认版本兼容性
if [ ! -f /opt/mysql-lab06/audit/server_audit.so ]; then
  echo "⚠️ 自动下载失败，请手动操作："
  echo "1. 从一台 MariaDB 服务器上复制 /usr/lib/mysql/plugin/server_audit.so"
  echo "2. 放到 /opt/mysql-lab06/audit/server_audit.so"
  echo "3. 或从 https://mariadb.com/kb/en/mariadb-audit-plugin-options/ 下载"
fi
```

⚠️ **注意**：MariaDB Audit Plugin 的 MySQL 兼容版本号需与 MySQL 8.0 匹配。如果上述方法获取失败，可从已有的 MariaDB 服务器上复制 `server_audit.so` 文件。

**Step 2：安装审计插件**

```bash
# 将插件文件复制到 MySQL 插件目录
MYSQL_PLUGIN_DIR=$(sudo mysql -e "SHOW VARIABLES LIKE 'plugin_dir%';" -N -s | awk '{print $2}')
echo "MySQL plugin directory: $MYSQL_PLUGIN_DIR"

sudo cp /opt/mysql-lab06/audit/server_audit.so "$MYSQL_PLUGIN_DIR/"
sudo chmod 755 "$MYSQL_PLUGIN_DIR/server_audit.so"
sudo chown root:root "$MYSQL_PLUGIN_DIR/server_audit.so"

# 在 MySQL 中安装插件
sudo mysql << 'EOF'
INSTALL PLUGIN server_audit SONAME 'server_audit.so';

-- 验证安装
SELECT PLUGIN_NAME, PLUGIN_STATUS FROM INFORMATION_SCHEMA.PLUGINS 
  WHERE PLUGIN_NAME LIKE '%audit%';
EOF
```

预期输出：

```
+-------------+---------------+
| PLUGIN_NAME | PLUGIN_STATUS |
+-------------+---------------+
| server_audit | ACTIVE       |
+-------------+---------------+
```

**Step 3：配置审计策略**

```bash
sudo mysql << 'EOF'
-- 审计内容：连接事件 + 查询事件 + 表事件
SET GLOBAL server_audit_events = 'CONNECT,QUERY,TABLE';

-- 审计日志路径
SET GLOBAL server_audit_file_path = '/opt/mysql-lab06/audit/server_audit.log';

-- 审计日志轮转大小（100MB）
SET GLOBAL server_audit_file_rotate_size = 104857600;

-- 审计日志轮转数量
SET GLOBAL server_audit_file_rotations = 9;

-- 强制审计（包括拥有 SUPER 权限的用户）
SET GLOBAL server_audit_incl_users = '';

-- 排除特定用户（可选，如监控账号）
SET GLOBAL server_audit_excl_users = 'monitor_user';

-- 启用审计
SET GLOBAL server_audit_logging = ON;

-- 验证配置
SHOW VARIABLES LIKE 'server_audit%';
EOF
```

**Step 4：持久化审计配置**

```bash
sudo tee -a /etc/mysql/mysql.conf.d/mysqld.cnf << 'EOF'

# Audit Configuration (Lab06)
[mysqld]
server_audit_events=CONNECT,QUERY,TABLE
server_audit_file_path=/opt/mysql-lab06/audit/server_audit.log
server_audit_file_rotate_size=104857600
server_audit_file_rotations=9
server_audit_logging=ON
EOF

sudo systemctl restart mysql

# 确认审计恢复运行
sudo mysql -e "SHOW VARIABLES LIKE 'server_audit_logging';"
# Value 应为 ON
```

**Step 5：产生审计日志并分析**

```bash
# 模拟正常操作
mysql -u hr_user -p'Hr!Secure#2025' -h 192.168.100.20 \
  -e "SELECT name, department FROM salary_db.employees LIMIT 3;"

# 模拟越权尝试
mysql -u dev_user -p'Dev!Secure#2025' -h 192.168.100.20 \
  -e "SELECT salary FROM salary_db.employees;" 2>/dev/null || true

# 模拟可疑操作
mysql -u root -p'R00t!Secure#2025' \
  -e "DROP DATABASE IF EXISTS test_suspicious;"

# 查看审计日志
sudo tail -20 /opt/mysql-lab06/audit/server_audit.log
```

审计日志格式示例：

```
20250615 10:30:15,mysql-master,hr_user,192.168.100.1,5,0,CONNECT,,,0
20250615 10:30:15,mysql-master,hr_user,192.168.100.1,5,27,QUERY,,'SELECT name, department FROM salary_db.employees LIMIT 3'
20250615 10:30:16,mysql-master,dev_user,192.168.100.1,6,0,CONNECT,,,0
20250615 10:30:16,mysql-master,dev_user,192.168.100.1,6,28,QUERY,,'SELECT salary FROM salary_db.employees'
20250615 10:30:17,mysql-master,root,localhost,7,0,CONNECT,,,0
20250615 10:30:17,mysql-master,root,localhost,7,29,QUERY,,'DROP DATABASE IF EXISTS test_suspicious'
```

**Step 6：安全事件溯源演练**

💡 **场景**：发现 finance_user 在凌晨 3 点异常访问了 salary_db，需要追踪其操作。

```bash
# 1. 按用户过滤
sudo grep "finance_user" /opt/mysql-lab06/audit/server_audit.log | head -10

# 2. 按时间范围过滤（凌晨 2:00-5:00）
sudo grep "finance_user" /opt/mysql-lab06/audit/server_audit.log | \
  awk -F',' '{print $1}' | sort -u

# 3. 提取所有 QUERY 事件
sudo grep "finance_user" /opt/mysql-lab06/audit/server_audit.log | \
  grep "QUERY" | awk -F',' '{print $9}'

# 4. 生成审计报告
sudo bash -c 'cat > /opt/mysql-lab06/scripts/audit_report.sh << "SCRIPT"
#!/bin/bash
# 审计报告生成脚本
LOG_FILE="/opt/mysql-lab06/audit/server_audit.log"
REPORT_FILE="/opt/mysql-lab06/audit/report_$(date +%Y%m%d_%H%M%S).txt"

echo "===== MySQL 安全审计报告 =====" > "$REPORT_FILE"
echo "生成时间: $(date)" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

echo "--- 登录统计（按用户） ---" >> "$REPORT_FILE"
grep "CONNECT" "$LOG_FILE" | awk -F"," "{print \$3}" | sort | uniq -c | sort -rn >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

echo "--- 失败登录 ---" >> "$REPORT_FILE"
grep "CONNECT" "$LOG_FILE" | grep ",1," >> "$REPORT_FILE" 2>/dev/null || echo "无失败登录" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

echo "--- DDL 操作 ---" >> "$REPORT_FILE"
grep "QUERY" "$LOG_FILE" | grep -iE "DROP|ALTER|CREATE|TRUNCATE|RENAME" | awk -F"," "{print \$1, \$3, \$9}" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

echo "--- 敏感表访问 ---" >> "$REPORT_FILE"
grep "salary_db.employees" "$LOG_FILE" | awk -F"," "{print \$1, \$3, \$9}" >> "$REPORT_FILE"

echo "" >> "$REPORT_FILE"
echo "报告已生成: $REPORT_FILE"
SCRIPT
chmod +x /opt/mysql-lab06/scripts/audit_report.sh'
```

✅ **验证点**：审计日志包含 CONNECT/QUERY/TABLE 事件，能按用户/时间/操作类型溯源

### 2.6 本课小结

| 控制层面 | 项目五（基础） | 项目六（高级） |
|----------|---------------|---------------|
| 权限粒度 | 库级/表级 | 列级 + 存储过程级 |
| 权限管理 | 逐用户授权 | RBAC 角色批量管理 |
| 审计能力 | 通用查询日志 | 专业审计插件 + 事件溯源 |
| 日志分析 | 手动 grep | 自动化审计报告脚本 |

---

## 第 3 课 数据加密与安全传输

### 3.1 本课要解决的问题

项目五保障了「谁能访问」，项目六第 1 课保障了「传输过程加密」，但数据落盘后仍为明文。如果攻击者直接拷走 `.ibd` 文件，数据即泄露。本课解决 **「拿走也读不了」** 的问题。

### 3.2 本课交付物

- `salary_db` 启用透明数据加密（TDE），`.ibd` 文件无法被直接读取
- 应用层 AES-256 加密函数可用，写入和读取正确
- 动态数据脱敏视图生效，身份证号/手机号显示为掩码

### 3.3 透明数据加密（TDE）

MySQL 8.0 企业版支持 TDE，社区版需要借助 Keyring 插件实现类似功能。

**Step 1：启用 Keyring 文件插件**

```bash
# 提前创建 keyring 文件目录
sudo mkdir -p /opt/mysql-lab06/keyring
sudo chown mysql:mysql /opt/mysql-lab06/keyring

# 在 MySQL 配置中添加 keyring 插件（必须放在 [mysqld] 最早位置）
sudo sed -i '/^\[mysqld\]/a\early-plugin-load=keyring_file.so\nkeyring_file_data=/opt/mysql-lab06/keyring/keyring' /etc/mysql/mysql.conf.d/mysqld.cnf

sudo systemctl restart mysql

# 验证 keyring 插件已加载
sudo mysql -e "SELECT PLUGIN_NAME, PLUGIN_STATUS FROM INFORMATION_SCHEMA.PLUGINS WHERE PLUGIN_NAME='keyring_file';"
```

预期输出：

```
+--------------+---------------+
| PLUGIN_NAME  | PLUGIN_STATUS |
+--------------+---------------+
| keyring_file | ACTIVE        |
+--------------+---------------+
```

**Step 2：创建加密表空间**

```bash
sudo mysql << 'EOF'
-- 查看当前加密设置
SHOW VARIABLES LIKE 'table_encryption_privilege_check';

-- 创建使用加密的表
USE salary_db;

-- 方式一：在 CREATE TABLE 时指定加密
CREATE TABLE employees_encrypted (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL,
    salary DECIMAL(10,2) NOT NULL,
    id_card VARCHAR(18) NOT NULL,
    bank_account VARCHAR(30) NOT NULL,
    ENCRYPTION='Y'
) ENGINE=InnoDB ENCRYPTION='Y';

-- 从原表导入数据
INSERT INTO employees_encrypted (name, salary, id_card, bank_account)
SELECT name, salary, id_card, bank_account FROM employees;

-- 验证加密状态
SELECT TABLE_NAME, TABLE_SCHEMA, ENCRYPTION 
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_SCHEMA='salary_db' AND ENCRYPTION='Y';
EOF
```

**Step 3：验证加密文件无法直接读取**

```bash
# 查找加密表的 .ibd 文件
sudo find /var/lib/mysql/salary_db/ -name "employees*.ibd" -ls

# 对比：未加密表 vs 加密表
echo "=== 未加密表（可读明文）==="
sudo strings /var/lib/mysql/salary_db/employees.ibd | grep -E "张三|李四|110101" | head -5

echo "=== 加密表（应无法读到明文）==="
sudo strings /var/lib/mysql/salary_db/employees_encrypted.ibd | grep -E "张三|李四|110101" | head -5
# 加密表的 .ibd 文件中不应包含可读的姓名或身份证号
```

✅ **验证点**：加密表的 `.ibd` 文件中无法通过 `strings` 命令读取到明文数据

**Step 4：全局启用表加密（默认所有新建表加密）**

```bash
sudo mysql << 'EOF'
-- 设置默认表加密
SET GLOBAL default_table_encryption = ON;
SET PERSIST default_table_encryption = ON;

-- 验证
SHOW VARIABLES LIKE 'default_table_encryption';
EOF
```

⚠️ **注意**：Keyring 文件方式仅适用于开发/测试环境。生产环境应使用 `keyring_okv`（Oracle Key Vault）或 `keyring_hashicorp`（HashiCorp Vault）进行密钥管理。

### 3.4 应用层加密

即使没有 TDE，也可以在 SQL 层面对敏感字段加密。

**Step 1：创建 AES 加密/解密函数封装**

```bash
sudo mysql << 'EOF'
USE salary_db;

-- 创建加密存储过程：加密银行卡号
DELIMITER //
CREATE PROCEDURE sp_encrypt_bank_account(
    IN p_id INT,
    IN p_key VARCHAR(64)
)
BEGIN
    UPDATE employees 
    SET bank_account = TO_BASE64(AES_ENCRYPT(bank_account, p_key))
    WHERE id = p_id;
END //
DELIMITER ;

-- 创建解密存储过程
DELIMITER //
CREATE PROCEDURE sp_decrypt_bank_account(
    IN p_id INT,
    IN p_key VARCHAR(64)
)
BEGIN
    SELECT id, name, 
        CAST(AES_DECRYPT(FROM_BASE64(bank_account), p_key) AS CHAR) AS bank_account_decrypted
    FROM employees 
    WHERE id = p_id;
END //
DELIMITER ;
EOF
```

**Step 2：使用加密函数**

```bash
sudo mysql << 'EOF'
USE salary_db;

-- 定义加密密钥（32 字节 = AES-256）
SET @enc_key = 'ThisIsA32ByteKeyForAES256Encrypt!';

-- 先备份原始数据
CREATE TABLE employees_backup AS SELECT * FROM employees;

-- 加密所有银行卡号
UPDATE employees 
SET bank_account = TO_BASE64(AES_ENCRYPT(bank_account, @enc_key));

-- 查看加密后的数据（密文）
SELECT id, name, LEFT(bank_account, 20) AS encrypted_bank FROM employees LIMIT 3;

-- 解密查看
SELECT id, name, 
    CAST(AES_DECRYPT(FROM_BASE64(bank_account), @enc_key) AS CHAR) AS bank_account_plain
FROM employees LIMIT 3;

-- 恢复原始数据（用于后续实验）
DROP TABLE employees;
RENAME TABLE employees_backup TO employees;
EOF
```

✅ **验证点**：加密后 `bank_account` 字段为 Base64 密文，解密后能还原为明文

### 3.5 数据脱敏

在查询层面隐藏敏感数据，适用于开发/测试/报表场景。

**Step 1：创建脱敏视图**

```bash
sudo mysql << 'EOF'
USE salary_db;

-- 身份证号脱敏：110101199001011234 → 110101****1234
CREATE OR REPLACE VIEW v_employees_masked AS
SELECT 
    id,
    name,
    department,
    position,
    salary,
    -- 身份证号脱敏：保留前6位和后4位
    CONCAT(LEFT(id_card, 6), '****', RIGHT(id_card, 4)) AS id_card_masked,
    -- 手机号脱敏：保留前3位和后4位
    CONCAT(LEFT(phone, 3), '****', RIGHT(phone, 4)) AS phone_masked,
    -- 银行卡号脱敏：保留后4位
    CONCAT('****', RIGHT(bank_account, 4)) AS bank_account_masked,
    created_at
FROM employees;

-- 验证脱敏效果
SELECT id, name, id_card_masked, phone_masked, bank_account_masked 
FROM v_employees_masked LIMIT 5;
EOF
```

预期输出：

```
+----+------+-------------------+---------------+---------------------+
| id | name | id_card_masked    | phone_masked  | bank_account_masked |
+----+------+-------------------+---------------+---------------------+
|  1 | 张三 | 110101****1234   | 138****8001   | ****0001            |
|  2 | 李四 | 110101****2345   | 138****8002   | ****0002            |
+----+------+-------------------+---------------+---------------------+
```

**Step 2：为不同角色分配脱敏视图权限**

```bash
sudo mysql << 'EOF'
-- HR 用户只能访问脱敏视图
REVOKE SELECT ON salary_db.employees FROM 'hr_user'@'192.168.100.%';
GRANT SELECT ON salary_db.v_employees_masked TO 'hr_user'@'192.168.100.%';

-- 开发用户也只能访问脱敏视图
REVOKE SELECT (id, name, department, position) ON salary_db.employees FROM 'dev_user'@'192.168.100.%';
GRANT SELECT ON salary_db.v_employees_masked TO 'dev_user'@'192.168.100.%';

FLUSH PRIVILEGES;
EOF
```

**Step 3：验证脱敏权限**

```bash
# HR 用户查看脱敏视图
mysql -u hr_user -p'Hr!Secure#2025' -h 192.168.100.20 \
  -e "SELECT name, id_card_masked, phone_masked FROM salary_db.v_employees_masked LIMIT 3;"

# HR 用户尝试查原表（应失败）
mysql -u hr_user -p'Hr!Secure#2025' -h 192.168.100.20 \
  -e "SELECT * FROM salary_db.employees;" 2>&1 | head -3
```

✅ **验证点**：脱敏视图正确显示掩码数据，原表直接访问被拒绝

### 3.6 本课小结

| 加密层面 | 技术手段 | 适用场景 |
|----------|---------|---------|
| 存储加密 | TDE + Keyring | 全表加密，对应用透明 |
| 字段加密 | AES_ENCRYPT/DECRYPT | 特定敏感字段加密 |
| 数据脱敏 | 视图 + 字符串函数 | 查询层面隐藏敏感数据 |

---

## 第 4 课 高级备份恢复与容灾

### 4.1 本课要解决的问题

项目五完成了 `mysqldump` 逻辑备份，但生产环境需要：**物理热备（不锁表）、增量备份、时间点恢复（PITR）、容灾架构**。

### 4.2 本课交付物

- 使用 XtraBackup 完成一次全量热备 + 增量备份
- 模拟误删数据后，通过 PITR 恢复到指定时间点
- 自动化备份脚本 crontab 配置完成
- VM-1 + VM-2 主从复制搭建成功，数据实时同步

### 4.3 Percona XtraBackup 物理热备

**背景知识**

| 特性 | mysqldump（项目五） | XtraBackup（项目六） |
|------|--------------------|--------------------|
| 备份方式 | 逻辑备份（SQL 语句） | 物理备份（数据文件副本） |
| 锁表 | 需要锁表（单事务可减少） | 不锁表（热备） |
| 备份速度 | 慢（逐行导出） | 快（文件拷贝） |
| 恢复速度 | 慢（逐行执行 SQL） | 快（文件拷回） |
| 增量备份 | 不支持 | 支持 |
| 适用规模 | 小型数据库 | 中大型数据库 |

**Step 1：创建备份用户**

```bash
sudo mysql << 'EOF'
-- 创建 XtraBackup 专用用户
CREATE USER 'bkpuser'@'localhost' IDENTIFIED BY 'Bkp!Secure#2025';
GRANT BACKUP_ADMIN, PROCESS, RELOAD, LOCK TABLES, REPLICATION CLIENT 
  ON *.* TO 'bkpuser'@'localhost';
GRANT SELECT ON performance_schema.log_status TO 'bkpuser'@'localhost';
GRANT SELECT ON performance_schema.key_component_account TO 'bkpuser'@'localhost';
FLUSH PRIVILEGES;
EOF
```

**Step 2：全量备份**

```bash
# 创建全量备份目录
FULL_BACKUP_DIR="/opt/mysql-lab06/backup/full_$(date +%Y%m%d_%H%M%S)"

# 执行全量备份
xtrabackup --backup \
  --user=bkpuser \
  --password='Bkp!Secure#2025' \
  --target-dir="$FULL_BACKUP_DIR" \
  2>&1 | tail -20

# 验证备份完成
echo "=== 全量备份目录 ==="
ls -la "$FULL_BACKUP_DIR/" | head -15
echo "=== 备份大小 ==="
du -sh "$FULL_BACKUP_DIR/"
```

预期输出末尾：

```
xtrabackup: Transaction log of lsn (...) to (...) was copied.
completed OK!
```

**Step 3：准备（Prepare）全量备份**

备份文件拷贝出来后处于不一致状态，需要 `--prepare` 使其可恢复：

```bash
xtrabackup --prepare \
  --target-dir="$FULL_BACKUP_DIR" \
  2>&1 | tail -10

# 应输出：completed OK!
```

✅ **验证点**：全量备份 + prepare 均输出 `completed OK!`

**Step 4：增量备份**

先在 orders_db 中插入一些新数据，模拟业务增量：

```bash
sudo mysql << 'EOF'
USE orders_db;

INSERT INTO orders (order_no, customer_name, amount, status) VALUES
('ORD-20250104-0006', '成都网络科技', 45000.00, 'paid'),
('ORD-20250104-0007', '武汉数据服务', 67800.00, 'pending'),
('ORD-20250105-0008', '南京软件开发', 32100.00, 'shipped');
EOF
```

```bash
# 基于全量备份做增量
INCR_BACKUP_DIR="/opt/mysql-lab06/backup/incr_$(date +%Y%m%d_%H%M%S)"

xtrabackup --backup \
  --user=bkpuser \
  --password='Bkp!Secure#2025' \
  --target-dir="$INCR_BACKUP_DIR" \
  --incremental-basedir="$FULL_BACKUP_DIR" \
  2>&1 | tail -10

echo "=== 增量备份大小 ==="
du -sh "$INCR_BACKUP_DIR/"
```

✅ **验证点**：增量备份大小远小于全量备份

### 4.4 时间点恢复（PITR）

💡 **场景**：运维人员在 14:30 误删了 orders_db 的全部数据，需要恢复到 14:29 的状态。

**Step 1：模拟误操作**

```bash
# 记录当前时间
date '+%Y-%m-%d %H:%M:%S'
# 例：2025-06-15 14:30:00

# 模拟误删
sudo mysql -e "DROP DATABASE orders_db;"

# 确认数据丢失
sudo mysql -e "SHOW DATABASES;" | grep orders_db
# 无输出 = 数据丢失
```

**Step 2：恢复全量备份**

```bash
# 1. 停止 MySQL
sudo systemctl stop mysql

# 2. 清空数据目录（危险操作，生产环境应先备份！）
sudo mv /var/lib/mysql /var/lib/mysql.corrupted
sudo mkdir /var/lib/mysql
sudo chown mysql:mysql /var/lib/mysql

# 3. 恢复全量备份
xtrabackup --copy-back \
  --target-dir="$FULL_BACKUP_DIR" \
  2>&1 | tail -10

# 4. 修复权限
sudo chown -R mysql:mysql /var/lib/mysql

# 5. 启动 MySQL
sudo systemctl start mysql

# 6. 验证
sudo mysql -e "SELECT COUNT(*) FROM orders_db.orders;"
# 应返回恢复时的数据行数
```

**Step 3：使用 binlog 做 PITR（精确到秒）**

全量备份只能恢复到备份时刻，之后的数据变更需要通过 binlog 重放：

```bash
# 查看全量备份结束时的 binlog 位置
cat "$FULL_BACKUP_DIR/xtrabackup_binlog_info"
# 例：binlog.000003    157

# 查看当前 binlog 文件列表
sudo ls -la /var/lib/mysql/binlog.*

# 找到误操作之前的 binlog 位置
# 方法1：按时间搜索
sudo mysqlbinlog --start-datetime="2025-06-15 14:00:00" \
  --stop-datetime="2025-06-15 14:29:59" \
  /var/lib/mysql/binlog.000003 | head -30

# 方法2：搜索 DROP DATABASE 语句确认位置
sudo grep -n "DROP DATABASE" /var/lib/mysql/binlog.* 2>/dev/null | head -5

# 重放 binlog（从备份位置到误操作之前）
sudo mysqlbinlog \
  --start-position=157 \
  --stop-datetime="2025-06-15 14:29:59" \
  /var/lib/mysql/binlog.000003 | sudo mysql

# 验证恢复结果
sudo mysql -e "SELECT COUNT(*) FROM orders_db.orders;"
```

✅ **验证点**：数据恢复到误操作前的状态，后续新增的订单也能找回

### 4.5 自动化备份脚本

```bash
sudo tee /opt/mysql-lab06/scripts/auto_backup.sh << 'SCRIPT'
#!/bin/bash
# MySQL 自动化备份脚本 (XtraBackup)
# 用法: ./auto_backup.sh [full|incr]

set -euo pipefail

BACKUP_ROOT="/opt/mysql-lab06/backup"
LOG_FILE="/opt/mysql-lab06/backup/backup.log"
BK_USER="bkpuser"
BK_PASS="Bkp!Secure#2025"
DATE=$(date +%Y%m%d_%H%M%S)

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"; }

MODE=${1:-full}

if [ "$MODE" = "full" ]; then
    TARGET_DIR="${BACKUP_ROOT}/full_${DATE}"
    log "开始全量备份: $TARGET_DIR"
    xtrabackup --backup --user="$BK_USER" --password="$BK_PASS" \
        --target-dir="$TARGET_DIR" 2>>"$LOG_FILE"
    
    log "准备全量备份..."
    xtrabackup --prepare --target-dir="$TARGET_DIR" 2>>"$LOG_FILE"
    
    # 记录最新全量备份路径（增量备份需要）
    echo "$TARGET_DIR" > "${BACKUP_ROOT}/.last_full"
    
elif [ "$MODE" = "incr" ]; then
    LAST_FULL=$(cat "${BACKUP_ROOT}/.last_full" 2>/dev/null || echo "")
    if [ -z "$LAST_FULL" ] || [ ! -d "$LAST_FULL" ]; then
        log "错误：未找到全量备份，请先执行全量备份"
        exit 1
    fi
    TARGET_DIR="${BACKUP_ROOT}/incr_${DATE}"
    log "开始增量备份 (基于: $LAST_FULL): $TARGET_DIR"
    xtrabackup --backup --user="$BK_USER" --password="$BK_PASS" \
        --target-dir="$TARGET_DIR" \
        --incremental-basedir="$LAST_FULL" 2>>"$LOG_FILE"
else
    log "未知模式: $MODE (使用 full 或 incr)"
    exit 1
fi

log "备份完成: $TARGET_DIR"

# 清理 7 天前的备份
find "$BACKUP_ROOT" -maxdepth 1 -type d -mtime +7 -name "full_*" -exec rm -rf {} \;
find "$BACKUP_ROOT" -maxdepth 1 -type d -mtime +7 -name "incr_*" -exec rm -rf {} \;
log "已清理 7 天前的旧备份"
SCRIPT

sudo chmod +x /opt/mysql-lab06/scripts/auto_backup.sh
```

**配置 crontab 定时执行**：

```bash
# 编辑 MySQL 用户的 crontab
sudo crontab -e -u root
# 添加以下内容：
# 每天凌晨 2:00 全量备份
# 0 2 * * * /opt/mysql-lab06/scripts/auto_backup.sh full >> /opt/mysql-lab06/backup/backup.log 2>&1
# 每 4 小时增量备份
# 0 */4 * * * /opt/mysql-lab06/scripts/auto_backup.sh incr >> /opt/mysql-lab06/backup/backup.log 2>&1

# 手动测试
sudo /opt/mysql-lab06/scripts/auto_backup.sh full
```

✅ **验证点**：`backup.log` 显示备份成功，备份目录生成

### 4.6 主从复制搭建

**Step 1：配置主服务器（VM-1）**

```bash
# 在 VM-1 上操作
sudo tee -a /etc/mysql/mysql.conf.d/mysqld.cnf << 'EOF'

# Replication Master Configuration (Lab06)
[mysqld]
server-id=1
log_bin=mysql-bin
binlog_format=ROW
binlog_do_db=salary_db
binlog_do_db=orders_db
binlog_do_db=audit_db
sync_binlog=1
innodb_flush_log_at_trx_commit=1
EOF

sudo systemctl restart mysql
```

```bash
# 创建复制用户
sudo mysql << 'EOF'
CREATE USER 'repl_user'@'192.168.100.%' IDENTIFIED BY 'Repl!Secure#2025';
GRANT REPLICATION SLAVE ON *.* TO 'repl_user'@'192.168.100.%';
FLUSH PRIVILEGES;

-- 查看主服务器状态
SHOW MASTER STATUS;
EOF
```

记录 `File` 和 `Position` 值，例如：

```
+------------------+----------+---------------------------+
| File             | Position | Binlog_Do_DB              |
+------------------+----------+---------------------------+
| mysql-bin.000001 |      157 | salary_db,orders_db,audit_db |
+------------------+----------+---------------------------+
```

**Step 2：配置从服务器（VM-2）**

```bash
# 在 VM-2 上操作
sudo tee -a /etc/mysql/mysql.conf.d/mysqld.cnf << 'EOF'

# Replication Slave Configuration (Lab06)
[mysqld]
server-id=2
relay_log=mysql-relay
read_only=ON
super_read_only=ON
EOF

sudo systemctl restart mysql
```

**Step 3：同步主服务器数据到从服务器**

```bash
# 在 VM-1 上用 XtraBackup 备份
xtrabackup --backup \
  --user=bkpuser \
  --password='Bkp!Secure#2025' \
  --target-dir=/tmp/master_backup \
  2>&1 | tail -5

xtrabackup --prepare \
  --target-dir=/tmp/master_backup \
  2>&1 | tail -5

# 将备份传到 VM-2
scp -r /tmp/master_backup student@192.168.100.21:/tmp/master_backup
```

```bash
# 在 VM-2 上恢复
sudo systemctl stop mysql
sudo rm -rf /var/lib/mysql/*
xtrabackup --copy-back --target-dir=/tmp/master_backup
sudo chown -R mysql:mysql /var/lib/mysql
sudo systemctl start mysql
```

**Step 4：配置复制关系**

```bash
# 在 VM-2 上操作
# 从备份中获取 binlog 位置
cat /tmp/master_backup/xtrabackup_binlog_info
# 例：mysql-bin.000001    157

sudo mysql << 'EOF'
CHANGE MASTER TO
    MASTER_HOST='192.168.100.20',
    MASTER_USER='repl_user',
    MASTER_PASSWORD='Repl!Secure#2025',
    MASTER_LOG_FILE='mysql-bin.000001',
    MASTER_LOG_POS=157,
    GET_MASTER_PUBLIC_KEY=1;

START SLAVE;
EOF
```

**Step 5：验证主从复制**

```bash
# 在 VM-2 上检查复制状态
sudo mysql -e "SHOW SLAVE STATUS\G" | grep -E "Slave_IO_Running|Slave_SQL_Running|Seconds_Behind"
```

预期输出：

```
             Slave_IO_Running: Yes
            Slave_SQL_Running: Yes
        Seconds_Behind_Master: 0
```

**Step 6：数据同步验证**

```bash
# 在 VM-1 上插入数据
sudo mysql << 'EOF'
USE orders_db;
INSERT INTO orders (order_no, customer_name, amount, status) VALUES
('ORD-20250106-0009', '天津云服务', 55600.00, 'pending');
EOF

# 在 VM-2 上查询（应能看到新数据）
sudo mysql -e "SELECT order_no, customer_name, amount FROM orders_db.orders ORDER BY id DESC LIMIT 1;"
# 应输出 ORD-20250106-0009 | 天津云服务 | 55600.00
```

✅ **验证点**：`Slave_IO_Running` 和 `Slave_SQL_Running` 均为 Yes，主库写入后从库可查

### 4.7 MHA 高可用架构（选做）

MHA（Master High Availability）可在主库宕机时自动切换到从库，实现故障自动恢复。

**Step 1：安装 MHA**

```bash
# 在 VM-1（Manager + Node）和 VM-2（Node）上安装
# 两台机器都执行：
sudo apt install -y libdbd-mysql-perl libdbi-perl libterm-readkey-perl

# 下载 MHA Node（两台都装）
wget https://github.com/yoshinorim/mha4mysql-node/releases/download/v0.58/mha4mysql-node_0.58-0.all.deb
sudo dpkg -i mha4mysql-node_0.58-0.all.deb

# 仅在 VM-1 上安装 MHA Manager
wget https://github.com/yoshinorim/mha4mysql-manager/releases/download/v0.58/mha4mysql-manager_0.58-0.all.deb
sudo dpkg -i mha4mysql-manager_0.58-0.all.deb
```

**Step 2：配置 SSH 免密登录**

```bash
# 两台 VM 都执行
ssh-keygen -t rsa -N "" -f ~/.ssh/id_rsa

# 在 VM-1 上
ssh-copy-id student@192.168.100.21

# 在 VM-2 上
ssh-copy-id student@192.168.100.20
```

**Step 3：配置 MHA**

```bash
# 在 VM-1 上创建 MHA 配置
sudo mkdir -p /etc/mha
sudo tee /etc/mha/app1.cnf << 'EOF'
[server default]
manager_workdir=/var/log/mha/app1
manager_log=/var/log/mha/app1/manager.log
user=mha_monitor
password=Mha!Monitor#2025
repl_user=repl_user
repl_password=Repl!Secure#2025
ssh_user=student

[server1]
hostname=192.168.100.20
port=3306
candidate_master=1

[server2]
hostname=192.168.100.21
port=3306
candidate_master=1
EOF
```

```bash
# 创建 MHA 监控用户
sudo mysql << 'EOF'
CREATE USER 'mha_monitor'@'192.168.100.%' IDENTIFIED BY 'Mha!Monitor#2025';
GRANT ALL PRIVILEGES ON *.* TO 'mha_monitor'@'192.168.100.%';
FLUSH PRIVILEGES;
EOF
```

**Step 4：验证 MHA 配置**

```bash
# 检查 SSH 连通性
masterha_check_ssh --conf=/etc/mha/app1.cnf

# 检查复制状态
masterha_check_repl --conf=/etc/mha/app1.cnf

# 启动 MHA Monitor（前台运行测试）
masterha_manager --conf=/etc/mha/app1.cnf
```

💡 **实操：模拟主库故障切换**

```bash
# 在 VM-1 上停止 MySQL 模拟宕机
sudo systemctl stop mysql

# 观察 MHA 日志，应自动将 VM-2 提升为新主库
tail -f /var/log/mha/app1/manager.log

# 在 VM-2 上确认已成为主库
sudo mysql -e "SHOW MASTER STATUS;"
# VM-2 应显示 read_only=OFF
```

✅ **验证点**：主库宕机后，MHA 自动将 VM-2 提升为主库

### 4.8 本课小结

| 恢复能力 | 项目五（基础） | 项目六（高级） |
|----------|---------------|---------------|
| 备份方式 | mysqldump 逻辑备份 | XtraBackup 物理热备 + 增量 |
| 恢复粒度 | 整库恢复 | 全量 + 增量 + PITR 秒级恢复 |
| 自动化 | 手动执行 | crontab 定时 + 脚本 |
| 容灾 | 无 | 主从复制 + MHA 自动切换 |

---

## 项目六总结

### 知识体系回顾

```
MySQL 高级安全维护
├── 认证安全（第 1 课）
│   ├── 密码策略 → STRONG + 12位
│   ├── 认证插件 → caching_sha2_password
│   └── SSL/TLS  → 自定义 CA + 强制加密
├── 访问控制与审计（第 2 课）
│   ├── 列级权限 → 敏感字段隔离
│   ├── RBAC     → 角色批量管理
│   └── 审计插件  → MariaDB Audit + 事件溯源
├── 数据加密（第 3 课）
│   ├── TDE      → Keyring 透明加密
│   ├── 字段加密  → AES_ENCRYPT/DECRYPT
│   └── 数据脱敏  → 视图 + 掩码
└── 备份容灾（第 4 课）
    ├── 物理热备  → XtraBackup 全量+增量
    ├── PITR     → binlog 时间点恢复
    ├── 自动化    → crontab + 备份脚本
    └── 容灾      → 主从复制 + MHA 高可用
```

### 与项目五的衔接

| 维度 | 项目五（基础） | 项目六（高级） |
|------|---------------|---------------|
| 认证 | root 密码 + 匿名用户清理 | 强密码策略 + 认证插件 + SSL |
| 授权 | 库级/表级最小权限 | 列级 + RBAC 角色 |
| 审计 | 通用查询日志 | 专业审计插件 + 溯源分析 |
| 加密 | 无 | TDE + 字段加密 + 脱敏 |
| 备份 | mysqldump | XtraBackup + PITR + 自动化 |
| 容灾 | 无 | 主从复制 + MHA |
