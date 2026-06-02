---
title: "08.项目八 Windows内网安全"
---

# 08.项目八 Windows内网安全

---

# 课前回顾

本项目以前序项目所建立的服务器配置、远程管理、域管理和应用安全知识为基础，从网络边界视角理解 Windows 内网安全。

**回顾问题：**

1. 为什么生产环境中不应为了省事而关闭 Windows Defender 防火墙？
2. RDP、WinRM、SMB 分别使用哪些常见端口？哪些主机确实需要开放这些服务？
3. 域控制器为什么不应与普通业务服务器放在同一安全区域？
4. 当攻击者已经进入一台内网主机后，网络分段和最小权限如何限制影响范围？

> **授权边界**：本项目仅限在教师提供的虚拟机靶场或已取得书面授权的测试环境中实施。不得扫描、转发或访问不属于本实验的网络和系统。

---

# 学习目标

| 层次 | 内容 |
| --- | --- |
| 知识 | 理解私有地址、路由、NAT、端口转发和内网分段的区别；理解横向移动风险及其常见防御措施 |
| 技能 | 能够搭建双网段虚拟实验环境；能够使用 `netsh interface portproxy` 完成受控的 TCP 端口转发；能够使用 RRAS 完成可选的 NAT 实验；能够盘点内网暴露面并实施基础加固 |
| 素养 | 树立“内网不等于可信网络”的意识；坚持最小权限、最小暴露面和授权测试原则 |

---

# 重难点梳理

| 类型 | 内容 | 说明 |
| --- | --- | --- |
| 重点 | 网络隔离与最小暴露面 | 默认拒绝跨区域访问，只允许业务所需流量 |
| 重点 | `portproxy` 与 NAT 的区别 | `portproxy` 是 TCP 代理，不是完整 NAT |
| 重点 | Windows 防火墙规则 | 使用限定来源地址的规则，避免直接关闭防火墙 |
| 难点 | RRAS NAT | 理解内外网卡、默认网关和地址转换之间的关系 |
| 难点 | 身份安全 | 理解 SMB 签名、`Protected Users` 和特权账号隔离的适用范围 |

---

# 任务一 搭建隔离的内网实验环境

## 理论知识

### 私有 IP 地址

RFC 1918 定义了三段私有 IPv4 地址。这些地址不会在公共互联网中直接路由。

| 地址块 | 前缀长度 | 地址范围 |
| --- | --- | --- |
| `10.0.0.0/8` | `/8` | `10.0.0.0` - `10.255.255.255` |
| `172.16.0.0/12` | `/12` | `172.16.0.0` - `172.31.255.255` |
| `192.168.0.0/16` | `/16` | `192.168.0.0` - `192.168.255.255` |

> 私有地址、NAT 和防火墙解决的是不同问题。NAT 主要用于地址转换，不能替代访问控制、防火墙和日志审计。

### 实验拓扑

本项目使用两个虚拟网络模拟边界网络和内部服务器区。

```text
VMnet8：边界实验网 192.168.10.0/24

Kali                    SRV01
192.168.10.10   <---->  192.168.10.20
                        192.168.100.20
                              |
                              |
VMnet1：内部服务器网 192.168.100.0/24
                              |
                        SRV02
                        192.168.100.30
```

| 虚拟机 | 角色 | 网卡配置 |
| --- | --- | --- |
| Kali Linux | 管理与验证终端 | `192.168.10.10/24`，连接 VMnet8 |
| SRV01 | 双网卡边界服务器 | `192.168.10.20/24`，连接 VMnet8；`192.168.100.20/24`，连接 VMnet1 |
| SRV02 | 内部业务服务器 | `192.168.100.30/24`，连接 VMnet1 |

> 实验开始前请创建虚拟机快照。VMnet8 的实际 VMware NAT 网关可能不是 `192.168.10.2`，应以“虚拟网络编辑器”中显示的值为准。

## 实践操作

### 实验1：配置虚拟网络

**第一步：配置 VMware 网络**

1. 打开 VMware Workstation 的“虚拟网络编辑器”。
2. 将 VMnet8 设为 NAT 模式，子网设为 `192.168.10.0/24`。
3. 将 VMnet1 设为仅主机模式，子网设为 `192.168.100.0/24`。
4. 为 SRV01 添加两块网卡，分别连接 VMnet8 和 VMnet1。
5. Kali 仅连接 VMnet8，SRV02 仅连接 VMnet1。

**第二步：配置 Kali**

先使用 `nmcli connection show` 确认连接名称，再执行：

```bash
sudo nmcli connection modify "Wired connection 1" \
  ipv4.addresses 192.168.10.10/24 \
  ipv4.gateway 192.168.10.2 \
  ipv4.dns 192.168.10.2 \
  ipv4.method manual

sudo nmcli connection up "Wired connection 1"
ip addr show
```

**第三步：配置 SRV01**

以管理员身份运行 PowerShell。先用 `Get-NetAdapter` 确认网卡名称，再按实际名称修改变量。

```powershell
Get-NetAdapter | Select-Object Name, InterfaceDescription, Status, MacAddress

$ExternalNic = "以太网"
$InternalNic = "以太网 2"

New-NetIPAddress -InterfaceAlias $ExternalNic `
  -IPAddress 192.168.10.20 -PrefixLength 24 -DefaultGateway 192.168.10.2

New-NetIPAddress -InterfaceAlias $InternalNic `
  -IPAddress 192.168.100.20 -PrefixLength 24

Get-NetIPAddress -AddressFamily IPv4 |
  Select-Object InterfaceAlias, IPAddress, PrefixLength
```

> 如果网卡已有 DHCP 地址或默认路由，请先用 `Get-NetIPAddress` 和 `Get-NetRoute` 检查现状，避免重复添加地址或默认网关。

**第四步：配置 SRV02**

```powershell
Get-NetAdapter | Select-Object Name, Status

$InternalNic = "以太网"

New-NetIPAddress -InterfaceAlias $InternalNic `
  -IPAddress 192.168.100.30 -PrefixLength 24

Get-NetIPAddress -AddressFamily IPv4 |
  Select-Object InterfaceAlias, IPAddress, PrefixLength
```

此时不要将 SRV02 的 DNS 指向 SRV01，除非 SRV01 已配置 DNS 服务或 DNS 转发。域环境中，域成员通常应使用 AD DNS；独立实验机可暂不配置 DNS。

**第五步：验证初始隔离**

```bash
# 在 Kali 上执行
ping -c 2 192.168.10.20
ping -c 2 192.168.100.30
```

```powershell
# 在 SRV01 上执行
Test-Connection 192.168.10.10 -Count 2
Test-Connection 192.168.100.30 -Count 2
```

预期结果：

| 测试路径 | 预期 |
| --- | --- |
| Kali -> SRV01 外网卡 | 可以通信 |
| SRV01 内网卡 -> SRV02 | 可以通信 |
| Kali -> SRV02 | 初始状态下不能直接通信 |

---

# 任务二 配置受控的端口转发

## 理论知识

### `portproxy` 与 RRAS

Windows Server 中常见的两种转发方式如下。

| 方式 | 能力 | 适用场景 |
| --- | --- | --- |
| `netsh interface portproxy` | TCP 连接代理 | 临时、明确、少量端口的实验或管理场景 |
| RRAS | 路由、NAT、VPN | 需要完整地址转换和路由能力的服务器场景 |

> `portproxy` 不是完整 NAT。它只代理指定的 TCP 监听端口，不转发 UDP，也不应被当作网络边界防火墙。

## 实践操作

### 实验2：发布 SRV02 的测试 Web 页面

**第一步：在 SRV02 安装 IIS**

```powershell
Install-WindowsFeature -Name Web-Server -IncludeManagementTools

Set-Content -Path "C:\inetpub\wwwroot\index.html" -Value @"
<html>
  <body>
    <h1>SRV02 internal test page</h1>
  </body>
</html>
"@

Invoke-WebRequest http://127.0.0.1/ -UseBasicParsing
```

**第二步：在 SRV01 配置 TCP 转发**

```powershell
Get-Service iphlpsvc
Start-Service iphlpsvc
Set-Service iphlpsvc -StartupType Automatic

netsh interface portproxy add v4tov4 `
  listenaddress=192.168.10.20 listenport=8080 `
  connectaddress=192.168.100.30 connectport=80 protocol=tcp

New-NetFirewallRule `
  -DisplayName "LAB-Allow-TCP-8080-from-Kali" `
  -Direction Inbound -Action Allow -Protocol TCP `
  -LocalAddress 192.168.10.20 -LocalPort 8080 `
  -RemoteAddress 192.168.10.10

netsh interface portproxy show all
```

**第三步：在 Kali 验证**

```bash
curl http://192.168.10.20:8080/
nmap -sT -p 8080 192.168.10.20
```

预期可以看到 SRV02 的测试页面，但 Kali 仍然不能直接访问 `192.168.100.30`。

**第四步：清理实验规则**

```powershell
netsh interface portproxy delete v4tov4 `
  listenaddress=192.168.10.20 listenport=8080

Remove-NetFirewallRule -DisplayName "LAB-Allow-TCP-8080-from-Kali"
```

### 实验3：可选的 RRAS NAT

RRAS NAT 实验用于理解完整地址转换。它与实验2的 `portproxy` 是两条独立路径，不应混用。

**第一步：在 SRV01 安装 RRAS**

```powershell
Install-WindowsFeature RemoteAccess,Routing -IncludeManagementTools
Install-RemoteAccess -VpnType RoutingOnly
rrasmgmt.msc
```

**第二步：使用 RRAS 管理器配置**

1. 在 RRAS 管理器中右键本机，选择“配置并启用路由和远程访问”。
2. 选择“自定义配置”。
3. 启用“NAT”和“LAN 路由”。
4. 将 `192.168.10.20` 所在接口设为公用接口并启用 NAT。
5. 将 `192.168.100.20` 所在接口设为专用接口。

**第三步：在 SRV02 增加默认路由**

```powershell
New-NetRoute -DestinationPrefix "0.0.0.0/0" `
  -InterfaceAlias "以太网" -NextHop 192.168.100.20

Get-NetRoute -DestinationPrefix "0.0.0.0/0"
```

**第四步：验证 SRV02 到边界实验网的出站访问**

先在 Kali 上启动临时 Web 服务：

```bash
python3 -m http.server 8000 --bind 192.168.10.10
```

再在 SRV02 上访问：

```powershell
Invoke-WebRequest http://192.168.10.10:8000/ -UseBasicParsing
```

> RRAS NAT 不是安全策略。生产环境仍需使用防火墙规则限制允许的来源、目标和端口。

## 任务二知识点总结

| 知识点 | 要点 |
| --- | --- |
| `portproxy` | 用于少量 TCP 端口代理，规则清晰但能力有限 |
| RRAS NAT | 用于完整路由和地址转换，配置时要明确内外网接口 |
| Windows 防火墙 | 转发规则必须搭配限定来源地址的入站规则 |
| 实验清理 | 完成验证后删除临时端口转发和防火墙规则 |

---

# 任务三 认识受控隧道与出站风险

## 理论知识

### 受控隧道的双重属性

SSH 本地端口转发、frp 等工具既可以用于合法远程运维，也可能被攻击者滥用。企业环境应同时落实审批、资产登记、最小权限、出站访问控制和日志审计。

| 场景 | 合法用途 | 风险控制 |
| --- | --- | --- |
| SSH 本地端口转发 | 通过堡垒机访问内部 Web 管理页 | 限定账号、目标、时间和日志 |
| frp TCP 映射 | 临时发布测试服务 | 限定监听端口、认证令牌和来源地址 |
| 任意 SOCKS 代理 | 通用代理能力 | 基础课程不部署；企业环境原则上禁止未经审批使用 |

> 本讲义只演示内部 Web 页面映射，不映射 RDP、WinRM、SMB，不部署通用 SOCKS 代理。

## 实践操作

### 实验4：使用 SSH 本地端口转发访问内部 Web 页面

此实验要求 SRV01 已按项目五的方法安装并启用 OpenSSH Server。

```powershell
# 在 SRV01 上检查 SSH 服务
Get-Service sshd
```

在 Kali 上建立本地端口转发：

```bash
ssh -L 18080:192.168.100.30:80 administrator@192.168.10.20 -N
```

另开一个 Kali 终端验证：

```bash
curl http://127.0.0.1:18080/
```

按 `Ctrl+C` 关闭 SSH 会话后，本地转发立即失效。

### 实验5：frp TCP 映射演示

frp 版本更新较快。教师应在备课时从官方仓库的 Releases 页面下载并固定一个经过测试的版本，不要在讲义中长期写死“最新版”。

官方仓库：<https://github.com/fatedier/frp>

**第一步：在 Kali 配置 `frps.toml`**

```toml
bindPort = 7000

auth.method = "token"
auth.token = "<替换为随机令牌>"

allowPorts = [
  { single = 10002 }
]

webServer.addr = "127.0.0.1"
webServer.port = 7500
webServer.user = "admin"
webServer.password = "<替换为强密码>"
```

启动服务端：

```bash
./frps -c ./frps.toml
```

**第二步：在 SRV02 配置 `frpc.toml`**

前提：已完成 RRAS NAT 实验，SRV02 可以访问 Kali 的 `192.168.10.10:7000`。

```toml
serverAddr = "192.168.10.10"
serverPort = 7000

auth.method = "token"
auth.token = "<与服务端相同的随机令牌>"

[[proxies]]
name = "srv02-web"
type = "tcp"
localIP = "127.0.0.1"
localPort = 80
remotePort = 10002
```

启动客户端：

```powershell
.\frpc.exe -c .\frpc.toml
```

**第三步：在 Kali 验证并清理**

```bash
curl http://127.0.0.1:10002/
```

完成验证后，停止 `frpc` 和 `frps` 进程，删除临时配置文件。不要将实验令牌用于其他环境。

### 关于 nps

早期讲义常将 nps 与 frp 并列介绍。`ehang-io/nps` 官方仓库已经归档，最后一个官方 Release 也已较旧。本课程仅将其作为历史案例，不再安排部署实验。新部署应优先选择仍在维护、完成版本固定和安全评估的工具。

## 任务三知识点总结

| 知识点 | 要点 |
| --- | --- |
| 隧道工具 | 具有双重属性，必须纳入审批和审计 |
| SSH 转发 | 适合受控的单端口管理场景 |
| frp | 固定经过测试的版本，使用认证令牌并限制可映射端口 |
| 出站控制 | 服务器不应默认允许任意外连 |

---

# 任务四 盘点内网暴露面

## 理论知识

### 暴露面盘点

内网安全评估不等于无边界扫描。首先要明确授权范围，再从资产、端口、服务、身份和日志五个维度进行盘点。

| 维度 | 关注内容 |
| --- | --- |
| 资产 | 主机名、IP 地址、操作系统、业务角色 |
| 网络 | 路由、邻居、监听端口、已建立连接 |
| 服务 | IIS、SMB、RDP、WinRM、数据库等 |
| 身份 | 本地管理员、域组成员、服务账号 |
| 日志 | 失败登录、账号变更、策略变更、异常出站连接 |

## 实践操作

### 实验6：在 SRV02 上采集基础信息

```powershell
hostname
ipconfig /all
route print
arp -a
netstat -ano

whoami /all
net user
net localgroup administrators

Get-Service |
  Where-Object Status -eq "Running" |
  Select-Object Name, DisplayName, StartType

Get-NetTCPConnection |
  Sort-Object LocalPort |
  Select-Object LocalAddress, LocalPort, RemoteAddress, RemotePort, State
```

### 实验7：从授权管理节点验证必要端口

在 SRV01 上检查 SRV02 的常见管理端口。实际生产环境中，只应开放业务确实需要的端口。

```powershell
$Target = "192.168.100.30"
$Ports = 80, 445, 3389, 5985

foreach ($Port in $Ports) {
  Test-NetConnection -ComputerName $Target -Port $Port |
    Select-Object ComputerName, RemotePort, TcpTestSucceeded
}
```

在 Kali 上只扫描实验授权范围：

```bash
nmap -sT -sV -p 8080 192.168.10.20
```

> 不要使用不加范围限制的漏洞脚本扫描生产网络。扫描会产生负载和告警，必须事先审批并安排窗口。

### 实验8：查看失败登录日志

在 Windows 服务器上查看近期失败登录事件：

```powershell
Get-WinEvent -FilterHashtable @{
  LogName = "Security"
  Id      = 4625
} -MaxEvents 20 |
  Select-Object TimeCreated, Id, Message
```

建议同时关注：

| 事件 ID | 含义 |
| --- | --- |
| `4624` | 登录成功 |
| `4625` | 登录失败 |
| `4720` | 创建用户账号 |
| `4732` | 将成员加入本地安全组 |
| `4776` | NTLM 凭据验证 |

---

# 任务五 实施内网安全加固

## 理论知识

### 纵深防御

内网安全不能依赖单一产品。常见措施包括：

1. 网络分段：将办公区、服务器区、管理区和域控制器区分开。
2. 主机防火墙：按来源地址、目标端口和业务需要放行。
3. 身份隔离：普通账号、服务器管理账号和域管理账号分离。
4. 协议加固：启用 SMB 签名，减少 NTLM 使用。
5. 出站控制：限制服务器连接未知公网地址和非常用端口。
6. 日志审计：集中采集 Windows 安全日志、防火墙日志和边界流量日志。

## 实践操作

### 实验9：配置限定来源地址的防火墙规则

以下示例仅允许管理网主机 `192.168.100.20` 访问 SRV02 的 RDP 和 WinRM。执行前应检查是否已有更宽泛的放行规则。

```powershell
Set-NetFirewallProfile -Profile Domain,Private,Public -Enabled True

Get-NetFirewallRule -Direction Inbound -Enabled True |
  Select-Object Name, DisplayName, Action, Profile

New-NetFirewallRule `
  -DisplayName "Allow-RDP-from-AdminHost" `
  -Direction Inbound -Action Allow -Protocol TCP `
  -LocalPort 3389 -RemoteAddress 192.168.100.20

New-NetFirewallRule `
  -DisplayName "Allow-WinRM-HTTP-from-AdminHost" `
  -Direction Inbound -Action Allow -Protocol TCP `
  -LocalPort 5985 -RemoteAddress 192.168.100.20
```

> 新建窄范围规则之前，应禁用或收紧已有的宽范围放行规则。不同语言版本 Windows 的内置规则显示名称可能不同，应先检查再修改，不要照抄显示名称批量禁用。

### 实验10：检查并要求 SMB 签名

SMB 签名可以降低 SMB 中继和篡改风险。Windows Server 2025 默认要求入站和出站 SMB 签名；较早系统仍应显式检查和配置。

```powershell
Get-SmbServerConfiguration |
  Select-Object RequireSecuritySignature, EnableSecuritySignature

Get-SmbClientConfiguration |
  Select-Object RequireSecuritySignature, EnableSecuritySignature

Set-SmbServerConfiguration -RequireSecuritySignature $true -Force
Set-SmbClientConfiguration -RequireSecuritySignature $true -Force
```

> 启用前应评估旧版客户端、第三方 NAS 和业务程序兼容性。安全加固不应跳过变更测试。

### 实验11：理解 `Protected Users`

`Protected Users` 是 Active Directory 域中的安全组，不适用于本地账号。对于加入该组的域账号，域控制器会限制 NTLM、摘要式身份验证和凭据委派等较弱机制。

```powershell
# 仅在域控制器上执行，先用测试账号验证兼容性
Get-ADGroupMember -Identity "Protected Users"

Add-ADGroupMember `
  -Identity "Protected Users" `
  -Members "Lab-Privileged-Test"
```

> 不要直接将现有域管理员批量加入该组。应先使用测试账号验证 Kerberos、远程管理、计划任务和旧系统兼容性，避免造成管理中断。

### 实验12：了解 `krbtgt` 密码重置流程

当域已经遭受严重入侵、需要使伪造 Kerberos 票据失效时，才考虑重置 `krbtgt` 密码。该操作不是普通课堂练习，也不应写成两条立即执行的命令。

正确原则：

1. 使用 Microsoft 提供的 `New-KrbtgtKeys.ps1` 脚本或组织批准的流程。
2. 在所有可写域控制器之间确认复制正常。
3. 完成第一次重置后，等待复制和票据生命周期窗口，再进行第二次重置。
4. 在维护窗口中执行，并准备回退与业务验证方案。

官方脚本：<https://github.com/microsoft/New-KrbtgtKeys.ps1>

### 特权访问模型

传统的 Tier 0 / Tier 1 / Tier 2 模型有助于理解账号隔离，但 Microsoft 当前更推荐企业访问模型（Enterprise access model）。课程中应掌握以下原则：

| 账号类型 | 允许登录位置 | 禁止事项 |
| --- | --- | --- |
| 域和身份系统管理账号 | 专用安全管理工作站、域控管理路径 | 不登录普通办公终端和业务服务器 |
| 服务器管理账号 | 专用管理节点、授权服务器 | 不作为日常办公账号 |
| 普通办公账号 | 普通终端和业务系统 | 不授予服务器管理权限 |

---

# 课前检查清单

| 检查项 | 操作 | 通过标准 |
| --- | --- | --- |
| 虚拟机快照 | VMware 快照管理器 | 三台虚拟机均有实验前快照 |
| 双网卡配置 | SRV01 运行 `Get-NetIPAddress -AddressFamily IPv4` | 同时存在 `192.168.10.20` 和 `192.168.100.20` |
| 初始隔离 | Kali 执行 `ping -c 2 192.168.100.30` | 初始状态下不能直接访问 SRV02 |
| IIS 测试页 | SRV02 执行 `Invoke-WebRequest http://127.0.0.1/` | 返回测试页面 |
| `portproxy` | SRV01 执行 `netsh interface portproxy show all` | 只显示本次实验所需规则 |
| 防火墙 | SRV01、SRV02 执行 `Get-NetFirewallProfile` | 三个配置文件均启用 |
| 清理 | 删除临时映射和临时规则 | 实验结束后无遗留监听端口 |

---

# 项目八知识点总结

| 知识点 | 要点 |
| --- | --- |
| 私有地址 | 私有地址不会在公共互联网中直接路由 |
| NAT | 用于地址转换，不是防火墙 |
| `portproxy` | Windows 自带的 TCP 代理，适用于少量端口 |
| RRAS | Windows Server 的路由、NAT 和 VPN 角色 |
| 隧道工具 | 合法运维与攻击滥用并存，应纳入审批、审计和出站控制 |
| 暴露面盘点 | 从资产、网络、服务、身份和日志五个维度排查 |
| SMB 签名 | 降低 SMB 中继和篡改风险 |
| `Protected Users` | 适用于域账号，需要先验证兼容性 |
| 特权访问模型 | 高权限账号只在专用管理路径中使用 |

---

# 课堂思考

1. 为什么 NAT 不能替代防火墙？
2. `portproxy` 与 RRAS NAT 的能力边界有何不同？
3. 为什么服务器出站流量也需要控制？
4. 为什么不应直接将全部域管理员加入 `Protected Users`？
5. 如何设计“管理区 -> 服务器区 -> 域控区”的最小放行规则？

---

# 参考资料

1. Microsoft Learn：[`netsh interface portproxy`](https://learn.microsoft.com/windows-server/networking/technologies/netsh/netsh-interface-portproxy)
2. Microsoft Learn：[Install Remote Access as a VPN server](https://learn.microsoft.com/windows-server/remote/remote-access/get-started-install-ras-as-vpn)
3. Microsoft Learn：[SMB signing overview](https://learn.microsoft.com/windows-server/storage/file-server/smb-signing)
4. Microsoft Learn：[Protected Users security group](https://learn.microsoft.com/windows-server/security/credentials-protection-and-management/protected-users-security-group)
5. Microsoft Learn：[Securing privileged access](https://learn.microsoft.com/security/privileged-access-workstations/privileged-access-access-model)
6. Microsoft GitHub：[`New-KrbtgtKeys.ps1`](https://github.com/microsoft/New-KrbtgtKeys.ps1)
7. frp 官方仓库：[`fatedier/frp`](https://github.com/fatedier/frp)
8. nps 归档仓库：[`ehang-io/nps`](https://github.com/ehang-io/nps)
