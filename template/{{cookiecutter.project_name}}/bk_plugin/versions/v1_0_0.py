import logging

from bk_plugin_framework.kit import (
    Context,
    ContextRequire,
    Field,
    InputsModel,
    OutputsModel,
    Plugin,
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

    def execute(self, inputs: Inputs, context: Context):
        context.outputs["world"] = inputs.hello
