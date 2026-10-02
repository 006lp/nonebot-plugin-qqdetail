<div align="center">
    <a href="https://v2.nonebot.dev/store">
    <img src="https://github.com/Misty02600/nonebot-plugin-template/releases/download/assets/NoneBotPlugin.png" width="310" alt="logo"></a>

# ✨ Nonebot-Plugin-QQDetail

**基于 NoneBot2 的 QQ 公开资料卡片插件**

多目标查询 · 中文 / Emoji 卡片 · 文本输出 · 群通知 · 延时撤回

[![License](https://img.shields.io/badge/license-AGPL--3.0--only-blue)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![NoneBot2](https://img.shields.io/badge/NoneBot2-2.5.0%2B-EA5252)](https://nonebot.dev/)
[![Adapter](https://img.shields.io/badge/adapter-OneBot%20V11-4B8BBE)](#installation)

[安装](#installation) · [使用](#usage) · [配置](#configuration) · [常见问题](#faq) · [参与贡献](#contributing)

</div>

## 📖 功能

| 功能 | 说明 |
| :--- | :--- |
| 🔎 多目标查询 | 支持 QQ 号、文字 @QQ 号和实际 At，按输入顺序去重 |
| 🎨 资料卡片 | 中文与 Emoji、QQ 头像、长文本换行和自动分页 |
| 📝 文本输出 | 通过命令参数切换，图片渲染失败时自动回退 |
| 🛡️ 查询保护 | SUPERUSERS 与保护名单、自查、电话和邮箱脱敏 |
| 👋 群通知 | 可选入群 / 主动退群查询，支持群白名单 |
| ⏱️ 延时撤回 | 成功结果默认 10 秒撤回，可配置关闭 |

资料来自 OneBot V11 的陌生人及群成员接口。协议端返回的字段不同，插件只展示可用资料；扩展字段的支持情况以所用协议端为准。

<a id="installation"></a>

## 💿 安装

需要 **Python 3.10+、NoneBot2 2.5.0+、nonebot-plugin-alconna 0.62.1+**，以及已连接的 **OneBot V11** 适配器与协议端。

### 使用 nb-cli

~~~shell
nb plugin install nonebot-plugin-qqdetail
~~~

### 使用包管理器

在机器人项目根目录执行：

~~~shell
uv add nonebot-plugin-qqdetail
~~~

在现有 `[tool.nonebot]` 插件列表中加入本插件：

~~~toml
[tool.nonebot]
plugins = ["nonebot_plugin_qqdetail"]
~~~

也可在初始化 NoneBot 后直接加载：

~~~python
nonebot.load_plugin("nonebot_plugin_qqdetail")
~~~

<a id="usage"></a>

## 🎉 使用

示例使用 `/` 前缀，实际前缀遵循机器人配置中的 `COMMAND_START`。命令同时支持群聊和私聊。

| 命令示例 | 功能 |
| :--- | :--- |
| `/qqdetail` | 查询自己的资料 |
| `/qqdetail 123456` | 查询指定 QQ 号 |
| `/qqdetail @某人` | 查询被 At 的用户 |
| `/qqdetail 123456 @234567 @某人` | 查询多个目标，重复目标只查询一次 |
| `/qqdetail 123456 --text` | 本次使用文本输出 |
| `/box @某人 --image` | 本次使用图片输出 |
| `/qqdetail --help` | 查看命令帮助 |

默认别名：`qq资料`、`查qq`、`查q`、`box`、`盒`、`开盒`。

> [!NOTE]
> `--text` 和 `--image` 不能同时使用。不接受 `@全体成员`；指定目标无效或全部被拒绝时不会回退自查。一个目标查询或发送失败时，其他目标仍会继续处理。

### 文本展示示例

~~~text
QQ号：123456
昵称：示例用户 🐱
群昵称：示例群名片
群身份：成员
性别：男
电话：138******78
邮箱：a***@example.com
QQ等级：太阳x1 月亮x1 (20)
签名：你好，NoneBot！
~~~

示例仅展示部分字段。实际输出由配置和协议端返回的数据决定，默认使用图片。

<a id="configuration"></a>

## ⚙️ 配置

所有配置均为可选项，在机器人项目的 `.env` 文件中设置即可。

| 配置项 | 默认值 | 说明 |
| :--- | :---: | :--- |
| `qqdetail_output_mode` | `"image"` | 默认输出方式：`image` 或 `text` |
| `qqdetail_recall_time` | `10` | 成功结果的撤回秒数；`0` 关闭，错误提示不撤回 |
| `qqdetail_desensitize` | `true` | 电话与邮箱脱敏，同时作用于图片和文本 |
| `qqdetail_font_path` | 随包字体 | 可选文本字体文件路径 |
| `qqdetail_display_options` | 默认字段，UID 除外 | 支持中文标签或字段键，按固定字段顺序展示 |
| `qqdetail_command_aliases` | 上述别名 | 自定义别名，保留主命令 `qqdetail` |
| `qqdetail_only_admin` | `false` | 开启后，仅 SUPERUSERS 可查询他人 |
| `qqdetail_protect_ids` | `[]` | 禁止他人查询的 QQ 号，支持数字或字符串 |
| `qqdetail_auto_enter` | `false` | 自动查询入群成员 |
| `qqdetail_auto_exit` | `false` | 自动查询主动退群成员；踢人不触发 |
| `qqdetail_auto_groups` | `[]` | 自动查询的群白名单；为空时适用于全部群 |

**常用配置示例：**

~~~dotenv
QQDETAIL_OUTPUT_MODE=image
QQDETAIL_RECALL_TIME=10
QQDETAIL_DESENSITIZE=true
QQDETAIL_DISPLAY_OPTIONS=["QQ号","昵称","群昵称","性别","QQ等级","签名"]
~~~

### 查询权限与群通知

~~~dotenv
QQDETAIL_ONLY_ADMIN=true
QQDETAIL_PROTECT_IDS=["123456"]

QQDETAIL_AUTO_ENTER=true
QQDETAIL_AUTO_EXIT=false
QQDETAIL_AUTO_GROUPS=["234567"]
~~~

机器人始终不可查询。SUPERUSERS 和保护名单禁止他人查询，用户可以自查；群主、群管理员身份不会自动授予 SUPERUSERS 权限。

自动通知跳过机器人、SUPERUSERS 和保护名单，不受手动查询的 `qqdetail_only_admin` 限制，也不阻断其他插件。通知查询失败时保持静默。

### 全部展示字段

中文标签与字段键均可用于 `qqdetail_display_options`，展示顺序如下：

| 中文标签 | 字段键 |
| :--- | :--- |
| QQ号 | `user_id` |
| UID | `uid` |
| QID | `qid` |
| 昵称 | `nickname` |
| 备注 | `remark` |
| 群昵称 | `card` |
| 群头衔 | `title` |
| 群身份 | `role` |
| 性别 | `sex` |
| 生日 | `birthday` |
| 星座 | `constellation` |
| 生肖 | `zodiac` |
| 年龄 | `age` |
| 血型 | `kBloodType` |
| 电话 | `phoneNum` |
| 邮箱 | `eMail` |
| 家乡 | `homeTown` |
| 现居 | `address` |
| 地区 | `area` |
| 学校 | `college` |
| 职位 | `pos` |
| 职业 | `makeFriendCareer` |
| 个性标签 | `labels` |
| 风险账号 | `unfriendly` |
| 机器人账号 | `is_robot` |
| 隐藏QQ等级 | `isHideQQLevel` |
| 特权图标 | `isHidePrivilegeIcon` |
| 屏蔽用户 | `isBlock` |
| 免打扰 | `isMsgDisturb` |
| 特别关心 | `isSpecialCareOpen` |
| 空间特别关心 | `isSpecialCareZone` |
| 自定义状态 | `customStatusDescInfo` |
| 企点企业 | `qidian_enterprise_name` |
| QQVIP | `is_vip` |
| 年VIP | `is_years_vip` |
| VIP等级 | `vip_level` |
| 群等级 | `level` |
| QQ等级 | `qqLevel` |
| 加群时间 | `join_time` |
| 最后发言 | `last_sent_time` |
| 注册时间 | `reg_time` |
| 登录天数 | `login_days` |
| 签名 | `long_nick` |

可使用中文标签，也可使用字段键，例如：

~~~dotenv
QQDETAIL_DISPLAY_OPTIONS=["QQ号","nickname","card","qqLevel","long_nick"]
~~~

默认启用全部字段，UID 除外。缺失和无效字段会跳过，未开启的标志不会显示为“否”。生肖按农历春节划分，时间统一为 UTC+8；协议端返回的歧义家乡编码保留原值。

<a id="faq"></a>

## 💬 常见问题

### 为什么部分资料没有显示？

私聊只查询陌生人资料，群聊还会查询群成员资料。检查 `qqdetail_display_options` 是否包含目标字段，以及协议端是否返回有效值。任一接口失败时仍会使用另一来源的可用资料，退群后的群成员信息可能无法获取。

### 图片发送异常时如何使用文本？

本次查询加上 `--text`，或设置 `QQDETAIL_OUTPUT_MODE=text`。头像下载失败会使用占位头像，字体或图片渲染失败会自动回退为文本。插件附带中文和单色 Emoji 字体，无需另行安装系统字体。

### 长资料会如何展示？

卡片每页最多 24 行，总计超过 160 行时会提示截断；单字段最多 4096 个字符。文本按 3000 字符分段发送，各页或各段分别撤回。

### 如何保留查询结果，或者沿用原来的文本输出？

~~~dotenv
QQDETAIL_OUTPUT_MODE=text
QQDETAIL_RECALL_TIME=0
~~~

`qqdetail_recall_time=0` 对图片和文本均可关闭撤回。

<a id="contributing"></a>

## 🤝 参与贡献

欢迎通过 [Bug 反馈](https://github.com/006lp/nonebot-plugin-qqdetail/issues/new?template=bug_report.yml) 和 [功能建议](https://github.com/006lp/nonebot-plugin-qqdetail/issues/new?template=feature_request.yml) 参与改进。反馈问题时请附上版本、命令、相关配置和复现步骤，并移除个人资料与密钥。

Fork 仓库并创建分支，使用 uv 准备开发环境：

~~~shell
uv sync --locked
uv pip install "nonebot2[fastapi]" nonebug pytest pytest-asyncio ruff
~~~

修改代码时补充相关测试和文档，再提交 PR。新增运行依赖使用 `uv add <package>`，同时提交 `pyproject.toml` 与 `uv.lock`。分支 push 和 PR 会自动运行 [CI](.github/workflows/ci.yml)，在 Ubuntu / Python 3.13 上执行格式检查、测试和包构建。

## ⚠️ 重要提醒

*   **学习交流用途**：本插件仅供学习和交流使用，请勿用于任何非法目的
*   **隐私保护**：查询用户信息时请尊重他人隐私，确保使用符合相关法律法规
*   **免责声明**：用户需对自身使用行为负责，开发者不对使用本插件产生的任何后果承担责任

## 📃 许可与致谢

本项目采用 [GNU AGPL v3](LICENSE)（`AGPL-3.0-only`）。
中文与 Emoji 字体来自 Noto 项目，各自遵循 SIL OFL 1.1，详见 [字体说明](nonebot_plugin_qqdetail/resources/README.md)。

## 🙏 致谢

[astrbot_plugin_box](https://github.com/Zhalslar/astrbot_plugin_box)，本插件参考了其设计思路。

