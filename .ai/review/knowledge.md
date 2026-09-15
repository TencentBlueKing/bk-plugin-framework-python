# Python 插件框架源码知识库

本文件帮助审查者定位源码和理解已有契约，不是当前缺陷列表。首次核对基于远程 `master` 的 `2872f8929e2d1373604fca837297681db55e3269`（2026-09-09）；审查每个 PR 时仍以实际 base/head 为准。完整路径相对仓库根目录，版本号是这一基准的事实，不能代替实际安装包或部署镜像版本。

路径简写约定：`kit/`、`hub/`、`utils/`、`services/`、`runtime/schedule/`、`runtime/callback/`、`runtime/loghub/`、`runtime/executor.py`、`runtime/callbacker.py`、`constants.py` 和 `envs.py` 均以 `bk-plugin-framework/bk_plugin_framework/` 为根；`config/`、`packages/`、`schema.py` 以 `runtime/bk-plugin-runtime/bk_plugin_runtime/` 为根；框架 `tests/`、`pytest.ini` 以 `bk-plugin-framework/` 为根。模板内部路径以对应的生成项目为根。

## 仓库及包边界

| 位置 | 责任及审查含义 |
| --- | --- |
| `bk-plugin-framework/bk_plugin_framework/` | 定义插件 SDK、版本发现、HTTP 协议、执行器、Schedule/日志模型、Celery 调度及回调。这里的 `runtime/` 是 **framework 包内的执行实现**。 |
| `runtime/bk-plugin-runtime/bk_plugin_runtime/` | 另一个独立发布包，提供 Django 配置、WSGI、根 URL、登录/APIGW 集成、静态资源、管理入口及内置 ESB SDK。不是前一行的同名子目录。 |
| `template/{{cookiecutter.project_name}}/` | Cookiecutter 生成的插件项目骨架：`bk_plugin/versions`、`forms`、依赖、启动进程及部署钩子。修改模板只影响后续生成或主动迁移的项目。 |
| `docker/base/Dockerfile` | 用模板默认依赖构建基础镜像；插件项目 Dockerfile 在它上面安装业务额外依赖。 |

`bk-plugin-framework/pyproject.toml` 与其 `bk_plugin_framework/__version__.py` 当前均为 `2.3.15`，framework 精确依赖 `bk-plugin-runtime==2.1.9`。`runtime/bk-plugin-runtime/pyproject.toml` 与其 `bk_plugin_runtime/__version__.py` 当前均为 `2.1.9`。两个包分别通过 `.github/workflows/framework_python_package_pypi.yml`、`.github/workflows/runtime_python_package_pypi.yml` 发布，tag 前缀分别是 `bk-plugin-framework-v` 和 `bk-plugin-runtime-v`。

两份 pyproject 声明 Python `^3.8.0,<4.0`，APIGW 依赖另有 Python `<3.13` 条件；不能据此声称整个范围均经验证。framework 使用 Pydantic `>=1.0,<3`，`kit/plugin.py`、`kit/__init__.py`、`envs.py`、`runtime/executor.py` 优先导入 `pydantic.v1` 再回退。runtime 依赖 Django `>=2.2.6,<5`、Celery `^5.4.0`、blueapps `>=4.15.1,<5.0` 等。依赖升级需核对实际解析结果与相应兼容分支。

## 插件注册、模型与表单

入口链是 `bk-plugin-framework/bk_plugin_framework/services/bpf_service/apps.py:BpfServiceConfig.ready` → `utils/module_load.py:discover_plugins` → 导入 `bk_plugin.versions` 下非下划线开头的模块 → `kit/plugin.py:PluginMeta` → `hub/__init__.py:VersionHub._register_plugin`。

`PluginMeta` 要求 `Meta.version` 为字符串，长度不超过 128，并匹配 `^[0-9]+\.[0-9]+\.[0-9][a-z0-9]*$`。不要用完整 SemVer 规则替代实际正则。重复版本直接报错；`VersionHub.versions()` 按字符串倒序返回，未作数值语义排序。发现失败、重复导入、改名或删除版本都可能影响启动和在途任务恢复。

`kit/plugin.py` 的 `Inputs`、`ContextInputs`、`Outputs` 分别继承 `InputsModel`、`ContextRequire`、`OutputsModel`。前两者在 `runtime/executor.py` 首次调用和调度恢复时实际构造并校验；`Outputs` 用于声明 schema，执行结果来自可变的 `context.outputs`，执行器没有统一构造 Outputs 实例进行校验。不要将 schema 声明等同于响应数据已经校验。

`Plugin.dict()` 输出 `desc/version/enable_plugin_callback/inputs/context_inputs/outputs/forms`；`forms.renderform` 是 `bk_plugin/forms/<version>/form.js` 的原始内容，缺少文件时 `VersionHub` 记录警告并设为 `None`。`InputsForm` 额外属性会合入输入 schema 的 properties。修改默认值、必填项、类型、嵌套定义和表单 `tag_code` 时，需要同时考虑编辑表单、调用方传参及旧 Schedule 保存的 JSON。

模板示例在 `template/{{cookiecutter.project_name}}/bk_plugin/versions/v1_0_0.py`：版本 `1.0.0` 的输入为 `hello`，上下文需要 `executor`，输出写入 `world`。对应 `bk_plugin/forms/1.0.0/form.js` 的 `tag_code` 为 `hello`。表单的 `$.atoms` 键来自 Cookiecutter 的 app_code，不能与类名或项目目录名混用。

## HTTP 协议和状态

根 URL 在 `runtime/bk-plugin-runtime/bk_plugin_runtime/urls.py`，挂载 `bk-plugin-framework/bk_plugin_framework/services/bpf_service/urls.py`。下表列的是后端路径；APIGW 的外部路径另见资源模板，末尾斜杠不能推断为一致。

| 后端入口 | 实现与响应语义 |
| --- | --- |
| `GET /bk_plugin/meta/` | `services/bpf_service/api/meta.py`：返回 app code、版本列表、描述、framework/runtime 版本、`allow_scope`。 |
| `GET /bk_plugin/detail/<version>` | `services/bpf_service/api/detail.py`：读取注册类并返回 `Plugin.dict()`；不存在的版本为 404。 |
| `POST /bk_plugin/invoke/<version>` | `services/bpf_service/api/invoke.py`：请求必须有 dict 型 `inputs` 与 `context`，同步调用 `BKPluginExecutor.execute`，返回 `result/data/trace_id/message`。 |
| `GET /bk_plugin/schedule/<trace_id>` | `services/bpf_service/api/schedule.py`：按执行 trace 查询 Schedule，读取 outputs、state、err、创建和结束时间；不存在记录时返回 `result=False`，不是插件成功。 |
| `POST /bk_plugin/callback/<token>/` | `services/bpf_service/api/callback.py`：解析 token、读取 JSON 请求体、尝试投递 callback 任务。200/`result=True` 表示受理投递，不代表业务执行已经结束。 |

`constants.py:State` 的持久化/协议值为 `EMPTY=1`、`POLL=2`、`CALLBACK=3`、`SUCCESS=4`、`FAIL=5`。`Invoke.post` 中 `result=True` 可同时携带 `state=5`；调用方需要分别处理传输/协议失败和插件失败。外层 DRF 请求格式错误返回 400；模型校验和插件异常通常由执行器转换为 FAIL；版本不存在返回 404。不要只看 HTTP 200 或 result 判断执行结果。

`services/bpf_service/middlewares.py:TraceIDInjectMiddleware` 为每次 HTTP 请求生成 UUID hex；invoke 的返回 trace 用于之后查 Schedule。查询接口的顶层 `trace_id` 是这次查询请求的跟踪号，`data.trace_id` 才是被查询的执行。此机制不是按调用方请求键去重。

`kit/plugin.py:Plugin.wait_poll`、`wait_callback` 仅改变实例标志，不会中断 execute；最终由执行器决定状态。没有异常且不再等待时才结束为 SUCCESS；每次调度会重新实例化插件并再次调用 execute。需要跨轮保存的数据放在 `context.storage`/`context.outputs`，不能依赖进程内插件实例一直存在。

## 执行、持久化、调度与幂等

`bk-plugin-framework/bk_plugin_framework/runtime/executor.py:BKPluginExecutor.execute` 依次校验输入与上下文，创建 `State.EMPTY/invoke_count=1` 的 Context，执行插件，再判断等待模式。只有 POLL/CALLBACK 创建 Schedule；同步成功/失败不必有可查询的 Schedule。异步数据通过 `_dump_schedule_data` 保存为 JSON，包含原始 inputs、`context.data/storage/outputs` 及顶层 outputs；等待时会重新按原始上下文构造 `context.data`。客户端对象、连接、任意 Python 对象不能被假定可以跨 JSON/Celery 边界使用。

`runtime/schedule/models.py:Schedule` 以 `trace_id` 为主键，记录 `plugin_version/state/invoke_count/data/scheduling/err/created_at/finish_at`。恢复链是 `runtime/schedule/celery/tasks.py:schedule` → 按存储版本从 VersionHub 找插件 → `BKPluginExecutor.schedule` → 从旧 JSON 重新校验并恢复 Context。原版本的模型和逻辑会被在途任务继续使用；破坏性模型或状态语义变更需要考虑新增插件版本、旧数据读取和回滚兼容。

首次和后续 POLL 都使用 `apply_async(..., queue="plugin_schedule", countdown=plugin.poll_interval)`；写 Schedule 与发 MQ 是两个操作。审查改动时逐步追踪外部副作用、持久化、投递、重试与终态，不能预设它们原子提交。`schedule` 读取 Schedule 遇到 `OperationalError/InterfaceError` 已有 Celery 最多 6 次重试，倒计时 `min(2 ** retries * 5, 60)`；重试耗尽和其他错误路径另有失败处理，不可把“没有 DB 重试”当作当前事实。

`BKPluginExecutor.schedule` 区分 `Plugin.Error` 与意外异常：前者保存本轮序列化数据和 err，后者的失败更新不保存本轮 data；终态通常写 finish_at。其他辅助失败路径更新的字段不一定相同，涉及变更时应逐条检查实际分支，不能假设所有失败已经相同处理。

`runtime/schedule/models.py:apply_schedule_lock` 用 `scheduling=False` 的条件更新申请锁；`runtime/schedule/utils.py:ScheduleLock` 在退出时释放。此锁由 `runtime/callback/celery/tasks.py` 的 callback 任务使用，抢锁失败会延迟 1–5 秒重新投递，拿锁后再检查状态为 CALLBACK；普通 poll 任务没有使用同一锁。callback_id 用于传递回调身份，本仓库未提供已消费 callback_id 的独立持久化去重表。不能将“有 trace 主键/有调度锁”描述为 invoke、poll、callback 全链路 exactly-once。

`runtime/schedule/celery/beat.py` 注册过期记录清理任务，`ScheduleManger.delete_expired_schedule` 仅删除 finish_at 早于阈值的记录，默认保留天数来自 `envs.py:SCHEDULE_PERSISTENT_DAYS=30`。队列定义在 `runtime/schedule/celery/queues.py` 和 `runtime/callback/celery/queues.py`，与模板 worker 订阅的 `plugin_schedule,plugin_callback,schedule_delete` 对齐。

## 两种回调方向

外部系统回调插件：`kit/plugin.py:prepare_callback` → `runtime/callback/api.py:prepare_callback` 生成 callback_id，将 `callback_id:trace_id` 通过 Fernet 加密到 URL token。默认密钥由 `envs.py:compute_settings` 从 BK_APP_SECRET 派生，可被 Settings 更高优先级来源覆盖。URL 使用 APIGW host 和 `BK_PLUGIN_APIGW_STAGE_NAME`。解析校验解密和两个 32 字符标识；当前 decrypt 调用没有传 ttl，不能假定 token 自动过期。`callback()` 检查 Schedule 为 CALLBACK 后向 `plugin_callback` 投递 JSON 字符串，worker 再解码并交给执行器。

插件通知接入系统：`runtime/executor.py:_plugin_finish_callback` 在相应 schedule 完成/失败路径检查 `Meta.enable_plugin_callback` 和 `ContextInputs.plugin_callback_info`，调用 `runtime/callbacker.py:PluginCallbacker`。它使用回调信息中的 URL/data 发请求，默认最多尝试 3 次，失败记录日志；本机制与上面的 token 回调入口不同，也不是插件 `State` 的另一个枚举。不能把 schedule 的通知行为无条件套到首次同步 execute 上。涉及此处变更时检查 URL 来源、超时、TLS、敏感日志和重复发送的实际影响。

## 登录、APIGW、业务域与 tenant

`runtime/bk-plugin-runtime/bk_plugin_runtime/config/default.py` 在 blueapps 默认配置上追加 APIGW Generic/App/User JWT 中间件，DRF 默认认证和权限分别为 `ApiGatewayJWTAuthentication`、`ApiGatewayPermission`，并使用 `packages/apigw/backends.py:APIGWUserModelBackend` 创建/获取用户。外部依赖中的 JWT 校验和用户/租户行为需检查对应安装版本，不能仅凭本地后端签名推断。

invoke 和 plugin_api_dispatch 显式使用 `apigw_require`、禁用 DRF authentication_classes 并应用 `services/bpf_service/api/permissions.py:ScopeAllowPermission`；callback 同样有 `apigw_require`。meta/detail/schedule 视图覆盖为 `AllowAny` 并有 login_exempt，因此分析请求能否绕过授权时必须同时追踪 URL 可达性、中间件、实际网关资源权限和部署网络边界。`isPublic` 表示网关资源公开可见，不等同于匿名免认证。

`ScopeAllowPermission` 从 `bk_plugin.meta.allow_scope` 读取按调用 app_code 定义的业务域；未配置或调用应用不在字典中默认放行，已配置应用需精确匹配 `Bkplugin-Scope-Type` 与 `Bkplugin-Scope-Value`。它读取 `request.app.bk_app_code`，不是通过用户输入声明自己的应用身份。此业务域机制不能代替租户隔离。

`services/bpf_service/api/plugin_api_dispatch.py` 只接收 `/bk_plugin/plugin_api/` 前缀和 GET/POST，经 Django resolve 分发本地视图；转发自定义头和 APIGW JWT，用请求里的 username 构造 `_force_auth_user`。检查这条链时区分网关认证的应用/用户与委托执行用户名，继续追踪目标视图及其下游业务权限。`kit/api.py:PluginAPIView`、`kit/decorators.py` 处理 dev cookie 与非 dev JWT/应用 access token，下游鉴权不能仅凭请求携带 username 判定有效。

环境差异是已有行为：`config/dev.py` 默认豁免 APIGW 来源校验；`config/stag.py` 对 `BK_APIGW_REQUIRE_EXEMPT` 使用“变量存在”判断；项目 `bk_plugin.settings` 可覆盖配置。本地调试通过不能作为生产 APIGW 认证证据。

这一基准的 framework/runtime Python 与模板配置未见显式 tenant 字段或租户头传递实现；Schedule 和 LogEntry 模型没有 tenant 列。这是源码边界说明，不证明部署一定有跨租户漏洞或完全不支持多租户。涉及 tenant 的 PR 必须追踪可信租户来源、blueapps/APIGW 版本、用户身份、ORM 查询、缓存/MQ key、异步上下文和下游请求；明确共享部署还是按租户独立部署，缺少外部证据时保留未知。

## 网关资源与数据库迁移

`bk-plugin-framework/bk_plugin_framework/services/bpf_service/management/commands/sync_apigateway_if_changed.py` 先生成 definition.yaml，再把 `management/commands/support-files/resources.yaml` 复制为项目 resources.yaml；不是从当前 URL 自动扫描资源。比较二者组合哈希后调用 `sync_drf_apigateway`，同步失败记录 success=False；未变更时仍获取公钥。状态存在 `services/bpf_service/models.py:APIGatewaySyncState`，对应迁移位于 `services/bpf_service/migrations/0001_initial.py`。

实际同步资源包括 invoke、callback、schedule、plugin_api/openapi/private 子路径及 dispatch。当前 schedule 资源 `/bk_plugin/schedule/{id}` 要求 app 验证，不要求 user/resource permission；这与视图 schema 装饰器声明不同，`tests/services/bpf_service/test_resources_yaml.py` 明确锁定资源模板行为。自定义 plugin_api、openapi、private 的 user/app 要求也各不相同；不得按目录名推定权限。`runtime/bk-plugin-runtime/bk_plugin_runtime/schema.py` 还会覆盖 drf-spectacular 的 exclude 行为；文档可见性、实际同步资源和后端访问控制是三件事。

Schedule 的初始表及后续 finish_at、scheduling、err 等变化在 `bk-plugin-framework/bk_plugin_framework/runtime/schedule/migrations/`；日志表在 `runtime/loghub/models.py` 与对应 migrations。调整模型需考虑存量表、历史 JSON、分批部署和回滚读取能力。`runtime/bk-plugin-runtime/bk_plugin_runtime/config/dev.py` 默认 SQLite，并保留显式配置/检测 MySQL 的兼容路径；stag/prod 配置继承 blueapps 环境配置，不能拿 SQLite 或 mock 证明真实 MySQL 并发/连接恢复。

## 模板、镜像和验证入口

`template/cookiecutter.json` 的基础镜像当前是 `bk-plugin-python-base:2.3.14`，模板 requirements 也 pin `bk-plugin-framework==2.3.14`，与仓库 framework 当前版本不是同一个值。默认依赖由 `docker/base/Dockerfile` 预装；`template/{{cookiecutter.project_name}}/Dockerfile` 仅安装 `custom_requirements.txt`。修改 requirements 不会自动改变一个已构建基础镜像，修改源码也不会自动更新生成项目已安装的包。

`template/{{cookiecutter.project_name}}/runtime.txt` 为 Python `3.10.5`；`app_desc.yml` 定义 web、schedule、beat、c-monitor 进程与 preRelease；`bin/sync_apigateway.sh` 先执行 migrate，再执行网关同步，是带 DB/外部写入的部署入口，不能当普通只读测试运行。`bin/manage.py` 配置 Django/runtime 模块；本地调试命令为 `python bin/manage.py rundebugserver`，所需环境见 `bk-plugin-framework/bk_plugin_framework/services/debug_panel/management/commands/rundebugserver.py`。

当前主要框架测试入口来自 `.github/workflows/framework_unittest.yml`，使用 Python 3.10.5、Poetry 1.8.5，在 `bk-plugin-framework/` 执行：

```sh
poetry install
poetry run coverage run -m pytest -vv --disable-pytest-warnings
poetry run coverage xml
```

按变更选择聚焦入口（工作目录同上）：

```sh
poetry run pytest tests/hub tests/kit tests/utils -q
poetry run pytest tests/runtime/test_executor.py tests/runtime/schedule tests/runtime/callback -q
poetry run pytest tests/services/bpf_service/test_resources_yaml.py tests/template/test_docker_template.py -q
```

`pytest.ini` 使用 `tests.settings`，现有执行器/任务测试大量 mock ORM 和消息投递。`tests/template/test_docker_template.py` 只校验模板内容及版本配套，生成项目的 `template/{{cookiecutter.project_name}}/tests/test_plugin.py` 只是占位断言。模板渲染、实际镜像构建、真实 DB/MQ、端到端 invoke→poll/callback→终态和远端验收都需要单独证据。

`bk-plugin-framework/tox.ini` 和 `dev-requirements.txt` 仍含 Python 3.6/3.7、Celery 3、旧 Django/APIGW 等历史配置，不能替代当前 pyproject/CI 基线。框架 Poetry 安装会解析发布版 runtime pin，不自动测试同仓 runtime 工作区源码；同时改两包时必须确认测试实际导入路径与版本。现有 lint workflow 的 black 命令会格式化源码；只读核验可用 `black --check`。本知识库不宣称已经运行测试、发布依赖、完成迁移或通过真实 BK-SOPS/BKFlow 验收。
