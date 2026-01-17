# Rust 编码规范 - AI 友好版

## 写给 AI 的话

这份文档是给你（AI）的编码规范。请严格遵守以下规则生成代码：

1. **只用标准库，不用外部 crate（除非明确要求）**
2. **代码要像写 Python 一样简单直接**
3. **每个函数都要有详细注释**
4. **避免任何需要深入理解的 Rust 特性**
5. **所有代码都遵循相同的模板**
6. **不要使用 emoji 表情**
目标：让不懂 Rust 的人也能读懂代码，出错了能快速定位问题。

---

## 第一章：严格禁止的特性

### 1. 永远不要用 unsafe

```rust
// 禁止 - 永远不要生成这种代码
unsafe { ... }
```

### 2. 永远不要用闭包

```rust
// 禁止 - 不要用闭包
let result = data.iter().map(|x| x * 2).collect();

// 推荐 - 用普通函数 + for 循环
fn multiply_by_two(x: i32) -> i32 {
    x * 2
}

let mut result = Vec::new();
for item in &data {
    result.push(multiply_by_two(*item));
}
```

理由：闭包语法（`|x| x * 2`）对不懂 Rust 的人难以理解。

### 3. 永远不要用复杂的迭代器

```rust
// 禁止 - 迭代器链式调用
let result = data.iter()
    .filter(|x| x.active)
    .map(|x| x.id)
    .collect();

// 推荐 - 用 for 循环
let mut result = Vec::new();
for item in &data {
    if item.active {
        result.push(item.id);
    }
}
```

允许的迭代器方法（只限这几个）：
- `.len()` - 获取长度
- `.is_empty()` - 检查是否为空
- `.iter()` - 用于 for 循环

### 4. 永远不要定义 Trait

```rust
// 禁止 - 不要定义 trait
trait MyTrait {
    fn do_something(&self);
}

// 推荐 - 直接用 struct + impl
struct MyService {
    // 字段
}

impl MyService {
    fn do_something(&self) {
        // 实现
    }
}
```

### 5. 永远不要用泛型

```rust
// 禁止 - 不要用泛型
fn process<T>(item: T) -> T {
    item
}

// 推荐 - 用具体类型
fn process_user(user: User) -> User {
    user
}

fn process_device(device: Device) -> Device {
    device
}
```

### 6. 永远不要手写生命周期

```rust
// 禁止 - 不要写生命周期参数
fn get<'a>(x: &'a str) -> &'a str {
    x
}

// 推荐 - 返回 owned 类型
fn get(x: &str) -> String {
    x.to_string()
}
```

### 7. 永远不要用智能指针（99%情况）

```rust
// 禁止 - 不要用这些
Arc<Mutex<Data>>
Rc<RefCell<Data>>
Box<dyn Trait>

// 推荐 - 直接 clone
let data_copy = data.clone();
```

### 8. 永远不要自己写宏

```rust
// 禁止 - 不要定义宏
macro_rules! my_macro {
    // ...
}
```

---

## 第二章：标准代码模板

### 模板1：数据结构定义

每个数据结构都用这个模板：

```rust
// 数据结构：用户
// 说明：存储用户的基本信息
pub struct User {
    pub id: i64,           // 用户ID
    pub name: String,      // 用户名
    pub email: String,     // 邮箱
}

// 实现：构造函数
impl User {
    // 创建新用户
    // 参数：id - 用户ID, name - 用户名, email - 邮箱
    // 返回：新的 User 实例
    pub fn new(id: i64, name: String, email: String) -> Self {
        Self { id, name, email }
    }
}

// 实现：默认值
impl Default for User {
    fn default() -> Self {
        Self {
            id: 0,
            name: String::new(),
            email: String::new(),
        }
    }
}

// 实现：Debug（用于打印调试）
impl std::fmt::Debug for User {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        write!(f, "User {{ id: {}, name: {}, email: {} }}",
               self.id, self.name, self.email)
    }
}

// 实现：Clone（用于复制）
impl Clone for User {
    fn clone(&self) -> Self {
        User {
            id: self.id,
            name: self.name.clone(),
            email: self.email.clone(),
        }
    }
}
```

注意：
- 每个字段都有注释
- 每个函数都有注释说明功能、参数、返回值
- 手动实现 Debug 和 Clone（不用 derive 宏）

### 模板2：Service 层（业务逻辑）

```rust
// Service：用户服务
// 职责：处理用户相关的业务逻辑
pub struct UserService {
    data_path: String,  // 数据文件路径
}

impl UserService {
    // 创建用户服务
    // 参数：data_path - 数据文件路径
    // 返回：UserService 实例
    pub fn new(data_path: String) -> Self {
        println!("[UserService] 创建服务，数据路径: {}", data_path);
        Self { data_path }
    }

    // 获取用户
    // 参数：id - 用户ID
    // 返回：成功返回 User，失败返回错误信息
    pub fn get_user(&self, id: i64) -> Result<User, String> {
        println!("[UserService] 开始获取用户，ID: {}", id);

        // 步骤1：读取文件
        let content = match std::fs::read_to_string(&self.data_path) {
            Ok(c) => {
                println!("[UserService] 成功读取文件");
                c
            }
            Err(e) => {
                let error_msg = format!("读取文件失败: {}", e);
                println!("[UserService] 错误: {}", error_msg);
                return Err(error_msg);
            }
        };

        // 步骤2：查找用户（这里简化，实际应该解析 JSON）
        // TODO: 实现真正的查找逻辑
        let user = User {
            id: id,
            name: String::from("测试用户"),
            email: String::from("test@example.com"),
        };

        println!("[UserService] 成功找到用户: {:?}", user);
        Ok(user)
    }

    // 保存用户
    // 参数：user - 要保存的用户
    // 返回：成功返回 ()，失败返回错误信息
    pub fn save_user(&self, user: &User) -> Result<(), String> {
        println!("[UserService] 开始保存用户: {:?}", user);

        // 步骤1：转换为 JSON 字符串
        let json = format!(
            r#"{{"id":{},"name":"{}","email":"{}"}}"#,
            user.id, user.name, user.email
        );
        println!("[UserService] 生成 JSON: {}", json);

        // 步骤2：写入文件
        match std::fs::write(&self.data_path, json) {
            Ok(_) => {
                println!("[UserService] 成功保存用户");
                Ok(())
            }
            Err(e) => {
                let error_msg = format!("写入文件失败: {}", e);
                println!("[UserService] 错误: {}", error_msg);
                Err(error_msg)
            }
        }
    }
}
```

注意：
- 每个函数开始都打印日志
- 每个步骤都有注释
- 错误都转换为字符串
- 成功和失败都打印日志

### 模板3：错误处理

**统一使用 `Result<T, String>`：**

```rust
// 函数签名模板
pub fn function_name(param: Type) -> Result<ReturnType, String> {
    // 步骤1：验证输入
    if param.is_invalid() {
        let error = String::from("输入无效");
        println!("[函数名] 错误: {}", error);
        return Err(error);
    }

    // 步骤2：执行操作
    let result = match some_operation() {
        Ok(r) => r,
        Err(e) => {
            let error = format!("操作失败: {}", e);
            println!("[函数名] 错误: {}", error);
            return Err(error);
        }
    };

    // 步骤3：返回结果
    println!("[函数名] 成功");
    Ok(result)
}
```

**调用时的错误处理：**

```rust
// 方式1：match（推荐，最清晰）
match get_user(1) {
    Ok(user) => {
        println!("成功获取用户: {:?}", user);
        // 继续处理
    }
    Err(e) => {
        println!("获取用户失败: {}", e);
        // 错误处理
    }
}

// 方式2：if let（适合只关心成功的情况）
if let Ok(user) = get_user(1) {
    println!("成功获取用户: {:?}", user);
}

// 方式3：? 操作符（只在其他返回 Result 的函数中使用）
fn caller() -> Result<(), String> {
    let user = get_user(1)?;  // 自动传播错误
    println!("用户: {:?}", user);
    Ok(())
}
```

### 模板4：main 函数

```rust
fn main() {
    println!("========== 程序开始 ==========");

    // 步骤1：初始化
    println!("\n[main] 步骤1：初始化服务");
    let user_service = UserService::new(String::from("data/users.json"));

    // 步骤2：执行业务逻辑
    println!("\n[main] 步骤2：获取用户");
    match user_service.get_user(1) {
        Ok(user) => {
            println!("[main] 成功: {:?}", user);
        }
        Err(e) => {
            println!("[main] 失败: {}", e);
            return;  // 出错就退出
        }
    }

    // 步骤3：保存数据
    println!("\n[main] 步骤3：保存用户");
    let new_user = User::new(2, String::from("新用户"), String::from("new@example.com"));
    match user_service.save_user(&new_user) {
        Ok(_) => println!("[main] 保存成功"),
        Err(e) => println!("[main] 保存失败: {}", e),
    }

    println!("\n========== 程序结束 ==========");
}
```

注意：
- 明确的步骤标记
- 每步都打印日志
- 清晰的开始/结束标记

---

## 第三章：文件组织规范

### 标准项目结构

```
项目名/
├── Cargo.toml
├── src/
│   ├── main.rs           # 程序入口
│   ├── models.rs         # 数据结构定义
│   ├── user_service.rs   # 用户服务
│   ├── device_service.rs # 设备服务
│   └── config.rs         # 配置
└── data/
    └── users.json        # 数据文件
```

### main.rs 模板

```rust
// 模块导入
mod models;
mod user_service;
mod device_service;
mod config;

// 使用声明
use models::User;
use user_service::UserService;

// 程序入口
fn main() {
    println!("========== 程序开始 ==========");

    // 在这里编写主要逻辑

    println!("========== 程序结束 ==========");
}
```

### models.rs 模板

```rust
// 文件：models.rs
// 说明：定义所有数据结构

// ==================== User ====================

pub struct User {
    pub id: i64,
    pub name: String,
}

impl User {
    pub fn new(id: i64, name: String) -> Self {
        Self { id, name }
    }
}

impl Default for User {
    fn default() -> Self {
        Self {
            id: 0,
            name: String::new(),
        }
    }
}

impl std::fmt::Debug for User {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        write!(f, "User {{ id: {}, name: {} }}", self.id, self.name)
    }
}

impl Clone for User {
    fn clone(&self) -> Self {
        User {
            id: self.id,
            name: self.name.clone(),
        }
    }
}

// ==================== Device ====================

pub struct Device {
    pub id: i64,
    pub mac: String,
}

// ... 类似的实现
```

---

## 第四章：常用操作标准写法

### 1. 读取文件

```rust
// 读取文件内容
// 参数：path - 文件路径
// 返回：成功返回文件内容，失败返回错误信息
fn read_file(path: &str) -> Result<String, String> {
    println!("[read_file] 读取文件: {}", path);

    match std::fs::read_to_string(path) {
        Ok(content) => {
            println!("[read_file] 成功，文件大小: {} 字节", content.len());
            Ok(content)
        }
        Err(e) => {
            let error = format!("读取文件失败: {}", e);
            println!("[read_file] 错误: {}", error);
            Err(error)
        }
    }
}
```

### 2. 写入文件

```rust
// 写入文件
// 参数：path - 文件路径, content - 内容
// 返回：成功返回 ()，失败返回错误信息
fn write_file(path: &str, content: &str) -> Result<(), String> {
    println!("[write_file] 写入文件: {}", path);
    println!("[write_file] 内容长度: {} 字节", content.len());

    match std::fs::write(path, content) {
        Ok(_) => {
            println!("[write_file] 写入成功");
            Ok(())
        }
        Err(e) => {
            let error = format!("写入文件失败: {}", e);
            println!("[write_file] 错误: {}", error);
            Err(error)
        }
    }
}
```

### 3. 遍历列表

```rust
// 处理用户列表
fn process_users(users: &Vec<User>) {
    println!("[process_users] 开始处理，共 {} 个用户", users.len());

    let mut count = 0;
    for user in users {
        count = count + 1;
        println!("[process_users] 处理第 {} 个用户: {:?}", count, user);

        // 具体处理逻辑
        let name_upper = user.name.to_uppercase();
        println!("[process_users] 转换后的名字: {}", name_upper);
    }

    println!("[process_users] 处理完成");
}
```

### 4. 查找元素

```rust
// 在列表中查找用户
// 参数：users - 用户列表, id - 要查找的ID
// 返回：找到返回 Some(User)，找不到返回 None
fn find_user(users: &Vec<User>, id: i64) -> Option<User> {
    println!("[find_user] 查找用户，ID: {}", id);

    for user in users {
        if user.id == id {
            println!("[find_user] 找到用户: {:?}", user);
            return Some(user.clone());
        }
    }

    println!("[find_user] 未找到用户");
    None
}

// 使用示例
fn example_find() {
    let users = vec![/* ... */];

    match find_user(&users, 1) {
        Some(user) => {
            println!("找到: {:?}", user);
        }
        None => {
            println!("未找到");
        }
    }
}
```

### 5. 转换和映射

```rust
// 提取所有用户的ID
fn get_user_ids(users: &Vec<User>) -> Vec<i64> {
    println!("[get_user_ids] 提取用户ID，共 {} 个用户", users.len());

    let mut ids = Vec::new();
    for user in users {
        ids.push(user.id);
    }

    println!("[get_user_ids] 提取完成，共 {} 个ID", ids.len());
    ids
}
```

### 6. 过滤列表

```rust
// 过滤出名字长度大于5的用户
fn filter_long_names(users: &Vec<User>) -> Vec<User> {
    println!("[filter_long_names] 开始过滤，共 {} 个用户", users.len());

    let mut result = Vec::new();
    for user in users {
        if user.name.len() > 5 {
            println!("[filter_long_names] 保留用户: {:?}", user);
            result.push(user.clone());
        }
    }

    println!("[filter_long_names] 过滤完成，保留 {} 个用户", result.len());
    result
}
```

### 7. 使用 HashMap

```rust
use std::collections::HashMap;

// 创建用户索引
fn create_user_index(users: &Vec<User>) -> HashMap<i64, User> {
    println!("[create_user_index] 创建索引，共 {} 个用户", users.len());

    let mut index = HashMap::new();

    for user in users {
        println!("[create_user_index] 添加用户到索引: ID {}", user.id);
        index.insert(user.id, user.clone());
    }

    println!("[create_user_index] 索引创建完成");
    index
}

// 从索引查找用户
fn find_in_index(index: &HashMap<i64, User>, id: i64) -> Option<User> {
    println!("[find_in_index] 查找 ID: {}", id);

    match index.get(&id) {
        Some(user) => {
            println!("[find_in_index] 找到: {:?}", user);
            Some(user.clone())
        }
        None => {
            println!("[find_in_index] 未找到");
            None
        }
    }
}
```

### 8. 字符串操作

```rust
// 字符串拼接
fn concat_strings(a: &str, b: &str) -> String {
    let mut result = String::new();
    result.push_str(a);
    result.push_str(" ");
    result.push_str(b);
    result
}

// 或用 format!
fn concat_with_format(a: &str, b: &str) -> String {
    format!("{} {}", a, b)
}

// 字符串转换
fn string_operations(s: &str) -> String {
    println!("[string_operations] 输入: {}", s);

    // 转大写
    let upper = s.to_uppercase();
    println!("[string_operations] 大写: {}", upper);

    // 转小写
    let lower = s.to_lowercase();
    println!("[string_operations] 小写: {}", lower);

    // 去除空格
    let trimmed = s.trim();
    println!("[string_operations] 去除空格: {}", trimmed);

    trimmed.to_string()
}

// 字符串分割
fn split_string(s: &str) -> Vec<String> {
    println!("[split_string] 分割字符串: {}", s);

    let mut parts = Vec::new();
    for part in s.split(',') {
        let trimmed = part.trim().to_string();
        println!("[split_string] 部分: {}", trimmed);
        parts.push(trimmed);
    }

    println!("[split_string] 共 {} 个部分", parts.len());
    parts
}
```

---

## 第五章：调试和错误追踪

### 1. 打印调试信息

**规则：每个函数都要打印日志**

```rust
fn my_function(param: i32) -> Result<String, String> {
    // 函数开始
    println!("[my_function] 开始，参数: {}", param);

    // 关键步骤
    println!("[my_function] 步骤1：验证参数");
    if param < 0 {
        println!("[my_function] 错误：参数不能为负数");
        return Err(String::from("参数不能为负数"));
    }

    // 中间变量
    let result = param * 2;
    println!("[my_function] 步骤2：计算结果 = {}", result);

    // 函数结束
    println!("[my_function] 成功完成");
    Ok(result.to_string())
}
```

### 2. 打印数据结构

```rust
// 打印简单类型
let id = 123;
println!("ID = {}", id);

// 打印字符串
let name = String::from("test");
println!("Name = {}", name);

// 打印自定义类型（需要实现 Debug）
let user = User { id: 1, name: String::from("Alice") };
println!("User = {:?}", user);

// 打印 Vec
let numbers = vec![1, 2, 3];
println!("Numbers = {:?}", numbers);

// 打印 HashMap
let mut map = HashMap::new();
map.insert("key", "value");
println!("Map = {:?}", map);
```

### 3. 错误定位模板

```rust
fn complex_operation() -> Result<(), String> {
    println!("\n========== 开始复杂操作 ==========");

    // 步骤1
    println!("\n[complex_operation] 步骤1：读取配置");
    let config = match read_config() {
        Ok(c) => {
            println!("[complex_operation] 步骤1成功");
            c
        }
        Err(e) => {
            println!("[complex_operation] 步骤1失败: {}", e);
            return Err(format!("步骤1失败: {}", e));
        }
    };

    // 步骤2
    println!("\n[complex_operation] 步骤2：处理数据");
    let data = match process_data(&config) {
        Ok(d) => {
            println!("[complex_operation] 步骤2成功");
            d
        }
        Err(e) => {
            println!("[complex_operation] 步骤2失败: {}", e);
            return Err(format!("步骤2失败: {}", e));
        }
    };

    // 步骤3
    println!("\n[complex_operation] 步骤3：保存结果");
    match save_result(&data) {
        Ok(_) => {
            println!("[complex_operation] 步骤3成功");
        }
        Err(e) => {
            println!("[complex_operation] 步骤3失败: {}", e);
            return Err(format!("步骤3失败: {}", e));
        }
    }

    println!("\n========== 复杂操作完成 ==========");
    Ok(())
}
```

当出错时，你会看到：
```
========== 开始复杂操作 ==========

[complex_operation] 步骤1：读取配置
[read_config] 读取文件: config.txt
[read_config] 错误: No such file or directory
[complex_operation] 步骤1失败: 读取文件失败: No such file or directory
```

这样就能立即知道是在"步骤1：读取配置"时出错了。

---

## 第六章：给 AI 的具体指令

### 生成代码时必须遵守：

1. **每个文件开头都写注释**
```rust
// 文件：user_service.rs
// 说明：用户服务，负责用户的增删改查
// 创建时间：2026-01-16
```

2. **每个函数都写详细注释**
```rust
// 函数名：get_user
// 功能：根据ID获取用户信息
// 参数：
//   - id: i64 - 用户ID
// 返回：
//   - 成功：Ok(User) - 用户对象
//   - 失败：Err(String) - 错误信息
// 注意：如果用户不存在，返回错误而不是 None
pub fn get_user(id: i64) -> Result<User, String> {
    // 实现
}
```

3. **所有函数都打印日志**
```rust
pub fn any_function() -> Result<(), String> {
    println!("[any_function] 开始执行");

    // ... 逻辑

    println!("[any_function] 执行完成");
    Ok(())
}
```

4. **错误信息要详细**
```rust
// 不好
return Err(String::from("失败"));

// 好
return Err(format!("读取文件失败，路径: {}, 原因: {}", path, e));
```

5. **变量名要清晰**
```rust
// 不好
let u = get_user();
let d = get_data();

// 好
let user = get_user();
let user_data = get_data();
```

6. **不要用缩写**
```rust
// 不好
let usr_svc = UserService::new();
let cfg = load_config();

// 好
let user_service = UserService::new();
let config = load_config();
```

7. **每个步骤都要标记**
```rust
fn process() -> Result<(), String> {
    // 步骤1：验证输入
    println!("步骤1：验证输入");

    // 步骤2：读取数据
    println!("步骤2：读取数据");

    // 步骤3：保存结果
    println!("步骤3：保存结果");

    Ok(())
}
```

8. **for 循环要有计数**
```rust
let mut count = 0;
for item in &list {
    count = count + 1;
    println!("处理第 {} 项: {:?}", count, item);
}
```

---

## 第七章：问题排查清单

当代码出错时，按这个顺序检查：

### 检查清单

1. **看错误信息**
```
错误信息会指出：
- 哪个文件
- 哪一行
- 什么错误
```

2. **找到出错的函数**
```
根据日志输出，找到最后一个成功的步骤：
[function1] 开始
[function1] 步骤1成功
[function1] 步骤2失败: xxxx  <-- 这里出错了
```

3. **检查参数**
```rust
// 在函数开始打印所有参数
fn my_function(id: i64, name: &str) -> Result<(), String> {
    println!("[my_function] 参数 id = {}, name = {}", id, name);
    // ...
}
```

4. **检查中间变量**
```rust
// 打印中间变量
let result = some_calculation();
println!("计算结果: {}", result);
```

5. **检查文件路径**
```rust
// 检查文件是否存在
let path = "data/users.json";
if !std::path::Path::new(path).exists() {
    println!("文件不存在: {}", path);
}
```

6. **检查数据类型转换**
```rust
// 打印转换前后的值
let s = "123";
println!("转换前: {}", s);
let n = s.parse::<i32>().unwrap();
println!("转换后: {}", n);
```

### 常见错误和解决方法

**错误1：找不到文件**
```
错误信息: No such file or directory
解决：
1. 检查文件路径是否正确
2. 检查文件是否存在
3. 打印完整路径：println!("完整路径: {:?}", std::fs::canonicalize(path));
```

**错误2：类型不匹配**
```
错误信息: expected `String`, found `&str`
解决：
使用 .to_string() 转换：
let s: String = string_slice.to_string();
```

**错误3：值被移动**
```
错误信息: value moved here
解决：
使用 clone：
let copy = original.clone();
```

**错误4：借用检查错误**
```
错误信息: cannot borrow as mutable
解决：
1. 不要同时有可变和不可变借用
2. 或者 clone 一份数据
```

---

## 第八章：完整示例

### 完整的 User CRUD 示例

```rust
// 文件：user_service.rs
// 说明：用户服务，提供用户的增删改查功能
// 创建时间：2026-01-16

use std::collections::HashMap;
use std::fs;

// ==================== 数据结构 ====================

pub struct User {
    pub id: i64,
    pub name: String,
    pub email: String,
}

impl User {
    pub fn new(id: i64, name: String, email: String) -> Self {
        Self { id, name, email }
    }
}

impl std::fmt::Debug for User {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        write!(f, "User{{ id:{}, name:{}, email:{} }}",
               self.id, self.name, self.email)
    }
}

impl Clone for User {
    fn clone(&self) -> Self {
        User {
            id: self.id,
            name: self.name.clone(),
            email: self.email.clone(),
        }
    }
}

// ==================== Service ====================

pub struct UserService {
    users: HashMap<i64, User>,
    file_path: String,
}

impl UserService {
    // 创建服务
    pub fn new(file_path: String) -> Self {
        println!("[UserService::new] 创建用户服务");
        println!("[UserService::new] 数据文件: {}", file_path);

        Self {
            users: HashMap::new(),
            file_path: file_path,
        }
    }

    // 加载数据
    pub fn load(&mut self) -> Result<(), String> {
        println!("[UserService::load] 开始加载数据");

        // 检查文件是否存在
        if !std::path::Path::new(&self.file_path).exists() {
            println!("[UserService::load] 文件不存在，创建新文件");
            return Ok(());
        }

        // 读取文件
        let content = match fs::read_to_string(&self.file_path) {
            Ok(c) => {
                println!("[UserService::load] 读取文件成功，大小: {} 字节", c.len());
                c
            }
            Err(e) => {
                let error = format!("读取文件失败: {}", e);
                println!("[UserService::load] 错误: {}", error);
                return Err(error);
            }
        };

        // 这里应该解析 JSON，简化起见直接返回
        // TODO: 实现 JSON 解析

        println!("[UserService::load] 加载完成");
        Ok(())
    }

    // 保存数据
    pub fn save(&self) -> Result<(), String> {
        println!("[UserService::save] 开始保存数据");
        println!("[UserService::save] 用户数量: {}", self.users.len());

        // 转换为 JSON
        let mut json_array = String::from("[");

        let mut count = 0;
        for (id, user) in &self.users {
            if count > 0 {
                json_array.push_str(",");
            }

            let user_json = format!(
                r#"{{"id":{},"name":"{}","email":"{}"}}"#,
                user.id, user.name, user.email
            );
            json_array.push_str(&user_json);

            count = count + 1;
        }

        json_array.push_str("]");
        println!("[UserService::save] 生成 JSON: {}", json_array);

        // 写入文件
        match fs::write(&self.file_path, json_array) {
            Ok(_) => {
                println!("[UserService::save] 保存成功");
                Ok(())
            }
            Err(e) => {
                let error = format!("写入文件失败: {}", e);
                println!("[UserService::save] 错误: {}", error);
                Err(error)
            }
        }
    }

    // 创建用户
    pub fn create(&mut self, user: User) -> Result<(), String> {
        println!("[UserService::create] 创建用户: {:?}", user);

        // 检查是否已存在
        if self.users.contains_key(&user.id) {
            let error = format!("用户已存在，ID: {}", user.id);
            println!("[UserService::create] 错误: {}", error);
            return Err(error);
        }

        // 添加到 HashMap
        self.users.insert(user.id, user);
        println!("[UserService::create] 创建成功");

        Ok(())
    }

    // 获取用户
    pub fn get(&self, id: i64) -> Result<User, String> {
        println!("[UserService::get] 获取用户，ID: {}", id);

        match self.users.get(&id) {
            Some(user) => {
                println!("[UserService::get] 找到用户: {:?}", user);
                Ok(user.clone())
            }
            None => {
                let error = format!("用户不存在，ID: {}", id);
                println!("[UserService::get] 错误: {}", error);
                Err(error)
            }
        }
    }

    // 更新用户
    pub fn update(&mut self, user: User) -> Result<(), String> {
        println!("[UserService::update] 更新用户: {:?}", user);

        // 检查是否存在
        if !self.users.contains_key(&user.id) {
            let error = format!("用户不存在，ID: {}", user.id);
            println!("[UserService::update] 错误: {}", error);
            return Err(error);
        }

        // 更新
        self.users.insert(user.id, user);
        println!("[UserService::update] 更新成功");

        Ok(())
    }

    // 删除用户
    pub fn delete(&mut self, id: i64) -> Result<(), String> {
        println!("[UserService::delete] 删除用户，ID: {}", id);

        match self.users.remove(&id) {
            Some(_) => {
                println!("[UserService::delete] 删除成功");
                Ok(())
            }
            None => {
                let error = format!("用户不存在，ID: {}", id);
                println!("[UserService::delete] 错误: {}", error);
                Err(error)
            }
        }
    }

    // 列出所有用户
    pub fn list(&self) -> Vec<User> {
        println!("[UserService::list] 列出所有用户");
        println!("[UserService::list] 用户数量: {}", self.users.len());

        let mut result = Vec::new();
        for (_id, user) in &self.users {
            result.push(user.clone());
        }

        result
    }
}

// ==================== main.rs ====================

fn main() {
    println!("========== 用户管理系统 ==========\n");

    // 创建服务
    println!("步骤1：创建服务");
    let mut service = UserService::new(String::from("data/users.json"));

    // 加载数据
    println!("\n步骤2：加载数据");
    match service.load() {
        Ok(_) => println!("加载成功"),
        Err(e) => println!("加载失败: {}", e),
    }

    // 创建用户
    println!("\n步骤3：创建用户");
    let user1 = User::new(1, String::from("张三"), String::from("zhangsan@example.com"));
    match service.create(user1) {
        Ok(_) => println!("创建成功"),
        Err(e) => println!("创建失败: {}", e),
    }

    let user2 = User::new(2, String::from("李四"), String::from("lisi@example.com"));
    match service.create(user2) {
        Ok(_) => println!("创建成功"),
        Err(e) => println!("创建失败: {}", e),
    }

    // 列出所有用户
    println!("\n步骤4：列出所有用户");
    let all_users = service.list();
    for user in &all_users {
        println!("  - {:?}", user);
    }

    // 获取单个用户
    println!("\n步骤5：获取用户");
    match service.get(1) {
        Ok(user) => println!("获取成功: {:?}", user),
        Err(e) => println!("获取失败: {}", e),
    }

    // 更新用户
    println!("\n步骤6：更新用户");
    let updated_user = User::new(1, String::from("张三(已更新)"), String::from("zhangsan_new@example.com"));
    match service.update(updated_user) {
        Ok(_) => println!("更新成功"),
        Err(e) => println!("更新失败: {}", e),
    }

    // 删除用户
    println!("\n步骤7：删除用户");
    match service.delete(2) {
        Ok(_) => println!("删除成功"),
        Err(e) => println!("删除失败: {}", e),
    }

    // 保存数据
    println!("\n步骤8：保存数据");
    match service.save() {
        Ok(_) => println!("保存成功"),
        Err(e) => println!("保存失败: {}", e),
    }

    println!("\n========== 程序结束 ==========");
}
```

---

## 总结

### 给 AI 的核心指令

生成 Rust 代码时：

1. **只用标准库**
2. **不用闭包，用普通函数**
3. **不用复杂迭代器，用 for 循环**
4. **不用 Trait、泛型、生命周期**
5. **所有函数都打印日志**
6. **所有函数都有详细注释**
7. **所有错误都用 Result<T, String>**
8. **所有变量名都要清晰完整**
9. **手动实现 Debug 和 Clone**
10. **每个步骤都标记清楚**

### 核心模板

```rust
// 数据结构模板
pub struct DataType {
    pub field: Type,
}

impl DataType {
    pub fn new(...) -> Self { ... }
}

impl Debug for DataType { ... }
impl Clone for DataType { ... }

// 函数模板
pub fn function_name(param: Type) -> Result<ReturnType, String> {
    println!("[function_name] 开始");

    // 逻辑

    println!("[function_name] 完成");
    Ok(result)
}

// Service 模板
pub struct Service {
    field: Type,
}

impl Service {
    pub fn new(...) -> Self { ... }
    pub fn operation(&self, ...) -> Result<..., String> { ... }
}
```

记住：**简单、清晰、可追踪** 比性能更重要。
