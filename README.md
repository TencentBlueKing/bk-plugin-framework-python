<!-- TOC -->

- [🧐bk-plugin-framework](#1-🧐bk-plugin-framework)
- [🚀快速开始](#2-🚀快速开始)
    - [创建你的第一个插件项目](#21-创建你的第一个插件项目)
- [📦DEMO](#3-📦DEMO)
- [📊benchmark](#4-📊benchmark)
- [🧾基础概念](#5-🧾基础概念)
    - [插件构成](#51-插件构成)
    - [插件项目结构](#52-插件项目结构)
        - [开发者需要关注的](#521-开发者需要关注的)
        - [开发者不需要（不应该）关注的](#522-开发者不需要（不应该）关注的)
    - [一次插件调用的状态转换](#53-一次插件调用的状态转换)
- [📚如何开发插件](#6-📚如何开发插件)
    - [定义插件](#61-定义插件)
    - [插件元数据](#62-插件元数据)
        - [我应该在什么时候开发一个新的插件版本？](#621-我应该在什么时候开发一个新的插件版本？)
    - [定义输入模型(可选)](#63-定义输入模型(可选))
        - [输入模型字段定义说明(可选)](#631-输入模型字段定义说明(可选))
        - [嵌套输入模型定义](#632-嵌套输入模型定义)
    - [定义输出模型(可选)](#64-定义输出模型(可选))
    - [定义上下文输入模型(可选)](#65-定义上下文输入模型(可选))
    - [插件初始化方法(可选)](#66-插件初始化方法(可选))
    - [定义插件执行逻辑](#67-定义插件执行逻辑)
        - [执行错误](#671-执行错误)
        - [等待调度](#672-等待调度)
        - [等待回调](#673-等待回调)
        - [执行成功](#674-执行成功)
        - [inputs: Inputs 输入参数说明](#675-inputs:Inputs输入参数说明)
        - [context: Context 输入参数说明](#676-context:Context输入参数说明)
            - [trace_id: str](#6761-trace_id:str)
            - [data: ContextRequire](#6762-data:ContextRequire)
            - [state: State](#6763-state:State)
            - [invoke_count: int](#6764-invoke_count:int)
            - [storage: dict](#6765-storage:dict)
            - [outputs: dict](#6766-outputs:dict)
    - [定义插件前端表单(可选)](#68-定义插件前端表单(可选))
        - [表单存放位置](#681-表单存放位置)
        - [表单构成](#682-表单构成)
        - [表单开发指南](#683-表单开发指南)
        - [可使用的 Tag 及说明](#684-可使用的Tag及说明)
    - [定义表单数据接口(可选)](#69-定义表单数据接口(可选))
    - [插件配置](#610-插件配置)
- [🔬如何在本地调试插件](#7-🔬如何在本地调试插件)
    - [环境准备](#71-环境准备)
    - [准备 DB](#72-准备DB)
    - [启动调试进程](#73-启动调试进程)
- [各系统插件开发说明](#8-各系统插件开发说明)
    - [标准运维](#81-标准运维)

<!-- /TOC -->






<a id="toc_anchor" name="#1-🧐bk-plugin-framework"></a>

# 1. 🧐bk-plugin-framework

bk-plugin-framework 是一个轻量化系统插件开发框架，开发者只需要使用该框架进行插件开发，并将其部署到蓝鲸 PaaS 平台上，即可完成系统插件的开发和接入。

接入系统通过调用 bk-plugin-framework 暴露出来的标准接口，完成系统插件功能的实现

> [系统如何接入插件服务](./docs/how_to_integrate.md)

![](./docs/assets/img/flow.png)

<a id="toc_anchor" name="#2-🚀快速开始"></a>

# 2. 🚀快速开始

<a id="toc_anchor" name="#21-创建你的第一个插件项目"></a>

## 2.1. 创建你的第一个插件项目

```shell
pip install cookiecutter
cookiecutter https://github.com/TencentBlueKing/bk-plugin-framework-python/ --directory template
```

- [📚如何开发插件](#61-定义插件)
- [🔬如何在本地调试插件](#71-环境准备)


<a id="toc_anchor" name="#3-📦DEMO"></a>

# 3. 📦DEMO

[传送门](./bk_plugin/versions/v1_0_0.py)

<a id="toc_anchor" name="#4-📊benchmark"></a>

# 4. 📊benchmark

[测试数据](./docs/benchmark.md)

<a id="toc_anchor" name="#5-🧾基础概念"></a>

# 5. 🧾基础概念

<a id="toc_anchor" name="#51-插件构成"></a>

## 5.1. 插件构成

一个插件由以下元素构成

- Meta：插件元数据
- Inputs：插件调用输入模型
- ContextInputs：插件调用上下文输入模型
- Outputs：插件输出模型
- execute method：插件调用逻辑

![](./docs/assets/img/plugin.png)

<a id="toc_anchor" name="#52-插件项目结构"></a>

## 5.2. 插件项目结构

```
├── Procfile
├── app_desc.yml
├── bin
│   ├── manage.py
│   └── post_compile
├── bk_plugin
│   ├── __init__.py
│   ├── forms
│   │   └── 1.0.0
│   │       └── form.js
│   ├── meta.py
│   └── versions
│       ├── __init__.py
│       └── v1_0_0.py
└── requirements.txt
```

<a id="toc_anchor" name="#521-开发者需要关注的"></a>

### 5.2.1. 开发者需要关注的

- bk_plugin/forms：存放每个插件版本对应的接入系统表单配置
- bk_plugin/meta.py：定义插件级别的元信息
- bk_plugin/versions：存放每个版本的插件定义，所有插件定义必须位于该目录下，目录下文件名不做限制，框架会自动从该目录下发现插件
- requirements.txt：插件需要依赖的第三方库

<a id="toc_anchor" name="#522-开发者不需要（不应该）关注的"></a>

### 5.2.2. 开发者不需要（不应该）关注的

- Procfile：插件运行时进程定义文件
- app_desc.yml：插件描述文件
- bin/maange.py：运行时命令入口
- bin/post_compile：插件部署后置操作

<a id="toc_anchor" name="#53-一次插件调用的状态转换"></a>

## 5.3. 一次插件调用的状态转换

一个插件在一次执行声明周期中可能会经过下图所示的状态转换，每种状态说明如下：

- EMPTY：初始状态，每次插件调用都会从这个状态开始
- SUCCESS：执行成功状态，插件在 `execute` 方法中如果没有抛出任何异常，没有 `self.wait_poll` 和 `self.wait_callback` 的调用，就会进入成功状态，**SUCCESS 是一次调用的结束状态**
- FAIL：执行失败状态，一旦插件在 `execute` 方法中抛出任何已知或不可预知的异常，都会进入失败状态，**FAIL 也是一次调用的结束状态**
- POLL：轮询状态，插件一旦在 `execute` 中调用了 `self.wait_poll` 方法，并且后续没有抛出异常，就会进入轮询状态，处于 POLL 状态的调用会在一定时间后被运行时拉起，并再次执行 `execute` 方法。
- CALLBACK：回调状态，插件一旦在 `execute` 中调用了 `self.wait_callback` 方法，并且后续没有抛出异常，就会进入回调状态，处于 CALLBACK 状态的插件会等待来自外部的回调，收到回调后，该次调用会被运行时拉起，并再次执行 `execute` 方法。

通过框架提供的方法，你可以在插件逻辑中进行任意合法的状态流转，以适配不同的业务场景

![](./docs/assets/img/plugin_status.png)

<a id="toc_anchor" name="#6-📚如何开发插件"></a>

# 6. 📚如何开发插件

<a id="toc_anchor" name="#61-定义插件"></a>

## 6.1. 定义插件

所有的插件都需要继承 `bk_plugin_framework.kit.Plugin`，如下所示

```python
from bk_plugin_framework.kit import Plugin

class SopsExecPlugin(Plugin):
    pass
```

<a id="toc_anchor" name="#62-插件元数据"></a>

## 6.2. 插件元数据

在每个插件类中我们需要定义 `Meta` 内部类，其中包含该版本插件的元数据：

- version：插件版本号，必须符合 [语义化版本](https://semver.org/lang/zh-CN/)，**同一个插件项目内每个插件类的版本号不能冲突**。
- desc(可选)：该版本插件的描述信息

```python
from bk_plugin_framework.kit import Plugin

class SopsExecPlugin(Plugin):

    class Meta:
        version = "1.0.0"
```

<a id="toc_anchor" name="#621-我应该在什么时候开发一个新的插件版本？"></a>

### 6.2.1. 我应该在什么时候开发一个新的插件版本？

如果你的插件发生了以下任一项或多项破坏性的改动，为了不影响插件现有版本的使用，请开发一个新版本插件：

- 插件的输入模型中`增加`了必填的输入参数
- 插件的输入模型中`删除`了必填的输入参数
- 插件的上下文输入模型中`增加`了必填的输入参数
- 插件的上下文输入模型中`删除`了必填的输入参数
- 插件的输出模型中`删除`了某个输出参数
- 插件的输出模型中某个输出参数的`类型`发生了变化
- 插件的表单`增加`了必填的参数
- 插件的表单`删除`了必填的参数
- 插件的表单`数据结构`发生了变化
- 插件的功能发生了翻天覆地的变化

<a id="toc_anchor" name="#63-定义输入模型(可选)"></a>

## 6.3. 定义输入模型(可选)

每个插件都需要包含一个继承自 `bk_plugin_framework.kit.InputsModel` 的内部类 `Inputs` 来声明该插件的输入模型，输入模型的作用如下：

- 声明插件所需的输入字段，字段类型类型以及字段说明
- 对插件调用插件的输入进行校验，该职责由插件运行时框架完成

```python
from bk_plugin_framework.kit import Plugin, InputsModel, Field

class SopsExecPlugin(Plugin):
    ...

    class Inputs(InputsModel):
        template_id: int
        task_name: str
        constants: dict = Field(default={}, description="任务全局变量")

    ...
```

<a id="toc_anchor" name="#631-输入模型字段定义说明(可选)"></a>

### 6.3.1. 输入模型字段定义说明(可选)

```python
class Inputs(InputsModel):
    int_field: int  # int 类型必填
    str_field: str  # str 类型必填
    no_required_field: dict = {"a": 1}  # dict 类型非必填，默认值为 {"a": 1}
    detail_field: bool = Field(default=True, description="字段详细说明")  # bool 类型非必填，默认值为 True
```

<a id="toc_anchor" name="#632-嵌套输入模型定义"></a>

### 6.3.2. 嵌套输入模型定义

```python
class Inputs(InputsModel):
    class Options(InputsModel):
        name: str
        value: str

    action: str
    options: Options


def execute(self, inputs: InputsModel, context: ContextRequire):
    option_name = inputs.options.name
    option_value = inputs.options.value
```

<a id="toc_anchor" name="#64-定义输出模型(可选)"></a>

## 6.4. 定义输出模型(可选)

每个插件都需要包含一个继承自 `bk_plugin_framework.kit.OutputsModel` 的内部类 `Outputs` 来声明该插件的输入模型，输入模型的作用如下：

- 声明插件的输出字段，字段类型以及字段说明

**输出模型的定义方式与输入模型定义方式相同，只是基类不同**

```python

from bk_plugin_framework.kit import Plugin, OutputsModel, Field

class SopsExecPlugin(Plugin):

    ...

    class Outputs(OutputsModel):
        task_id: int = Field(title="标准运维任务 ID", description="")
        task_url: str = Field(title="标准运维任务 URL", description="")

    ...
```

<a id="toc_anchor" name="#65-定义上下文输入模型(可选)"></a>

## 6.5. 定义上下文输入模型(可选)

每个插件都需要包含一个继承自 `bk_plugin_framework.kit.ContextRequire` 的内部类 `ContextInputs` 来声明该插件的上下文输入模型，该模型的作用如下：

- 声明插件的上下文输入字段，字段类型以及字段说明

上下文输入模型与输入模型的差别在于：输入模型中包含的是**插件用户**需要感知到的字段。而上下文输入模型中包含的是**插件用户**不需要感知，**插件使用系统**需要感知的字段

**上下文输入模型的定义方式与输入模型定义方式相同，只是基类不同**

```python

from bk_plugin_framework.kit import Plugin, ContextRequire, Field

class SopsExecPlugin(Plugin):

    ...

    class ContextInputs(ContextRequire):
        biz_cc_id: int = Field(title="业务 cc id", description="业务在 cmdb 中的 id")
        executor: str = Field(title="任务执行人")
    ...
```

<a id="toc_anchor" name="#66-插件初始化方法(可选)"></a>

## 6.6. 插件初始化方法(可选)

如果你希望在插件实例化的时候做一些初始化工作，那么可以重载插件的 `__init__` 方法。

**但是千万别忘了在里面调用父类的 `__init__()` 方法噢！**

```python

import os

from bk_plugin_framework.kit import Plugin

class SopsExecPlugin(Plugin):

    ...

    def __init__(self):
        super().__init__()
        # 从环境变量中获取调用标准运维 API 所需的 APP_CODE 与 APP_SECRET
        self.app_code = os.getenv("BKSOPS_API_APP_CODE")
        self.app_secret = os.getenv("BKSOPS_API_APP_SECRET")
    ...
```

<a id="toc_anchor" name="#67-定义插件执行逻辑"></a>

## 6.7. 定义插件执行逻辑

插件的 `execute` 方法定义了插件的执行逻辑，该方法必须接受两个输入参数：`inputs: Inputs` 与 `context: Context`。

<a id="toc_anchor" name="#671-执行错误"></a>

### 6.7.1. 执行错误

在插件执行过程中，如果遇到了需要让本次调用进入失败状态的情况（例如，外部接口调用失败），可以通过抛出 `self.Error` 来让插件进入失败状态

```python
def execute(self, inputs: Inputs, context: Context):
    success = False
    if not success:
        raise self.Error("error message")
```

<a id="toc_anchor" name="#672-等待调度"></a>

### 6.7.2. 等待调度

在某些场景下，依次调用执行的任务可能会耗费很长时间，这时候如果一直在 `execute` 中使用 `while` 来等待是不太合适的，此时我们可以调用 `self.wait_poll(interval)` 方法来让本次调用进入等待调度状态，当 wait_poll 调用成功且 execute 正常返回后，execute 方法会在 `interval` 秒后被再次拉起执行。

可以通过 `context.state` 来判断当前是否处于 POLL 状态，来确定本次调用目前所处的阶段。

如果需要在每次调度间传递一些数据，那么可以通过将数据写入 `context.storage` 来达到存储临时数据的目的。

```python
def execute(self, inputs: Inputs, context: Context):
    if context.state is State.EMPTY:
        context.storage["task_id"] = create_task()
        # 在这里调用self.wait_poll()进入调度状态
        # 此时context.state由引擎负责调整变为State.POLL
        self.wait_poll(5)
    if context.state is State.POLL:
        state = get_task_state(context.storage["task_id"])
        if state == "SUCCESS":
            return  # 任务执行成功，本次调用成功
        elif state == "FAIL":
            raise self.Error("task fail")  # 任务执行失败，本次调用失败
        elif state == "RUNNING":
            self.wait_poll(5)  # 五秒后再次执行
```



### 6.7.3. 等待回调

调用第三方系统执行任务可能耗时很长，这个时候我们要在任务执行完成之后进行一些操作，一方面我们可以使用上面的`self.wait_poll(interval)`轮询任务是否执行完成；另一方面，如果第三方系统支持回调，我们可以使用`self.wait_callback()`等待第三方系统执行完成任务之后，回调插件服务，在接受到第三方系统等回调请求后，`execute `方法会被再次拉起执行。

可以通过 `context.state` 来判断当前是否处于 CALLBACK 状态，来确定本次调用目前所处的阶段。

如果需要识别多次回调的唯一性，可以通过`context.callback.id`获取此次回调的id

如果第三方系统回调有数据返回，可以通过`context.callback.data`获取返回的回调数据

```python
def execute(self, inputs: Inputs, context: Context):
    if context.state is State.EMPTY:
        # 生成回调的所需的url和标识回调唯一性的id
        pre_callback = self.prepare_callback(context)
        # 暂存回调id，用于回调到来之时，处理job回调的相关逻辑
        context.storage["job_callback_id"] = pre_callback.id
        job_kwargs = {
            "bk_biz_id": 1,
            "ip_list": [],
            # 传入回调url
            "bk_callback": pre_callback.url,
        }
        client.job.fast_execute_script(job_kwargs)
        # 此时context.state由引擎负责调整变为State.CALLBACK
        self.wait_callback()
    if context.state is State.CALLBACK:
        # 如果回调id是执行job任务的回调id，则处理一些相应逻辑
        if context.callback.id == context.storage["job_callback_id"]:
            do_something(context.callback.data)
            return  # 任务执行成功，本次调用成功

        # 如果有其他回调，也可以处理其相应逻辑
        else:
            do_else_something(context.callback.data)
        	# 处理完成之后，可以选择继续回调，还是return 插件执行完成
            self.wait_callback()
```

<a id="toc_anchor" name="#674-执行成功"></a>

### 6.7.4. 执行成功

若 execute 中如果没有抛出任何异常，没有 `self.wait_poll` 和 `self.wait_callback` 的调用，就会进入成功状态

<a id="toc_anchor" name="#675-inputs:Inputs输入参数说明"></a>

### 6.7.5. inputs: Inputs 输入参数说明

插件调用输入，插件输入模型 `Plugin.Inputs` 对象，你可以通过 `inputs.template_id` 方式访问其内部字段，且无需对该成员的类型和存在性进行判断，插件运行时框架会保证传入的 `inputs` 对象中字段的合法性

```python
class SopsExecPlugin(Plugin):
    ...

    class Inputs(InputsModel):
        template_id: int
        task_name: str
        constants: dict = Field(default={}, description="任务全局变量")

    def execute(self, inputs: Inputs, context: Context):
        template_id = inputs.template_id
        task_name = inputs.task_name
        constants = inputs.constants
    ...
```

<a id="toc_anchor" name="#676-context:Context输入参数说明"></a>

### 6.7.6. context: Context 输入参数说明

插件调用上下文，用于记录一次调用中的上下文信息，该对象包含以下字段：

<a id="toc_anchor" name="#6761-trace_id:str"></a>

#### 6.7.6.1. trace_id: str

trace_id，在一次调用发生前生成，在同一次调用中不会发生变化

```python
def execute(self, inputs: Inputs, context: Context):
    logger.info("[%s] execute" % context.trace_id)
```

<a id="toc_anchor" name="#6762-data:ContextRequire"></a>

#### 6.7.6.2. data: ContextRequire

插件定义上下文输入模型 `Plugin.ContextInputs` 对象，你可以通过 `data.template_id` 方式访问其内部字段，且无需对该成员的类型和存在性进行判断，插件运行时框架会保证传入的 `data` 对象中字段的合法性，若插件没有定义 `ContextInputs`，该字段值为 `None`

```python
class ContextInputs(ContextRequire):
    biz_cc_id: int = Field(title="业务 cc id", description="业务在 cmdb 中的 id")
    executor: str = Field(title="任务执行人")

def execute(self, inputs: Inputs, context: Context):
    bk_biz_id = context.data.biz_cc_id
    executor = context.data.executor
```

<a id="toc_anchor" name="#6763-state:State"></a>

#### 6.7.6.3. state: State

本次调用所处状态，值为 [1.2.3. 一次插件调用的状态转换](#123-一次插件调用的状态转换) 中所描述的 `EMPTY`, `SCHEDULE`, `CALLBACK` 状态的一种

```python
def execute(self, inputs: Inputs, context: Context):
    if context.state is State.EMPTY:
        # create task
        pass
    elif context.state is State.POLL:
        # poll task
        pass
```

<a id="toc_anchor" name="#6764-invoke_count:int"></a>

#### 6.7.6.4. invoke_count: int

本次调用中 `execute` 方法执行的次数

```python
def execute(self, inputs: Inputs, context: Context):
    logger.info("%s times execute" % context.invoke_count)
```

<a id="toc_anchor" name="#6765-storage:dict"></a>

#### 6.7.6.5. storage: dict

插件调用临时数据存储，你可以在这里存储一些在执行过程中生成的临时数据，便于调用进入 `POLL` 或 `CALLBACK` 状态后被再次拉起执行时进行读取。**该字段中存储的数据必须能够正常进行 JSON 序列化/反序列化。**

```python
def execute(self, inputs: Inputs, context: Context):
    if context.state is State.EMPTY:
        context.storage["task_id"] = 123
    elif context.state is State.POLL:
        task_id = context.storage["task_id"]
```

<a id="toc_anchor" name="#6766-outputs:dict"></a>

#### 6.7.6.6. outputs: dict

插件输出数据，插件执行的输出数据可以记录到该字段中。**该字段中存储的数据必须能够正常进行 JSON 序列化/反序列化。**

```python

class Outputs(OutputsModel):
    task_id: int = Field(title="标准运维任务 ID", description="")
    task_url: str = Field(title="标准运维任务 URL", description="")

def execute(self, inputs: Inputs, context: Context):
    context.outputs["task_id"] = 123
    context.outputs["task_url"] = "xxx"
```

<a id="toc_anchor" name="#68-定义插件前端表单(可选)"></a>

## 6.8. 定义插件前端表单(可选)

每个版本的插件都需要开发一个与之对应的前端表单，便于接入系统展示对用户友好的输入信息填写页面，表单生成的数据会作为 inputs 传递到插件的 `execute` 方法中。

**虽然前端表单开发是个可选项，但我们强烈建议您为有输入的插件开发前端表单，否则用户就没有办法在页面上使用您的插件了😢**

![](./docs/assets/img/form_to_plugin.png)

<a id="toc_anchor" name="#681-表单存放位置"></a>

### 6.8.1. 表单存放位置

框架会从 `bk_plugin/forms/{version}/form.js` 文件中获取版本号为 `{version}` 的插件表单定义。

> 例如，1.0.0 的表单定义应该存放在 `bk_plugin/forms/1.0.0/form.js` 文件中

```
bk_plugin
├── __init__.py
├── forms
│   └── 1.0.0
│       └── form.js
└── versions
    ├── __init__.py
    └── v1_0_0.py
```

<a id="toc_anchor" name="#682-表单构成"></a>

### 6.8.2. 表单构成

插件表单由多个 tag 构成，每个 tag 代表一个独立的表单项（输入框，文本框，下拉框，时间选择器...），同时可以通过 combine 来将多个 tag 组合成一个复合 tag。

下图展示了表单中 tag 与插件 Inputs 中定义的输入字段的映射：

![](./docs/assets/img/form_map_inputs.png)

<a id="toc_anchor" name="#683-表单开发指南"></a>

### 6.8.3. 表单开发指南

`form.js` 表单文件需要包含一个全局的 tag 数组定义，示例如下：

```js
(function () {
    $.atoms["{{your plugin app code}}"] = [
        ...
    ]
})();
```

然后在数组中定义表单 tag 即可

```js
(function () {
    $.atoms["{{your plugin app code}}"] = [
        {
            "type": "input",
            "attrs": {
                "name": "模板ID",
                "hookable": true,
            },
            "tag_code": "template_id"
        }
    ]
})();
```

<a id="toc_anchor" name="#684-可使用的Tag及说明"></a>

### 6.8.4. 可使用的 Tag 及说明

[Tag 使用说明](./docs/tags.md)

<a id="toc_anchor" name="#69-定义表单数据接口(可选)"></a>

## 6.9. 定义表单数据接口(可选)

> 若要使用该功能，请确保 bk-plugin-framework 的版本 >= 0.7.0

在某些场景下，我们可能需要获取我们需要在插件表单项（如下拉框，表格等）中展示的数据源，这时，就需要在插件中定义对应的数据接口为插件表单提供数据源

以下拉框为例，我们的插件中可能需要展示一个让用户从任务列表中选择某个任务的下拉框，其表单定义如下所示：

```js
(function () {
    $.atoms["bk-plugin-demo"] = [
        {
            "type": "select",
            "attrs": {
                "name": "任务列表拉取",
                "remote_url": $.context.bk_plugin_api_host["bk-plugin-demo"] + "bk_plugin/plugin_api/task_list/123",
            },
            "events": [],
            "methods": {},
            "tag_code": "task_list"
        }
    ]
})();
```

可以看到，表单中请求了 `bk_plugin/plugin_api/task_list/123` 这个 API，所以我们也需要在插件中提供对应的数据接口。

首先，我们需要在 `bk_plugin` 目录下新建 `apis` 模块，如下所示

```
bk_plugin
├── __init__.py
├── apis
├── forms
├── meta.py
└── versions
```

然后，在 `apis` 目录下新建 `task_list.py` 文件，用于定义数据接口，其实现如下（**数据源接口必须继承自 `PluginAPIView`**）：

```py
# task_list.py
from rest_framework.response import Response
from bk_plugin_framework.kit.api import PluginAPIView


class TaskList(PluginAPIView):
    def get(self, request, biz_id):
        return Response(
            [{"text": "task 1", "value": 1}, {"text": "task 2", "value": 2}]
        )
```

最后，在 `apis` 目录下新建 `urls.py` 文件，并定义接口路由：

```py
# urls.py
from django.urls import path
from . import task_list

urlpatterns = [
    path(r"task_list/<int:biz_id>", task_list.TaskList.as_view()),
]
```

到这里，一个数据接口的定义就完成了，此时 apis 的目录结构如下所示

```
bk_plugin
├── __init__.py
├── apis
│   ├── __init__.py
│   ├── task_list.py
│   └── urls.py
├── forms
├── meta.py
└── versions
```

<a id="toc_anchor" name="#7-🔬如何在本地调试插件"></a>

## 6.10. 插件配置

如果需要修改一些插件的配置，可以通过以下环境变量进行相应的配置

- SCHEDULE_PERSISITEN_DAYS：插件调度的过期时间，单位为天；周期任务每天执行一次清理(成功/失败)的过期插件调度记录

# 7. 🔬如何在本地调试插件

<a id="toc_anchor" name="#71-环境准备"></a>

## 7.1. 环境准备

请确保本地开发环境安装了以下组件：

- mysql（如果本地使用sqlite作为数据库则不需要该组件）
- rabbitmq or reids（如果插件没有 wait_poll 或 wait_callback 操作则不需要该组件）

安装依赖前，请确保 pip 源中配置了内部源：

```
[global]
index-url = https://mirrors.tencent.com/tencent_pypi/simple/
trusted-host = mirrors.tencent.com
```

准备一个舒适的 Python 环境，安装插件所需的依赖

```bash
# 请务必确保 pip 版本大于 21.0.0
pip --version
# 如果 pip 版本过旧，请升级 pip 版本
pip install --upgrade pip
pip install -r requirements.txt
```

后续的所有命令操作，请确保当前会话中存在以下环境变量：

```bash
export BKPAAS_APP_ID="" # 插件 app code，从 paas 开发者中心获取
export BKPAAS_APP_SECRET="" # 插件 app secret paas 开发者中心获取

export BK_INIT_SUPERUSER="admin" # 数据库初始化管理员
export BK_PLUGIN_RUNTIME_BROKER_URL="amqp://guest:guest@localhost:5672//" # broker url，如果插件没有 wait_poll 或 wait_callback 操作可以不设置该变量
export DJANGO_SETTINGS_MODULE="bk_plugin_runtime.settings"
export BK_APP_CONFIG_PATH="bk_plugin_runtime.config"
```

如果想在本地使用 MySQL，请确保存在以下环境变量并进行相应的配置

```bash
export BK_PLUGIN_DEV_USE_MYSQL="1" # 本地使用mysql数据库
export BK_PLUGIN_RUNTIME_DB_USER="" # 本地 DB 用户名
export BK_PLUGIN_RUNTIME_DB_PWD="root960201" # 本地 DB 密码
export BK_PLUGIN_RUNTIME_DB_HOST="localhost" # 本地 DB 域名
export BK_PLUGIN_RUNTIME_DB_PORT="3306" # 本地 DB 端口
```

<a id="toc_anchor" name="#72-准备DB"></a>

## 7.2. 准备 DB

进入项目根目录，初始化数据库

```bash
python bin/manage.py migrate
```

<a id="toc_anchor" name="#73-启动调试进程"></a>

## 7.3. 启动调试进程

启动调试服务器

```bash
python bin/manage.py runserver
```

> 如果插件会进入 POLL 或 CALLBACK 状态，需要额外运行 worker 进程

> ```bash
> celery worker -A blueapps.core.celery -P threads -n schedule_worker@%h -c 500 -Q plugin_schedule -l DEBUG
> ```

访问 `localhost:8000` 进入调试页面

![](./docs/assets/img/debug_panel.png)


<a id="toc_anchor" name="#8-各系统插件开发说明"></a>

# 8. 各系统插件开发说明


<a id="toc_anchor" name="#81-标准运维"></a>

## 8.1. 标准运维

在开发标准运维系统插件时，可以在上下文输入中定义这些字段，标准运维会根据当前流程任务执行的上下文传入插件中：

- project_id(int)：当前任务所属标准运维项目ID
- project_name(str)：当前任务所属标准运维项目名
- bk_biz_id(int)：当前任务所属 CMDB 业务 ID
- bk_biz_name(str)：当前任务所属 CMDB 业务名
- operator(str)：当前任务操作者（点击开始按钮的人）
- executor(str)：当前任务执行人（调用第三方系统 API 使用的身份）
- task_id(int)：当前任务 ID
- task_name(str)：当前任务名

## Support

- [蓝鲸论坛](https://bk.tencent.com/s-mart/community)
- [蓝鲸 DevOps 在线视频教程](https://cloud.tencent.com/developer/edu/major-100008)
- 联系我们，技术交流QQ群：

<img src="https://github.com/Tencent/bk-PaaS/raw/master/docs/resource/img/bk_qq_group.png" width="250" hegiht="250" align=center />


## BlueKing Community

- [BK-CI](https://github.com/Tencent/bk-ci)：蓝鲸持续集成平台是一个开源的持续集成和持续交付系统，可以轻松将你的研发流程呈现到你面前。
- [BK-BCS](https://github.com/Tencent/bk-bcs)：蓝鲸容器管理平台是以容器技术为基础，为微服务业务提供编排管理的基础服务平台。
- [BK-BCS-SaaS](https://github.com/Tencent/bk-bcs-saas)：蓝鲸容器管理平台SaaS基于原生Kubernetes和Mesos自研的两种模式，提供给用户高度可扩展、灵活易用的容器产品服务。
- [BK-PaaS](https://github.com/Tencent/bk-PaaS)：蓝鲸PaaS平台是一个开放式的开发平台，让开发者可以方便快捷地创建、开发、部署和管理SaaS应用。
- [BK-SOPS](https://github.com/Tencent/bk-sops)：标准运维（SOPS）是通过可视化的图形界面进行任务流程编排和执行的系统，是蓝鲸体系中一款轻量级的调度编排类SaaS产品。
- [BK-CMDB](https://github.com/Tencent/bk-cmdb)：蓝鲸配置平台是一个面向资产及应用的企业级配置管理平台。

## Contributing

如果你有好的意见或建议，欢迎给我们提 Issues 或 Pull Requests，为蓝鲸开源社区贡献力量。

1. 本项目使用 [Poetry](https://python-poetry.org/) 进行开发、构建及发布，本地开发环境搭建请参考 Poetry 官方文档
2. PR 需要通过 CI 中的所有代码风格检查，单元测试及集成测试才可被接受合并
3. 新增加的模块请确保完备的单元测试覆盖

## License

基于 MIT 协议， 详细请参考[LICENSE](LICENSE.txt)
