
<div align="center">
    <a href="https://v2.nonebot.dev/store">
    <img src="https://raw.githubusercontent.com/fllesser/nonebot-plugin-template/refs/heads/resource/.docs/NoneBotPlugin.svg" width="300" alt="logo"></a>
</div>

<div align="center">

## ✨ *基于 NoneBot2 的 QQ 用户信息查询插件* ✨

<a href="./LICENSE">
    <img src="https://img.shields.io/github/license/006lp/nonebot-plugin-qqdetail.svg" alt="license">
</a>
<a href="https://pypi.python.org/pypi/nonebot-plugin-qqdetail">
    <img src="https://img.shields.io/pypi/v/nonebot-plugin-qqdetail.svg" alt="pypi">
</a>
<img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="python">
<img src="https://img.shields.io/badge/adapter-OneBot_V11-blueviolet" alt="adapter">
<a href="https://github.com/astral-sh/uv">
    <img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json" alt="uv">
</a>
</div>

</div>

## 📖 介绍

一个基于 NoneBot2 的插件，用于查询 QQ 用户的公开信息。通过 QQ 号或 @用户 方式获取用户资料，包括昵称、头像、等级、生日、VIP 等信息。数据来源于 OneBot 协议提供的用户信息接口。

目前仅支持 OneBot V11 协议。

## 📁 项目结构

```
nonebot-plugin-qqdetail/
├── __init__.py           # 插件入口，包含 PluginMetadata
├── config.py             # 配置模型（使用 Pydantic v2）
├── matchers.py           # 事件处理器（命令和通知）
├── utils.py              # 工具函数和数据处理
├── draw.py               # 图片生成逻辑
├── assets/               # 资源文件夹（需手动创建）
│   ├── 可爱字体.ttf      # 中文字体
│   └── NotoColorEmoji.ttf       # Emoji 字体
├── pyproject.toml        # 项目配置
├── README.md             # 使用文档
├── .env.example          # 配置示例
└── .gitignore            # Git 忽略文件
```

## 💿 安装

<details open>
<summary>使用 nb-cli 安装</summary>

在 NoneBot2 项目的根目录下打开命令行，运行以下命令进行安装：

```bash
nb plugin install nonebot-plugin-qqdetail --upgrade
```

如需使用国内镜像源（如清华源）加速安装：

```bash
nb plugin install nonebot-plugin-qqdetail --upgrade -i https://pypi.tuna.tsinghua.edu.cn/simple
```
</details>

<details>
<summary>使用包管理器安装</summary>

在 NoneBot2 项目的根目录下（或插件目录，取决于项目结构），打开命令行，使用你偏好的包管理器运行相应命令：

<details open>
<summary>uv</summary>

```bash
uv add nonebot-plugin-qqdetail
```
安装仓库 master 分支：

```bash
uv add git+https://github.com/006lp/nonebot-plugin-qqdetail@master
```
</details>

<details>
<summary>pdm</summary>

```bash
pdm add nonebot-plugin-qqdetail
```
安装仓库 master 分支：

```bash
pdm add git+https://github.com/006lp/nonebot-plugin-qqdetail@master
```
</details>

<details>
<summary>poetry</summary>

```bash
poetry add nonebot-plugin-qqdetail
```
安装仓库 master 分支：

```bash
poetry add git+https://github.com/006lp/nonebot-plugin-qqdetail@master
```
</details>

<br/>
然后，**手动或使用 `nb` 命令**将插件加载到你的 NoneBot2 项目中。
如果使用 `pyproject.toml` 管理插件，请确保在 `[tool.nonebot]` 部分添加了插件名：

```toml
[tool.nonebot]
# ... 其他配置 ...
plugins = ["nonebot_plugin_qqdetail"] # 确保你的插件代码在 nonebot_plugin_qqdetail 文件夹下
# 或者如果你直接放在根目录的插件文件夹，可能是 "your_plugins_folder.qqdetail" 之类的路径
# ... 其他插件 ...
```

</details>

## ⚙️ 配置

插件通过 `.env` 文件进行配置，所有配置项均为可选，默认为推荐设置。

### 基础配置

| 配置项                    | 必填  | 默认值  | 说明                                      |
| :------------------------ | :---: | :-----: | :---------------------------------------- |
| `QQDETAIL_ONLY_ADMIN`     |  否   | `false` | 仅管理员可用（默认：false）               |
| `QQDETAIL_BOX_BLACKLIST`  |  否   |  `[]`   | 黑名单用户列表（这些用户的资料无法被查询） |
| `QQDETAIL_WHITELIST_GROUPS` |  否   |  `[]`   | 群聊白名单（仅这些群可使用命令，留空则所有群都可用） |

### 自动获取配置

| 配置项                               | 必填  | 默认值  | 说明                                      |
| :----------------------------------- | :---: | :-----: | :---------------------------------------- |
| `QQDETAIL_AUTO_BOX_CONFIG__INCREASE_BOX` |  否   | `false` | 自动获取新入群用户信息                    |
| `QQDETAIL_AUTO_BOX_CONFIG__DECREASE_BOX` |  否   | `false` | 自动获取退群用户信息                      |
| `QQDETAIL_AUTO_BOX_CONFIG__WHITE_GROUPS` |  否   |  `[]`   | 自动获取功能的群聊白名单（留空则所有群都启用） |

### 速率限制配置

| 配置项                                   | 必填  | 默认值 | 说明                                      |
| :--------------------------------------- | :---: | :----: | :---------------------------------------- |
| `QQDETAIL_RATE_LIMIT_CONFIG__TIME`       |  否   |  `0`   | 速率限制时间（分钟），0表示不限制         |
| `QQDETAIL_RATE_LIMIT_CONFIG__WHITE_GROUPS` |  否   |  `[]`   | 速率限制白名单群聊（这些群不受速率限制） |
| `QQDETAIL_RATE_LIMIT_CONFIG__WHITE_USERS` |  否   |  `[]`   | 速率限制白名单用户（这些用户不受速率限制） |

### 显示配置

你可以精细控制要显示的用户信息字段（默认为全部显示）：

| 分类     | 配置项                                           | 说明         |
| :------- | :----------------------------------------------- | :----------- |
| **基本信息** | `QQDETAIL_DISPLAY_CONFIG__CARD`                | 群昵称       |
|          | `QQDETAIL_DISPLAY_CONFIG__TITLE`               | 群头衔       |
|          | `QQDETAIL_DISPLAY_CONFIG__SEX`                 | 性别         |
|          | `QQDETAIL_DISPLAY_CONFIG__AGE`                 | 年龄         |
| **生日相关** | `QQDETAIL_DISPLAY_CONFIG__BIRTHDAY_CONFIG__ENABLE` | 生日         |
|          | `QQDETAIL_DISPLAY_CONFIG__BIRTHDAY_CONFIG__CONSTELLATION` | 星座     |
|          | `QQDETAIL_DISPLAY_CONFIG__BIRTHDAY_CONFIG__ZODIAC` | 生肖         |
| **联系信息** | `QQDETAIL_DISPLAY_CONFIG__PHONE_NUM`            | 手机号码     |
|          | `QQDETAIL_DISPLAY_CONFIG__EMAIL`               | 邮箱         |
|          | `QQDETAIL_DISPLAY_CONFIG__POST_CODE`           | 邮编         |
| **地理信息** | `QQDETAIL_DISPLAY_CONFIG__HOME_TOWN`            | 家乡         |
|          | `QQDETAIL_DISPLAY_CONFIG__ADDRESS`             | 现居地       |
| **其他信息** | `QQDETAIL_DISPLAY_CONFIG__BLOOD_TYPE`           | 血型         |
|          | `QQDETAIL_DISPLAY_CONFIG__CAREER`              | 职业         |
|          | `QQDETAIL_DISPLAY_CONFIG__REMARK`              | 备注         |
|          | `QQDETAIL_DISPLAY_CONFIG__LABELS`              | 标签         |
|          | `QQDETAIL_DISPLAY_CONFIG__UNFRIENDLY`          | 风险账号标记 |
| **VIP 信息** | `QQDETAIL_DISPLAY_CONFIG__VIP_CONFIG__ENABLE`   | VIP          |
|          | `QQDETAIL_DISPLAY_CONFIG__VIP_CONFIG__YEARS_VIP` | 年VIP        |
|          | `QQDETAIL_DISPLAY_CONFIG__VIP_CONFIG__VIP_LEVEL` | VIP等级      |
| **活动信息** | `QQDETAIL_DISPLAY_CONFIG__LOGIN_DAYS`           | 连续登录天数 |
|          | `QQDETAIL_DISPLAY_CONFIG__LEVEL`               | 群等级       |
|          | `QQDETAIL_DISPLAY_CONFIG__JOIN_TIME`           | 加群时间     |
| **个性签名** | `QQDETAIL_DISPLAY_CONFIG__LONG_NICK`            | 个性签名     |

**`.env` 文件配置示例：**

```env
# 基础配置
QQDETAIL_ONLY_ADMIN=false
QQDETAIL_BOX_BLACKLIST=["123456789", "987654321"]
QQDETAIL_WHITELIST_GROUPS=["123456789"]

# 自动获取配置
QQDETAIL_AUTO_BOX_CONFIG__INCREASE_BOX=false
QQDETAIL_AUTO_BOX_CONFIG__DECREASE_BOX=false
QQDETAIL_AUTO_BOX_CONFIG__WHITE_GROUPS=["123456789"]

# 速率限制配置
QQDETAIL_RATE_LIMIT_CONFIG__TIME=5
QQDETAIL_RATE_LIMIT_CONFIG__WHITE_GROUPS=["123456789"]
QQDETAIL_RATE_LIMIT_CONFIG__WHITE_USERS=["123456789"]

# 显示配置（关闭手机号显示以保护隐私）
QQDETAIL_DISPLAY_CONFIG__PHONE_NUM=false
```

**注意:** `.env` 具体示例参见`.env.example`。另外，文件中的列表通常需要以 JSON 字符串的形式提供。

## 🎉 使用

### 指令表

| 指令                            |  别名  | 权限  | 需要@ |   范围    | 说明                                                                            |
| :------------------------------ | :----: | :---: | :---: | :-------: | :------------------------------------------------------------------------------ |
| `/detail <QQ号 或 @用户 或 无>` | `info` | 群员  | 可选  | 群聊/私聊 | 查询目标 QQ 用户的详细信息。支持 QQ 号、@用户，或不带参数查询自己。 |

### 使用说明

*   **`<QQ号>`**: 输入 5-11 位的有效 QQ 号码
*   **`@用户`**: 在群聊中直接 @ 指定的群成员
*   **无参数**: 直接发送指令查询发送者本人的信息
*   **数据来源**: 基于 OneBot 协议获取用户信息，准确性取决于连接的 OneBot 实现
*   **权限控制**: 支持多种权限控制，如管理员专用、用户黑名单等

### 🎨 返回示例

**查询成功示例：**
```
[图片：用户头像和彩色文字]
QQ号：123456789
昵称：示例昵称
性别：男
年龄：20
生日：05-15
星座：金牛座
生肖：龙
现居：广东-深圳
QQ等级：50级
注册时间：2010年
签名：这是一个示例签名。
```

**格式错误示例：**
```
命令格式错误、QQ号无效或包含多余参数。
请使用：
/detail <QQ号(5-11位)> 或 /detail @用户
/info <QQ号(5-11位)> 或 /info @用户
/detail (查询自己)
```

**查询失败示例：**
```
获取 QQ 信息失败 (UID: 123456789)。
原因：用户信息获取失败
```

## ⚠️ 重要提醒

*   **学习交流用途**：本插件仅供学习和交流使用，请勿用于任何非法目的
*   **隐私保护**：查询用户信息时请尊重他人隐私，确保使用符合相关法律法规
*   **免责声明**：用户需对自身使用行为负责，开发者不对使用本插件产生的任何后果承担责任

## 📄 许可证

本项目采用 [AGPL-3.0](./LICENSE) (GNU Affero General Public License v3.0) 开源许可证。

### AGPL-3.0 许可证说明

AGPL-3.0 是 GNU 自由软件基金会发布的开源许可证，特别适用于网络应用。其主要特点包括：

* **网络服务条款**：如果您修改本软件并通过网络提供服务，必须公开修改后的完整源代码
* **Copyleft 特性**：任何基于本项目的衍生作品必须采用相同的许可证
* **用户自由保护**：确保用户在使用网络服务时享有修改和再分发的自由

有关许可证的完整条款，请查看 [LICENSE](./LICENSE) 文件或访问 [GNU 官网](https://www.gnu.org/licenses/agpl-3.0.html)。

## 🙏 致谢

*   **NoneBot2 社区**：提供了优秀的机器人开发框架
*   **OneBot 协议**：提供了标准化的机器人通信协议
*   **AstrbotPlugin-ProfileSearch**：本插件参考了其设计思路