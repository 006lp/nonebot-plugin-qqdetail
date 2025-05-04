
<div align="center">
    <a href="https://v2.nonebot.dev/store">
    <img src="https://raw.githubusercontent.com/fllesser/nonebot-plugin-template/refs/heads/resource/.docs/NoneBotPlugin.svg" width="300" alt="logo"></a>
</div>

<div align="center">

## ✨ *基于 Nonebot2 的 QQ 详细信息查询插件* ✨

<a href="./LICENSE">
    <img src="https://img.shields.io/github/license/006lp/nonebot-plugin-qqdetail.svg" alt="license">
</a>
<a href="https://pypi.python.org/pypi/nonebot-plugin-qqdetail">
    <img src="https://img.shields.io/pypi/v/nonebot-plugin-qqdetail.svg" alt="pypi">
</a>
<img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="python">
<img src="https://img.shields.io/badge/adapter-OneBot_V11-blueviolet" alt="adapter">
<a href="https://github.com/astral-sh/ruff">
    <img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json" alt="ruff">
</a>
<a href="https://github.com/astral-sh/uv">
    <img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json" alt="uv">
</a>
</div>

</div>

## 📖 介绍

一个简单的 NoneBot2 插件，允许机器人通过 QQ 号或 @用户 查询 QQ 用户的公开详细信息（如昵称、头像、QID、等级、IP归属地等）。数据来源于第三方 API。

仅支持 OneBot V11 协议。

## 💿 安装

<details open>
<summary>使用 nb-cli 安装</summary>
在 NoneBot2 项目的根目录下打开命令行，输入以下指令即可安装

```bash
nb plugin install nonebot-plugin-qqdetail --upgrade
```
如果需要使用 PyPI 镜像源（例如清华源）：

```bash
nb plugin install nonebot-plugin-qqdetail --upgrade -i https://pypi.tuna.tsinghua.edu.cn/simple
```
</details>

<details>
<summary>使用包管理器安装</summary>
在 NoneBot2 项目的插件目录下（或项目根目录，取决于你的项目结构和包管理器），打开命令行，根据你使用的包管理器，输入相应的安装命令：

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

插件支持通过 `.env` 文件进行配置。

| 配置项               | 必填  | 默认值 | 说明                                                                      |
| :------------------- | :---: | :----: | :------------------------------------------------------------------------ |
| `QQDETAIL_WHITELIST` |  否   |  `[]`  | QQ 号码列表。白名单内的用户，只有超级用户才能查询其信息（自己查自己除外） |

**`.env` 文件配置示例：**

```env
# QQDetail 插件配置
# 白名单内的 QQ 号，只有 Superuser 可以查询 (除了用户自己查自己)
# 值需要是有效的 JSON 列表字符串，例如: '["10001", "10002"]'
QQDETAIL_WHITELIST='["12345678", "87654321"]'
```

**注意:** `.env` 文件中的列表通常需要以 JSON 字符串的形式提供。

## 🎉 使用

### 指令表

| 指令                            |  别名  | 权限  | 需要@ |   范围    | 说明                                                                            |
| :------------------------------ | :----: | :---: | :---: | :-------: | :------------------------------------------------------------------------------ |
| `/detail <QQ号 或 @用户 或 无>` | `info` | 群员  | 可选  | 群聊/私聊 | 查询目标QQ用户的详细信息。参数可以是5-11位QQ号，@提及用户，或不带参数查询自己。 |

### 说明

*   **`<QQ号>`**: 必须是 5 到 11 位的纯数字。
*   **`@用户`**: 在群聊中可以直接 @ 群成员。
*   **无参数**: 如果直接发送 `/detail` 或 `/info`，则查询发送者本人的信息。
*   **数据来源**: 本插件使用 `https://api.yyy001.com/` 提供的公开接口查询信息，结果的准确性和可用性取决于该 API。
*   **白名单**: 如果配置了 `QQDETAIL_WHITELIST`，则列表中的 QQ 号只有超级用户 (`SUPERUSERS`) 可以查询，除非用户是自己查询自己。

### 🎨 返回示例

*查询成功示例:*
```
[图片：用户头像]
查询对象：123456789
昵称：示例昵称
QID：example_qid
性别：男
年龄：20
等级：Lv.50
VIP等级：VIP7
注册时间：2010-01-01
签名：这是一个示例签名。
IP城市：广东 深圳
```

*格式错误示例:*
```
命令格式错误、QQ号无效或包含多余参数。
请使用：
/detail <QQ号(5-11位)> 或 /detail @用户
/info <QQ号(5-11位)> 或 /info @用户
/detail (查询自己)
```

*查询失败示例:*
```
获取QQ信息失败 (UID: 123456789)。
原因：API请求失败: 404
```

## ⚠️ 使用警告

*   **仅供学习交流使用！** 请勿用于非法用途。
*   **尊重隐私！** 查询他人信息可能涉及隐私，请确保你的使用符合相关法律法规和平台规定。
*   **数据准确性！** 插件依赖第三方 API，无法保证信息的绝对准确性和实时性。
*   用户应对自己的使用行为负责，开发者不承担任何因使用此插件造成的直接或间接责任。

## 📃 许可证

本项目采用 [AGPL-3.0](./LICENSE) 许可证。

## 🙏 致谢

*   **API 提供方**: [https://api.yyy001.com/](https://api.yyy001.com/)
