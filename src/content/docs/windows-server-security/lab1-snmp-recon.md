---
title: 实验一：服务器信息收集与SNMP枚举渗透
---

# 实验一：服务器信息收集与SNMP枚举渗透

# 实验一：服务器信息收集与SNMP枚举渗透

> 对应章节：项目一 走进Windows服务器
实验目标：掌握针对Windows Server的信息收集方法，包括端口扫描、服务识别、SNMP枚举等，理解信息泄露的安全风险
预计用时：90分钟（知识讲解30分钟 + 动手实验60分钟）
难度等级：⭐⭐（初级）
> 

---

# 第一部分：前置知识讲解

<aside>
📚

本部分为实验前的理论知识储备，建议在动手操作之前完整阅读。理解"为什么这样做"远比"怎样做"更重要，知识点与后续实验步骤一一对应。

</aside>

## 0. 渗透测试中的信息收集方法论

### 0.1 为什么信息收集是渗透测试的第一步？

在真实攻防场景中，**信息收集（Reconnaissance）** 往往占据渗透测试 60% 以上的时间。一个经验丰富的攻击者在尚未发送任何攻击载荷之前，就已经通过信息收集勾勒出目标的完整轮廓：

- **操作系统与版本** → 决定可利用的漏洞范围（如 MS17-010 只影响特定 Windows 版本）
- **开放端口与服务** → 决定攻击入口（445 端口意味着 SMB，3389 意味着 RDP）
- **服务版本号** → 精确匹配 CVE 漏洞库
- **运行中的进程与软件** → 发现第三方软件漏洞（如旧版 Adobe、Java）
- **网络拓扑与其他主机** → 横向移动的基础

> **核心理念**："未知攻，焉知防"——只有理解攻击者如何收集信息，才能知道该保护什么、该隐藏什么。
> 

### 0.2 信息收集的两大类型

| 类型 | 特点 | 典型技术 | 是否与目标交互 |
| --- | --- | --- | --- |
| **主动信息收集** | 直接与目标交互，会留下日志 | Nmap 扫描、SNMP 枚举、Banner 抓取 | 是 |

本实验聚焦于**主动信息收集**，在受控的实验环境中进行，不会对任何外部系统产生影响。

---

## 1. Windows 服务器基础回顾

### 1.1 Windows Server 与普通 Windows 的区别

Windows Server 并不是普通 Windows 的简单"加强版"，它在服务组件和默认配置上有本质差别：

- **默认启用更多网络服务**：SMB、RPC、WinRM 等服务默认开启，攻击面大
- **支持服务器角色（Role）**：AD 域控、DNS、DHCP、IIS、文件共享等以"角色"形式模块化安装
- **存在域环境**：一旦加入 Active Directory 域，单点失陷可能导致整域失陷
- **远程管理通道多**：RDP (3389)、WinRM (5985/5986)、SMB Admin 共享 (C$, ADMIN$)

### 1.2 服务器用途分类（与扫描结果对应）

当你扫到一台 Windows Server，可以根据开放端口快速判断它的角色：

| 开放端口组合 | 可能的服务器角色 |
| --- | --- |
| 80, 443 | Web 服务器（IIS） |
| 1433 | 数据库服务器（SQL Server） |
| 161, 162 | 网管/监控服务器（本实验重点） |

---

## 2. 网络扫描基础

### 2.1 TCP/IP协议栈回顾

网络扫描的基础是TCP/IP协议栈。扫描工具通过发送特定协议的数据包并分析响应来判断目标主机的状态。理解TCP三次握手（SYN → SYN-ACK → ACK）是理解Nmap扫描原理的前提：

```
扫描方                          目标主机
  |---- SYN（我要连接）---------->|
  |<--- SYN-ACK（同意，你呢？）----|
  |---- ACK（我也同意）---------->|
  |                              |
  |===== 连接建立，开始通信 =====|
```

**Nmap扫描类型对比**：

| 扫描类型 | 原理 | 优点 | 缺点 |
| --- | --- | --- | --- |
| `-sS`（SYN扫描） | 只发送SYN，收到SYN-ACK后发RST断开 | 快速隐蔽，不完成完整连接 | 需要root权限 |
| `-sT`（全连接扫描） | 完成完整TCP三次握手 | 无需root权限 | 易被日志记录 |
| `-sU`（UDP扫描） | 发送UDP数据包 | 能发现UDP服务 | 速度慢，准确性低 |
| `-sn`（主机发现） | 只发送ICMP或ARP请求 | 快速发现存活主机 | 无法获取端口信息 |

### 2.2 Nmap常用参数速记卡

```
# 基础扫描组合

# 快速扫描常用端口
nmap -sS -sV -A 192.168.1.20

# 全端口扫描（较慢）
nmap -p- -T4 192.168.1.20

# 只扫描常见高危端口
nmap -p 21,22,23,80,135,139,443,445,3389 192.168.1.20
```

**参数逐个拆解**：

- `-sS`：SYN 半开扫描（默认且推荐）
- `-sV`：探测服务版本，对应发送 Nmap 探针并匹配指纹
- `-A`：Aggressive 模式，等价于 `-sV -O --script=default --traceroute`
- `-p-`：扫描全部 65535 个端口（区别于默认的前 1000 个）
- `-T0` ~ `-T5`：扫描速度，T4 是实验环境常用，T0/T1 用于隐蔽扫描
- `-Pn`：跳过主机存活检测，直接扫端口（目标禁 ping 时必用）

### 2.3 扫描的三层递进思路

```
第一层：发现存活主机    →  -sn（快速，只判断是否在线）
第二层：发现开放端口    →  -sS / -sT / -sU
第三层：识别服务与版本  →  -sV / -A / --script
```

理解这个递进关系，你就能根据实验目标选择合适的扫描深度，而不是一股脑 `nmap -A -p-`。

---

## 3. SNMP 协议精讲

### 3.1 SNMP 是什么？

**SNMP（Simple Network Management Protocol，简单网络管理协议）** 是一个由 IETF 制定的、基于 UDP 的应用层协议，用于在 IP 网络中管理和监控网络设备、服务器、应用程序等实体的状态与性能。

一句话概括：**SNMP 就是心电图之于病人的作用——给网络设备做连续体检。**

**核心特点**：

- **端口**：代理端监听 UDP **161**（接收查询），管理站监听 UDP **162**（接收 Trap 告警）
- **传输层**：使用 UDP（不是 TCP），无连接、开销低，即使失包也不会阻塞被监控设备
- **协议模型**："管理站 + 代理"（Manager-Agent）的 C/S 模型
- **数据组织**：所有可管理变量都被组织在一个名为 **MIB** 的树形数据库中，每个变量有唯一的 **OID**

**版本演进历史**：

| 版本 | 发布年份 | 核心特点 | 安全性 |
| --- | --- | --- | --- |
| SNMPv1 | 1988 | 最早版本，定义 Get/Set/Trap 基础操作 | 极差（明文团体名） |
| SNMPv2c | 1996 | 增加 GetBulk 和 Inform，错误处理更完善 | 仍差（仍然明文团体名） |
| SNMPv3 | 2004 | 引入用户认证、消息加密、访问控制 | 好（推荐生产使用） |

> 注：由于 SNMPv2c 保留了 v1 的团体名模型（另有一个安全增强的 SNMPv2u / SNMPv2* 未被广泛采用），所以目前网络中大量存在的是 v1/v2c，也正是我们本实验攻击的目标。
> 

---

### 3.2 SNMP 的典型应用场景

SNMP 虽然有安全问题，但因为其轻量级、单完备和广泛的设备支持，仍然是企业网络运维的核心协议。常见应用场景：

1. **服务器与网络设备监控**
    - Zabbix、PRTG、SolarWinds、Cacti 等监控平台大多基于 SNMP 拉取数据
    - 监控 CPU、内存、磁盘、网口流量等指标
2. **网络拓扑自动发现**
    - 通过 SNMP 获取路由器的 ARP 表、路由表、LLDP 邻居信息，自动绘制网络拓扑图
3. **打印机、UPS、摄像头等物联网设备管理**
    - 打印机水粉剩余量、UPS 电池状态通常都通过 SNMP 暴露
4. **告警上报（Trap）**
    - 设备故障、端口 down、登录失败等事件主动推送给 NMS
5. **网络设备配置下发（少见）**
    - 通过 SNMP `Set` 操作修改设备配置（安全风险高，实际中多用 NETCONF 替代）

<aside>
💡

举例：一个有 500 台路由器的企业，运维不可能一台台登录查看状态。拿一台 Zabbix 服务器，配置好 SNMP 模板，就能统一拉取所有设备的 CPU、端口流量，并在端口 down 时自动报警。这就是 SNMP 的价值。

</aside>

---

### 3.3 SNMP 工作模型

SNMP 采用 **管理者-代理**（Manager-Agent）架构，通信过程如下：

```
┌──────────────┐    Get/GetNext/Set      ┌──────────────┐
│  NMS（管理者）│ ──────────────────────► │  Agent（代理）│
│  Kali Linux   │ ◄────────────────────── │  Windows Server│
└──────────────┘    Response（MIB数据）   └──────────────┘
                      ◄── Trap（主动告警）──┘
```

**两个角色的分工**：

- **NMS（Network Management Station，管理站）**：发出查询、接收数据的一端，如 Zabbix 服务器、本实验的 Kali
- **Agent（代理）**：运行在被管理设备上的小程序，维护本地 MIB 数据，响应 NMS 的查询

**SNMP 的 5 种核心 PDU（操作）**：

| 操作 | 方向 | 作用 | 类比 |
| --- | --- | --- | --- |
| `Get` | Manager → Agent | 读取指定 OID 的值 | SQL 的 SELECT 某一行 |
| `GetNext` | Manager → Agent | 读取 MIB 树中下一个 OID | 数据库游标的 next() |
| `GetBulk`（v2c+） | Manager → Agent | 一次读取大批 OID，提高效率 | 批量 SELECT |
| `Set` | Manager → Agent | 修改指定 OID 的值 | SQL 的 UPDATE |
| `Trap` / `Inform` | Agent → Manager | 代理主动上报事件，无需查询 | 数据库触发器 |

理解了这五种操作，你也就理解了为什么实验里使用的是 `snmpwalk`（底层就是重复调用 `GetNext` 遍历整棵 MIB 树）。

---

### 3.4 MIB 和 OID：SNMP 的数据组织方式

这是 SNMP 最核心也最难理解的概念，请认真理解这两个术语，之后的一切命令都是在此基础上的应用。

#### 什么是 MIB？

**MIB（Management Information Base，管理信息库）** 是一份**数据结构定义**，它告诉 SNMP：

- 这台设备能被管理的所有"变量"有哪些（例如 CPU 使用率、接口流量、系统描述）
- 每个变量叫什么名字、是什么类型、怎么读取

**关键澄清**：MIB **不是**设备里储存实际数据的数据库，而是一份用 **ASN.1 语法**书写的文本文件（`.mib` 文件），它只是一份"字典"或"图纸"。真正的值存储在 Agent 中，查询时实时返回。

**常见 MIB 文件**：

- **RFC1213-MIB / MIB-II**：最基础的 MIB，所有设备都必须支持，包含系统信息、接口、IP、TCP、UDP 等
- **HOST-RESOURCES-MIB**：主机资源，包含磁盘、进程、已安装软件（本实验重点）
- **厂商私有 MIB**：如 Cisco 有 CISCO-PROCESS-MIB、Windows 有 LANMANAGER-MIB

#### 什么是 OID？

**OID（Object Identifier，对象标识符）** 是 MIB 中每个变量的"全球唯一身份证号"，形式为用点分割的整数序列：

```
1.3.6.1.2.1.1.1.0
│ │ │ │ │ │ │ │ └─ .0 表示标量值（特定实例）
│ │ │ │ │ │ │ └─── sysDescr
│ │ │ │ │ │ └───── system
│ │ │ │ │ └─────── mib-2
│ │ │ │ └───────── mgmt
│ │ │ └─────────── internet
│ │ └───────────── dod  (US Dept of Defense)
│ └─────────────── org
└───────────────── iso
```

**类比理解**：

- OID 像 **文件路径**：`/usr/local/bin/ls` 就是 Linux 下一个唯一文件的路径
- OID 像 **身份证号**：全球唯一，说出号码就知道指的是哪个人
- OID 像 **电话国家码 + 区号 + 号码**：分层注册，永不冲突

**一些重要的根 OID**：

- `1.3.6.1.2.1`：标准 MIB-II（所有设备都应支持）
- `1.3.6.1.4.1`：厂商私有扩展，后面跟的数字是 IANA 分配的厂商编号
    - `1.3.6.1.4.1.9` = Cisco
    - `1.3.6.1.4.1.311` = Microsoft
    - `1.3.6.1.4.1.2021` = Net-SNMP（Linux 上最常见的 Agent）

#### MIB 和 OID 的关系

```
MIB（说明书） ──定义──→ OID 结构 + 名字 + 类型
                            ↓
           Agent（设备软件）──实现──→ 实际值
                            ↑
         Manager（NMS）──用 OID 查询──→
```

举个具体例子：

- MIB 文件中写着：`sysDescr OBJECT-TYPE ... ::= { system 1 }`，意思是系统描述的 OID 是 `1.3.6.1.2.1.1.1`
- 你运行 `snmpget -v2c -c public 192.168.1.20 1.3.6.1.2.1.1.1.0`
- Agent 收到后，返回实际值：`"Hardware: Intel64 ... Windows Server 2025 ..."`

#### 为什么 OID 后面总有个 `.0`？

- 如果查询的是**标量值**（只有一个值，如主机名），在 OID 后面加 `.0` 表示"取的是唯一那个实例"
- 如果查询的是**表格**（如进程列表有很多行），后面跟行索引，如 `1.3.6.1.2.1.25.4.2.1.2.244` 表示 PID=244 的进程名

---

### 3.5 SNMP 常用工具与命令用法

Kali 默认安装了 **Net-SNMP** 工具套件，包含以下常用命令：

| 命令 | 作用 | 使用场景 |
| --- | --- | --- |
| `snmpget` | 读取指定 OID 的值 | 已知具体 OID，目标明确 |
| `snmpgetnext` | 读取紧跟在指定 OID 后面的下一个 OID | 不知道确切 OID，想探索表结构 |
| `snmpwalk` | 从指定 OID 开始遍历整棵子树 | 大量枚举（渗透测试常用） |
| `snmpbulkwalk` | 使用 GetBulk 的批量版 walk | 目标表很大时提高速度 |
| `snmpset` | 修改指定 OID 的值 | 需要 RW 团体名（如 private） |
| `snmptranslate` | OID 与文字名称互转 | 把 `1.3.6.1.2.1.1.1.0` 翻译成 `sysDescr.0` |

**命令通用格式**：

```
snmp<command> -v<版本> -c <团体名> <目标IP> [OID]
```

**具体示例**：

```
# 1. 用 snmpget 读取单个值（系统描述）
snmpget -v2c -c public 192.168.1.20 sysDescr.0
snmpget -v2c -c public 192.168.1.20 1.3.6.1.2.1.1.1.0
# 等效，前者需要 MIB 文件解析

# 2. 用 snmpwalk 遍历整个系统分支
snmpwalk -v2c -c public 192.168.1.20 system
snmpwalk -v2c -c public 192.168.1.20 1.3.6.1.2.1.1

# 3. 不指定 OID = 遍历所有可访问的数据（数据量很大）
snmpwalk -v2c -c public 192.168.1.20

# 4. 用 snmptranslate 翻译 OID
snmptranslate -On SNMPv2-MIB::sysDescr.0
# 输出：.1.3.6.1.2.1.1.1.0
snmptranslate -Of .1.3.6.1.2.1.1.1.0
# 输出：.iso.org.dod.internet.mgmt.mib-2.system.sysDescr.0

# 5. 调试模式：看原始报文，便于学习协议
snmpwalk -v2c -c public -d 192.168.1.20 system
```

**SNMPv3 查询示例**（生产环境推荐）：

```
snmpwalk -v3 -u 用户名 -l authPriv -a SHA -A "认证密码" -x AES -X "加密密码" 192.168.1.20
```

<aside>
⚠️

**常见问题**：`snmpwalk` 返回 `Timeout: No Response` 不一定是服务没开——还可能是：
① 版本不匹配（服务器只开 v3，你用了 v2c）
② 团体名错误
③ 防火墙或 PermittedManagers 限制了来源 IP
④ UDP 161 未放行

</aside>

---

### 3.6 MIB 树结构与常用 OID

SNMP 的信息以树形结构组织，下面是一个常见子树的直观示意：

```
iso(1) → org(3) → dod(6) → internet(1) → mgmt(2) → mib-2(1)
                                                    ├── system(1)
                                                    │   ├── sysDescr(1.0)    ← 系统描述
                                                    │   ├── sysObjectID(2.0)  ← 系统OID
                                                    │   ├── sysUpTime(3.0)    ← 运行时间
                                                    │   └── sysContact(4.0)   ← 管理员
                                                    ├── interfaces(2)         ← 网络接口
                                                    ├── ip(4)                 ← IP信息
                                                    ├── icmp(5)               ← ICMP统计
                                                    ├── tcp(6)                ← TCP连接
                                                    ├── udp(7)                ← UDP监听
                                                    ├── host(25)              ← 主机资源
                                                    │   ├── hrSystem(1)       ← 系统信息
                                                    │   ├── hrStorage(2)      ← 存储信息
                                                    │   ├── hrDevice(3)       ← 设备信息
                                                    │   └── hrSWRun(4)        ← 运行进程
                                                    └── ...
```

**常用OID速查表**：

| OID | 获取内容 | 命令示例 |
| --- | --- | --- |
| 1.3.6.1.2.1.1.1.0 | 系统描述（OS版本） | `snmpget -v2c -c public IP 1.3.6.1.2.1.1.1.0` |
| 1.3.6.1.2.1.1.5.0 | 主机名 | `snmpget -v2c -c public IP 1.3.6.1.2.1.1.5.0` |
| 1.3.6.1.2.1.1.3.0 | 系统运行时间 | `snmpget -v2c -c public IP 1.3.6.1.2.1.1.3.0` |
| 1.3.6.1.2.1.25.4.2 | 运行进程列表 | `snmpwalk -v2c -c public IP 1.3.6.1.2.1.25.4.2` |
| 1.3.6.1.2.1.25.6.3 | 已安装软件 | `snmpwalk -v2c -c public IP 1.3.6.1.2.1.25.6.3` |
| 1.3.6.1.2.1.4.20 | IP地址表 | `snmpwalk -v2c -c public IP 1.3.6.1.2.1.4.20` |
| 1.3.6.1.2.1.4.22 | ARP缓存表 | `snmpwalk -v2c -c public IP 1.3.6.1.2.1.4.22` |

---

### 3.7 SNMP安全性分析

```
安全性排序：SNMPv3 >> SNMPv2c = SNMPv1

SNMPv1/v2c 的致命弱点：
┌────────────────────────────────────────────────────┐
│ 1. 团体名（Community String）= 明文"密码"          │
│    默认 public（只读）、private（读写）            │
│    可通过网络嗅探直接捕获                         │
│                                                    │
│ 2. 无数据加密                                      │
│    所有MIB数据明文传输，包含系统版本、进程列表等     │
│                                                    │
│ 3. 无消息认证                                      │
│    攻击者可伪造SNMP响应，发送虚假告警              │
│                                                    │
│ 4. 默认配置极弱                                    │
│    大多数设备安装后使用默认public团体名            │
└────────────────────────────────────────────────────┘

SNMPv3 的安全增强：
- USM（User-based Security Model）：用户名+密码认证
- 支持MD5/SHA认证 + DES/AES加密
- 支持访问控制（View-based Access Control）
```

### 3.8 SNMP 枚举能拿到多"离谱"的信息？

相比单纯的端口扫描，SNMP 枚举的信息密度要高得多。一次成功的 `snmpwalk` 可能直接暴露：

- 操作系统精确版本（精确到 Build 号）
- 主机名、域名、系统管理员联系方式
- **所有正在运行的进程**（包括杀软进程名，可用于规避）
- 已安装软件及版本号（直接对照 CVE 库）
- 所有网卡、IP、路由表、ARP 表（内网横向移动地图）
- 共享文件夹、打印机、用户账户

可以说，一个配置不当的 SNMP 服务，等同于把服务器的"身份证"交给任何人查看。

---

## 4. Windows高危端口速记

在做信息收集实验时，以下端口发现意味着什么：

| 端口 | 服务 | 发现后的攻击思路 |
| --- | --- | --- |
| 21 | FTP | 匿名登录？弱口令？嗅探明文密码？ |
| 23 | Telnet | 明文传输，可嗅探凭据，应禁用 |
| 80/443 | HTTP/HTTPS | Web漏洞扫描、目录遍历、SQL注入 |
| 135 | RPC | 可能存在远程代码执行漏洞 |
| 139/445 | SMB/NetBIOS | MS17-010永恒之蓝、空会话枚举 |
| 161 | SNMP | 默认团体名枚举（本实验重点） |
| 389/636 | LDAP | 域控制器，域渗透入口 |
| 1433 | SQL Server | 弱口令爆破、SQL注入 |
| 3306 | MySQL | 弱口令爆破 |
| 3389 | RDP | 弱口令暴力破解（BlueKeep） |
| 5985/5986 | WinRM | 远程PowerShell执行 |

---

## 5. 本实验的知识链路图

```mermaid
flowchart LR
    A[信息收集方法论] --> B[主动扫描]
    B --> C[Nmap 主机发现]
    C --> D[Nmap 端口/服务识别]
    D --> E{发现 161/UDP?}
    E -->|是| F[SNMP 枚举]
    F --> G[默认团体名 public]
    G --> H[泄露系统信息]
    H --> I[安全加固]
    I --> J[验证加固效果]
    E -->|否| K[其他攻击面]
```

<aside>
🎯

**实验关键提示**：本实验的核心在于理解 SNMPv1/v2c 使用默认团体名 `public` 可泄露大量系统信息。实验流程为：
发现SNMP服务（nmap -sU）→ 使用默认团体名枚举（snmpwalk）→ 分析泄露信息的安全影响 → 修改团体名加固 → 验证加固效果。

</aside>

---

# 第二部分：实验操作

```
┌─────────────────────┐              NAT模式                 ┌─────────────────────┐
│    Kali Linux       │           192.168.1.0/24             │  Windows Server     │
│   2025.4（攻击机）    │◄──────────────────────────────────► │    2025（靶机）     │
│  IP: 192.168.1.10   │                                      │  IP: 192.168.1.20   │
└─────────────────────┘                                      └─────────────────────┘
```

**虚拟机设置**（靶机）：

| 项目 | 配置 |
| --- | --- |
| 内存 | 4 GB |
| 网络适配器 | NAT模式 |
| 快照 | 实验前创建快照（命名：实验一-初始状态） |

**靶机初始配置脚本**（以管理员身份在PowerShell中执行）：

```powershell
# ============================================
# 靶机环境初始化脚本 - 实验一
# ============================================

# 1. 安装SNMP服务
Install-WindowsFeature SNMP-Service, SNMP-WMI-Provider -IncludeManagementTools

# 2. 配置防火墙放行SNMP（UDP 161）
New-NetFirewallRule -DisplayName "SNMP Service" -Direction Inbound -Protocol UDP -LocalPort 161 -Action Allow

# 3. 创建测试账户
net user admin P@ssw0rd /add
net localgroup Administrators admin /add

# 4. 启用远程注册表（默认已启用）
Set-Service -Name "RemoteRegistry" -StartupType Automatic

# 5. 重启
Restart-Computer -Force
```

**SNMP服务配置**（重启后在图形界面完成）：

1. 运行 `services.msc`，找到 **SNMP Service**
2. 右键 → 属性 → **安全** 选项卡
3. 添加团体名 `public`，权限设为 **READ ONLY**
4. 勾选 **接受来自任何主机的 SNMP 数据包**
5. 点击确定，重启SNMP服务

**攻击机配置**：

| 项目 | 配置 |
| --- | --- |
| 内存 | 2 GB |
| 网络适配器 | NAT模式 |

**攻击机网络配置**：

```
# 编辑网络配置文件
sudo nano /etc/network/interfaces

# 或者使用 NetworkManager
sudo nmcli connection show
sudo nmcli connection modify "Wired connection 1" ipv4.addresses 192.168.1.10/24 ipv4.gateway 192.168.1.2
sudo nmcli connection up "Wired connection 1"

# 验证IP
ip addr show
ping 192.168.1.20
```

---

## 任务一：主机发现与端口扫描

**步骤1：使用Nmap进行主机发现**

```
# 扫描整个网段，发现存活主机
nmap -sn 192.168.1.0/24

# 预期输出：
# Nmap scan report for 192.168.1.20
# Host is up (0.0010s latency).
# Nmap done: 256 IP addresses (2 hosts up) scanned in 2.5 seconds

# 也可以使用快速主机发现
nmap -sn -PE -PA 192.168.1.0/24
```

**步骤2：使用ARP扫描发现主机**

```
# 使用arp-scan进行二层发现
sudo arp-scan -l

# 预期输出：
# 192.168.1.1  xx:xx:xx:xx:xx:xx  VMware
# 192.168.1.20 xx:xx:xx:xx:xx:xx  VMware
# 192.168.1.10 xx:xx:xx:xx:xx:xx  (本机)

# 使用netdiscover
sudo netdiscover -r 192.168.1.0/24
```

> **知识关联**：对应讲义中”服务器用途分类”——通过扫描确认目标是一台服务器而非普通工作站。
> 

---

**步骤3：全端口扫描**

```
# 扫描全部65535个端口
sudo nmap -p- -T4 192.168.1.20

# 预期输出：
# PORT     STATE SERVICE
# 135/tcp  open  msrpc
# 139/tcp  open  netbios-ssn
# 445/tcp  open  microsoft-ds
# 161/udp  open  snmp
# 3389/tcp open  ms-wbt-server

# 也可以只扫描常见端口（更快）
nmap -p 1-1024 -T4 192.168.1.20
```

> **知识关联**：对应讲义中”Windows服务端口分类”和”高危端口重点关注”——139/445是SMB端口，3389是RDP端口，161是SNMP端口。
> 

**步骤4：服务版本探测**

```
# 探测开放端口的服务版本信息
nmap -sV -p 135,139,445,161,3389 192.168.1.20

# 预期输出：
# PORT     STATE SERVICE     VERSION
# 135/tcp  open  msrpc       Microsoft Windows RPC
# 139/tcp  open  netbios-ssn Windows Server 2025 netbios-ssn
# 445/tcp  open  microsoft-ds Windows Server 2025 microsoft-ds
# 3389/tcp open  ms-wbt-server Microsoft Terminal Services

# 使用-A参数同时执行脚本扫描和OS识别
nmap -A 192.168.1.20
```

**步骤5：使用Nmap脚本进行漏洞扫描**

```
# 扫描常见服务漏洞
nmap --script vuln 192.168.1.20

# 也可以针对特定服务进行漏洞扫描
nmap --script smb-vuln* -p 445 192.168.1.20
nmap --script ftp-vuln* -p 21 192.168.1.20
nmap --script http-vuln* -p 80 192.168.1.20

# 注意：漏洞扫描可能触发安全设备告警，仅在授权环境使用
```

> **知识关联**：对应讲义中”Windows系统服务”——通过扫描识别目标运行的哪些服务，评估攻击面。
> 

---

## 任务二：SNMP 枚举渗透

**步骤6：使用默认团体名枚举系统信息**

```
# 使用snmpwalk遍历全部MIB信息（使用默认团体名public）
snmpwalk -v2c -c public 192.168.1.20

# 获取系统描述（OS版本）
# 预期输出：HOST-RESOURCES-MIB::hrSystemUptime.0 = Timeticks: ...

# 获取主机名
snmpwalk -v2c -c public 192.168.1.20 1.3.6.1.2.1.1.5.0

# 获取系统运行时间
snmpwalk -v2c -c public 192.168.1.20 1.3.6.1.2.1.1.3.0
```

> **安全分析**：攻击者仅凭默认团体名`public`，无需任何用户名密码即可获取操作系统版本和主机名。
> 

**步骤7：枚举运行中的进程**

```
# 获取正在运行的进程列表
snmpwalk -v2c -c public 192.168.1.20 1.3.6.1.2.1.25.4.2.1.2

# 预期输出：
# HOST-RESOURCES-MIB::hrSWRunName.1 = STRING: "System Idle Process"
# HOST-RESOURCES-MIB::hrSWRunName.4 = STRING: "System"
# HOST-RESOURCES-MIB::hrSWRunName.244 = STRING: "svchost.exe"
# ...

# 获取进程路径信息
snmpwalk -v2c -c public 192.168.1.20 1.3.6.1.2.1.25.4.2.1.4

# 安全分析：攻击者可通过进程列表发现安全软件（杀毒、EDR等）
```

**步骤8：枚举已安装软件**

```
# 获取已安装软件列表
snmpwalk -v2c -c public 192.168.1.20 1.3.6.1.2.1.25.6.3

# 分析输出：找出有已知漏洞的软件版本
# 例如发现 Adobe Reader 旧版本 → 可能有PDF漏洞
# 例如发现 Java 旧版本 → 可能有反序列化漏洞
```

**步骤9：枚举网络接口信息**

```
# 获取网络接口详细信息
snmpwalk -v2c -c public 192.168.1.20 1.3.6.1.2.1.2.2

# 获取IP地址表
snmpwalk -v2c -c public 192.168.1.20 1.3.6.1.2.1.4.20

# 获取ARP表（发现同网段其他主机）
snmpwalk -v2c -c public 192.168.1.20 1.3.6.1.2.1.4.22
```

> **知识关联**：对应讲义中”SNMP服务详解”——SNMPv1/v2c使用明文团体名认证，默认`public`团体名可读取大量敏感信息。
> 

**步骤10：使用Nmap SNMP脚本进行自动化枚举**

```
# 自动化枚举Windows系统信息
nmap -sU -p 161 --script snmp-sysdescr 192.168.1.20
nmap -sU -p 161 --script snmp-processes 192.168.1.20
nmap -sU -p 161 --script snmp-win32-services 192.168.1.20
nmap -sU -p 161 --script snmp-netstat 192.168.1.20

# 使用onesixtyone工具爆破SNMP团体名
onesixtyone -c /usr/share/wordlists/onesixtyone/wordlist.txt 192.168.1.20
```

- `-sU`：UDP 扫描模式。SNMP 使用 UDP/161，因此需要 UDP 扫描才能触发相应的探测。
- `-p 161`：指定只扫描/探测 161 端口（SNMP Agent 默认监听端口），速度快且目标明确。
- `--script <脚本名>`：调用 Nmap NSE（Nmap Scripting Engine）脚本，对 SNMP 服务进行“更高层”的自动化枚举。
    - `snmp-sysdescr`：读取系统描述 `sysDescr`（操作系统/版本/设备信息），用于快速指纹识别。
    - `snmp-processes`：枚举运行中的进程列表（常用于发现安全软件进程、第三方服务、可疑组件）。
    - `snmp-win32-services`：枚举 Windows 服务列表（可用于定位高危/可被利用的服务，或识别系统角色）。
    - `snmp-netstat`：枚举网络连接/监听端口（类似 `netstat` 信息），可辅助发现更多可攻击的服务端口。
- `onesixtyone -c <wordlist> <IP>`：使用字典批量尝试 SNMP 团体名（Community String）。
如果命中（例如 `public`），目标会返回 SNMP 响应，说明该团体名有效。团体名相当于 SNMPv1/v2c 的“口令”，配置弱或使用默认值会导致严重信息泄露。

<aside>
⚠️

注意：上述 NSE 脚本和 onesixtyone 在默认情况下通常会尝试使用 `public` 团体名。若靶机修改了团体名或配置了 PermittedManagers（只允许指定管理站 IP），则会出现超时无响应，需要改用正确团体名并确认访问来源 IP 在允许列表中。

</aside>

---

## 任务三：安全加固与验证

**步骤11：修改团体名并限制访问来源**

在Windows Server靶机上执行：

```powershell
# 方法一：通过注册表修改
# 修改团体名
reg add "HKLM\SYSTEM\CurrentControlSet\Services\SNMP\Parameters\ValidCommunities" /v "MyS3cret@2024" /t REG_DWORD /d 4 /f

# 删除默认public团体名
reg delete "HKLM\SYSTEM\CurrentControlSet\Services\SNMP\Parameters\ValidCommunities" /v "public" /f

# 限制仅允许指定IP访问
reg add "HKLM\SYSTEM\CurrentControlSet\Services\SNMP\Parameters\PermittedManagers" /v "1" /t REG_SZ /d "192.168.1.10" /f

# 重启SNMP服务
Restart-Service SNMP
```

**步骤12：验证加固效果**

```
# 使用旧团体名public，应超时无响应
snmpwalk -v2c -c public 192.168.1.20
# 预期输出：Timeout: No Response from 192.168.1.20

# 使用新团体名，正常获取数据
snmpwalk -v2c -c "MyS3cret@2024" 192.168.1.20
# 预期输出：正常返回SNMP信息

# 从非授权IP尝试，应超时（需换一台机器测试）
```

---

# 第三部分：实验记录与思考

## 实验记录清单

| 序号 | 记录项 | 说明 |
| --- | --- | --- |
| 1 | Nmap扫描结果截图 | 包含端口列表和服务版本 |
| 2 | SNMP枚举结果 | 系统版本、主机名、进程列表、安装软件 |
| 3 | 安全风险评估 | 基于枚举信息分析存在的安全风险 |
| 4 | 加固前后对比 | 修改团体名前后的访问效果对比截图 |

## 思考题

1. 为什么SNMP默认团体名`public`如此危险？它能泄露哪些信息？
2. 结合讲义中的”最小化服务原则”，分析靶机上哪些服务是不必要的？
3. 如果生产环境必须使用SNMP，应该采取哪些安全措施？
4. SNMPv3相比v1/v2c有哪些安全增强？

## 环境清理脚本

```powershell
# 恢复靶机到初始快照，或手动执行以下清理：
# 1. 卸载SNMP服务
Uninstall-WindowsFeature -Name SNMP-Service, SNMP-WMI-Provider

# 2. 删除测试账户
net user admin /delete

# 3. 启用防火墙
Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled True

# 4. 关闭远程注册表
Set-Service -Name "RemoteRegistry" -StartupType Disabled
Stop-Service "RemoteRegistry"
```

> **免责声明**：本实验仅用于授权的安全教学环境。对任何未授权系统进行扫描或渗透测试属于违法行为。
>