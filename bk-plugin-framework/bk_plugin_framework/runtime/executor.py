# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making 蓝鲸智云 - PaaS平台 (BlueKing - PaaS System) available.
Copyright (C) 2022 THL A29 Limited, a Tencent company. All rights reserved.
Licensed under the MIT License (the "License"); you may not use this file except in compliance with the License.
You may obtain a copy of the License at
http://opensource.org/licenses/MIT
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.
"""

import json
import typing
import logging

from celery import current_app
from pydantic import ValidationError
from django.utils.timezone import now

from bk_plugin_framework.kit import Plugin, Context, State, InputsModel, ContextRequire, Callback
from bk_plugin_framework.runtime.schedule.models import Schedule

logger = logging.getLogger("bk_plugin")

FINISH_STATES = {State.FAIL, State.SUCCESS}
UNFINISHED_STATES = {State.POLL, State.CALLBACK}


class ExecuteResult:
    def __init__(self, state: State, outputs: typing.Optional[dict], err: typing.Optional[str]):
        self.state = state
        self.outputs = outputs
        self.err = err


class BKPluginExecutor:
    SCHEDULE_TASK_NAME = "bk_plugin_framework.runtime.schedule.celery.tasks.schedule"

    def __init__(self, trace_id: str):
        self.trace_id = trace_id

    def _dump_schedule_data(self, inputs: dict, context: dict, outputs: dict):
        return json.dumps(
            {
                "inputs": inputs,
                "context": context,
                "outputs": outputs,
            }
        )

    def _load_schedule_data(self, schedule: Schedule) -> dict:
        return json.loads(schedule.data)

    def _set_schedule_state(self, trace_id: str, state: State):
        update_kwargs = {"state": state.value}
        if state in FINISH_STATES:
            update_kwargs["finish_at"] = now()
        try:
            Schedule.objects.filter(trace_id=trace_id).update(**update_kwargs)
        except Exception:
            logger.exception("[execute] set schedule state error")

    def execute(
        self, plugin_cls: Plugin, inputs: typing.Dict[str, typing.Any], context_inputs: typing.Dict[str, typing.Any]
    ) -> ExecuteResult:

        # user inputs validation
        input_cls = getattr(plugin_cls, "Inputs", InputsModel)
        try:
            valid_inputs = input_cls(**inputs)
        except ValidationError as e:
            return ExecuteResult(state=State.FAIL, outputs=None, err="inputs validation error: %s" % str(e))

        # user context inputs validation
        context_inputs_cls = getattr(plugin_cls, "ContextInputs", ContextRequire)
        try:
            valid_context_inputs = context_inputs_cls(**context_inputs)
        except ValidationError as e:
            return ExecuteResult(state=State.FAIL, outputs=None, err="context validation error: %s" % str(e))

        # domain object initialization
        context = Context(
            trace_id=self.trace_id, data=valid_context_inputs, state=State.EMPTY, invoke_count=1, outputs={}
        )
        plugin = plugin_cls()

        # run execute method
        try:
            logger.info("[execute] plugin start execute")
            plugin.execute(inputs=valid_inputs, context=context)
        except Plugin.Error as e:
            logger.exception("[execute] plugin execute failed")
            return ExecuteResult(state=State.FAIL, outputs=None, err="plugin execute failed: %s" % str(e))
        except Exception as e:
            logger.exception("[execute] plugin execute raise unexpected error")
            return ExecuteResult(
                state=State.FAIL, outputs=None, err="plugin execute raise unexpected error: %s" % str(e)
            )

        # check plugin state
        if plugin.is_wating_poll:
            state = State.POLL
        elif plugin.is_waiting_callback:
            state = State.CALLBACK
        else:
            state = State.SUCCESS

        if state in UNFINISHED_STATES:
            # avoid user change on inputs and context.data
            context.data = context_inputs_cls(**context_inputs)

            # prepare persistent data for schedule
            try:
                schedule_data = self._dump_schedule_data(
                    inputs=inputs, context=context.schedule_context, outputs=context.outputs
                )
            except Exception as e:
                logger.exception("[execute] schedule data json dumps error")
                return ExecuteResult(state=State.FAIL, outputs=None, err="plugin context json dumps error: %s" % str(e))

            # create schedule model
            try:
                schedule = Schedule.objects.create(
                    trace_id=self.trace_id,
                    state=state.value,
                    plugin_version=plugin_cls.Meta.version,
                    data=schedule_data,
                )

                logger.info("[execute] plugin wait {}".format("poll" if plugin.is_wating_poll else "callback"))

            except Exception as e:
                logger.exception("[execute] schedule create error")
                return ExecuteResult(state=State.FAIL, outputs=None, err="schedule create error: %s" % str(e))

        if state is State.POLL:
            # dispatch schedule task with schedule model
            try:
                task_id = current_app.tasks[self.SCHEDULE_TASK_NAME].apply_async(
                    kwargs={"trace_id": self.trace_id},
                    countdown=plugin.poll_interval,
                    queue="plugin_schedule",
                )
            except Exception as e:
                logger.exception("[execute] schedule task dispatch error")

                # try to fix pending schedule model state when dispatch failed
                self._set_schedule_state(trace_id=schedule.trace_id, state=State.FAIL)

                return ExecuteResult(state=State.FAIL, outputs=None, err="schedule task dispatch error: %s" % str(e))

            logger.info("[execute] task delay success, task_id: %s, count_down: %s" % (task_id, plugin.poll_interval))

        return ExecuteResult(state=state, outputs=context.outputs, err=None)

    def schedule(self, plugin_cls: Plugin, schedule: Schedule, callback_info: dict = {}):

        # load schedule data
        logger.info("[schedule] load schedule data")
        try:
            schedule_data = self._load_schedule_data(schedule)
        except Exception:
            logger.exception("[schedule] schedule data load error")
            self._set_schedule_state(trace_id=schedule.trace_id, state=State.FAIL)
            return

        # inputs validation
        logger.info("[schedule] validate inputs")
        input_cls = getattr(plugin_cls, "Inputs", InputsModel)
        try:
            valid_inputs = input_cls(**schedule_data["inputs"])
        except ValidationError:
            logger.exception(
                "[schedule] inputs load error, please make sure plugin Inputs model has not make break change"
            )
            self._set_schedule_state(trace_id=schedule.trace_id, state=State.FAIL)
            return

        # context inputs validation
        logger.info("[schedule] validate context value")
        context_inputs_cls = getattr(plugin_cls, "ContextInputs", ContextRequire)
        try:
            valid_context_inputs = context_inputs_cls(**schedule_data["context"]["data"])
        except ValidationError:
            logger.exception(
                "[schedule] context inputs load error, please make sure plugin ContextInputs model has not make break change"  # noqa
            )
            self._set_schedule_state(trace_id=schedule.trace_id, state=State.FAIL)
            return

        # schedule execute prepare
        logger.info("[schedule] prepare context and plugin")
        invoke_count = schedule.invoke_count + 1
        execute_fail = False
        unexpected_error_raise = False
        state = State.CALLBACK if schedule.state is State.CALLBACK.value else State.POLL
        context = Context(
            trace_id=self.trace_id,
            data=valid_context_inputs,
            state=state,
            invoke_count=invoke_count,
            callback=Callback(
                callback_id=callback_info.get("callback_id"), callback_data=callback_info.get("callback_data")
            ),
            outputs=schedule_data["context"]["outputs"],
            storage=schedule_data["context"]["storage"],
        )
        plugin = plugin_cls()
        err = ""

        # run schedule execute
        logger.info("[schedule] run execute")
        try:
            plugin.execute(inputs=valid_inputs, context=context)
        except Plugin.Error as e:
            logger.exception("[schedule] plugin execute failed")
            err = "plugin schedule failed: %s" % str(e)
            execute_fail = True
        except Exception as e:
            logger.exception("[schedule] plugin execute raise unexpected error")
            err = "plugin schedule failed: %s" % str(e)
            unexpected_error_raise = True

        context.data = context_inputs_cls(**schedule_data["context"]["data"])
        try:
            schedule_data = self._dump_schedule_data(
                inputs=schedule_data["inputs"], context=context.schedule_context, outputs=context.outputs
            )
        except Exception:
            logger.exception("[execute] schedule data json dumps error")
            self._set_schedule_state(trace_id=schedule.trace_id, state=State.FAIL)
            return

        if execute_fail:
            update_fields = {
                "state": State.FAIL.value,
                "invoke_count": invoke_count,
                "data": schedule_data,
                "finish_at": now(),
                "err": err,
            }

        elif unexpected_error_raise:
            # don't save context storage and data when raise unexpected error
            update_fields = {
                "state": State.FAIL.value,
                "invoke_count": invoke_count,
                "finish_at": now(),
                "err": err,
            }

        elif plugin.is_wating_poll:
            update_fields = {"state": State.POLL.value, "invoke_count": invoke_count, "data": schedule_data}
            logger.info("[schedule] plugin wait poll")

        elif plugin.is_waiting_callback:
            update_fields = {"state": State.CALLBACK.value, "invoke_count": invoke_count, "data": schedule_data}
            logger.info("[schedule] plugin wait callback")

        else:
            update_fields = {
                "state": State.SUCCESS.value,
                "invoke_count": invoke_count,
                "data": schedule_data,
                "finish_at": now(),
            }

        try:
            Schedule.objects.filter(trace_id=schedule.trace_id).update(**update_fields)
        except Exception:
            logger.exception("[schedule] schedule object update error")
            self._set_schedule_state(trace_id=schedule.trace_id, state=State.FAIL)
            return

        try:
            if not execute_fail and not unexpected_error_raise and plugin.is_wating_poll:
                task_id = current_app.tasks[self.SCHEDULE_TASK_NAME].apply_async(
                    kwargs={"trace_id": self.trace_id},
                    countdown=plugin.poll_interval,
                    queue="plugin_schedule",
                )
                logger.info(
                    "[schedule] task delay success, task_id: %s, count_down: %s" % (task_id, plugin.poll_interval)
                )
        except Exception:
            logger.exception("[schedule] schedule task dispatch error")
            # set failed to prevent infinity poll at caller side
            self._set_schedule_state(trace_id=schedule.trace_id, state=State.FAIL)
            return

        logger.info("[schedule] plugin execute schedule done")
