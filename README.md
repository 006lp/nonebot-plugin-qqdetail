# nonebot-plugin-qqdetail

这是一个基于 NoneBot2 的 QQ 资料查询插件，目标是通过 OneBot V11 接口查询用户公开资料与群成员资料，并以清晰、可测试、可维护的方式重新实现。

## ⚠️ 正在重构中...

当前已完成文本查询 MVP：支持 Alconna 命令解析、OneBot V11 资料查询、基础权限校验、字段转换和文本输出。

## 开发基线

- Python 3.10+
- NoneBot2 2.5.0+
- nonebot-plugin-alconna 0.62.0+
- nonebot-adapter-onebot 2.4.6+
- uv

## 使用方式

加载插件后发送：

```text
qqdetail
qqdetail 123456
qq资料 123456
qqdetail @某人
```

未指定目标时查询发送者；群聊中查询他人时会尝试补充群成员资料。

## 配置项

在 NoneBot 配置中可设置：

- `qqdetail_only_admin`：是否仅允许管理员查询他人，默认 `false`。
- `qqdetail_protect_ids`：保护用户 ID 集合，默认空。
- `qqdetail_display_options`：展示字段列表，默认展示全部支持字段。
- `qqdetail_command_aliases`：命令别名，默认 `{"qq资料", "查qq", "查q"}`。

## 开发与验证

本仓库强制使用 uv：

```powershell
uv run ruff format --no-cache .
uv run ruff check --no-cache .
uv run pytest -q
```

## 迭代计划

1. 已完成：插件元数据、配置模型、Alconna 文本查询 MVP、字段转换、权限校验、测试工具链。
2. 下一步：补充真实 OneBot 事件集成测试或模拟测试。
3. 后续：增加图片输出、头像下载、缓存和可选撤回。