---
title: "06 项目六 MySQL 数据库高级安全维护 — 课堂逐字稿（第 1-3 课）"
---

# 06 项目六 MySQL 数据库高级安全维护 — 课堂逐字稿（第 1-3 课）

---

## 第 1 课：Navicat 连接与界面认知（从命令行走向图形化管理）

同学们好，今天我们开始第六个项目——MySQL 数据库高级安全维护。

先回顾一下，项目五我们干了什么。我们让 MySQL 在 Ubuntu 虚拟机上跑起来了，配了安全基线，创建了业务账号，学了四类日志。用一句话总结：命令行能装、能连、能授权、能看日志。

但是同学们想想，真实工作中，数据库管理员天天对着黑窗口敲命令行吗？不是的。绝大多数运维场景，大家都在用图形化工具。所以项目的核心目标很简单：**怎么像数据库管理员一样，用图形化工具完成日常管理**。

先说一句最重要的话，你们记住就行：**Navicat 是"可视化操作台"，MySQL Server 仍然在虚拟机里运行。界面上你点的每一步，底层最终都会变成 SQL 或者 MySQL 协议操作**。图形化工具不会替你运行数据库，它只是让你更方便地操作数据库。

### 新建和测试连接

好，我们先建立连接。大家打开宿主机 Windows 上的 Navicat。

点击左上角"连接"，选择"MySQL"。弹出一个配置窗口，按下面填写：

- 连接名：写 `MySQL-Ubuntu-Root`，这个是你自己取的名字，方便区分
- 主机：`192.168.100.20`，这是我们虚拟机的 IP
- 端口：`3306`，MySQL 默认端口
- 用户名：`root`
- 密码：`123456`

填好之后先别急着点确定，先点下面的"测试连接"。

好，有些同学报错了对吧？连不上？

这是正常的。还记得项目五我们做了什么吗？我们执行了 `mysql_secure_installation`，里面有一个选项叫"禁止 root 远程登录"，当时我们选了 Yes。所以 root 只能从虚拟机本机登录，从 Windows 宿主机是连不进去的。**这是正常的安全设计**。

那怎么办？我们不开放 root 远程登录，而是创建一个专门的管理员账号。大家切到虚拟机终端，用 `sudo mysql` 登录进去，执行下面两条命令：

```sql
CREATE USER 'dba'@'192.168.100.%' IDENTIFIED WITH mysql_native_password BY '123456';
GRANT ALL PRIVILEGES ON *.* TO 'dba'@'192.168.100.%' WITH GRANT OPTION;
```

我来解释一下这两条命令。第一条，创建一个叫 `dba` 的用户，只允许从 `192.168.100.x` 网段连接，认证插件选 `mysql_native_password` 确保 Navicat 能兼容，密码是 `123456`。第二条，给他所有权限，包括可以给别的用户授权的能力。

注意，`ALL PRIVILEGES` 在生产环境绝对不要给远程账号。这里只是课堂管理演示用的。

好，创建完了，回到 Navicat。把用户名从 `root` 改成 `dba`，再点测试连接。这回应该成功了。成功后点确定保存。

### 认识 Navicat 主界面

连接建好了，双击打开。大家现在看到的就是 Navicat 的主界面。我带大家认识六个核心区域，后面每节课都会用到。

**第一个，左侧连接树。** 就是左边这一栏，展开了之后能看到数据库、表、视图、函数、事件这些对象。你之前用 `SHOW DATABASES;` 看到的内容，这里一目了然。

**第二个，对象工具栏。** 在连接树的上方，有新建表、设计表、打开表、删除对象这些按钮。你之前用 `CREATE TABLE` 干的事，这里点点就能做。

**第三个，查询窗口。** 点上面菜单栏的"查询"→"新建查询"，就打开了。在这里你可以写 SQL 然后执行。这是非常重要的功能——图形化操作完之后，用 SQL 来验证结果到底对不对。

**第四个，表设计器。** 右键一张表选"设计表"，就能看到字段、主键、索引、外键这些信息，还能图形化修改。

**第五个，用户管理。** 右键连接选"管理用户"，可以创建账号、分配权限、锁定账号。你之前用 `CREATE USER` 和 `GRANT` 干的事，这里也能做。

**第六个，工具菜单。** 上面菜单栏的"工具"里面有导入导出、转储 SQL 文件、运行 SQL 文件、数据传输、结构同步。这些是数据维护的常用功能，后面第 4 课会细讲。

我画一张对应关系表，帮大家建立直观印象：

| 命令行操作 | Navicat 中的位置 | 用途 |
| --- | --- | --- |
| `SHOW DATABASES;` | 左侧连接树 | 查看数据库列表 |
| `CREATE DATABASE ...` | 右键连接 → 新建数据库 | 创建业务库 |
| `CREATE TABLE ...` | 右键表 → 新建表 | 设计表结构 |
| `GRANT ...` | 用户管理 / 权限页 | 授权 |
| `SHOW PROCESSLIST;` | 工具 → 服务器监控 / 进程列表 | 查看连接与执行中的 SQL |
| `mysqldump` | 转储 SQL 文件 / 运行 SQL 文件 | 备份与还原 |

看到了吧？你在命令行敲的每一个操作，Navicat 里都有对应的图形化入口。不是说图形化替代命令行，而是两种方式殊途同归。

### 图形化操作后的命令行验证

现在大家跟我一起，在 Navicat 里打开一个查询窗口，验证一下当前连接的身份和状态：

```sql
-- 查看当前连接身份
SELECT USER(), CURRENT_USER();

-- 查看数据库列表
SHOW DATABASES;

-- 查看当前服务器版本
SELECT VERSION();
```

执行一下。`USER()` 返回的是"你用谁的名义连上来的"，应该是 `dba@192.168.100.1` 这种格式，后面那个数字是你宿主机的 IP。`CURRENT_USER()` 返回的是"MySQL 实际匹配到的账号记录"，应该是 `dba@192.168.100.%`。

注意看，两个结果的主机部分可能不一样。你从宿主机 `.1` 连接的，但匹配到的是 `.%` 网段的规则。项目五讲过这个知识点，还记得吧？

`SHOW DATABASES;` 应该能看到 mysql、information_schema、performance_schema、sys 这些系统库。`SELECT VERSION();` 应该显示 8.0.x 的版本号。

这就是我今天想强调的核心习惯：**每完成一个图形化操作，都要用 SQL 验证一下结果。不要点了就以为生效了，一定要验证**。

### 第 1 课小结

好，我们来总结一下今天学的内容：

1. **Navicat 是图形化客户端，不是数据库本身。** 数据库还在虚拟机里跑着，Navicat 只是远程连上去操作它的一个界面
2. **管理操作建议使用专门的 dba 管理账号，不建议开放 root 远程登录。** 今天我们创建了 `dba@192.168.100.%` 这个管理账号
3. **图形化操作后要用 SQL 验证结果，避免"点了但不知道是否生效"。** 这个习惯从今天开始就要养成

### 学生实操任务（40 分钟）

现在大家自己动手，完成以下任务：

**任务 1：创建 dba 管理账号并连接 Navicat**

1. 在虚拟机终端用 `sudo mysql` 登录 MySQL
2. 执行 `CREATE USER` 和 `GRANT` 创建 `dba@192.168.100.%` 管理账号
3. 在 Navicat 中新建连接，用 dba 账号连接成功

**任务 2：认识主界面并验证**

1. 在 Navicat 中打开查询窗口
2. 执行 `SELECT USER(), CURRENT_USER();` 并截图保存结果
3. 执行 `SHOW DATABASES;` 记录能看到哪些数据库
4. 执行 `SELECT VERSION();` 记录 MySQL 版本号

**任务 3：熟悉六个功能区域**

1. 找到左侧连接树，展开查看数据库列表
2. 找到对象工具栏，认一下新建表、设计表的按钮
3. 找到工具菜单，认一下转储 SQL 文件、运行 SQL 文件的入口
4. 右键连接找到"管理用户"入口

**验收标准：**
- dba 账号能通过 Navicat 成功连接虚拟机 MySQL
- 查询窗口能执行 SQL 并返回正确结果
- 能指出 Navicat 六个功能区域分别在什么位置
- 能说出 Navicat 和 MySQL Server 的关系

---

## 第 2 课：Navicat 图形化建库建表（管理数据库对象）

同学们好，上节课我们学会了用 Navicat 连接 MySQL，认识了主界面的六个功能区域。今天这节课，我们来干数据库管理员最常干的活——**建库、建表、改字段、建索引、建外键、查看表数据**。

本课我们会用 Navicat 创建一个员工管理实验库 `employees_lab`，后面第 3 课的权限管理也会用这个库来练习。所以这节课的内容一定要跟紧，建出来的表后面要用的。

### 创建数据库

先建库。在 Navicat 左侧连接树上，对着你的连接名点右键，选择"新建数据库"。

弹出一个窗口，三个关键项要填：

- 数据库名：`employees_lab`
- 字符集：选 `utf8mb4`
- 排序规则：选 `utf8mb4_unicode_ci`

点确定，然后在左侧连接上右键选"刷新"，就能看到新建的库了。

为什么仍然选 utf8mb4？项目五已经讲过了，MySQL 的 `utf8` 不是真正的完整 UTF-8，它只能存 3 字节的字符，存不了 Emoji。图形化建库的时候也要主动选 `utf8mb4`，不要偷懒用默认值。

建好之后在查询窗口验证一下：

```sql
SHOW CREATE DATABASE employees_lab;
```

看输出里的 `CREATE DATABASE employees_lab` 后面是不是跟着 `CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci`。如果不是，说明你建的时候选错了，删掉重来。

### 创建部门表 departments

好，库建好了。接下来建第一张表——部门表 `departments`。

在左侧展开 `employees_lab`，对着"表"点右键，选择"新建表"。打开的就是表设计器。

添加三个字段：

**第一个字段：`dept_id`**
- 类型选 `varchar`，长度填 `10`
- 允许空那里取消勾选，就是不允许为空
- 键那一列选"主键"
- 这个字段是部门编号，用来唯一标识一个部门

**第二个字段：`dept_name`**
- 类型选 `varchar`，长度填 `50`
- 不允许为空
- 这个字段是部门名称，后面我们要给它加唯一索引，防止部门重名

**第三个字段：`created_at`**
- 类型选 `timestamp`
- 不允许为空
- 默认值设置为 `CURRENT_TIMESTAMP`，这样每插入一条记录就自动记录创建时间

三个字段都设好了，给 `dept_name` 加唯一索引。在设计器里找到"索引"页签，新建一个索引，字段选 `dept_name`，索引类型选 `UNIQUE`。

最后保存，表名填 `departments`。

保存后在查询窗口验证：

```sql
SHOW CREATE TABLE employees_lab.departments\G
```

看输出，确认主键、唯一索引、默认值都对。

### 创建员工表 employees

继续，在"表"上右键，新建第二张表 `employees`。

这张表字段多一些，一个一个来：

**`emp_id`** — 员工编号
- 类型 `int`
- 不允许空
- 设为主键
- 勾选"自动递增"（AUTO_INCREMENT），这样插入数据时不用手动填 ID

**`emp_name`** — 员工姓名
- 类型 `varchar`，长度 `50`
- 不允许空

**`dept_id`** — 所属部门
- 类型 `varchar`，长度 `10`
- 不允许空
- 这个字段后面要做外键，关联到 departments 表的 dept_id
- 先给它建一个普通索引：在"索引"页签新建索引，名称填 `idx_dept_id`，字段选 `dept_id`

**`salary`** — 薪资
- 类型 `decimal`，长度填 `10,2`，意思是总共 10 位，小数点后 2 位
- 允许为空（有些人可能还没定薪）
- 这里特别注意：**金额字段一定用 DECIMAL，不要用 FLOAT**。FLOAT 是浮点数，有精度丢失的问题，存钱绝对不能用

**`hire_date`** — 入职日期
- 类型 `date`
- 不允许空

**`updated_at`** — 更新时间
- 类型 `timestamp`
- 默认值设 `CURRENT_TIMESTAMP`
- 勾选"根据当前时间戳更新"（ON UPDATE CURRENT_TIMESTAMP），这样每次修改记录都会自动更新这个字段

六个字段都设好了。接下来做外键。

### 图形化创建外键

在 `employees` 表的设计器里，找到"外键"页签，点新建外键：

- 外键名称：`fk_emp_dept`
- 字段：选 `dept_id`
- 参考数据库：`employees_lab`
- 参考表：`departments`
- 参考字段：`dept_id`

设好之后保存。

我来解释一下外键的作用：它确保了 `employees` 表里的 `dept_id` 必须在 `departments` 表里存在。你不能给一个员工分配一个不存在的部门。这就是引用完整性。

如果外键创建失败，常见原因有四个，大家记一下：

1. **两边字段类型或长度不一致**——比如一个是 `varchar(10)`，另一个是 `varchar(20)`
2. **被引用字段不是主键或唯一索引**——外键必须引用一个有唯一约束的字段
3. **表引擎不是 InnoDB**——MySQL 只有 InnoDB 引擎支持外键
4. **已有数据违反约束**——如果表里已经有了不符合外键规则的数据，创建会失败

保存后，对应的 SQL 如果你在命令行执行的话，等价于：

```sql
CREATE TABLE employees_lab.employees (
    emp_id INT PRIMARY KEY AUTO_INCREMENT,
    emp_name VARCHAR(50) NOT NULL,
    dept_id VARCHAR(10) NOT NULL,
    salary DECIMAL(10,2),
    hire_date DATE NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_dept_id (dept_id),
    CONSTRAINT fk_emp_dept FOREIGN KEY (dept_id)
        REFERENCES employees_lab.departments(dept_id)
);
```

你看，你在图形界面上点点选选，最终生成的就是这条 SQL。殊途同归。

### 录入数据

表建好了，接下来往里面插数据。

先打开 `departments` 表。对着 `departments` 双击或者右键选"打开表"，下面会出现一个表格视图。直接在表格里填数据：

| dept_id | dept_name |
| --- | --- |
| d001 | 技术部 |
| d002 | 财务部 |
| d003 | 运营部 |

填完之后点下面的对号保存。注意 `created_at` 不用填，它会自动填当前时间。

然后打开 `employees` 表，添加三条数据：

| emp_name | dept_id | salary | hire_date |
| --- | --- | --- | --- |
| 张三 | d001 | 8500.00 | 2024-03-01 |
| 李四 | d002 | 7800.00 | 2024-04-15 |
| 王五 | d003 | 6900.00 | 2024-05-20 |

注意 `emp_id` 不用填，它是自增的。`updated_at` 也不用填。

数据录入好之后，在查询窗口跑一个联表查询验证：

```sql
SELECT e.emp_id, e.emp_name, d.dept_name, e.salary, e.hire_date
FROM employees_lab.employees e
JOIN employees_lab.departments d ON e.dept_id = d.dept_id;
```

应该返回 3 行结果，每行都显示员工信息和对应的部门名称。如果报错或者数据不对，回去检查录入有没有问题。

### 修改表结构的安全流程

最后一件事，图形化改表很方便，但也最容易出事。我给大家定一个安全流程，以后不管在哪改表都按这个来：

**第一步：修改前先备份。** 右键表 → "转储 SQL 文件"，先把当前表结构和数据导出来。万一改坏了能恢复。

**第二步：在测试库验证。** 如果有测试库，先在测试库上改一遍看看效果。

**第三步：用设计表修改。** 右键表 → "设计表"，在这里改字段或索引。

**第四步：保存前看 SQL。** Navicat 在保存前会让你确认生成的 SQL。看看有没有意外的 `DROP` 或者 `ALTER`，确认没问题再保存。

**第五步：保存后再验证。** 在查询窗口执行：

```sql
SHOW CREATE TABLE employees_lab.employees\G
```

确认修改生效了。

### 第 2 课小结

总结一下今天的内容：

1. **Navicat 可以完成建库、建表、字段、索引、外键等对象管理。** 以后 DBA 日常工作大部分时间就是跟这些打交道
2. **金额字段用 DECIMAL，中文库表统一 utf8mb4。** 这两个是铁律，不要用 FLOAT 存钱，不要用 utf8 存中文
3. **图形化改表前先备份，保存前看 SQL，保存后再验证。** 三个步骤缺一不可

### 学生实操任务（45 分钟）

现在大家自己动手，完成以下任务：

**任务 1：创建 employees_lab 数据库**

1. 在 Navicat 中新建数据库 `employees_lab`
2. 字符集选 `utf8mb4`，排序规则选 `utf8mb4_unicode_ci`
3. 用 `SHOW CREATE DATABASE employees_lab;` 验证

**任务 2：创建 departments 表**

1. 新建表 `departments`
2. 字段：`dept_id varchar(10)` 主键、`dept_name varchar(50)` 不允许空加唯一索引、`created_at timestamp` 默认 CURRENT_TIMESTAMP
3. 保存后用 `SHOW CREATE TABLE employees_lab.departments\G` 验证

**任务 3：创建 employees 表**

1. 新建表 `employees`
2. 字段：`emp_id int` 主键自增、`emp_name varchar(50)` 不允许空、`dept_id varchar(10)` 不允许空加普通索引、`salary decimal(10,2)` 允许空、`hire_date date` 不允许空、`updated_at timestamp` 默认 CURRENT_TIMESTAMP + ON UPDATE
3. 创建外键 `fk_emp_dept`：`dept_id` 关联 `departments.dept_id`
4. 保存后用 `SHOW CREATE TABLE employees_lab.employees\G` 验证

**任务 4：录入数据**

1. 往 `departments` 插入 3 条数据：技术部、财务部、运营部
2. 往 `employees` 插入 3 条数据：张三、李四、王五
3. 执行联表查询验证数据正确

**任务 5：体验修改表结构的安全流程**

1. 先对 `employees` 表执行"转储 SQL 文件"备份
2. 用设计表给 `employees` 添加一个新字段 `phone varchar(20)` 允许空
3. 保存前查看生成的 SQL
4. 保存后用 `SHOW CREATE TABLE` 验证字段已添加
5. 验证完毕后删除 `phone` 字段恢复原状

**验收标准：**
- `employees_lab` 数据库存在且字符集为 utf8mb4
- `departments` 表有主键和唯一索引
- `employees` 表有主键、自增、普通索引、外键
- 联表查询返回 3 行正确的员工-部门数据
- 能演示"先备份再改表再验证"的安全流程

---

## 第 3 课：Navicat 用户与权限管理（图形化落实最小权限）

同学们好，上节课我们用 Navicat 建了 `employees_lab` 库，建了 `departments` 和 `employees` 两张表，还插入了数据。今天这节课，我们继续用这个库，但换个角度——**用户和权限管理**。

项目五已经讲过 `CREATE USER`、`GRANT`、`REVOKE` 这些命令行操作。今天我们不讲新概念，重点是：**怎么在 Navicat 里完成同样的权限管理，并且验证权限边界到底有没有生效**。

### 角色设计

在动手之前，我们先想清楚要创建哪些账号。以 `employees_lab` 为例，按最小权限原则，设计三类账号：

**第一个：reader — 只读账号**
- 权限：只有 `SELECT`
- 适用场景：数据分析、报表查询。这类人只需要看数据，不需要改

**第二个：writer — 读写账号**
- 权限：`SELECT`、`INSERT`、`UPDATE`、`DELETE`
- 适用场景：应用系统。能查能写能改能删，但不能改表结构

**第三个：developer — 开发账号**
- 权限：`SELECT`、`INSERT`、`UPDATE`、`DELETE`、`CREATE`、`ALTER`、`INDEX`
- 适用场景：开发测试。除了读写数据，还能建表、改表结构、建索引

三个账号的来源主机都是 `192.168.100.%`，密码统一 `123456`。

注意看，没有一个账号给了 `ALL PRIVILEGES`，也没有给 `DROP` 权限。这就是最小权限原则——只给够用的权限，不多给。

图形化工具让授权变得特别方便，勾勾选选就行。但越方便越要谨慎，不要为了省事给业务账号 `ALL PRIVILEGES`。

### 在 Navicat 中创建用户

好，开始创建。对着你的连接点右键，选择"管理用户"，或者从菜单里找到用户管理的入口。

点"新建用户"，填写信息：

- 用户名：`reader`
- 主机：`192.168.100.%`
- 密码：`123456`
- 认证插件：选 `mysql_native_password`

选 `mysql_native_password` 是为了确保 Navicat 能兼容。如果用 MySQL 8.0 默认的 `caching_sha2_password`，某些旧版本的 Navicat 可能连不上。

保存。按同样的方式创建 `writer` 和 `developer`。

如果创建的时候报错，说密码不符合策略，那是因为密码验证组件在拦你。切到查询窗口执行：

```sql
SET GLOBAL validate_password.policy = LOW;
SET GLOBAL validate_password.length = 6;
```

把密码策略降低到只检查长度 6 位，然后回去重新创建。这个操作项目五也做过。

### 在 Navicat 中分配权限

用户建好了，接下来分配权限。

在用户管理界面，选中 `reader@192.168.100.%`，点开"权限"页签。这里能看到所有数据库的权限配置。找到 `employees_lab` 这个库，只勾选 `SELECT`，其他都不勾。保存。

同样给 `writer` 分配权限：找到 `employees_lab`，勾选 `SELECT`、`INSERT`、`UPDATE`、`DELETE`。保存。

给 `developer` 分配权限：找到 `employees_lab`，勾选 `SELECT`、`INSERT`、`UPDATE`、`DELETE`、`CREATE`、`ALTER`、`INDEX`。保存。

保存之后，切到查询窗口，用 SQL 验证一下权限是不是真的分配成功了：

```sql
SHOW GRANTS FOR 'reader'@'192.168.100.%';
SHOW GRANTS FOR 'writer'@'192.168.100.%';
SHOW GRANTS FOR 'developer'@'192.168.100.%';
```

`reader` 应该只显示 `GRANT SELECT`，`writer` 显示 `GRANT SELECT, INSERT, UPDATE, DELETE`，`developer` 显示 `GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX`。

如果和你预期的不一样，说明图形化操作的时候勾错了，回去重新调整。

### 用不同连接验证权限边界

光看 `SHOW GRANTS` 还不够。**必须用目标账号真正登录进去执行操作，才能确认权限边界是否符合预期。**

为什么？因为权限是连接时按账号身份匹配的。你在管理员连接里看 `SHOW GRANTS`，看到的是配置信息，不代表实际连接就一定能按预期工作。

现在大家跟我一起操作：

在 Navicat 里新建三个连接：

- 连接名 `MySQL-reader`，用户名 `reader`，密码 `123456`，主机 `192.168.100.20`
- 连接名 `MySQL-writer`，用户名 `writer`，密码 `123456`，主机 `192.168.100.20`
- 连接名 `MySQL-developer`，用户名 `developer`，密码 `123456`，主机 `192.168.100.20`

三个连接都测试一下，确保能连上。

然后在三个连接里分别执行以下测试：

**测试 1：SELECT 查询（三个账号都应该成功）**

```sql
SELECT * FROM employees_lab.employees;
```

三个连接都执行一下，应该都能看到 3 条员工数据。

**测试 2：INSERT 插入（reader 应该失败，writer 和 developer 应该成功）**

```sql
INSERT INTO employees_lab.departments VALUES ('d004', '人事部', NOW());
```

用 `reader` 执行——应该报 `ERROR 1142`，权限不足。
用 `writer` 执行——应该成功。
用 `developer` 执行——应该成功。

**测试 3：UPDATE 更新（reader 应该失败，writer 和 developer 应该成功）**

```sql
UPDATE employees_lab.employees SET salary = salary + 100 WHERE emp_id = 1;
```

用 `reader` 执行——报权限不足。
用 `writer` 执行——成功。
用 `developer` 执行——成功。

**测试 4：CREATE TABLE 建表（reader 和 writer 应该失败，developer 应该成功）**

```sql
CREATE TABLE employees_lab.tmp_test (id INT);
```

用 `reader` 执行——报权限不足。
用 `writer` 执行——报权限不足。
用 `developer` 执行——成功。

**测试 5：DROP DATABASE 删库（三个账号都应该失败）**

```sql
DROP DATABASE employees_lab;
```

三个账号都执行——全部报权限不足。没有给任何账号 `DROP` 权限，这就是安全底线。

我把结果整理成一张表，方便大家对照：

| 测试操作 | reader | writer | developer |
| --- | --- | --- | --- |
| `SELECT * FROM employees` | 成功 | 成功 | 成功 |
| `INSERT INTO departments` | 失败 | 成功 | 成功 |
| `UPDATE employees SET salary` | 失败 | 成功 | 成功 |
| `CREATE TABLE tmp_test` | 失败 | 失败 | 成功 |
| `DROP DATABASE employees_lab` | 失败 | 失败 | 失败 |

如果某个账号的结果和表里不一样，回去检查权限配置。

### 图形化锁定、解锁和删除账号

最后，我们来讲账号的生命周期管理。在用户管理界面里，你能完成这些操作：

**场景一：员工离职了，但不确定他之前创建的视图或存储过程是否还在被系统使用。**

这时候不要直接删除账号，而是先**锁定**。在用户管理里选中账号，找到锁定选项，锁定它。对应的 SQL 是：

```sql
ALTER USER 'reader'@'192.168.100.%' ACCOUNT LOCK;
```

锁定了之后，这个账号就登不进去了，但是它创建的视图、存储过程还在，不影响依赖它的业务。

**场景二：员工回来了，需要恢复使用。**

解锁就行了：

```sql
ALTER USER 'reader'@'192.168.100.%' ACCOUNT UNLOCK;
```

**场景三：确认这个账号不再需要了，要删除。**

删除之前，先检查有没有依赖。在查询窗口执行：

```sql
SELECT * FROM information_schema.VIEWS WHERE DEFINER LIKE '%reader%';
SELECT * FROM information_schema.ROUTINES WHERE DEFINER LIKE '%reader%';
```

如果返回空，说明没有视图或存储过程依赖这个账号，可以安全删除。如果有记录返回，就要先处理这些依赖对象，然后再删。

确认没问题后，在用户管理里删除账号。对应的 SQL 是：

```sql
DROP USER 'reader'@'192.168.100.%';
```

**场景四：怀疑密码泄露了。**

修改密码：

```sql
ALTER USER 'reader'@'192.168.100.%' IDENTIFIED BY '654321';
```

我在这里整理一张对照表：

| 场景 | Navicat 操作 | SQL 对应 |
| --- | --- | --- |
| 员工离职但不确定是否仍被系统使用 | 锁定账号 | `ALTER USER ... ACCOUNT LOCK;` |
| 账号恢复使用 | 解锁账号 | `ALTER USER ... ACCOUNT UNLOCK;` |
| 账号确认废弃 | 删除用户 | `DROP USER ...;` |
| 怀疑密码泄露 | 修改密码 | `ALTER USER ... IDENTIFIED BY ...;` |

记住一个原则：**删除是最后的手段，锁定是更安全的中间步骤**。生产环境里，不确定就先锁，观察几天确认没问题再删。

### 第 3 课小结

总结一下今天的内容：

1. **Navicat 能创建用户、分配权限、锁定账号和删除账号。** 这些操作和命令行的 `CREATE USER`、`GRANT`、`ALTER USER`、`DROP USER` 完全对应
2. **权限设计仍然遵循最小权限原则。** reader 只能查，writer 能增删改查，developer 还能改结构，但没有人能删库
3. **图形化授权后必须用 SHOW GRANTS 和不同账号连接双重验证。** 只看配置不够，必须真的用目标账号登录执行操作才能确认权限边界

### 学生实操任务（45 分钟）

现在大家自己动手，完成以下任务：

**任务 1：创建三个业务账号**

1. 在 Navicat 用户管理中创建 `reader@192.168.100.%`
2. 创建 `writer@192.168.100.%`
3. 创建 `developer@192.168.100.%`
4. 密码统一 `123456`，认证插件选 `mysql_native_password`

**任务 2：分配权限**

1. `reader`：对 `employees_lab` 只有 `SELECT`
2. `writer`：对 `employees_lab` 有 `SELECT, INSERT, UPDATE, DELETE`
3. `developer`：对 `employees_lab` 有 `SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX`
4. 保存后用 `SHOW GRANTS FOR` 验证三个账号的权限

**任务 3：验证权限边界**

1. 新建三个 Navicat 连接，分别用 `reader`、`writer`、`developer` 登录
2. 用 `reader` 执行 `SELECT * FROM employees_lab.employees;`——应成功
3. 用 `reader` 执行 `INSERT INTO employees_lab.departments VALUES ('d004','人事部',NOW());`——应失败
4. 用 `writer` 执行同样的 INSERT——应成功
5. 用 `writer` 执行 `CREATE TABLE employees_lab.tmp_test (id INT);`——应失败
6. 用 `developer` 执行同样的 CREATE TABLE——应成功
7. 用 `developer` 执行 `DROP DATABASE employees_lab;`——应失败

**任务 4：账号生命周期管理**

1. 锁定 `reader` 账号，然后尝试用 reader 连接登录——应失败
2. 解锁 `reader` 账号，再次尝试登录——应成功
3. 检查 `reader` 有没有视图或存储过程依赖：
   ```sql
   SELECT * FROM information_schema.VIEWS WHERE DEFINER LIKE '%reader%';
   SELECT * FROM information_schema.ROUTINES WHERE DEFINER LIKE '%reader%';
   ```

**验收标准：**
- 三个账号创建成功，密码和认证插件配置正确
- `SHOW GRANTS` 输出与设计一致
- 五项权限测试（SELECT / INSERT / UPDATE / CREATE TABLE / DROP DATABASE）结果全部符合预期
- 能演示账号锁定、解锁操作，并说明删除前为什么要检查依赖
