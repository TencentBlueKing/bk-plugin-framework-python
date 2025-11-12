import logging

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

logger = logging.getLogger("bk_plugin")


class MyPlugin(Plugin):
    class Meta:
        version = "1.0.0"
        desc = "this is an example version"

    class Inputs(InputsModel):
        hello: str

    class Outputs(OutputsModel):
        world: str

    class ContextInputs(ContextRequire):
        executor: str = Field(title="任务执行人")

    # 如果需要凭证，取消注释以下类（与 ContextInputs 并行）
    # class Credentials(CredentialModel):
    #     bk_access_token = Credential(key="bk_access_token", name="蓝鲸 access token", description="用于调用蓝鲸 API 的 access token")

    def execute(self, inputs: Inputs, context: Context):
        # 如果声明了 Credentials，可以通过 context.credentials 访问凭证
        # credential_value = context.credentials.get("bk_access_token")
        context.outputs["world"] = inputs.hello
