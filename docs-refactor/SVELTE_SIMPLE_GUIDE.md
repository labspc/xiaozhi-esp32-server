# Svelte 前端框架简化指南 - AI 友好版

## 写给 AI 的话

这是 Svelte 框架的简化使用指南，必须严格遵守：

1. **只用 Svelte 的基础功能**
2. **不用高级特性（stores 复杂用法、context、高阶组件等）**
3. **代码要简单直接**
4. **每个组件都打印日志**
5. **所有代码都遵循相同模板**
6. **配合 RUST_SIMPLE_GUIDE.md 和 AXUM_SIMPLE_GUIDE.md 一起使用**

目标：让不懂 Svelte 的人也能看懂前端代码，出错了能快速定位。

---

## 第一章：Svelte 禁止使用的特性

### 1. 禁止使用复杂的 Stores 组合

```svelte
<!-- 禁止 - 不要用复杂的 derived stores -->
<script>
import { derived, writable } from 'svelte/store'

const count = writable(0)
const doubled = derived(count, $count => $count * 2)
const tripled = derived(doubled, $doubled => $doubled * 1.5)
</script>

<!-- 推荐 - 用简单的响应式变量 -->
<script>
let count = 0
let doubled = 0
let tripled = 0

function updateCount(newCount) {
    console.log('[updateCount] 更新计数:', newCount)
    count = newCount
    doubled = count * 2
    tripled = doubled * 1.5
    console.log('[updateCount] 结果:', { count, doubled, tripled })
}
</script>
```

### 2. 禁止使用 Context API

```svelte
<!-- 禁止 - 不要用 setContext/getContext -->
<script>
import { setContext, getContext } from 'svelte'

setContext('theme', { color: 'blue' })
const theme = getContext('theme')
</script>

<!-- 推荐 - 用简单的 props 传递 -->
<script>
export let theme = { color: 'blue' }
console.log('[Component] 接收到 theme:', theme)
</script>
```

### 3. 禁止使用 Actions

```svelte
<!-- 禁止 - 不要用自定义 actions -->
<script>
function customAction(node, params) {
    // 复杂的 DOM 操作
}
</script>
<div use:customAction={{ param: 'value' }}>内容</div>

<!-- 推荐 - 用 onMount 和普通函数 -->
<script>
import { onMount } from 'svelte'

let divElement
onMount(() => {
    console.log('[onMount] 初始化 DOM 元素')
    // 简单的初始化操作
})
</script>
<div bind:this={divElement}>内容</div>
```

### 4. 禁止使用 Transitions 的高级特性

```svelte
<!-- 禁止 - 不要自定义复杂的过渡函数 -->
<script>
import { cubicOut } from 'svelte/easing'

function customTransition(node, { duration }) {
    return {
        duration,
        css: t => {
            const eased = cubicOut(t)
            return `transform: scale(${eased})`
        }
    }
}
</script>

<!-- 推荐 - 用简单的内置过渡或 CSS -->
<script>
import { fade } from 'svelte/transition'
</script>
<div transition:fade>内容</div>
```

### 5. 禁止使用插槽的高级特性

```svelte
<!-- 禁止 - 不要用命名插槽和 slot props -->
<slot name="header" {data} />

<!-- 推荐 - 用简单的默认插槽或直接传递 props -->
<script>
export let headerData = null
</script>
{#if headerData}
    <div class="header">{headerData.title}</div>
{/if}
<slot />
```

### 6. 禁止使用动态组件

```svelte
<!-- 禁止 - 不要用 svelte:component -->
<script>
import ComponentA from './A.svelte'
import ComponentB from './B.svelte'

let selected = 'A'
const components = { A: ComponentA, B: ComponentB }
</script>
<svelte:component this={components[selected]} />

<!-- 推荐 - 用 if/else 显式切换 -->
<script>
import ComponentA from './A.svelte'
import ComponentB from './B.svelte'

let selected = 'A'
console.log('[Component] 当前选中:', selected)
</script>

{#if selected === 'A'}
    <ComponentA />
{:else if selected === 'B'}
    <ComponentB />
{/if}
```

---

## 第二章：基础 package.json

```json
{
  "name": "xiaozhi-web",
  "version": "1.0.0",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "devDependencies": {
    "@sveltejs/vite-plugin-svelte": "^3.0.0",
    "svelte": "^4.0.0",
    "vite": "^5.0.0"
  },
  "dependencies": {
    "axios": "^1.6.0"
  }
}
```

注意：
- 不需要复杂的状态管理库（Pinia、Redux）
- 不需要 UI 框架（保持简单）
- 只用 axios 做 HTTP 请求（简单直接）

---

## 第三章：标准项目结构

```
xiaozhi-web/
├── index.html             # 入口 HTML
├── package.json
├── vite.config.js         # Vite 配置
├── src/
│   ├── main.js           # 程序入口
│   ├── App.svelte        # 根组件
│   ├── apis/             # API 层（重要）
│   │   ├── http.js       # HTTP 封装
│   │   ├── user.js       # 用户 API
│   │   ├── device.js     # 设备 API
│   │   └── agent.js      # 智能体 API
│   ├── components/       # 可复用组件
│   │   ├── DeviceCard.svelte
│   │   ├── UserDialog.svelte
│   │   └── AudioPlayer.svelte
│   ├── pages/            # 页面组件
│   │   ├── Login.svelte
│   │   ├── Home.svelte
│   │   ├── DeviceList.svelte
│   │   └── ModelConfig.svelte
│   ├── stores/           # 简单状态管理
│   │   ├── user.js       # 用户状态
│   │   └── config.js     # 配置状态
│   ├── utils/            # 工具函数
│   │   ├── format.js     # 格式化工具
│   │   └── logger.js     # 日志工具
│   └── router/           # 简单路由
│       └── index.js
└── public/
    └── assets/           # 静态资源
```

---

## 第四章：核心模板

### 模板1：main.js（程序入口）

```javascript
// 文件：main.js
// 说明：程序入口
// 创建时间：2026-01-16

console.log('========== 应用启动 ==========')

import App from './App.svelte'

// 步骤1：创建 Svelte 应用
console.log('[main] 步骤1：创建应用')
const app = new App({
    target: document.getElementById('app'),
    props: {
        appName: '小智管理平台'
    }
})

console.log('[main] 应用创建成功')
console.log('====================================')

export default app
```

### 模板2：App.svelte（根组件）

```svelte
<!-- 文件：App.svelte -->
<!-- 说明：应用根组件，管理全局状态和路由 -->
<!-- 创建时间：2026-01-16 -->

<script>
import { onMount } from 'svelte'
import Login from './pages/Login.svelte'
import Home from './pages/Home.svelte'
import { user } from './stores/user.js'

// Props
export let appName = '应用'

// State
let currentPage = 'login'  // 当前页面：login / home
let isLoading = true

// 步骤1：初始化
onMount(() => {
    console.log('\n========== 应用初始化 ==========')
    console.log('[App] 应用名称:', appName)

    // 步骤1.1：检查登录状态
    console.log('[App] 步骤1.1：检查登录状态')
    checkLoginStatus()

    // 步骤1.2：加载完成
    console.log('[App] 步骤1.2：加载完成')
    isLoading = false

    console.log('====================================\n')
})

// 检查登录状态
// 功能：从本地存储读取 token，判断是否已登录
function checkLoginStatus() {
    console.log('[checkLoginStatus] 开始检查')

    const token = localStorage.getItem('token')
    if (token) {
        console.log('[checkLoginStatus] 发现 token，已登录')
        currentPage = 'home'
    } else {
        console.log('[checkLoginStatus] 未发现 token，未登录')
        currentPage = 'login'
    }
}

// 处理登录成功
// 参数：event.detail.token - 登录令牌
function handleLoginSuccess(event) {
    console.log('[handleLoginSuccess] 登录成功')
    console.log('[handleLoginSuccess] token:', event.detail.token)

    // 保存 token
    localStorage.setItem('token', event.detail.token)

    // 更新 store
    user.set({
        isAuthenticated: true,
        token: event.detail.token
    })

    // 跳转到首页
    console.log('[handleLoginSuccess] 跳转到首页')
    currentPage = 'home'
}

// 处理登出
function handleLogout() {
    console.log('[handleLogout] 用户登出')

    // 清除 token
    localStorage.removeItem('token')

    // 重置 store
    user.set({
        isAuthenticated: false,
        token: ''
    })

    // 跳转到登录页
    console.log('[handleLogout] 跳转到登录页')
    currentPage = 'login'
}
</script>

<!-- 加载中 -->
{#if isLoading}
    <div class="loading">
        <p>加载中...</p>
    </div>
<!-- 登录页 -->
{:else if currentPage === 'login'}
    <Login on:loginSuccess={handleLoginSuccess} />
<!-- 首页 -->
{:else if currentPage === 'home'}
    <Home on:logout={handleLogout} />
<!-- 未知页面 -->
{:else}
    <div class="error">
        <p>页面不存在</p>
    </div>
{/if}

<style>
.loading {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
    font-size: 18px;
}

.error {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
    color: red;
}
</style>
```

### 模板3：HTTP 请求封装（apis/http.js）

```javascript
// 文件：apis/http.js
// 说明：HTTP 请求封装，统一处理请求和响应
// 创建时间：2026-01-16

import axios from 'axios'

// 步骤1：配置基础 URL
console.log('[http] 步骤1：配置 axios')
const BASE_URL = 'http://localhost:8002'

// 创建 axios 实例
const http = axios.create({
    baseURL: BASE_URL,
    timeout: 30000,  // 30秒超时
    headers: {
        'Content-Type': 'application/json'
    }
})

// 请求拦截器
// 功能：在发送请求前，自动添加认证 token
http.interceptors.request.use(
    (config) => {
        console.log('\n[http.request] ========== 发送请求 ==========')
        console.log('[http.request] URL:', config.url)
        console.log('[http.request] 方法:', config.method)

        // 步骤1：从本地存储获取 token
        const token = localStorage.getItem('token')
        if (token) {
            console.log('[http.request] 添加 Authorization header')
            config.headers.Authorization = `Bearer ${token}`
        } else {
            console.log('[http.request] 未找到 token')
        }

        // 步骤2：打印请求参数
        if (config.params) {
            console.log('[http.request] 查询参数:', config.params)
        }
        if (config.data) {
            console.log('[http.request] 请求体:', config.data)
        }

        console.log('[http.request] ====================================\n')
        return config
    },
    (error) => {
        console.log('[http.request] 请求配置失败:', error)
        return Promise.reject(error)
    }
)

// 响应拦截器
// 功能：统一处理响应和错误
http.interceptors.response.use(
    (response) => {
        console.log('\n[http.response] ========== 收到响应 ==========')
        console.log('[http.response] 状态码:', response.status)
        console.log('[http.response] 数据:', response.data)

        // 步骤1：检查业务状态码
        const { code, msg, data } = response.data

        if (code === 0 || code === 'success') {
            console.log('[http.response] 业务处理成功')
            console.log('[http.response] ====================================\n')
            return data  // 只返回业务数据
        } else if (code === 401) {
            console.log('[http.response] 认证失败，跳转到登录页')
            localStorage.removeItem('token')
            window.location.href = '/login'
            return Promise.reject(new Error('未授权'))
        } else {
            console.log('[http.response] 业务处理失败:', msg)
            console.log('[http.response] ====================================\n')
            return Promise.reject(new Error(msg || '请求失败'))
        }
    },
    (error) => {
        console.log('\n[http.response] ========== 请求错误 ==========')
        console.log('[http.response] 错误信息:', error.message)

        if (error.response) {
            // 服务器返回错误状态码
            console.log('[http.response] 响应状态码:', error.response.status)
            console.log('[http.response] 响应数据:', error.response.data)
        } else if (error.request) {
            // 请求已发出，但没有收到响应
            console.log('[http.response] 网络错误：未收到响应')
        } else {
            // 请求配置出错
            console.log('[http.response] 请求配置错误')
        }

        console.log('[http.response] ====================================\n')
        return Promise.reject(error)
    }
)

// 导出 HTTP 方法
export default {
    // GET 请求
    // 参数：url - 请求地址, params - 查询参数
    // 返回：Promise<data>
    get(url, params = {}) {
        console.log('[http.get] 发起 GET 请求:', url)
        return http.get(url, { params })
    },

    // POST 请求
    // 参数：url - 请求地址, data - 请求体数据
    // 返回：Promise<data>
    post(url, data = {}) {
        console.log('[http.post] 发起 POST 请求:', url)
        return http.post(url, data)
    },

    // PUT 请求
    // 参数：url - 请求地址, data - 请求体数据
    // 返回：Promise<data>
    put(url, data = {}) {
        console.log('[http.put] 发起 PUT 请求:', url)
        return http.put(url, data)
    },

    // DELETE 请求
    // 参数：url - 请求地址
    // 返回：Promise<data>
    delete(url) {
        console.log('[http.delete] 发起 DELETE 请求:', url)
        return http.delete(url)
    }
}
```

### 模板4：API 模块（apis/user.js）

```javascript
// 文件：apis/user.js
// 说明：用户相关的 API 接口
// 创建时间：2026-01-16

import http from './http.js'

// 用户登录
// 参数：username - 用户名, password - 密码
// 返回：Promise<{ token, userInfo }>
export async function login(username, password) {
    console.log('[api.user.login] 开始登录')
    console.log('[api.user.login] 用户名:', username)

    try {
        const data = await http.post('/api/auth/login', {
            username: username,
            password: password
        })

        console.log('[api.user.login] 登录成功')
        console.log('[api.user.login] 返回数据:', data)
        return data
    } catch (error) {
        console.log('[api.user.login] 登录失败:', error.message)
        throw error
    }
}

// 获取用户信息
// 返回：Promise<UserInfo>
export async function getUserInfo() {
    console.log('[api.user.getUserInfo] 获取用户信息')

    try {
        const data = await http.get('/api/user/info')
        console.log('[api.user.getUserInfo] 获取成功')
        return data
    } catch (error) {
        console.log('[api.user.getUserInfo] 获取失败:', error.message)
        throw error
    }
}

// 获取用户列表
// 参数：page - 页码, size - 每页数量
// 返回：Promise<{ list, total }>
export async function getUserList(page = 1, size = 10) {
    console.log('[api.user.getUserList] 获取用户列表')
    console.log('[api.user.getUserList] 页码:', page, '每页:', size)

    try {
        const data = await http.get('/api/user/list', {
            page: page,
            size: size
        })

        console.log('[api.user.getUserList] 获取成功，数量:', data.list.length)
        return data
    } catch (error) {
        console.log('[api.user.getUserList] 获取失败:', error.message)
        throw error
    }
}

// 创建用户
// 参数：userData - 用户数据 { username, email, password }
// 返回：Promise<{ userId }>
export async function createUser(userData) {
    console.log('[api.user.createUser] 创建用户')
    console.log('[api.user.createUser] 用户数据:', userData)

    try {
        const data = await http.post('/api/user/create', userData)
        console.log('[api.user.createUser] 创建成功，用户ID:', data.userId)
        return data
    } catch (error) {
        console.log('[api.user.createUser] 创建失败:', error.message)
        throw error
    }
}

// 更新用户
// 参数：userId - 用户ID, userData - 更新的数据
// 返回：Promise<void>
export async function updateUser(userId, userData) {
    console.log('[api.user.updateUser] 更新用户')
    console.log('[api.user.updateUser] 用户ID:', userId)
    console.log('[api.user.updateUser] 更新数据:', userData)

    try {
        await http.put(`/api/user/${userId}`, userData)
        console.log('[api.user.updateUser] 更新成功')
    } catch (error) {
        console.log('[api.user.updateUser] 更新失败:', error.message)
        throw error
    }
}

// 删除用户
// 参数：userId - 用户ID
// 返回：Promise<void>
export async function deleteUser(userId) {
    console.log('[api.user.deleteUser] 删除用户')
    console.log('[api.user.deleteUser] 用户ID:', userId)

    try {
        await http.delete(`/api/user/${userId}`)
        console.log('[api.user.deleteUser] 删除成功')
    } catch (error) {
        console.log('[api.user.deleteUser] 删除失败:', error.message)
        throw error
    }
}
```

### 模板5：简单状态管理（stores/user.js）

```javascript
// 文件：stores/user.js
// 说明：用户状态管理（简单版本）
// 创建时间：2026-01-16

import { writable } from 'svelte/store'

// 创建用户状态 store
// 说明：使用 writable store，可以直接读写
function createUserStore() {
    console.log('[store.user] 创建用户 store')

    // 初始状态
    const initialState = {
        isAuthenticated: false,
        token: '',
        userInfo: null
    }

    // 创建 writable store
    const { subscribe, set, update } = writable(initialState)

    return {
        // 订阅（用于 $user 语法）
        subscribe,

        // 设置完整状态
        // 参数：state - 新的状态对象
        set: (state) => {
            console.log('[store.user.set] 设置状态:', state)
            set(state)
        },

        // 登录
        // 参数：token - 登录令牌, userInfo - 用户信息
        login: (token, userInfo) => {
            console.log('[store.user.login] 用户登录')
            console.log('[store.user.login] token:', token)
            console.log('[store.user.login] userInfo:', userInfo)

            set({
                isAuthenticated: true,
                token: token,
                userInfo: userInfo
            })

            // 保存到 localStorage
            localStorage.setItem('token', token)
            localStorage.setItem('userInfo', JSON.stringify(userInfo))
        },

        // 登出
        logout: () => {
            console.log('[store.user.logout] 用户登出')

            set(initialState)

            // 清除 localStorage
            localStorage.removeItem('token')
            localStorage.removeItem('userInfo')
        },

        // 从 localStorage 恢复状态
        restore: () => {
            console.log('[store.user.restore] 恢复用户状态')

            const token = localStorage.getItem('token')
            const userInfoStr = localStorage.getItem('userInfo')

            if (token && userInfoStr) {
                console.log('[store.user.restore] 发现已保存的状态')
                const userInfo = JSON.parse(userInfoStr)

                set({
                    isAuthenticated: true,
                    token: token,
                    userInfo: userInfo
                })
            } else {
                console.log('[store.user.restore] 未发现已保存的状态')
            }
        }
    }
}

// 导出 store 实例
export const user = createUserStore()
```

### 模板6：页面组件（pages/Login.svelte）

```svelte
<!-- 文件：pages/Login.svelte -->
<!-- 说明：登录页面 -->
<!-- 创建时间：2026-01-16 -->

<script>
import { createEventDispatcher } from 'svelte'
import { login } from '../apis/user.js'

// 事件派发器（用于向父组件发送事件）
const dispatch = createEventDispatcher()

// State
let username = ''
let password = ''
let loading = false
let errorMessage = ''

// 处理登录
// 功能：调用登录 API，成功后通知父组件
async function handleLogin() {
    console.log('\n========== 开始登录 ==========')
    console.log('[Login] 用户名:', username)

    // 步骤1：验证输入
    console.log('[Login] 步骤1：验证输入')
    if (!username || !password) {
        console.log('[Login] 验证失败：用户名或密码为空')
        errorMessage = '请输入用户名和密码'
        return
    }

    // 步骤2：清除错误信息
    errorMessage = ''
    loading = true

    try {
        // 步骤3：调用登录 API
        console.log('[Login] 步骤3：调用登录 API')
        const data = await login(username, password)

        // 步骤4：登录成功
        console.log('[Login] 步骤4：登录成功')
        console.log('[Login] token:', data.token)

        // 步骤5：通知父组件
        console.log('[Login] 步骤5：发送 loginSuccess 事件')
        dispatch('loginSuccess', {
            token: data.token,
            userInfo: data.userInfo
        })

        console.log('[Login] 登录流程完成')
        console.log('====================================\n')

    } catch (error) {
        // 登录失败
        console.log('[Login] 登录失败:', error.message)
        errorMessage = error.message || '登录失败，请重试'

    } finally {
        loading = false
    }
}

// 处理回车键
function handleKeydown(event) {
    if (event.key === 'Enter') {
        console.log('[Login] 检测到回车键，触发登录')
        handleLogin()
    }
}
</script>

<div class="login-page">
    <div class="login-card">
        <h1 class="title">小智管理平台</h1>

        <div class="form">
            <!-- 用户名输入 -->
            <div class="form-item">
                <label for="username">用户名</label>
                <input
                    id="username"
                    type="text"
                    bind:value={username}
                    on:keydown={handleKeydown}
                    placeholder="请输入用户名"
                    disabled={loading}
                />
            </div>

            <!-- 密码输入 -->
            <div class="form-item">
                <label for="password">密码</label>
                <input
                    id="password"
                    type="password"
                    bind:value={password}
                    on:keydown={handleKeydown}
                    placeholder="请输入密码"
                    disabled={loading}
                />
            </div>

            <!-- 错误提示 -->
            {#if errorMessage}
                <div class="error-message">
                    {errorMessage}
                </div>
            {/if}

            <!-- 登录按钮 -->
            <button
                class="login-btn"
                on:click={handleLogin}
                disabled={loading}
            >
                {loading ? '登录中...' : '登录'}
            </button>
        </div>
    </div>
</div>

<style>
.login-page {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
    background: white;
    border-radius: 12px;
    padding: 40px;
    width: 100%;
    max-width: 400px;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
}

.title {
    font-size: 28px;
    font-weight: bold;
    color: #333;
    text-align: center;
    margin-bottom: 32px;
}

.form {
    display: flex;
    flex-direction: column;
    gap: 20px;
}

.form-item {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

label {
    font-size: 14px;
    font-weight: 500;
    color: #555;
}

input {
    padding: 12px 16px;
    border: 1px solid #e4e6ef;
    border-radius: 8px;
    font-size: 14px;
    background: #f6f8fb;
    transition: all 0.2s;
}

input:focus {
    outline: none;
    border-color: #667eea;
    background: white;
}

input:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}

.error-message {
    padding: 12px;
    background: #fee;
    border: 1px solid #fcc;
    border-radius: 8px;
    color: #c33;
    font-size: 14px;
}

.login-btn {
    padding: 14px;
    background: #667eea;
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 16px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
}

.login-btn:hover {
    background: #5568d3;
}

.login-btn:active {
    transform: scale(0.98);
}

.login-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}
</style>
```

### 模板7：列表页面（pages/DeviceList.svelte）

```svelte
<!-- 文件：pages/DeviceList.svelte -->
<!-- 说明：设备列表页面 -->
<!-- 创建时间：2026-01-16 -->

<script>
import { onMount } from 'svelte'
import { getDeviceList, deleteDevice } from '../apis/device.js'
import DeviceCard from '../components/DeviceCard.svelte'

// State
let devices = []
let loading = true
let errorMessage = ''

// 页面加载时获取设备列表
onMount(() => {
    console.log('[DeviceList] 组件挂载')
    fetchDevices()
})

// 获取设备列表
// 功能：从 API 获取设备列表并更新 state
async function fetchDevices() {
    console.log('\n========== 获取设备列表 ==========')
    console.log('[fetchDevices] 开始获取')

    loading = true
    errorMessage = ''

    try {
        // 调用 API
        const data = await getDeviceList()

        // 更新状态
        devices = data.list
        console.log('[fetchDevices] 获取成功，设备数量:', devices.length)
        console.log('[fetchDevices] 设备列表:', devices)

    } catch (error) {
        console.log('[fetchDevices] 获取失败:', error.message)
        errorMessage = error.message || '获取设备列表失败'

    } finally {
        loading = false
        console.log('====================================\n')
    }
}

// 删除设备
// 参数：event.detail.deviceId - 设备ID
async function handleDelete(event) {
    const deviceId = event.detail.deviceId
    console.log('\n========== 删除设备 ==========')
    console.log('[handleDelete] 设备ID:', deviceId)

    // 步骤1：确认删除
    const confirmed = confirm('确定要删除这个设备吗？')
    if (!confirmed) {
        console.log('[handleDelete] 用户取消删除')
        return
    }

    try {
        // 步骤2：调用删除 API
        console.log('[handleDelete] 步骤2：调用删除 API')
        await deleteDevice(deviceId)

        // 步骤3：从列表中移除
        console.log('[handleDelete] 步骤3：从列表中移除')
        devices = devices.filter(d => d.id !== deviceId)

        console.log('[handleDelete] 删除成功')
        console.log('====================================\n')

    } catch (error) {
        console.log('[handleDelete] 删除失败:', error.message)
        alert('删除失败：' + error.message)
    }
}

// 刷新列表
function handleRefresh() {
    console.log('[handleRefresh] 刷新列表')
    fetchDevices()
}
</script>

<div class="device-list-page">
    <div class="header">
        <h1>设备管理</h1>
        <button class="refresh-btn" on:click={handleRefresh}>
            刷新
        </button>
    </div>

    <!-- 加载中 -->
    {#if loading}
        <div class="loading">
            <p>加载中...</p>
        </div>

    <!-- 错误信息 -->
    {:else if errorMessage}
        <div class="error">
            <p>{errorMessage}</p>
            <button on:click={handleRefresh}>重试</button>
        </div>

    <!-- 设备列表 -->
    {:else if devices.length > 0}
        <div class="device-grid">
            {#each devices as device (device.id)}
                <DeviceCard
                    {device}
                    on:delete={handleDelete}
                />
            {/each}
        </div>

    <!-- 空状态 -->
    {:else}
        <div class="empty">
            <p>暂无设备</p>
        </div>
    {/if}
</div>

<style>
.device-list-page {
    padding: 20px;
    max-width: 1200px;
    margin: 0 auto;
}

.header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
}

h1 {
    font-size: 28px;
    color: #333;
}

.refresh-btn {
    padding: 10px 20px;
    background: #667eea;
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
}

.loading, .error, .empty {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    min-height: 300px;
}

.device-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 20px;
}
</style>
```

### 模板8：可复用组件（components/DeviceCard.svelte）

```svelte
<!-- 文件：components/DeviceCard.svelte -->
<!-- 说明：设备卡片组件 -->
<!-- 创建时间：2026-01-16 -->

<script>
import { createEventDispatcher } from 'svelte'

// Props
export let device = {
    id: '',
    name: '',
    mac: '',
    status: 'offline'
}

// 事件派发器
const dispatch = createEventDispatcher()

// 删除设备
function handleDelete() {
    console.log('[DeviceCard] 删除设备:', device.id)
    dispatch('delete', {
        deviceId: device.id
    })
}

// 查看详情
function handleView() {
    console.log('[DeviceCard] 查看设备详情:', device.id)
    dispatch('view', {
        deviceId: device.id
    })
}

// 计算状态样式
function getStatusClass(status) {
    if (status === 'online') {
        return 'status-online'
    } else if (status === 'offline') {
        return 'status-offline'
    } else {
        return 'status-unknown'
    }
}

// 计算状态文本
function getStatusText(status) {
    if (status === 'online') {
        return '在线'
    } else if (status === 'offline') {
        return '离线'
    } else {
        return '未知'
    }
}
</script>

<div class="device-card">
    <div class="card-header">
        <h3>{device.name}</h3>
        <span class="status {getStatusClass(device.status)}">
            {getStatusText(device.status)}
        </span>
    </div>

    <div class="card-body">
        <div class="info-item">
            <span class="label">MAC地址</span>
            <span class="value">{device.mac}</span>
        </div>
    </div>

    <div class="card-footer">
        <button class="btn-view" on:click={handleView}>
            查看
        </button>
        <button class="btn-delete" on:click={handleDelete}>
            删除
        </button>
    </div>
</div>

<style>
.device-card {
    background: white;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    transition: all 0.2s;
}

.device-card:hover {
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
    transform: translateY(-2px);
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
}

h3 {
    font-size: 18px;
    color: #333;
    margin: 0;
}

.status {
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 500;
}

.status-online {
    background: #d4edda;
    color: #155724;
}

.status-offline {
    background: #f8d7da;
    color: #721c24;
}

.status-unknown {
    background: #e2e3e5;
    color: #383d41;
}

.card-body {
    margin-bottom: 16px;
}

.info-item {
    display: flex;
    justify-content: space-between;
    padding: 8px 0;
}

.label {
    color: #666;
    font-size: 14px;
}

.value {
    color: #333;
    font-size: 14px;
    font-weight: 500;
}

.card-footer {
    display: flex;
    gap: 12px;
}

button {
    flex: 1;
    padding: 10px;
    border: none;
    border-radius: 8px;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.2s;
}

.btn-view {
    background: #667eea;
    color: white;
}

.btn-view:hover {
    background: #5568d3;
}

.btn-delete {
    background: #f56565;
    color: white;
}

.btn-delete:hover {
    background: #e53e3e;
}
</style>
```

---

## 第五章：给 AI 的具体指令

### 生成 Svelte 代码时必须遵守：

1. **所有组件都打印日志**
```svelte
<script>
function handleClick() {
    console.log('[ComponentName] 按钮被点击')
    // 处理逻辑
}
</script>
```

2. **每个函数都有详细注释**
```javascript
// 获取用户列表
// 参数：page - 页码, size - 每页数量
// 返回：Promise<{ list, total }>
async function getUserList(page, size) {
    // 实现
}
```

3. **使用简单的响应式变量，不用复杂的 stores**
```svelte
<script>
// 推荐
let count = 0

function increment() {
    count = count + 1
}
</script>
```

4. **API 调用使用 async/await**
```svelte
<script>
import { getUserList } from '../apis/user.js'

async function fetchUsers() {
    try {
        const data = await getUserList()
        users = data.list
    } catch (error) {
        errorMessage = error.message
    }
}
</script>
```

5. **使用 createEventDispatcher 向父组件传递事件**
```svelte
<script>
import { createEventDispatcher } from 'svelte'

const dispatch = createEventDispatcher()

function handleSubmit() {
    dispatch('submit', { data: formData })
}
</script>
```

6. **使用 bind 进行双向绑定**
```svelte
<input type="text" bind:value={username} />
<input type="checkbox" bind:checked={agreed} />
```

7. **条件渲染使用 if/else**
```svelte
{#if loading}
    <p>加载中...</p>
{:else if error}
    <p>错误：{error}</p>
{:else}
    <p>数据：{data}</p>
{/if}
```

8. **列表渲染使用 each**
```svelte
{#each items as item (item.id)}
    <div>{item.name}</div>
{/each}
```

9. **样式使用 scoped style**
```svelte
<style>
.button {
    padding: 10px;
    background: blue;
}
</style>
```

---

## 第六章：与后端交互标准流程

### 1. 认证流程

```svelte
<!-- Login.svelte -->
<script>
import { login } from '../apis/user.js'
import { user } from '../stores/user.js'

async function handleLogin() {
    console.log('[Login] 开始登录')

    // 步骤1：调用登录 API
    const data = await login(username, password)

    // 步骤2：保存到 store
    user.login(data.token, data.userInfo)

    // 步骤3：跳转
    window.location.href = '/home'
}
</script>
```

### 2. 数据获取流程

```svelte
<!-- DeviceList.svelte -->
<script>
import { onMount } from 'svelte'
import { getDeviceList } from '../apis/device.js'

let devices = []
let loading = true

onMount(() => {
    fetchDevices()
})

async function fetchDevices() {
    console.log('[fetchDevices] 开始获取')
    loading = true

    try {
        const data = await getDeviceList()
        devices = data.list
        console.log('[fetchDevices] 成功，数量:', devices.length)
    } catch (error) {
        console.log('[fetchDevices] 失败:', error.message)
    } finally {
        loading = false
    }
}
</script>
```

### 3. 表单提交流程

```svelte
<!-- CreateDevice.svelte -->
<script>
import { createDevice } from '../apis/device.js'

let formData = {
    name: '',
    mac: ''
}
let submitting = false

async function handleSubmit() {
    console.log('[handleSubmit] 提交表单')
    console.log('[handleSubmit] 表单数据:', formData)

    // 步骤1：验证
    if (!formData.name || !formData.mac) {
        alert('请填写完整信息')
        return
    }

    // 步骤2：提交
    submitting = true
    try {
        await createDevice(formData)
        console.log('[handleSubmit] 创建成功')
        alert('创建成功')
    } catch (error) {
        console.log('[handleSubmit] 创建失败:', error.message)
        alert('创建失败：' + error.message)
    } finally {
        submitting = false
    }
}
</script>

<form on:submit|preventDefault={handleSubmit}>
    <input bind:value={formData.name} placeholder="设备名称" />
    <input bind:value={formData.mac} placeholder="MAC地址" />
    <button type="submit" disabled={submitting}>
        {submitting ? '提交中...' : '提交'}
    </button>
</form>
```

---

## 第七章：常见场景模板

### 1. 分页列表

```svelte
<script>
import { onMount } from 'svelte'
import { getUserList } from '../apis/user.js'

let users = []
let currentPage = 1
let pageSize = 10
let total = 0
let loading = false

onMount(() => {
    fetchUsers()
})

async function fetchUsers() {
    console.log('[fetchUsers] 页码:', currentPage)
    loading = true

    try {
        const data = await getUserList(currentPage, pageSize)
        users = data.list
        total = data.total
        console.log('[fetchUsers] 总数:', total)
    } catch (error) {
        console.log('[fetchUsers] 失败:', error.message)
    } finally {
        loading = false
    }
}

function handlePageChange(page) {
    console.log('[handlePageChange] 切换到第', page, '页')
    currentPage = page
    fetchUsers()
}

function handlePrevPage() {
    if (currentPage > 1) {
        handlePageChange(currentPage - 1)
    }
}

function handleNextPage() {
    const maxPage = Math.ceil(total / pageSize)
    if (currentPage < maxPage) {
        handlePageChange(currentPage + 1)
    }
}
</script>

<div>
    <!-- 用户列表 -->
    {#each users as user (user.id)}
        <div>{user.name}</div>
    {/each}

    <!-- 分页 -->
    <div class="pagination">
        <button on:click={handlePrevPage} disabled={currentPage === 1}>
            上一页
        </button>
        <span>第 {currentPage} 页 / 共 {Math.ceil(total / pageSize)} 页</span>
        <button on:click={handleNextPage} disabled={currentPage >= Math.ceil(total / pageSize)}>
            下一页
        </button>
    </div>
</div>
```

### 2. 搜索功能

```svelte
<script>
import { onMount } from 'svelte'
import { searchDevices } from '../apis/device.js'

let keyword = ''
let devices = []
let loading = false

// 延时搜索（防抖）
let searchTimeout
function handleSearch() {
    console.log('[handleSearch] 搜索关键词:', keyword)

    // 清除之前的定时器
    if (searchTimeout) {
        clearTimeout(searchTimeout)
    }

    // 500ms 后执行搜索
    searchTimeout = setTimeout(() => {
        performSearch()
    }, 500)
}

async function performSearch() {
    console.log('[performSearch] 执行搜索')
    loading = true

    try {
        const data = await searchDevices(keyword)
        devices = data.list
        console.log('[performSearch] 找到', devices.length, '个结果')
    } catch (error) {
        console.log('[performSearch] 搜索失败:', error.message)
    } finally {
        loading = false
    }
}
</script>

<div>
    <input
        type="text"
        bind:value={keyword}
        on:input={handleSearch}
        placeholder="搜索设备"
    />

    {#if loading}
        <p>搜索中...</p>
    {:else}
        {#each devices as device (device.id)}
            <div>{device.name}</div>
        {/each}
    {/if}
</div>
```

### 3. 对话框组件

```svelte
<!-- ConfirmDialog.svelte -->
<script>
import { createEventDispatcher } from 'svelte'

// Props
export let visible = false
export let title = '确认'
export let message = '确定要执行此操作吗？'

const dispatch = createEventDispatcher()

function handleConfirm() {
    console.log('[ConfirmDialog] 用户确认')
    dispatch('confirm')
}

function handleCancel() {
    console.log('[ConfirmDialog] 用户取消')
    dispatch('cancel')
}

// 阻止事件冒泡
function handleBackdropClick(event) {
    if (event.target === event.currentTarget) {
        handleCancel()
    }
}
</script>

{#if visible}
    <div class="dialog-backdrop" on:click={handleBackdropClick}>
        <div class="dialog">
            <div class="dialog-header">
                <h3>{title}</h3>
            </div>
            <div class="dialog-body">
                <p>{message}</p>
            </div>
            <div class="dialog-footer">
                <button class="btn-cancel" on:click={handleCancel}>
                    取消
                </button>
                <button class="btn-confirm" on:click={handleConfirm}>
                    确认
                </button>
            </div>
        </div>
    </div>
{/if}

<style>
.dialog-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
}

.dialog {
    background: white;
    border-radius: 12px;
    width: 90%;
    max-width: 400px;
    padding: 24px;
}

.dialog-header h3 {
    margin: 0 0 16px 0;
    font-size: 20px;
    color: #333;
}

.dialog-body p {
    margin: 0 0 24px 0;
    color: #666;
    line-height: 1.5;
}

.dialog-footer {
    display: flex;
    gap: 12px;
}

button {
    flex: 1;
    padding: 10px;
    border: none;
    border-radius: 8px;
    cursor: pointer;
}

.btn-cancel {
    background: #e0e0e0;
    color: #333;
}

.btn-confirm {
    background: #667eea;
    color: white;
}
</style>
```

---

## 第八章：迁移策略

### 从 Vue 迁移到 Svelte 的对应关系

| Vue 特性 | Svelte 等价物 |
|---------|-------------|
| `data()` | 直接定义变量 `let count = 0` |
| `computed` | 使用 `$:` 响应式语句 |
| `methods` | 直接定义函数 |
| `props` | `export let propName` |
| `watch` | `$:` 监听变量变化 |
| `emit` | `createEventDispatcher()` |
| `v-model` | `bind:value` |
| `v-if` | `{#if}` |
| `v-for` | `{#each}` |
| `mounted` | `onMount()` |
| Vuex store | Svelte writable store |

### Vue 代码示例

```vue
<template>
    <div>
        <input v-model="username" />
        <button @click="handleClick">点击</button>
        <p v-if="showMessage">{{ message }}</p>
        <ul>
            <li v-for="item in items" :key="item.id">
                {{ item.name }}
            </li>
        </ul>
    </div>
</template>

<script>
export default {
    props: {
        title: String
    },
    data() {
        return {
            username: '',
            message: 'Hello',
            showMessage: false,
            items: []
        }
    },
    computed: {
        itemCount() {
            return this.items.length
        }
    },
    methods: {
        handleClick() {
            this.showMessage = !this.showMessage
            this.$emit('click', { username: this.username })
        }
    },
    mounted() {
        this.fetchItems()
    }
}
</script>
```

### 对应的 Svelte 代码

```svelte
<script>
import { onMount, createEventDispatcher } from 'svelte'

// Props
export let title = ''

// State
let username = ''
let message = 'Hello'
let showMessage = false
let items = []

// Computed (使用响应式语句)
$: itemCount = items.length

// 事件派发器
const dispatch = createEventDispatcher()

// Methods
function handleClick() {
    console.log('[handleClick] 按钮被点击')
    showMessage = !showMessage
    dispatch('click', { username: username })
}

async function fetchItems() {
    console.log('[fetchItems] 获取数据')
    // 获取数据的逻辑
}

// Lifecycle
onMount(() => {
    console.log('[onMount] 组件挂载')
    fetchItems()
})
</script>

<div>
    <input bind:value={username} />
    <button on:click={handleClick}>点击</button>
    {#if showMessage}
        <p>{message}</p>
    {/if}
    <ul>
        {#each items as item (item.id)}
            <li>{item.name}</li>
        {/each}
    </ul>
</div>
```

---

## 第九章：问题排查清单

### 1. 响应式更新不生效

```svelte
<script>
// 错误 - 直接修改数组元素不会触发更新
let items = [1, 2, 3]
items[0] = 10  // 不会触发更新

// 正确 - 重新赋值数组
let items = [1, 2, 3]
items[0] = 10
items = items  // 触发更新

// 或者使用展开运算符
items = [...items]
</script>
```

### 2. API 调用错误

```svelte
<script>
// 检查网络请求
async function fetchData() {
    console.log('[fetchData] 开始请求')
    console.log('[fetchData] URL:', API_URL)

    try {
        const data = await api.get('/endpoint')
        console.log('[fetchData] 响应数据:', data)
    } catch (error) {
        console.log('[fetchData] 请求失败:', error)
        console.log('[fetchData] 错误详情:', error.response)
    }
}
</script>
```

### 3. 组件事件不触发

```svelte
<!-- 父组件 -->
<script>
function handleEvent(event) {
    console.log('[Parent] 收到事件:', event.detail)
}
</script>
<ChildComponent on:customEvent={handleEvent} />

<!-- 子组件 -->
<script>
import { createEventDispatcher } from 'svelte'

const dispatch = createEventDispatcher()

function triggerEvent() {
    console.log('[Child] 发送事件')
    dispatch('customEvent', { data: 'test' })
}
</script>
```

---

## 总结

### 核心原则

1. **简单直接**：不用复杂特性
2. **详细日志**：每个函数都打印日志
3. **清晰注释**：每个函数都有功能说明
4. **响应式变量**：用简单的 `let` 变量
5. **async/await**：API 调用用 async/await
6. **组件通信**：用 props 和 events

### 标准工作流程

1. 定义 API 接口（apis/）
2. 创建页面组件（pages/）
3. 提取可复用组件（components/）
4. 处理状态管理（stores/）
5. 调试和测试
6. 查看日志排查问题

记住：**简单、清晰、可追踪**，这样 AI 生成的代码你也能看懂和维护。
