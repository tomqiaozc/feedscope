# Feedscope 使用指南

Feedscope 是一个 Twitter/X 社交媒体分析平台。你可以用它来监控特定 Twitter 账号的推文、用 AI 翻译推文内容、搜索和浏览 Twitter 用户资料，以及生成 API 密钥供外部程序调用。

线上地址：https://app-frontend-feedscope-prod.azurewebsites.net/

---

## 第一步：登录

打开线上地址，你会看到一个登录页面，上面有 **"Sign in with Google"** 按钮。

点击按钮，用你的 Google 账号完成授权即可登录。登录成功后会自动跳转到 Dashboard 首页。

> 如果配置了邮箱白名单（ALLOWED_EMAILS），只有白名单中的 Google 邮箱才能登录。

---

## 第二步：了解导航结构

登录后，左侧有一个侧边栏，分为上下两组导航：

**上方（核心功能）：**
- **Dashboard** — 首页，展示整体状态一览
- **Watchlists** — 监控列表，核心功能入口
- **Groups** — 分组管理，批量管理 Twitter 用户
- **Explore** — 搜索推文、浏览用户资料

**下方（配置与统计）：**
- **Settings** — 配置 TweAPI 凭证（必须先配置才能使用核心功能）
- **AI Settings** — 配置 AI 翻译服务
- **Webhooks** — 管理外部 API 访问密钥
- **Usage** — 查看 API 调用量和额度

---

## 第三步：配置 TweAPI 凭证（必须）

在使用任何 Twitter 数据功能之前，你需要先配置 TweAPI 凭证。

1. 点击左侧 **Settings**
2. 你会看到 "TweAPI Credentials" 区域，提示 "No TweAPI credentials configured"
3. 点击 **Add Credentials**
4. 在 **API Key** 输入框中填入你的 TweAPI API Key
5. （可选）在 **Cookie** 输入框中填入 Twitter Cookie — 某些高级功能（如获取书签）需要这个
6. 点击 **Save**

保存后，API Key 和 Cookie 会以 `••••••••••••` 脱敏显示，下方标注最后更新时间。

**后续修改：** 点击右上角的铅笔图标进入编辑模式。如果只想改其中一个字段，另一个留空即可（placeholder 会提示 "Leave blank to keep current"）。

**删除凭证：** 在编辑模式下点击红色 **Delete** 按钮，再点 **Confirm** 确认。

---

## 第四步：配置 AI 翻译（可选，但推荐）

如果你想使用 AI 翻译功能（将英文推文翻译成中文 + 生成锐评），需要配置 AI Provider。

1. 点击左侧 **AI Settings**
2. 在 **Provider** 下拉框中选择一个：
   - **Anthropic** — 使用 Claude，默认模型 `claude-sonnet-4-20250514`
   - **OpenAI** — 使用 GPT，默认模型 `gpt-4o-mini`
   - **Custom** — 使用自定义的 OpenAI 兼容接口，需要额外填 Base URL
3. 在 **API Key** 中填入对应的密钥
4. **Model** 会自动填入默认值，你也可以手动改成其他模型
5. **SDK Type** 是只读的，根据 Provider 自动决定
6. 点击 **Test Connection** 验证连接是否正常 — 成功后会显示 AI 的一句回复
7. 确认没问题后点击 **Save**

---

## 第五步：创建 Watchlist 并添加成员

这是 Feedscope 的核心功能 — 创建一个监控列表，加入你要追踪的 Twitter 账号，然后批量拉取他们的推文。

### 5.1 创建 Watchlist

1. 点击左侧 **Watchlists**
2. 点击右上角 **Create** 按钮
3. 弹出对话框，填写：
   - **Name**（必填）— 例如 "AI 大佬"
   - **Description**（可选）— 例如 "追踪 AI 领域的重要推文"
4. 点击 **Create**

创建成功后，你会在列表中看到一张卡片，显示名称、描述、成员数（0）、帖子数（0）。

### 5.2 添加成员

1. 点击刚创建的 Watchlist 卡片，进入详情页
2. 默认在 **Members** 标签页，点击 **Add Member**
3. 弹出对话框，填写：
   - **Username**（必填）— Twitter 用户名，不需要带 `@`，例如 `elonmusk`
   - **Display Name**（可选）— 你想给这个人起的备注名
   - **Notes**（可选）— 备注信息
   - **Tags**（可选）— 用逗号分隔的标签，例如 `tech, AI, founder`
4. 点击 **Add**

你可以添加多个成员。每个成员会以行的形式展示，包括头像、@用户名、备注和彩色标签药丸。

**编辑成员：** 悬停到成员行，点击铅笔图标可以修改备注和标签（用户名不可更改）。

**删除成员：** 悬停到成员行，点击垃圾桶图标。

---

## 第六步：抓取推文

配置好凭证、创建好 Watchlist 并添加成员后，就可以抓取推文了。

1. 在 Watchlist 详情页顶部，点击 **Fetch** 按钮
2. 会出现一个实时进度条，显示：
   - 当前正在抓取的用户名（如 "Fetching @elonmusk (1/3)..."）
   - 已抓取的帖子总数
   - 如果某个用户抓取出错，会以红色文字显示错误信息
3. 全部完成后，进度条消失，显示 "Fetch complete."

**取消抓取：** 在抓取过程中，Fetch 按钮会变成 **Cancel Fetch**，点击即可中止。已抓取到的推文会保留。

> 注意：每次 Fetch 会先清空该 Watchlist 的所有旧推文，然后重新拉取。

---

## 第七步：浏览和筛选推文

抓取完成后，点击 **Posts** 标签页查看推文。

### 推文卡片

每条推文显示：
- 作者头像、名称、发帖时间
- 推文正文（URL 会自动变成可点击的链接）
- 图片/视频（如果有的话）
- 互动数据：点赞数、转发数、回复数、浏览数

### 按标签筛选

页面顶部会显示你给成员设置的所有标签（如 `tech`、`AI`）。点击某个标签药丸，就只显示带该标签的成员的推文。再次点击取消筛选。

### 按成员筛选

如果 Watchlist 有多个成员，会出现一个 "All members" 下拉框。选择某个成员，就只显示该成员的推文。

### 加载更多

每页显示 50 条推文。如果还有更多，底部会出现 **Load More** 按钮。

### 删除推文

每条推文卡片上有垃圾桶图标，点击后确认即可删除该条推文。

---

## 第八步：AI 翻译推文

### 单条翻译

在 Posts 标签页中，每条推文都有一个翻译图标。点击后会调用 AI 进行翻译，完成后推文卡片底部会多出：
- **中文翻译** — 推文的中文翻译
- **锐评**（斜体）— AI 对推文的简短评论
- **引用翻译**（如果推文引用了别人的推文）

### 批量翻译

1. 在 Posts 标签页顶部右侧，有一个 **Translate All (N)** 按钮，N 是未翻译推文的数量
2. 点击后开始批量翻译，出现进度条显示：
   - 当前进度（如 "Translating post 3/10..."）
   - 已完成数和失败数
3. 每翻译完一条，对应的推文卡片会实时更新显示翻译内容
4. 全部完成后显示汇总（如 "Batch translate complete: 9 translated, 1 errors."）

**取消批量翻译：** 点击 **Cancel Translate** 即可中止，已翻译的内容会保留。

---

## 第九步：Explore — 搜索推文和浏览用户

### 搜索推文

1. 点击左侧 **Explore**
2. 在搜索框中输入关键词（例如 "AI agent"），按 Enter
3. 搜索结果以瀑布流形式展示推文卡片
4. 每条结果下方有 "View @xxx profile" 链接，可以跳转到该用户的详情页

### 用户详情页

点击用户链接后进入用户详情页（URL: `/explore/user/{username}`），包含：

**顶部资料卡：** 头像、显示名、@用户名、认证标记、个人简介、位置、网站链接、粉丝数/关注数/推文数。

**六个标签页：**
- **Tweets** — 该用户发的推文
- **Timeline** — 用户的时间线
- **Replies** — 用户的回复
- **Highlights** — 用户的精选推文
- **Followers** — 粉丝列表（每个粉丝可以点击，跳转到其详情页）
- **Following** — 关注列表（同上）

你也可以直接在地址栏输入 `/explore/user/elonmusk` 来访问某个用户。

---

## 第十步：Groups — 分组管理

Groups 用来管理 Twitter 用户的分组，支持批量导入。

### 创建 Group

1. 点击左侧 **Groups**
2. 点击 **Create**，填写名称和描述，确认

### 添加单个成员

1. 进入 Group 详情页
2. 点击 **Add Member**，输入 Username，确认

### 批量导入

1. 准备一个 `.txt` 或 `.csv` 文件，内容是 Twitter 用户名列表，支持以下格式：
   ```
   @elonmusk
   @BillGates
   satlovendrk, jack
   openai
   ```
   逗号分隔或换行分隔都可以，`@` 前缀可有可无。

2. 点击 **Import** 按钮，选择文件
3. 系统会自动解析并批量添加（文件大小限制 1MB）

---

## 第十一步：Webhooks — 创建外部 API 密钥

如果你想让外部脚本或程序通过 API 访问 Feedscope 的 Twitter 数据，需要创建 Webhook Key。

### 创建密钥

1. 点击左侧 **Webhooks**
2. 点击 **Create Key**
3. 填写 **Name**（必填）和 **Description**（可选）
4. 确认后会弹出一个对话框，**显示完整的 API 密钥**
5. 点击复制按钮保存密钥 — **关闭对话框后密钥将不再显示**

### 使用密钥调用 API

使用 `X-Webhook-Key` 请求头来调用外部 API，例如：

```bash
# 搜索推文
curl -H "X-Webhook-Key: YOUR_KEY" \
  "https://app-backend-feedscope-prod.azurewebsites.net/api/v1/external/search?q=AI&count=5"

# 查看用户信息
curl -H "X-Webhook-Key: YOUR_KEY" \
  "https://app-backend-feedscope-prod.azurewebsites.net/api/v1/external/user/elonmusk"

# 获取用户推文
curl -H "X-Webhook-Key: YOUR_KEY" \
  "https://app-backend-feedscope-prod.azurewebsites.net/api/v1/external/user/elonmusk/tweets?count=10"
```

### 轮换密钥

点击某个密钥旁的 **Rotate** 按钮，确认后旧密钥立即失效，系统生成新密钥并展示。

### 删除密钥

点击 **Delete** 按钮，确认后密钥被永久删除。

---

## 第十二步：Usage — 查看用量

点击左侧 **Usage** 进入用量统计页面。

**顶部三张汇总卡片：**
- **Total API Calls** — 所选日期范围内的总 API 调用次数
- **Webhook Calls** — 通过 Webhook Key 产生的调用次数
- **Credits Remaining** — TweAPI 剩余额度

**TweAPI Credits 详情卡：** 显示已使用额度、剩余额度、计费周期，以及一个使用量进度条。

**用量明细表：** 按日期分组，列出每天每个 API 端点的调用次数。可以通过顶部的 **From / To** 日期选择器修改查询范围，也可以点击 **Date** 或 **Count** 列标题进行排序。

---

## Dashboard — 一目了然

任何时候点击左侧 **Dashboard** 回到首页，可以看到六张状态卡片：

| 卡片 | 显示内容 | 点击跳转 |
|------|---------|---------|
| Credentials | TweAPI 凭证是否已配置（绿色勾 / 红色叉） | Settings |
| AI Provider | AI Provider 和模型名称，或 "Not configured" | AI Settings |
| Watchlists | 监控列表数量 | Watchlists |
| Groups | 分组数量 | Groups |
| API Calls (7d) | 最近 7 天 API 调用总次数 | Usage |
| Credits Remaining | TweAPI 剩余额度 | Usage |

---

## 快速上手流程总结

如果你是第一次使用，按这个顺序操作：

```
登录
  -> Settings：填入 TweAPI API Key
  -> AI Settings：填入 AI Provider 和 API Key，Test Connection
  -> Watchlists：创建一个监控列表
  -> 添加几个 Twitter 用户名作为成员（可以加标签）
  -> 点击 Fetch 抓取推文
  -> 切到 Posts 标签页浏览推文
  -> 点击 Translate All 批量翻译
  -> 去 Explore 搜索感兴趣的关键词
  -> 如有需要，创建 Webhook Key 供外部调用
```
