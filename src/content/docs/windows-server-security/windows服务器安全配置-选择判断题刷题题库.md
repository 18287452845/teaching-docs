---
title: "《Windows 服务器安全配置》选择 / 判断题刷题题库"
---

# 《Windows 服务器安全配置》选择 / 判断题刷题题库

---

## 第一部分　选择题

### 模块一　账户与本地安全策略（16 题）

**1.** 为降低口令暴力破解风险，本地安全策略中应优先配置的是（　）。

- A. 屏幕分辨率
- B. 账户锁定阈值
- C. 默认打印机
- D. 系统主题

<details><summary>答案与解析</summary>

**答案：B**　账户锁定阈值在连续登录失败达到设定次数后锁定账户，可有效抑制暴力破解。

</details>

**2.** 账户锁定阈值的主要作用是（　）。

- A. 提高磁盘读写速度
- B. 自动延长密码有效期
- C. 连续登录失败达到次数后锁定账户
- D. 关闭防火墙

<details><summary>答案与解析</summary>

**答案：C**　锁定阈值限制连续失败次数，超过即锁定，遏制在线暴力猜解。

</details>

**3.** 密码策略中“复杂性要求”通常指密码应（　）。

- A. 只能使用纯数字
- B. 长度不超过 6 位
- C. 与用户名相同
- D. 包含大小写字母、数字和符号的组合

<details><summary>答案与解析</summary>

**答案：D**　复杂性要求强制混合字符类型，提升口令熵值。

</details>

**4.** 本实验要求本地账户密码最小长度不少于（　）位。

- A. 10
- B. 4
- C. 6
- D. 8

<details><summary>答案与解析</summary>

**答案：A**　实验基线要求密码最小长度不少于 10 位。

</details>

**5.** 本实验要求账户锁定时间不少于（　）分钟。

- A. 1
- B. 15
- C. 5
- D. 0

<details><summary>答案与解析</summary>

**答案：B**　锁定时间不少于 15 分钟，延长攻击者重试间隔。

</details>

**6.** 在无业务需求时，Guest 账户应保持（　）状态。

- A. 启用
- B. 加入管理员组
- C. 禁用
- D. 共享给所有人

<details><summary>答案与解析</summary>

**答案：C**　Guest 易被滥用，无需求时应禁用。

</details>

**7.** “仅授予完成任务所需权限”体现的是（　）。

- A. 最大兼容原则
- B. 匿名访问原则
- C. 默认全允许原则
- D. 最小权限原则

<details><summary>答案与解析</summary>

**答案：D**　最小权限原则要求按需授权，缩小攻击面。

</details>

**8.** 下列做法不符合最小权限原则的是（　）。

- A. 给所有用户完全控制
- B. 按角色分配必要权限
- C. 为审计账号只读授权
- D. 为运维账号授予特定管理权限

<details><summary>答案与解析</summary>

**答案：A**　给所有用户完全控制违反最小权限，风险极高。

</details>

**9.** 审计（auditor）账号通常不应加入的组是（　）。

- A. Users
- B. Administrators
- C. 只读相关组
- D. 普通业务组

<details><summary>答案与解析</summary>

**答案：B**　审计账号默认不应进入 Administrators，避免越权。

</details>

**10.** 配置了账户锁定策略后，关于复杂密码的说法正确的是（　）。

- A. 可以取消复杂密码
- B. 密码可设为空
- C. 仍需要保留复杂密码要求
- D. 锁定策略能替代一切口令要求

<details><summary>答案与解析</summary>

**答案：C**　锁定与复杂密码是互补措施，不能相互替代。

</details>

**11.** 将运维用户授予远程登录权限时，应加入的内置组是（　）。

- A. Guests
- B. Backup Operators
- C. Replicator
- D. Remote Desktop Users

<details><summary>答案与解析</summary>

**答案：D**　Remote Desktop Users 组成员可进行远程桌面登录。

</details>

**12.** 创建本地用户应使用的 PowerShell 命令是（　）。

- A. New-LocalUser
- B. New-Item
- C. New-Website
- D. New-SmbShare

<details><summary>答案与解析</summary>

**答案：A**　New-LocalUser 用于创建本地账户。

</details>

**13.** 禁用本地 Guest 账户可使用的 PowerShell 命令是（　）。

- A. Stop-Service Guest
- B. Disable-LocalUser -Name Guest
- C. Remove-Item Guest
- D. Get-LocalUser Guest

<details><summary>答案与解析</summary>

**答案：B**　Disable-LocalUser 用于禁用本地账户。

</details>

**14.** 查看本机所有本地用户可使用（　）。

- A. Get-Website
- B. Get-SmbShare
- C. Get-LocalUser
- D. Get-Process

<details><summary>答案与解析</summary>

**答案：C**　Get-LocalUser 列出本地用户账户。

</details>

**15.** 账户锁定阈值设置得过低，可能带来的副作用是（　）。

- A. 磁盘空间不足
- B. 网卡速率下降
- C. 显示器老化
- D. 正常用户易被误锁定造成可用性下降

<details><summary>答案与解析</summary>

**答案：D**　阈值过低会让正常误输导致频繁锁定，影响可用性。

</details>

**16.** 管理本地密码与账户锁定策略最直接的工具是（　）。

- A. 本地安全策略 secpol.msc
- B. 画图工具
- C. 记事本
- D. 计算器

<details><summary>答案与解析</summary>

**答案：A**　secpol.msc 集中管理账户策略（密码、锁定）。

</details>

### 模块二　文件权限、共享与 EFS（18 题）

**17.** 远程访问共享目录时，用户最终获得的有效权限通常由共享权限和 NTFS 权限中的（　）决定。

- A. 较宽松权限
- B. 较严格权限
- C. 随机权限
- D. 管理员权限

<details><summary>答案与解析</summary>

**答案：B**　共享与 NTFS 权限叠加时取交集，即“较严格者”生效。

</details>

**18.** 对共享目录进行细粒度访问控制时，应重点配置（　）。

- A. 壁纸
- B. 分辨率
- C. NTFS 权限
- D. 主题颜色

<details><summary>答案与解析</summary>

**答案：C**　NTFS 权限支持到用户/组、文件级的精细控制。

</details>

**19.** EFS 主要用于（　）。

- A. 开放端口
- B. 安装 IIS
- C. 创建域控
- D. 加密 NTFS 文件

<details><summary>答案与解析</summary>

**答案：D**　EFS 对 NTFS 卷上的文件/文件夹进行透明加密。

</details>

**20.** 关于 IIS/共享目录的权限授予，正确的做法是（　）。

- A. 按需授予最小必要权限
- B. 长期授予 Everyone 完全控制
- C. 对所有人开放写入
- D. 禁用所有权限导致服务不可用

<details><summary>答案与解析</summary>

**答案：A**　应最小授权，避免 Everyone 完全控制。

</details>

**21.** 审计账号 auditor 对共享目录应配置的权限是（　）。

- A. 完全控制
- B. 只读
- C. 修改
- D. 写入并删除

<details><summary>答案与解析</summary>

**答案：B**　审计仅需查看，应只读。

</details>

**22.** 发布一个新的 SMB 共享可使用的 PowerShell 命令是（　）。

- A. New-LocalUser
- B. New-Website
- C. New-SmbShare
- D. New-Item

<details><summary>答案与解析</summary>

**答案：C**　New-SmbShare 创建并发布共享。

</details>

**23.** 命令行中修改 NTFS 访问控制列表常用的工具是（　）。

- A. ipconfig
- B. tasklist
- C. ping
- D. icacls

<details><summary>答案与解析</summary>

**答案：D**　icacls 用于查看/授予/移除 NTFS 权限。

</details>

**24.** EFS 加密一个文件后，验证加密状态可使用（　）。

- A. cipher /c 文件
- B. ping 文件
- C. format 文件
- D. copy 文件

<details><summary>答案与解析</summary>

**答案：A**　cipher /c 显示文件的加密状态信息。

</details>

**25.** 要使“普通用户不得访问 Salary 目录”，最直接的做法是（　）。

- A. 提升其为管理员
- B. 移除其在该目录上的访问权限
- C. 给予完全控制
- D. 禁用网卡

<details><summary>答案与解析</summary>

**答案：B**　通过 NTFS 权限移除其访问，实现禁止访问。

</details>

**26.** 共享权限与 NTFS 权限同时生效时，下列说法正确的是（　）。

- A. 取两者中更宽松的结果
- B. 只看共享权限
- C. 取两者中更严格的结果
- D. 只看 NTFS 权限

<details><summary>答案与解析</summary>

**答案：C**　网络访问时两层权限叠加取交集（更严格）。

</details>

**27.** 查看某共享的访问权限可使用（　）。

- A. Get-Date
- B. Get-Clipboard
- C. Get-Process
- D. Get-SmbShareAccess

<details><summary>答案与解析</summary>

**答案：D**　Get-SmbShareAccess 显示共享的访问控制项。

</details>

**28.** EFS 加密的密钥与（　）绑定。

- A. 用户账户/证书
- B. 屏幕分辨率
- C. 网卡 MAC
- D. 打印机

<details><summary>答案与解析</summary>

**答案：A**　EFS 使用用户证书及密钥，换用户无法直接解密。

</details>

**29.** 将 FinanceStaff 组配置为可修改 Salary 目录，应授予的 NTFS 权限大致是（　）。

- A. 只读
- B. 修改（Modify）
- C. 仅列出
- D. 拒绝

<details><summary>答案与解析</summary>

**答案：B**　可修改对应 Modify 权限。

</details>

**30.** 下列关于 Everyone 组的说法正确的是（　）。

- A. 必须授予完全控制
- B. 等同于 Administrators
- C. 应谨慎授权，避免完全控制
- D. 只能用于打印

<details><summary>答案与解析</summary>

**答案：C**　Everyone 范围过广，授权需谨慎。

</details>

**31.** EFS 与 BitLocker 的区别，描述正确的是（　）。

- A. EFS 只能加密整块磁盘
- B. EFS 用于开放端口
- C. EFS 用于安装网站
- D. EFS 针对文件/文件夹级加密

<details><summary>答案与解析</summary>

**答案：D**　EFS 文件级加密，BitLocker 卷级加密。

</details>

**32.** 创建目录结构 D:\CompanyShare\Public 可使用（　）。

- A. New-Item -ItemType Directory
- B. Get-Item
- C. Remove-Item
- D. Set-Date

<details><summary>答案与解析</summary>

**答案：A**　New-Item -ItemType Directory 创建目录。

</details>

**33.** 要让 auditor 在两个目录均“只读”，icacls 中对应的权限标识是（　）。

- A. F（完全控制）
- B. R（读取）
- C. M（修改）
- D. W（写入）

<details><summary>答案与解析</summary>

**答案：B**　R 表示读取权限。

</details>

**34.** 关闭 NTFS 权限继承的目的通常是（　）。

- A. 加快读盘
- B. 开放匿名
- C. 精确控制本目录的权限不被上级覆盖
- D. 卸载磁盘

<details><summary>答案与解析</summary>

**答案：C**　断开继承后可对目录单独设定权限。

</details>

### 模块三　远程桌面 RDP 安全（14 题）

**35.** 启用 RDP 网络级身份验证（NLA）的主要作用是（　）。

- A. 自动关闭防火墙
- B. 允许匿名登录
- C. 将端口改为 80
- D. 登录前完成身份验证

<details><summary>答案与解析</summary>

**答案：D**　NLA 在建立完整会话前先完成身份验证，降低资源消耗与攻击面。

</details>

**36.** 远程桌面默认使用的 TCP 端口是（　）。

- A. 3389
- B. 80
- C. 445
- D. 161

<details><summary>答案与解析</summary>

**答案：A**　RDP 默认监听 TCP 3389。

</details>

**37.** 限制 RDP 来源地址最适合通过（　）实现。

- A. 更换壁纸
- B. Windows 防火墙规则
- C. 删除日志
- D. 关闭网卡

<details><summary>答案与解析</summary>

**答案：B**　通过防火墙规则限定远程地址，实现来源访问控制。

</details>

**38.** 下列关于关闭防火墙解决 RDP 问题的说法，正确的是（　）。

- A. 是推荐做法
- B. 能提升安全
- C. 不推荐，应放行必要端口而非关闭防火墙
- D. 必须永久关闭

<details><summary>答案与解析</summary>

**答案：C**　关闭防火墙扩大风险，应精确放行而非关闭。

</details>

**39.** 仅允许特定用户远程登录，应将其加入（　）。

- A. Guests
- B. Power Users
- C. Print Operators
- D. Remote Desktop Users

<details><summary>答案与解析</summary>

**答案：D**　Remote Desktop Users 控制远程登录授权。

</details>

**40.** 启用 NLA 后，未通过身份验证的连接会（　）。

- A. 被提前拒绝
- B. 直接进入桌面
- C. 获得匿名会话
- D. 自动提权

<details><summary>答案与解析</summary>

**答案：A**　未通过验证者无法建立会话，被提前拒绝。

</details>

**41.** 将 RDP 来源限制为实验网段属于（　）。

- A. 性能优化
- B. 访问控制措施
- C. 日志清理
- D. 端口转发

<details><summary>答案与解析</summary>

**答案：B**　限定来源是有效的网络访问控制。

</details>

**42.** 启用远程桌面在注册表中需将 fDenyTSConnections 设为（　）。

- A. 1
- B. 2
- C. 0
- D. 255

<details><summary>答案与解析</summary>

**答案：C**　fDenyTSConnections=0 表示允许远程桌面连接。

</details>

**43.** 以下哪项不是 RDP 加固的合理措施（　）。

- A. 强制 NLA
- B. 限制来源 IP
- C. 仅授权必要用户
- D. 对所有 IP 开放 3389

<details><summary>答案与解析</summary>

**答案：D**　对所有 IP 开放 3389 扩大暴露面，应限制来源。

</details>

**44.** 为降低 RDP 暴露，可考虑（　）。

- A. 限制来源并强制 NLA
- B. 公网直接开放
- C. 禁用所有日志
- D. 共用管理员账号

<details><summary>答案与解析</summary>

**答案：A**　限制来源+NLA 是常见 RDP 加固组合。

</details>

**45.** RDP 登录成功与失败可在（　）中审计。

- A. 应用程序日志的打印记录
- B. 安全日志
- C. 磁盘碎片报告
- D. 显示设置

<details><summary>答案与解析</summary>

**答案：B**　Windows 安全日志记录 4624/4625 登录事件。

</details>

**46.** 测试到远程主机 3389 端口是否可达可使用（　）。

- A. Get-Date
- B. Get-Clipboard
- C. Test-NetConnection -Port 3389
- D. Get-Volume

<details><summary>答案与解析</summary>

**答案：C**　Test-NetConnection 可测试端口连通性。

</details>

**47.** 将 ops_admin 授予远程登录的命令大致是（　）。

- A. New-Website ops_admin
- B. New-SmbShare ops_admin
- C. Get-Process ops_admin
- D. Add-LocalGroupMember 'Remote Desktop Users' ops_admin

<details><summary>答案与解析</summary>

**答案：D**　把用户加入 Remote Desktop Users 组。

</details>

**48.** RDP 配合 NLA 主要缓解的风险是（　）。

- A. 未认证连接消耗资源与暴露面
- B. 磁盘碎片
- C. 屏幕老化
- D. 打印失败

<details><summary>答案与解析</summary>

**答案：A**　NLA 减少未认证连接带来的暴露与资源占用。

</details>

### 模块四　SMB 协议安全（16 题）

**49.** 下列协议版本中，应在生产环境优先禁用的是（　）。

- A. SMBv3
- B. SMBv1
- C. HTTPS
- D. RDP with NLA

<details><summary>答案与解析</summary>

**答案：B**　SMBv1 存在已知严重漏洞，应优先禁用。

</details>

**50.** 强制启用 SMB 服务端签名，可降低（　）风险。

- A. 屏幕老化
- B. 磁盘碎片
- C. NTLM 中继攻击
- D. 打印失败

<details><summary>答案与解析</summary>

**答案：C**　SMB 签名校验完整性，可缓解 NTLM 中继。

</details>

**51.** SMB 服务通常使用的 TCP 端口是（　）。

- A. 21
- B. 80
- C. 161
- D. 445

<details><summary>答案与解析</summary>

**答案：D**　SMB（CIFS）使用 TCP 445。

</details>

**52.** 限制匿名枚举账户与共享的主要目的是（　）。

- A. 减少信息泄露
- B. 提升显示效果
- C. 安装补丁
- D. 增加容量

<details><summary>答案与解析</summary>

**答案：A**　限制匿名枚举可减少账户/共享信息被探测。

</details>

**53.** 关闭 SMBv1 的主要原因是（　）。

- A. 会占用打印机
- B. 存在严重历史漏洞且易被蠕虫利用
- C. 导致分辨率下降
- D. 无法安装 IIS

<details><summary>答案与解析</summary>

**答案：B**　SMBv1 漏洞（如永恒之蓝）风险高，应禁用。

</details>

**54.** 检查/配置 SMB 服务端参数可使用的 PowerShell 命令是（　）。

- A. Set-Date
- B. Set-Clipboard
- C. Set-SmbServerConfiguration
- D. Set-Location

<details><summary>答案与解析</summary>

**答案：C**　Set-SmbServerConfiguration 配置服务端 SMB 选项。

</details>

**55.** 启用服务端 SMB 签名，对应配置项大致是（　）。

- A. DisableFirewall
- B. EnableGuest
- C. OpenAnonymous
- D. RequireSecuritySignature

<details><summary>答案与解析</summary>

**答案：D**　RequireSecuritySignature=$true 强制签名。

</details>

**56.** SMBv3 相比 SMBv1 的优势包括（　）。

- A. 支持加密、性能与安全性更好
- B. 更易被蠕虫利用
- C. 不支持签名
- D. 只能匿名访问

<details><summary>答案与解析</summary>

**答案：A**　SMBv3 支持传输加密等现代安全特性。

</details>

**57.** 限制 SMB 匿名访问，常涉及的注册表值是（　）。

- A. fDenyTSConnections
- B. RestrictAnonymous
- C. EnableLUA=0
- D. AutoShareWks

<details><summary>答案与解析</summary>

**答案：B**　RestrictAnonymous 限制匿名枚举。

</details>

**58.** 查看本机 SMB 共享列表可使用（　）。

- A. Get-Website
- B. Get-Process
- C. Get-SmbShare
- D. Get-Date

<details><summary>答案与解析</summary>

**答案：C**　Get-SmbShare 列出 SMB 共享。

</details>

**59.** 移除一个多余的测试共享可使用（　）。

- A. Remove-Website
- B. Stop-Process
- C. Clear-Host
- D. Remove-SmbShare

<details><summary>答案与解析</summary>

**答案：D**　Remove-SmbShare 删除指定共享。

</details>

**60.** NTLM 中继攻击中，SMB 签名的作用是（　）。

- A. 校验报文完整性使中继难以成功
- B. 加快传输
- C. 关闭日志
- D. 开放匿名

<details><summary>答案与解析</summary>

**答案：A**　签名保证完整性，破坏中继伪造。

</details>

**61.** 生产环境中关于 SMBv1 的正确态度是（　）。

- A. 始终启用
- B. 尽量禁用
- C. 仅在新系统启用
- D. 作为默认协议

<details><summary>答案与解析</summary>

**答案：B**　应尽量禁用 SMBv1。

</details>

**62.** 禁用 SMBv1 可通过（　）实现。

- A. New-Website
- B. cmdkey /list
- C. Disable-WindowsOptionalFeature -FeatureName SMB1Protocol
- D. Get-Date

<details><summary>答案与解析</summary>

**答案：C**　可通过可选功能或 Set-SmbServerConfiguration 关闭 SMB1。

</details>

**63.** 限制匿名枚举属于（　）类加固。

- A. 性能调优
- B. 显示美化
- C. 驱动更新
- D. 信息泄露防护

<details><summary>答案与解析</summary>

**答案：D**　属于减少信息暴露的加固。

</details>

**64.** SMB 共享的有效访问还会受到（　）影响。

- A. NTFS 权限
- B. 屏幕亮度
- C. CPU 主频
- D. 壁纸

<details><summary>答案与解析</summary>

**答案：A**　SMB 访问同时受 NTFS 权限约束。

</details>

### 模块五　安全日志与事件 ID（14 题）

**65.** Windows 安全日志中，常用于排查登录失败的事件 ID 是（　）。

- A. 4624
- B. 4625
- C. 7045
- D. 1102

<details><summary>答案与解析</summary>

**答案：B**　4625 表示登录失败。

</details>

**66.** Windows 安全日志中，通常表示登录成功的事件 ID 是（　）。

- A. 4625
- B. 1102
- C. 4624
- D. 7045

<details><summary>答案与解析</summary>

**答案：C**　4624 表示登录成功。

</details>

**67.** 事件 ID 1102 通常表示（　）。

- A. 登录成功
- B. 新服务安装
- C. 磁盘已满
- D. 审计日志被清除

<details><summary>答案与解析</summary>

**答案：D**　1102 表示安全审计日志被清除，是重要告警。

</details>

**68.** 事件 ID 7045 通常表示（　）。

- A. 系统中安装了新服务
- B. 登录失败
- C. 日志清除
- D. 共享创建

<details><summary>答案与解析</summary>

**答案：A**　7045 记录新服务的安装，常用于排查持久化。

</details>

**69.** 排查多次登录失败以发现暴力破解，应重点关注（　）。

- A. 4624
- B. 4625
- C. Date
- D. Hostname

<details><summary>答案与解析</summary>

**答案：B**　大量 4625 可能指示暴力破解。

</details>

**70.** 导出安全日志中指定事件可使用（　）。

- A. Get-Volume
- B. Get-Clipboard
- C. Get-WinEvent
- D. Get-Date

<details><summary>答案与解析</summary>

**答案：C**　Get-WinEvent 可按条件检索/导出事件。

</details>

**71.** 登录成功事件 4624 通常包含（　）等信息。

- A. 磁盘温度
- B. 显卡型号
- C. 壁纸路径
- D. 账户名、登录类型、来源

<details><summary>答案与解析</summary>

**答案：D**　4624 含账户、登录类型、源地址等。

</details>

**72.** 发现安全日志被清除（1102）时，应（　）。

- A. 视为可疑并进一步调查
- B. 直接忽略
- C. 关闭服务器
- D. 删除全部账户

<details><summary>答案与解析</summary>

**答案：A**　日志清除可能是攻击者掩盖痕迹的行为。

</details>

**73.** 一次成功 + 一次失败的 RDP 登录测试，应分别对应（　）。

- A. 7045 与 1102
- B. 4624 与 4625
- C. 4624 与 4624
- D. 1102 与 1102

<details><summary>答案与解析</summary>

**答案：B**　成功=4624，失败=4625。

</details>

**74.** 在事件查看器中，登录相关事件主要记录在（　）。

- A. 应用程序日志
- B. Setup 日志
- C. 安全日志
- D. 转发的事件

<details><summary>答案与解析</summary>

**答案：C**　登录审计记录在“安全”日志。

</details>

**75.** 使用 PowerShell 按事件 ID 过滤安全日志的参数是（　）。

- A. -Path C:\
- B. -Port 445
- C. -AsSecureString
- D. -FilterHashtable @{LogName='Security';Id=4625}

<details><summary>答案与解析</summary>

**答案：D**　FilterHashtable 可指定日志名与事件 ID。

</details>

**76.** 关于审计日志的正确做法是（　）。

- A. 妥善保留并定期审查
- B. 随意清除
- C. 只保留一天
- D. 禁用审计

<details><summary>答案与解析</summary>

**答案：A**　日志应保留并定期审查以便取证。

</details>

**77.** 短时间内同一账户出现大量 4625，最可能说明（　）。

- A. 磁盘损坏
- B. 正在遭受口令猜解
- C. 显示器故障
- D. 打印任务过多

<details><summary>答案与解析</summary>

**答案：B**　大量失败登录提示暴力破解。

</details>

**78.** HTTPS 网站排错请求与状态码，应优先看（　）。

- A. SNMP
- B. 壁纸
- C. IIS 访问日志
- D. 注册表 Run 键

<details><summary>答案与解析</summary>

**答案：C**　IIS 访问日志记录请求与状态码（与本模块取证相关）。

</details>

### 模块六　IIS 部署与加固（24 题）

**79.** IIS 默认网站访问日志最适合用于（　）。

- A. 修改本地密码
- B. 创建域用户
- C. 安装驱动
- D. 分析请求和状态码

<details><summary>答案与解析</summary>

**答案：D**　访问日志记录 URL、状态码、客户端等，便于分析。

</details>

**80.** 配置 IIS 自定义 404 页面主要用于（　）。

- A. 减少默认错误信息泄露
- B. 创建共享目录
- C. 允许匿名登录
- D. 增加管理员数量

<details><summary>答案与解析</summary>

**答案：A**　自定义错误页避免暴露默认错误中的路径/版本等信息。

</details>

**81.** IIS 目录浏览在无业务需求时应（　）。

- A. 永久开放
- B. 关闭
- C. 仅对 Guest 开放
- D. 绑定到 3389

<details><summary>答案与解析</summary>

**答案：B**　目录浏览会泄露文件结构，无需求应关闭。

</details>

**82.** IIS 为不同网站配置独立应用程序池的主要价值是（　）。

- A. 关闭日志
- B. 允许匿名共享
- C. 降低相互影响
- D. 绕过防火墙

<details><summary>答案与解析</summary>

**答案：C**　独立应用池实现进程隔离，单站故障不影响其他站。

</details>

**83.** 查看 IIS 网站状态可使用（　）。

- A. Get-LocalUser
- B. Get-SmbShare
- C. Get-Volume
- D. Get-Website

<details><summary>答案与解析</summary>

**答案：D**　Get-Website 列出站点及其状态。

</details>

**84.** 在 IIS 中统一管理站点安全配置常使用（　）。

- A. Web.config
- B. hosts
- C. boot.ini
- D. win.ini

<details><summary>答案与解析</summary>

**答案：A**　Web.config 是站点/应用级配置文件。

</details>

**85.** 同一端口部署多个网站，区分访问最常用（　）。

- A. 更换显示器
- B. 主机名（主机头）绑定
- C. 不同壁纸
- D. 随机端口

<details><summary>答案与解析</summary>

**答案：B**　主机头按域名区分同端口的多个站点。

</details>

**86.** 客户端访问主机头网站前，需要在（　）中添加解析。

- A. boot.ini
- B. 注册表 Run 键
- C. hosts 文件
- D. win.ini

<details><summary>答案与解析</summary>

**答案：C**　实验环境常用 hosts 添加域名到 IP 的解析。

</details>

**87.** 安装 IIS（含管理工具）可使用（　）。

- A. New-LocalUser
- B. cmdkey /list
- C. Get-Date
- D. Install-WindowsFeature Web-Server -IncludeManagementTools

<details><summary>答案与解析</summary>

**答案：D**　Install-WindowsFeature 安装 Web-Server 角色。

</details>

**88.** 创建一个新的应用程序池可使用（　）。

- A. New-WebAppPool
- B. New-SmbShare
- C. New-LocalUser
- D. New-NetIPAddress

<details><summary>答案与解析</summary>

**答案：A**　New-WebAppPool 创建应用池。

</details>

**89.** 创建绑定 8080 端口的网站可使用（　）。

- A. New-SmbShare -Port 8080
- B. New-Website -Port 8080
- C. cmdkey /add
- D. Get-Website -Port

<details><summary>答案与解析</summary>

**答案：B**　New-Website 创建站点并指定端口。

</details>

**90.** 启用 IIS 访问日志的主要意义是（　）。

- A. 加快网页加载
- B. 关闭防火墙
- C. 便于审计请求与排查问题
- D. 隐藏站点

<details><summary>答案与解析</summary>

**答案：C**　日志用于审计与排错。

</details>

**91.** 关闭目录浏览的安全意义是（　）。

- A. 提升分辨率
- B. 加密磁盘
- C. 增加端口
- D. 避免泄露目录结构与文件清单

<details><summary>答案与解析</summary>

**答案：D**　关闭后访问目录不再列出文件。

</details>

**92.** 自定义 404 与默认 404 相比，优点是（　）。

- A. 减少服务器信息泄露
- B. 暴露更多路径
- C. 提升匿名权限
- D. 关闭日志

<details><summary>答案与解析</summary>

**答案：A**　自定义错误页避免泄露默认错误细节。

</details>

**93.** 测试本机 8080 端口连通性可使用（　）。

- A. net user
- B. Test-NetConnection 127.0.0.1 -Port 8080
- C. gpupdate /force
- D. hostname

<details><summary>答案与解析</summary>

**答案：B**　Test-NetConnection 测试端口连通性。

</details>

**94.** 独立应用程序池带来的隔离主要体现在（　）。

- A. 共享同一进程
- B. 统一崩溃
- C. 工作进程相互独立、故障不串扰
- D. 绕过权限

<details><summary>答案与解析</summary>

**答案：C**　应用池=独立 w3wp 进程，隔离故障与身份。

</details>

**95.** IIS 中要让某站点经域名访问，需配置（　）。

- A. 壁纸
- B. 屏保
- C. 打印机
- D. 站点绑定的主机名

<details><summary>答案与解析</summary>

**答案：D**　绑定中的主机名决定域名访问。

</details>

**96.** 查看某网站绑定信息可使用（　）。

- A. Get-WebBinding
- B. Get-Date
- C. Get-Clipboard
- D. Get-Volume

<details><summary>答案与解析</summary>

**答案：A**　Get-WebBinding 查看站点绑定。

</details>

**97.** IIS 访问日志中最能反映请求结果的是（　）。

- A. 磁盘温度
- B. HTTP 状态码
- C. CPU 风扇转速
- D. 屏幕亮度

<details><summary>答案与解析</summary>

**答案：B**　状态码（200/404/500 等）反映请求结果。

</details>

**98.** 部署静态首页文件通常命名为（　）。

- A. boot.ini
- B. hosts
- C. index.html
- D. win.ini

<details><summary>答案与解析</summary>

**答案：C**　默认文档常用 index.html。

</details>

**99.** 将网站物理路径指向 C:\SecurePortal，对应参数是（　）。

- A. -Port
- B. -AsSecureString
- C. -RemoteAddress
- D. -PhysicalPath

<details><summary>答案与解析</summary>

**答案：D**　New-Website 的 -PhysicalPath 指定站点根目录。

</details>

**100.** 两个网站使用同一 80 端口但不同域名，依赖（　）区分。

- A. Host Header 主机头
- B. 不同分辨率
- C. 不同壁纸
- D. 不同显卡

<details><summary>答案与解析</summary>

**答案：A**　主机头区分同端口多站点。

</details>

**101.** IIS 站点级安全配置（如响应头、错误页）通常落在（　）。

- A. hosts
- B. web.config
- C. 桌面快捷方式
- D. 回收站

<details><summary>答案与解析</summary>

**答案：B**　web.config 承载站点配置。

</details>

**102.** 关闭目录浏览后，直接访问目录将（　）。

- A. 显示全部文件
- B. 下载整个磁盘
- C. 不再列出文件清单
- D. 开放匿名写

<details><summary>答案与解析</summary>

**答案：C**　目录浏览关闭后不列文件。

</details>

### 模块七　Web 安全响应头（10 题）

**103.** 为减少网站被点击劫持的风险，可添加的响应头是（　）。

- A. Server
- B. Date
- C. Content-Length
- D. X-Frame-Options

<details><summary>答案与解析</summary>

**答案：D**　X-Frame-Options 限制页面被 iframe 嵌套，防点击劫持。

</details>

**104.** IIS 响应头 X-Content-Type-Options 常用值是（　）。

- A. nosniff
- B. public
- C. anonymous
- D. allow

<details><summary>答案与解析</summary>

**答案：A**　nosniff 禁止浏览器 MIME 嗅探。

</details>

**105.** X-Frame-Options 设为 SAMEORIGIN 的含义是（　）。

- A. 允许任意站点嵌套
- B. 仅允许同源页面框架嵌套
- C. 禁止一切访问
- D. 开放匿名

<details><summary>答案与解析</summary>

**答案：B**　SAMEORIGIN 仅允许同源 iframe 嵌套。

</details>

**106.** X-Content-Type-Options: nosniff 的作用是（　）。

- A. 加密传输
- B. 关闭日志
- C. 阻止浏览器猜测响应内容类型
- D. 提升带宽

<details><summary>答案与解析</summary>

**答案：C**　防止 MIME 类型嗅探导致的脚本注入风险。

</details>

**107.** 点击劫持（Clickjacking）防护主要依赖（　）。

- A. Content-Length
- B. Server 头
- C. Date 头
- D. X-Frame-Options / CSP frame-ancestors

<details><summary>答案与解析</summary>

**答案：D**　通过框架嵌套限制头进行防护。

</details>

**108.** 在 IIS 中添加自定义响应头，配置节点是（　）。

- A. httpProtocol/customHeaders
- B. directoryBrowse
- C. appPools 名称
- D. hosts

<details><summary>答案与解析</summary>

**答案：A**　customHeaders 用于添加 HTTP 响应头。

</details>

**109.** 下列属于安全相关响应头的是（　）。

- A. Content-Length
- B. X-Frame-Options
- C. Date
- D. Server

<details><summary>答案与解析</summary>

**答案：B**　X-Frame-Options 属安全头，其余多为信息性头。

</details>

**110.** nosniff 可缓解的风险场景是（　）。

- A. 磁盘碎片
- B. 打印失败
- C. 将文本误当作可执行脚本解析
- D. 屏幕老化

<details><summary>答案与解析</summary>

**答案：C**　防止内容类型被错误解析执行。

</details>

**111.** 响应头 Server 暴露版本信息，安全上倾向于（　）。

- A. 完整公开
- B. 设为 nosniff
- C. 绑定 3389
- D. 隐藏或精简

<details><summary>答案与解析</summary>

**答案：D**　隐藏 Server 头减少指纹信息泄露。

</details>

**112.** 同时添加 nosniff 与 SAMEORIGIN，目的是（　）。

- A. 缓解 MIME 嗅探与点击劫持
- B. 开放匿名访问
- C. 关闭日志
- D. 提升分辨率

<details><summary>答案与解析</summary>

**答案：A**　两头分别防嗅探与点击劫持。

</details>

### 模块八　HTTPS 与传输安全（8 题）

**113.** HTTPS 主要提升网站传输过程中的（　）。

- A. 磁盘容量
- B. 机密性和完整性
- C. CPU 主频
- D. 用户数量

<details><summary>答案与解析</summary>

**答案：B**　HTTPS 通过 TLS 提供加密（机密性）与完整性保护。

</details>

**114.** 在隔离实验环境为网站启用 HTTPS，可创建（　）。

- A. 虚拟打印机
- B. 新本地用户
- C. 自签名证书
- D. 新共享

<details><summary>答案与解析</summary>

**答案：C**　实验中常用自签名证书完成 HTTPS 绑定。

</details>

**115.** 为网站增加 HTTPS 绑定时，需要关联（　）。

- A. 壁纸
- B. 打印机
- C. 声卡
- D. 服务器证书

<details><summary>答案与解析</summary>

**答案：D**　HTTPS 绑定需选择服务器证书。

</details>

**116.** 创建自签名证书的 PowerShell 命令是（　）。

- A. New-SelfSignedCertificate
- B. New-SmbShare
- C. New-LocalUser
- D. New-Item

<details><summary>答案与解析</summary>

**答案：A**　New-SelfSignedCertificate 生成自签名证书。

</details>

**117.** HTTPS 配置完成后，关于访问日志的正确做法是（　）。

- A. 可立即关闭
- B. 仍应保留以便审计
- C. 必须删除
- D. 与日志无关

<details><summary>答案与解析</summary>

**答案：B**　HTTPS 与是否保留日志无关，日志应保留。

</details>

**118.** HTTPS 默认使用的端口通常是（　）。

- A. 80
- B. 21
- C. 443
- D. 3389

<details><summary>答案与解析</summary>

**答案：C**　HTTPS 默认端口为 443（实验可自定义如 8443）。

</details>

**119.** HTTPS 相对 HTTP 的核心改进是（　）。

- A. 提升磁盘容量
- B. 增加 CPU 核数
- C. 扩大显示分辨率
- D. 传输加密与完整性校验

<details><summary>答案与解析</summary>

**答案：D**　TLS 提供加密与完整性。

</details>

**120.** 自签名证书在生产环境的局限是（　）。

- A. 不被外部客户端默认信任
- B. 无法加密
- C. 必须明文
- D. 不能绑定网站

<details><summary>答案与解析</summary>

**答案：A**　自签名证书默认不被外部信任，多用于内部/实验。

</details>

### 模块九　FTP 服务安全（12 题）

**121.** FTP 服务通常使用的控制连接端口是（　）。

- A. 22
- B. 21
- C. 3389
- D. 445

<details><summary>答案与解析</summary>

**答案：B**　FTP 控制连接默认使用 TCP 21。

</details>

**122.** FTP 基本身份验证的主要安全问题是（　）。

- A. 无法传输文件
- B. 只能本机访问
- C. 凭据可能明文传输
- D. 必须使用域控

<details><summary>答案与解析</summary>

**答案：C**　基本认证下口令可能以明文传输，易被嗅探。

</details>

**123.** 关闭 FTP 匿名访问可以（　）。

- A. 提升分辨率
- B. 关闭日志
- C. 增加磁盘
- D. 减少未授权访问风险

<details><summary>答案与解析</summary>

**答案：D**　禁用匿名可降低未授权访问。

</details>

**124.** 部署仅供 ftp_user 使用的 FTP 站点，应（　）。

- A. 启用基本认证、禁用匿名、仅授权该用户
- B. 开放匿名给所有人
- C. 授予 Everyone 完全控制
- D. 关闭防火墙

<details><summary>答案与解析</summary>

**答案：A**　限定认证用户、禁匿名是基本加固。

</details>

**125.** FTP 站点要可被外部访问，防火墙应（　）。

- A. 关闭所有端口
- B. 放行 TCP 21（及数据端口）
- C. 仅开放 3389
- D. 禁用网卡

<details><summary>答案与解析</summary>

**答案：B**　需放行 FTP 控制/数据端口。

</details>

**126.** 安装 IIS FTP 服务可使用（　）。

- A. New-LocalUser
- B. cmdkey /list
- C. Install-WindowsFeature Web-Ftp-Server
- D. Get-Date

<details><summary>答案与解析</summary>

**答案：C**　安装 Web-Ftp-Server 角色服务。

</details>

**127.** 相比 FTP，更安全的文件传输可考虑（　）。

- A. Telnet
- B. 明文 HTTP
- C. 关闭认证
- D. FTPS / SFTP 等加密方式

<details><summary>答案与解析</summary>

**答案：D**　加密传输优于明文 FTP。

</details>

**128.** FTP 基本认证下口令明文传输，缓解思路是（　）。

- A. 启用 FTP over TLS（FTPS）
- B. 改用更大字体
- C. 降低分辨率
- D. 关闭日志

<details><summary>答案与解析</summary>

**答案：A**　FTPS 对控制/数据通道加密。

</details>

**129.** 仅授权 ftp_user 访问 FTP 目录，应配合（　）。

- A. 壁纸设置
- B. NTFS 权限
- C. 屏保
- D. 声音设置

<details><summary>答案与解析</summary>

**答案：B**　用 NTFS 权限限定目录访问。

</details>

**130.** 创建 FTP 站点的 PowerShell 命令大致是（　）。

- A. New-SmbShare
- B. New-LocalGroup
- C. New-WebFtpSite
- D. New-NetIPAddress

<details><summary>答案与解析</summary>

**答案：C**　New-WebFtpSite 创建 FTP 站点。

</details>

**131.** FTP 匿名访问开启的风险是（　）。

- A. 提升安全
- B. 加密传输
- C. 隐藏站点
- D. 任何人可未授权访问

<details><summary>答案与解析</summary>

**答案：D**　匿名访问导致未授权风险。

</details>

**132.** FTP 验证应包含的客户端操作通常有（　）。

- A. 登录、上传、下载
- B. 更换壁纸
- C. 重启打印机
- D. 调亮屏幕

<details><summary>答案与解析</summary>

**答案：A**　完成登录与上传下载验证可用性与权限。

</details>

### 模块十　SNMP 安全（14 题）

**133.** SNMP 默认查询端口通常是（　）。

- A. TCP 161
- B. UDP 161
- C. UDP 3389
- D. TCP 445

<details><summary>答案与解析</summary>

**答案：B**　SNMP 查询默认使用 UDP 161。

</details>

**134.** SNMP 使用默认 public 团体名的主要风险是（　）。

- A. 无法启动 IIS
- B. 无法创建用户
- C. 容易泄露系统信息
- D. 自动关闭共享

<details><summary>答案与解析</summary>

**答案：C**　默认 public 易被读取系统信息。

</details>

**135.** SNMP 中用于标识可查询对象层次位置的是（　）。

- A. SID
- B. RID
- C. PID
- D. OID

<details><summary>答案与解析</summary>

**答案：D**　OID（对象标识符）标识 MIB 中对象的层次位置。

</details>

**136.** 加固 SNMP 时，对默认 public 团体名应（　）。

- A. 删除或替换为新团体名
- B. 保持不变
- C. 公开发布
- D. 设为空

<details><summary>答案与解析</summary>

**答案：A**　删除/更换默认团体名以降低风险。

</details>

**137.** 进一步收紧 SNMP，可（　）。

- A. 对所有 IP 开放
- B. 仅允许指定管理端 IP 访问
- C. 关闭防火墙
- D. 开放写权限给所有人

<details><summary>答案与解析</summary>

**答案：B**　限制可访问的管理端来源。

</details>

**138.** 通过 SNMP 团体名可查询到的常见信息包括（　）。

- A. 管理员明文口令
- B. 磁盘加密密钥
- C. 系统描述、主机名、运行时间
- D. BIOS 密码

<details><summary>答案与解析</summary>

**答案：C**　可读取系统描述、运行时间等信息。

</details>

**139.** 更换团体名并限制来源后，验证方式是（　）。

- A. 二者都成功
- B. 二者都失败
- C. 无需验证
- D. 旧团体名失败、新团体名成功

<details><summary>答案与解析</summary>

**答案：D**　应确认旧名失效、新名可用。

</details>

**140.** SNMP 团体名在只读场景应设为（　）。

- A. 只读（READ ONLY）
- B. 可读写
- C. 完全控制
- D. 匿名

<details><summary>答案与解析</summary>

**答案：A**　监控只读即可，避免读写。

</details>

**141.** 确认本机 UDP 161 是否开放可使用（　）。

- A. Get-Website
- B. Get-NetUDPEndpoint
- C. Get-SmbShare
- D. Get-Date

<details><summary>答案与解析</summary>

**答案：B**　Get-NetUDPEndpoint 查看 UDP 端点。

</details>

**142.** SNMP 加固后重启服务可使用（　）。

- A. Restart-Computer
- B. Stop-Process SNMP
- C. Restart-Service SNMP
- D. Clear-Host

<details><summary>答案与解析</summary>

**答案：C**　Restart-Service 重启 SNMP 服务使配置生效。

</details>

**143.** SNMP 限制管理端 IP，相关配置项常涉及（　）。

- A. fDenyTSConnections
- B. RestrictAnonymous
- C. AutoShare
- D. PermittedManagers

<details><summary>答案与解析</summary>

**答案：D**　PermittedManagers 限定允许的管理端。

</details>

**144.** SNMP 默认团体名风险的本质是（　）。

- A. 弱默认凭据导致信息暴露
- B. 端口太大
- C. UDP 不可用
- D. 无法解析域名

<details><summary>答案与解析</summary>

**答案：A**　public 属弱默认凭据。

</details>

**145.** 对外暴露 SNMP 且使用 public，攻击者可（　）。

- A. 直接格式化磁盘
- B. 枚举系统信息辅助进一步攻击
- C. 重置 BIOS
- D. 提升显示分辨率

<details><summary>答案与解析</summary>

**答案：B**　信息枚举可为后续攻击铺路。

</details>

**146.** SNMP 信息收集属于（　）阶段的典型活动。

- A. 数据销毁
- B. 物理破坏
- C. 信息收集/侦察
- D. 界面美化

<details><summary>答案与解析</summary>

**答案：C**　SNMP 常用于信息收集。

</details>

### 模块十一　数据保护与恢复（10 题）

**147.** 卷影副本的主要用途是（　）。

- A. 修改 RDP 端口
- B. 安装 IIS
- C. 开放匿名访问
- D. 辅助恢复文件历史版本

<details><summary>答案与解析</summary>

**答案：D**　卷影副本（Shadow Copy）保存历史版本，便于恢复。

</details>

**148.** 通过“以前的版本”恢复文件，依赖于（　）。

- A. 卷影副本/快照
- B. 壁纸缓存
- C. 打印队列
- D. 屏保

<details><summary>答案与解析</summary>

**答案：A**　“以前的版本”读取卷影副本中的历史快照。

</details>

**149.** 创建一次卷影副本的命令大致是（　）。

- A. New-LocalUser
- B. vssadmin create shadow /for=D:
- C. cmdkey /list
- D. Get-Date

<details><summary>答案与解析</summary>

**答案：B**　vssadmin create shadow 创建快照。

</details>

**150.** 查看现有卷影副本可使用（　）。

- A. Get-Website
- B. Get-SmbShare
- C. vssadmin list shadows
- D. ping

<details><summary>答案与解析</summary>

**答案：C**　vssadmin list shadows 列出已有快照。

</details>

**151.** 误删文件后，利用卷影副本恢复属于（　）。

- A. 信息收集
- B. 点击劫持
- C. 端口转发
- D. 数据可用性/恢复能力

<details><summary>答案与解析</summary>

**答案：D**　属于数据保护与恢复范畴。

</details>

**152.** EFS 与卷影副本相比，前者侧重（　）。

- A. 机密性（加密）
- B. 历史版本恢复
- C. 端口管理
- D. 站点部署

<details><summary>答案与解析</summary>

**答案：A**　EFS 提供加密（机密性），卷影副本提供恢复。

</details>

**153.** 配置卷影副本前后应分别（　）。

- A. 关闭日志
- B. 留存证据以便对比
- C. 删除账户
- D. 禁用网卡

<details><summary>答案与解析</summary>

**答案：B**　前后留证用于验证恢复效果。

</details>

**154.** 卷影副本通常以（　）为单位进行配置。

- A. 单个像素
- B. 打印任务
- C. 卷（如 D:）
- D. 壁纸

<details><summary>答案与解析</summary>

**答案：C**　卷影副本按卷启用与计划。

</details>

**155.** 演示历史版本恢复时，合理的步骤是（　）。

- A. 格式化→重装
- B. 关机→拔电
- C. 删除所有数据
- D. 写入→快照→修改/删除→还原

<details><summary>答案与解析</summary>

**答案：D**　先建快照再制造变化最后还原。

</details>

**156.** 下列属于数据保护措施的是（　）。

- A. 卷影副本与 EFS 加密
- B. 关闭防火墙
- C. 公开 SNMP
- D. 开放匿名共享

<details><summary>答案与解析</summary>

**答案：A**　卷影副本+EFS 属数据保护。

</details>

### 模块十二　持久化排查与应急响应（18 题）

**157.** 排查注册表自启动项时，常见检查位置是（　）。

- A. HKCU\Console
- B. HKCU\Software\Microsoft\Windows\CurrentVersion\Run
- C. HKLM\HARDWARE
- D. HKCR\CLSID

<details><summary>答案与解析</summary>

**答案：B**　Run 键是常见自启动持久化位置。

</details>

**158.** 排查计划任务中的异常启动项可优先使用（　）。

- A. Get-Disk
- B. Get-Clipboard
- C. Get-ScheduledTask
- D. Get-Date

<details><summary>答案与解析</summary>

**答案：C**　Get-ScheduledTask 列出计划任务。

</details>

**159.** 检查自动启动服务及其路径时，可优先使用（　）。

- A. Get-Date
- B. Get-Clipboard
- C. Get-Location
- D. Get-CimInstance Win32_Service

<details><summary>答案与解析</summary>

**答案：D**　Win32_Service 可查看服务及其可执行路径。

</details>

**160.** 限制 IIS 上传目录执行脚本的主要目的是（　）。

- A. 降低 WebShell 风险
- B. 提高匿名权限
- C. 关闭日志
- D. 增加端口

<details><summary>答案与解析</summary>

**答案：A**　禁止上传目录执行脚本可防 WebShell 落地执行。

</details>

**161.** 发现可疑服务时，合适的处理顺序是（　）。

- A. 删除全部服务
- B. 留证、判断、处置、复查
- C. 关闭服务器
- D. 忽略

<details><summary>答案与解析</summary>

**答案：B**　应先取证再判断处置并复查。

</details>

**162.** 清理持久化项后，下一步应（　）。

- A. 立即关闭日志
- B. 删除全部账户
- C. 再次检查并保存证据
- D. 关闭防火墙

<details><summary>答案与解析</summary>

**答案：C**　处置后应复查并留证。

</details>

**163.** 检查 Windows 已缓存网络凭据可以使用（　）。

- A. whoami
- B. hostname
- C. route print
- D. cmdkey /list

<details><summary>答案与解析</summary>

**答案：D**　cmdkey /list 列出缓存凭据。

</details>

**164.** 删除某条缓存凭据可使用（　）。

- A. cmdkey /delete:目标
- B. cmdkey /list
- C. whoami
- D. hostname

<details><summary>答案与解析</summary>

**答案：A**　cmdkey /delete 删除指定凭据。

</details>

**165.** 发现不认识的系统服务后，正确做法是（　）。

- A. 立即全部删除
- B. 先留证据再判断是否清理
- C. 直接重装系统
- D. 忽略不管

<details><summary>答案与解析</summary>

**答案：B**　先取证再判断，避免误删。

</details>

**166.** 计划任务中非 Microsoft 的项（　）。

- A. 一定都是恶意
- B. 一定都安全
- C. 需结合证据判断，不一定都是恶意
- D. 无需关注

<details><summary>答案与解析</summary>

**答案：C**　非 MS 项需结合证据分析，不能一概而论。

</details>

**167.** 上传目录禁止执行脚本，可通过（　）实现。

- A. 开放匿名写
- B. 关闭日志
- C. 提升应用池权限
- D. 处理程序映射/请求筛选限制脚本扩展名

<details><summary>答案与解析</summary>

**答案：D**　限制脚本扩展名/执行权限阻断 WebShell。

</details>

**168.** WebShell 的典型危害是（　）。

- A. 攻击者借此远程控制网站/服务器
- B. 提升屏幕亮度
- C. 加快磁盘
- D. 美化界面

<details><summary>答案与解析</summary>

**答案：A**　WebShell 可被远程控制利用。

</details>

**169.** 应急取证时优先保证（　）。

- A. 尽快删除可疑文件
- B. 证据完整性，先取证后处置
- C. 关机断电
- D. 格式化磁盘

<details><summary>答案与解析</summary>

**答案：B**　先取证保证可追溯。

</details>

**170.** 检查用户启动目录属于排查（　）。

- A. 显示设置
- B. 打印设置
- C. 持久化/自启动项
- D. 声音设置

<details><summary>答案与解析</summary>

**答案：C**　启动目录是常见自启动位置。

</details>

**171.** 排查持久化的常见位置不包括（　）。

- A. Run 键
- B. 计划任务
- C. 启动目录
- D. HKLM\HARDWARE

<details><summary>答案与解析</summary>

**答案：D**　HARDWARE 一般非持久化位置；Run/计划任务/启动目录才是。

</details>

**172.** 可疑自动启动服务，重点核对其（　）。

- A. 可执行文件路径与签名
- B. 壁纸
- C. 分辨率
- D. 字体

<details><summary>答案与解析</summary>

**答案：A**　核对服务对应的可执行路径与签名。

</details>

**173.** 处置可疑项后“复查”的意义是（　）。

- A. 美化系统
- B. 确认是否清除干净、有无残留或再生
- C. 提升带宽
- D. 增大磁盘

<details><summary>答案与解析</summary>

**答案：B**　复查确认处置效果，防止残留/复发。

</details>

**174.** 限制上传目录脚本执行属于（　）。

- A. 物理安全
- B. 显示优化
- C. 纵深防御中的应用层加固
- D. 打印管理

<details><summary>答案与解析</summary>

**答案：C**　属于应用层防护的一环。

</details>

### 模块十三　常用命令与排查工具（26 题）

**175.** 检查当前服务器共享列表可使用的 PowerShell 命令是（　）。

- A. Get-Process
- B. Get-HotFix
- C. Get-Service DNS
- D. Get-SmbShare

<details><summary>答案与解析</summary>

**答案：D**　Get-SmbShare 列出 SMB 共享。

</details>

**176.** 查看 TCP 监听端口可优先使用（　）。

- A. Get-NetTCPConnection
- B. Get-LocalUser
- C. Get-Website
- D. Get-SmbShareAccess

<details><summary>答案与解析</summary>

**答案：A**　Get-NetTCPConnection 查看 TCP 连接/监听。

</details>

**177.** 用于查看 Windows 防火墙规则的 PowerShell 命令是（　）。

- A. Get-SmbShare
- B. Get-NetFirewallRule
- C. Get-Website
- D. Get-LocalGroup

<details><summary>答案与解析</summary>

**答案：B**　Get-NetFirewallRule 列出防火墙规则。

</details>

**178.** 查看 IIS 网站状态可使用（　）。

- A. Get-LocalUser
- B. Get-SmbShare
- C. Get-Website
- D. Get-Volume

<details><summary>答案与解析</summary>

**答案：C**　Get-Website 显示站点状态。

</details>

**179.** 排查计划任务可优先使用（　）。

- A. Get-Disk
- B. Get-Clipboard
- C. Get-Date
- D. Get-ScheduledTask

<details><summary>答案与解析</summary>

**答案：D**　Get-ScheduledTask 列出计划任务。

</details>

**180.** 检查自动启动服务及其路径，可优先使用（　）。

- A. Get-CimInstance Win32_Service
- B. Get-Date
- C. Get-Clipboard
- D. Get-Location

<details><summary>答案与解析</summary>

**答案：A**　Win32_Service 查看服务及路径。

</details>

**181.** 测试本机 8080 端口连通性可使用（　）。

- A. net user
- B. Test-NetConnection 127.0.0.1 -Port 8080
- C. gpupdate /force
- D. hostname

<details><summary>答案与解析</summary>

**答案：B**　Test-NetConnection 测试端口连通。

</details>

**182.** 检查 Windows 已缓存网络凭据可以使用（　）。

- A. whoami
- B. hostname
- C. cmdkey /list
- D. route print

<details><summary>答案与解析</summary>

**答案：C**　cmdkey /list 查看缓存凭据。

</details>

**183.** 查看本机主机名最直接的命令是（　）。

- A. ping
- B. format
- C. copy
- D. hostname

<details><summary>答案与解析</summary>

**答案：D**　hostname 输出计算机名。

</details>

**184.** 查看 IPv4 地址可使用（　）。

- A. Get-NetIPAddress / ipconfig
- B. Get-Website
- C. Get-SmbShare
- D. Get-Date

<details><summary>答案与解析</summary>

**答案：A**　Get-NetIPAddress 或 ipconfig 查看 IP。

</details>

**185.** 查看操作系统版本信息可使用（　）。

- A. Get-Clipboard
- B. Get-CimInstance Win32_OperatingSystem
- C. Get-Volume
- D. Get-SmbShare

<details><summary>答案与解析</summary>

**答案：B**　Win32_OperatingSystem 含版本信息。

</details>

**186.** 创建本地组可使用（　）。

- A. New-Website
- B. New-Item
- C. New-LocalGroup
- D. New-SmbShare

<details><summary>答案与解析</summary>

**答案：C**　New-LocalGroup 创建本地组。

</details>

**187.** 把用户加入某本地组可使用（　）。

- A. Add-Content
- B. Add-Computer
- C. Add-Printer
- D. Add-LocalGroupMember

<details><summary>答案与解析</summary>

**答案：D**　Add-LocalGroupMember 添加组成员。

</details>

**188.** 配置 SMB 服务端参数（如签名）可使用（　）。

- A. Set-SmbServerConfiguration
- B. Set-Date
- C. Set-Clipboard
- D. Set-Location

<details><summary>答案与解析</summary>

**答案：A**　Set-SmbServerConfiguration 配置 SMB 服务端。

</details>

**189.** 创建网站使用（　），创建应用池使用 New-WebAppPool。

- A. New-LocalUser
- B. New-Website
- C. New-SmbShare
- D. New-NetIPAddress

<details><summary>答案与解析</summary>

**答案：B**　New-Website 创建站点。

</details>

**190.** 安装 Windows 角色/功能可使用（　）。

- A. Install-Module 只装PS模块
- B. cmdkey
- C. Install-WindowsFeature
- D. whoami

<details><summary>答案与解析</summary>

**答案：C**　Install-WindowsFeature 安装服务器角色/功能。

</details>

**191.** 检索安全日志事件可使用（　）。

- A. Get-Website
- B. Get-SmbShare
- C. Get-Volume
- D. Get-WinEvent

<details><summary>答案与解析</summary>

**答案：D**　Get-WinEvent 检索事件日志。

</details>

**192.** 查看某共享访问权限可使用（　）。

- A. Get-SmbShareAccess
- B. Get-Date
- C. Get-Clipboard
- D. Get-Process

<details><summary>答案与解析</summary>

**答案：A**　Get-SmbShareAccess 查看共享 ACL。

</details>

**193.** 查看 UDP 端点（如 SNMP 161）可使用（　）。

- A. Get-Website
- B. Get-NetUDPEndpoint
- C. Get-SmbShare
- D. Get-Date

<details><summary>答案与解析</summary>

**答案：B**　Get-NetUDPEndpoint 查看 UDP 端点。

</details>

**194.** 命令行修改 NTFS 权限可使用（　）。

- A. ipconfig
- B. tasklist
- C. icacls
- D. route

<details><summary>答案与解析</summary>

**答案：C**　icacls 管理 NTFS 权限。

</details>

**195.** 查看/创建卷影副本可使用（　）。

- A. whoami
- B. hostname
- C. ping
- D. vssadmin

<details><summary>答案与解析</summary>

**答案：D**　vssadmin 管理卷影副本。

</details>

**196.** 查看自启动命令的 WMI 类是（　）。

- A. Win32_StartupCommand
- B. Win32_BIOS
- C. Win32_Printer
- D. Win32_DiskDrive

<details><summary>答案与解析</summary>

**答案：A**　Win32_StartupCommand 列出启动项。

</details>

**197.** 以下命令与“查看本地用户”最相关的是（　）。

- A. Get-Website
- B. Get-LocalUser
- C. Get-SmbShare
- D. Get-Date

<details><summary>答案与解析</summary>

**答案：B**　Get-LocalUser 列出本地用户。

</details>

**198.** 删除指定缓存凭据使用（　）。

- A. cmdkey /list
- B. whoami
- C. cmdkey /delete:目标
- D. hostname

<details><summary>答案与解析</summary>

**答案：C**　cmdkey /delete 删除凭据。

</details>

**199.** 查看本机所有本地组可使用（　）。

- A. Get-Website
- B. Get-Volume
- C. Get-Date
- D. Get-LocalGroup

<details><summary>答案与解析</summary>

**答案：D**　Get-LocalGroup 列出本地组。

</details>

**200.** 查看 IIS 应用程序池可使用（　）。

- A. Get-IISAppPool / Get-Item IIS:\AppPools
- B. Get-SmbShare
- C. Get-LocalUser
- D. Get-Disk

<details><summary>答案与解析</summary>

**答案：A**　可用 Get-IISAppPool 或 WebAdministration 提供程序查看应用池。

</details>

---

## 第二部分　判断题（√ / ×）

### 模块一　账户与本地安全策略（8 题）

**1.** Guest 账户在无业务需求时应保持禁用状态。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　减少可被滥用的默认账户。

</details>

**2.** 配置账户锁定策略后，就不再需要复杂密码。（　）

<details><summary>答案与解析</summary>

**答案：×（错误）**　两者互补，复杂密码仍需保留。

</details>

**3.** 审计账号应默认加入 Administrators 组。（　）

<details><summary>答案与解析</summary>

**答案：×（错误）**　审计账号应低权限，不应进管理员组。

</details>

**4.** 最小权限原则要求只授予完成任务所必需的权限。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　按需授权，缩小攻击面。

</details>

**5.** 账户锁定阈值越大越安全。（　）

<details><summary>答案与解析</summary>

**答案：×（错误）**　阈值过大削弱防暴破效果，应取适中值。

</details>

**6.** 密码复杂性要求有助于提升口令强度。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　混合字符类型提高破解难度。

</details>

**7.** 多人共用同一管理员账号便于追责。（　）

<details><summary>答案与解析</summary>

**答案：×（错误）**　共用账号无法区分责任，应独立账号。

</details>

**8.** 锁定时间设置为 15 分钟可延长攻击者重试间隔。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　延长重试间隔抑制暴力破解。

</details>

### 模块二　文件权限、共享与 EFS（8 题）

**9.** 远程访问时有效权限取共享权限与 NTFS 权限中较严格者。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　两层权限取交集。

</details>

**10.** IIS 网站目录应长期授予 Everyone 完全控制权限。（　）

<details><summary>答案与解析</summary>

**答案：×（错误）**　应最小授权，避免 Everyone 完全控制。

</details>

**11.** EFS 可用于对 NTFS 文件进行加密。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　EFS 是 NTFS 的文件级加密功能。

</details>

**12.** 对共享目录做细粒度控制时 NTFS 权限比单纯共享权限更精细。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　NTFS 可精确到用户/文件级。

</details>

**13.** 只读权限足以满足审计账号查看文件的需求。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　审计只需查看，只读即可。

</details>

**14.** 换一个用户登录就能直接打开他人 EFS 加密的文件。（　）

<details><summary>答案与解析</summary>

**答案：×（错误）**　EFS 与用户证书绑定，他人无法直接解密。

</details>

**15.** 移除某用户在目录上的权限可实现禁止其访问。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　NTFS 权限可拒绝/移除访问。

</details>

**16.** 共享权限设为完全控制即可忽略 NTFS 权限。（　）

<details><summary>答案与解析</summary>

**答案：×（错误）**　仍取两者交集，NTFS 仍生效。

</details>

### 模块三　远程桌面 RDP 安全（7 题）

**17.** 限制 RDP 来源 IP 是一种有效的访问控制措施。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　限定来源缩小暴露面。

</details>

**18.** 关闭 Windows 防火墙是解决 RDP 连接问题的推荐做法。（　）

<details><summary>答案与解析</summary>

**答案：×（错误）**　应放行必要端口而非关闭防火墙。

</details>

**19.** RDP 默认使用 TCP 3389 端口。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　远程桌面默认端口为 3389。

</details>

**20.** 启用 NLA 可在登录前完成身份验证。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　NLA 提前完成认证。

</details>

**21.** 把 RDP 对公网所有地址开放有利于安全。（　）

<details><summary>答案与解析</summary>

**答案：×（错误）**　会显著扩大攻击面。

</details>

**22.** 仅将必要用户加入 Remote Desktop Users 符合最小权限。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　按需授权远程登录。

</details>

**23.** NLA 会允许匿名用户直接登录桌面。（　）

<details><summary>答案与解析</summary>

**答案：×（错误）**　NLA 恰恰要求先认证。

</details>

### 模块四　SMB 协议安全（8 题）

**24.** SMB 签名可降低 NTLM 中继攻击风险。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　签名校验完整性，缓解中继。

</details>

**25.** SMBv1 比 SMBv3 更适合新系统生产环境。（　）

<details><summary>答案与解析</summary>

**答案：×（错误）**　SMBv1 漏洞多，应禁用，SMBv3 更安全。

</details>

**26.** SMB 服务默认使用 TCP 445 端口。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　SMB 使用 445。

</details>

**27.** 限制匿名枚举有助于减少账户与共享信息泄露。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　减少匿名探测信息。

</details>

**28.** 应保留所有测试共享以便随时使用。（　）

<details><summary>答案与解析</summary>

**答案：×（错误）**　多余共享应移除，缩小暴露面。

</details>

**29.** 强制服务端 SMB 签名会导致打印机无法工作。（　）

<details><summary>答案与解析</summary>

**答案：×（错误）**　签名与打印无关，主要防中继。

</details>

**30.** 禁用 SMBv1 可降低被蠕虫类攻击利用的风险。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　SMBv1 漏洞曾被蠕虫广泛利用。

</details>

**31.** SMB 访问只看共享权限，与 NTFS 权限无关。（　）

<details><summary>答案与解析</summary>

**答案：×（错误）**　还受 NTFS 权限约束，取交集。

</details>

### 模块五　安全日志与事件 ID（7 题）

**32.** 事件 ID 4624 通常表示登录成功。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　4624=登录成功。

</details>

**33.** 事件 ID 4625 通常表示登录成功。（　）

<details><summary>答案与解析</summary>

**答案：×（错误）**　4625 表示登录失败。

</details>

**34.** 事件 ID 1102 表示安全审计日志被清除。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　1102=审计日志清除。

</details>

**35.** 事件 ID 7045 常表示安装了新服务。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　7045 记录新服务安装。

</details>

**36.** 短时间内大量 4625 事件可能意味着暴力破解。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　大量失败登录提示猜解。

</details>

**37.** 安全配置完成后无需再保留登录审计日志。（　）

<details><summary>答案与解析</summary>

**答案：×（错误）**　应保留日志用于审计取证。

</details>

**38.** 可用 Get-WinEvent 按事件 ID 检索安全日志。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　FilterHashtable 支持按 ID 过滤。

</details>

### 模块六　IIS 部署与加固（10 题）

**39.** 自定义 404 页面可减少默认错误信息泄露。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　避免默认错误页暴露信息。

</details>

**40.** IIS 目录浏览在无业务需求时应关闭。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　防止泄露目录结构。

</details>

**41.** 为不同网站配置独立应用程序池可降低相互影响。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　应用池隔离工作进程。

</details>

**42.** 主机名绑定可用于在同一端口部署多个 IIS 网站。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　主机头区分同端口站点。

</details>

**43.** IIS 访问日志可用于分析请求和状态码。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　日志含 URL/状态码等。

</details>

**44.** HTTPS 配置完成后可以不再保留访问日志。（　）

<details><summary>答案与解析</summary>

**答案：×（错误）**　日志仍需保留以便审计。

</details>

**45.** Web.config 可用于统一管理站点安全配置。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　站点级配置文件。

</details>

**46.** 目录浏览长期开放有助于提升网站安全性。（　）

<details><summary>答案与解析</summary>

**答案：×（错误）**　会泄露文件结构，应关闭。

</details>

**47.** 所有网站共用一个应用程序池更利于故障隔离。（　）

<details><summary>答案与解析</summary>

**答案：×（错误）**　共用会相互影响，独立池更隔离。

</details>

**48.** 访问主机头网站前可在客户端 hosts 添加域名解析。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　实验环境常用 hosts 解析。

</details>

### 模块七　Web 安全响应头（5 题）

**49.** X-Frame-Options 可用于降低点击劫持风险。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　限制框架嵌套。

</details>

**50.** X-Content-Type-Options 常用值是 nosniff。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　nosniff 禁止 MIME 嗅探。

</details>

**51.** SAMEORIGIN 允许任意外部站点用 iframe 嵌套本站。（　）

<details><summary>答案与解析</summary>

**答案：×（错误）**　SAMEORIGIN 仅允许同源嵌套。

</details>

**52.** Content-Length 是一种点击劫持防护头。（　）

<details><summary>答案与解析</summary>

**答案：×（错误）**　它是信息性头，与防护无关。

</details>

**53.** nosniff 有助于防止浏览器把响应误判为可执行脚本。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　禁止内容类型嗅探。

</details>

### 模块八　HTTPS 与传输安全（5 题）

**54.** HTTPS 主要提升传输过程中的机密性和完整性。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　TLS 提供加密与完整性。

</details>

**55.** HTTPS 配置完成后可以不再保留访问日志。（　）

<details><summary>答案与解析</summary>

**答案：×（错误）**　日志仍需保留以便审计。

</details>

**56.** 实验环境可使用自签名证书为网站启用 HTTPS。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　隔离环境常用自签名证书。

</details>

**57.** 启用 HTTPS 能增加服务器的磁盘容量。（　）

<details><summary>答案与解析</summary>

**答案：×（错误）**　HTTPS 与磁盘容量无关。

</details>

**58.** 自签名证书默认会被所有外部浏览器信任。（　）

<details><summary>答案与解析</summary>

**答案：×（错误）**　默认不被信任，多用于内部测试。

</details>

### 模块九　FTP 服务安全（7 题）

**59.** FTP 基本身份验证默认会对口令进行端到端加密。（　）

<details><summary>答案与解析</summary>

**答案：×（错误）**　基本认证口令可能明文传输。

</details>

**60.** 关闭 FTP 匿名访问可以减少未授权访问风险。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　禁匿名降低未授权访问。

</details>

**61.** FTP 控制连接默认使用 TCP 21 端口。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　FTP 控制端口为 21。

</details>

**62.** 启用 FTPS 可缓解 FTP 明文传输口令的问题。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　FTPS 对通道加密。

</details>

**63.** 为方便使用应始终开启 FTP 匿名访问。（　）

<details><summary>答案与解析</summary>

**答案：×（错误）**　匿名访问带来未授权风险。

</details>

**64.** 仅授权特定用户并配合 NTFS 权限可收紧 FTP 访问。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　认证+NTFS 双重限制。

</details>

**65.** FTP 比 SFTP/FTPS 更适合传输敏感数据。（　）

<details><summary>答案与解析</summary>

**答案：×（错误）**　明文 FTP 不适合敏感数据。

</details>

### 模块十　SNMP 安全（7 题）

**66.** SNMP 默认团体名 public 在生产环境中存在信息泄露风险。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　public 是弱默认凭据。

</details>

**67.** SNMP 默认查询端口是 UDP 161。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　SNMP 查询用 UDP 161。

</details>

**68.** OID 用于标识 SNMP 可查询对象的层次位置。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　OID 标识 MIB 对象。

</details>

**69.** 加固时应保留默认 public 团体名以便维护。（　）

<details><summary>答案与解析</summary>

**答案：×（错误）**　应删除或更换默认团体名。

</details>

**70.** 可仅允许指定管理端 IP 访问 SNMP 以收紧暴露面。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　限制来源是有效加固。

</details>

**71.** 更换团体名后，旧的 public 仍应能成功查询。（　）

<details><summary>答案与解析</summary>

**答案：×（错误）**　旧团体名应失效。

</details>

**72.** 监控类 SNMP 团体名通常设为只读即可。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　只读满足监控需求且更安全。

</details>

### 模块十一　数据保护与恢复（6 题）

**73.** 卷影副本可辅助恢复文件的历史版本。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　快照保存历史版本。

</details>

**74.** “以前的版本”功能依赖卷影副本。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　读取卷影快照。

</details>

**75.** 卷影副本主要用于修改 RDP 端口。（　）

<details><summary>答案与解析</summary>

**答案：×（错误）**　它用于历史版本恢复。

</details>

**76.** 配置卷影副本前后应留存证据以便对比。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　前后对比验证恢复。

</details>

**77.** EFS 用于加密，卷影副本用于恢复，二者侧重不同。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　机密性 vs 可恢复性。

</details>

**78.** 卷影副本一般以卷为单位进行配置。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　按卷启用与计划快照。

</details>

### 模块十二　持久化排查与应急响应（9 题）

**79.** 发现不认识的系统服务后，应先留证据再判断是否清理。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　先取证后处置。

</details>

**80.** 计划任务中所有非 Microsoft 项都一定是恶意项。（　）

<details><summary>答案与解析</summary>

**答案：×（错误）**　需结合证据判断，不能一概而论。

</details>

**81.** 上传目录禁止执行脚本有助于降低 WebShell 风险。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　阻断脚本执行防 WebShell。

</details>

**82.** 清理持久化项后应再次检查并保存证据。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　处置后复查并留证。

</details>

**83.** cmdkey /list 可用于查看已缓存的网络凭据。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　列出缓存凭据。

</details>

**84.** HKCU/HKLM 的 Run 键是常见的自启动持久化位置。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　Run 键常被用于持久化。

</details>

**85.** 应急响应应优先快速删除可疑文件而不留证据。（　）

<details><summary>答案与解析</summary>

**答案：×（错误）**　应先取证后处置。

</details>

**86.** 限制 IIS 上传目录执行脚本能降低 WebShell 落地执行风险。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　禁脚本执行阻断 WebShell。

</details>

**87.** 安全配置完成后应进行客户端验证。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　验证确保加固有效。

</details>

### 模块十三　常用命令与排查工具（13 题）

**88.** Get-SmbShare 可用于检查服务器共享列表。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　列出 SMB 共享。

</details>

**89.** Get-NetTCPConnection 可用于查看 TCP 监听端口。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　查看 TCP 连接/监听。

</details>

**90.** Get-NetFirewallRule 用于查看防火墙规则。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　列出防火墙规则。

</details>

**91.** Get-Website 可用于查看 IIS 网站状态。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　显示站点状态。

</details>

**92.** cmdkey /list 可查看已缓存的网络凭据。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　列出缓存凭据。

</details>

**93.** Test-NetConnection 可用于测试端口连通性。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　支持 -Port 测试。

</details>

**94.** Get-Process 可用于列出服务器上的 SMB 共享。（　）

<details><summary>答案与解析</summary>

**答案：×（错误）**　列共享应用 Get-SmbShare。

</details>

**95.** hostname 命令的作用是修改服务器的 IP 地址。（　）

<details><summary>答案与解析</summary>

**答案：×（错误）**　hostname 仅显示计算机名。

</details>

**96.** Install-WindowsFeature 可用于安装 IIS 等服务器角色。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　用于安装角色/功能。

</details>

**97.** icacls 主要用于查看显示器分辨率。（　）

<details><summary>答案与解析</summary>

**答案：×（错误）**　icacls 管理 NTFS 权限。

</details>

**98.** Get-Date 是排查计划任务的首选命令。（　）

<details><summary>答案与解析</summary>

**答案：×（错误）**　应使用 Get-ScheduledTask。

</details>

**99.** vssadmin 可用于创建和查看卷影副本。（　）

<details><summary>答案与解析</summary>

**答案：√（正确）**　管理卷影副本。

</details>

**100.** route print 可用于查看 Windows 已缓存的网络凭据。（　）

<details><summary>答案与解析</summary>

**答案：×（错误）**　查看缓存凭据用 cmdkey /list。

</details>

---

