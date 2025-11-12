# 插件凭证依赖声明

## 功能说明

插件框架支持插件声明依赖凭证。当插件声明需要凭证时，调用插件的平台需要在请求的顶层提供 `credentials` 字典，框架会在插件执行前检查请求中是否包含 `credentials` 字典，以及字典中是否包含所需的凭证字段，如果缺少则返回 400 错误。框架会将 `credentials` 作为 `Context` 对象的 `credentials` 属性传递给插件执行。

## 使用方式

### 在插件中声明依赖凭证

在插件类中定义 `Credentials` 类（继承自 `CredentialModel`，与 `ContextInputs` 并行）即可声明该插件需要凭证：

```python
from bk_plugin_framework.kit import (
    Plugin,
    InputsModel,
    OutputsModel,
    Field,
    ContextRequire,
    Context,
    Credential,
    CredentialModel,
)

class MyPlugin(Plugin):
    class Meta:
        version = "1.0.0"
        desc = "这是一个需要凭证的插件示例"

    class Inputs(InputsModel):
        action: str = Field(title="操作", description="要执行的操作")

    class Outputs(OutputsModel):
        result: str = Field(title="执行结果", description="操作执行的结果")

    class ContextInputs(ContextRequire):
        executor: str = Field(title="任务执行人")

    class Credentials(CredentialModel):
        bk_access_token = Credential(
            key="bk_access_token", name="蓝鲸 access token", description="用于调用蓝鲸 API 的 access token"
        )

    def execute(self, inputs: Inputs, context: Context):
        # 插件执行逻辑
        # 由于声明了 Credentials，框架会确保在执行到这里时 context.credentials 已经存在
        # 可以通过 credential key 访问具体的凭证值
        access_token = context.credentials.get("bk_access_token")
        # 使用 access_token 调用蓝鲸 API...
        context.outputs["result"] = f"操作 {inputs.action} 执行成功"
```

### 声明多个凭证

插件可以声明需要多个凭证：

```python
class MyPlugin(Plugin):
    class Meta:
        version = "1.0.0"
        desc = "这是一个需要多个凭证的插件示例"

    class ContextInputs(ContextRequire):
        executor: str = Field(title="任务执行人")

    class Credentials(CredentialModel):
        api_key = Credential(key="api_key", name="API 密钥", description="第三方服务的 API Key")
        api_secret = Credential(key="api_secret", name="API 密钥", description="第三方服务的 API Secret")

    def execute(self, inputs: Inputs, context: Context):
        api_key = context.credentials.get("api_key")
        api_secret = context.credentials.get("api_secret")
        # 使用 api_key 和 api_secret...
```

### 不声明凭证依赖（默认行为）

如果插件不需要凭证，可以不定义 `Credentials` 类：

```python
class MyPlugin(Plugin):
    class Meta:
        version = "1.0.0"
        desc = "这是一个不需要凭证的插件示例"

    # Credentials 类可以不定义，默认为不需要凭证

    # ... 其他代码
```

## 工作原理

1. **插件注册时**：框架会验证 `Credentials` 类是否继承自 `CredentialModel`
   - `Credentials` 是插件类的内部类，与 `ContextInputs` 并行
   - `Credentials` 类中的每个类属性必须是 `Credential` 类的实例
   - 每个 `Credential` 必须包含 `key` 字段（不能为空）
   - `name` 和 `description` 为可选字段
2. **插件调用时**：如果插件声明了 `Credentials` 类且包含凭证定义，框架会在执行插件前检查：
   - 验证调用方是否在请求顶层提供了 `credentials` 字典
   - 验证 `credentials` 字典中是否包含所有 `Credentials` 类中声明的 `key` 字段
   - 如果缺少 `credentials` 或缺少任何必需的 key，框架会返回 400 错误
   - 框架会将 `credentials` 作为 `Context` 对象的 `credentials` 属性传递给插件执行
3. **凭证访问**：插件可以通过 `context.credentials` 访问凭证字典，无需在 `ContextInputs` 中定义 `credentials` 字段

## CredentialModel 和 Credential 类说明

### CredentialModel

`CredentialModel` 是凭证模型的基类，用于声明插件需要的凭证。插件需要定义一个继承自 `CredentialModel` 的 `Credentials` 类。

### Credential

`Credential` 类用于定义单个凭证，包含以下字段：

- **key**（必填）：凭证在 `credentials` 字典中的 key
- **name**（可选）：凭证的显示名称，用于错误提示，如果不设置则使用 `key`
- **description**（可选）：凭证的描述信息

在 `Credentials` 类中，每个凭证作为类属性，值是 `Credential` 实例：

```python
class Credentials(CredentialModel):
    bk_access_token = Credential(
        key="bk_access_token",  # 必填：凭证的 key
        name="蓝鲸 access token",  # 可选：显示名称
        description="用于调用蓝鲸 API 的 access token"  # 可选：描述信息
    )
```

## 插件元数据

插件元数据接口会返回 `credentials` 列表，调用方可以根据该列表判断插件需要哪些凭证：

```json
{
  "version": "1.0.0",
  "desc": "这是一个需要凭证的插件示例",
  "credentials": [
    {
      "key": "bk_access_token",
      "name": "蓝鲸 access token",
      "description": "用于调用蓝鲸 API 的 access token"
    }
  ],
  "inputs": {...},
  "outputs": {...},
  ...
}
```

## 调用方式

对于声明了 `credentials` 的插件，调用方需要在调用时在顶层提供 `credentials` 字典，且字典中必须包含插件声明的所有 `key`：

```json
{
  "inputs": {
    "action": "some_action"
  },
  "context": {
    "executor": "admin"
  },
  "credentials": {
    "bk_access_token": "your_access_token_here"
  }
}
```

### 多个凭证的调用示例

```json
{
  "inputs": {
    "action": "some_action"
  },
  "context": {
    "executor": "admin"
  },
  "credentials": {
    "api_key": "your_api_key_here",
    "api_secret": "your_api_secret_here"
  }
}
```

## 凭证类型示例

### 示例 1：蓝鲸 Access Token

```python
class MyPlugin(Plugin):
    class Meta:
        version = "1.0.0"

    class ContextInputs(ContextRequire):
        executor: str = Field(title="任务执行人")

    class Credentials(CredentialModel):
        bk_access_token = Credential(key="bk_access_token", name="蓝鲸 access token")

    def execute(self, inputs: Inputs, context: Context):
        access_token = context.credentials.get("bk_access_token")
        # 使用 access_token...
```

调用时：
```json
{
  "context": {
    "executor": "admin"
  },
  "credentials": {
    "bk_access_token": "token_value"
  }
}
```

### 示例 2：API Key 和 Secret

```python
class MyPlugin(Plugin):
    class Meta:
        version = "1.0.0"

    class ContextInputs(ContextRequire):
        executor: str = Field(title="任务执行人")

    class Credentials(CredentialModel):
        api_key = Credential(key="api_key", name="API 密钥")
        api_secret = Credential(key="api_secret", name="API 密钥")

    def execute(self, inputs: Inputs, context: Context):
        api_key = context.credentials.get("api_key")
        api_secret = context.credentials.get("api_secret")
        # 使用 api_key 和 api_secret...
```

调用时：
```json
{
  "context": {
    "executor": "admin"
  },
  "credentials": {
    "api_key": "key_value",
    "api_secret": "secret_value"
  }
}
```

## 注意事项

1. `Credentials` 是插件类的内部类，与 `ContextInputs`、`Inputs`、`Outputs` 等并行
2. `Credentials` 类可以不定义，即不声明时插件不需要凭证
3. `Credentials` 类必须继承自 `CredentialModel`
4. 在 `Credentials` 类中，每个凭证作为类属性，值必须是 `Credential` 类的实例
5. 对于声明了 `Credentials` 的插件：
   - 每个 `Credential` 的 `key` 字段是必填的
   - `name` 和 `description` 是可选的
   - **不需要**在 `ContextInputs` 中定义 `credentials` 字段，凭证通过 `context.credentials` 访问
6. 调用方需要确保在调用插件时，在顶层 `credentials` 字典中提供所有 `Credentials` 类中声明的 `key`
7. `credentials` 是一个字典结构，可以包含多个凭证字段，但至少必须包含插件声明的所有 `key`
8. 如果缺少 `credentials` 或缺少任何必需的 `key`，框架会在插件执行前返回 400 错误，错误信息会列出所有缺少的凭证
9. 插件通过 `context.credentials` 访问凭证字典，例如：`context.credentials.get("bk_access_token")`
