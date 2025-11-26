"""
创建流程编排 (Flow 2)
处理新服务创建请求：意图识别 → 需求收集 → SIPOC生成 → 人工确认 → 服务创建 → 执行
"""
from typing import Optional
from ..agents import ProcessDesigner, ServiceBuilder
from rag_module.memory import MemoryManager
from service_module.mock_services import ServiceRegistry


class CreationCrew:
    """创建流程编排"""

    def __init__(
        self,
        service_registry: ServiceRegistry,
        memory_manager: MemoryManager,
    ):
        """
        初始化创建流程

        Args:
            service_registry: 服务注册表
            memory_manager: 记忆管理器
        """
        self.registry = service_registry
        self.memory = memory_manager

        # 初始化智能体
        self.process_designer = ProcessDesigner()
        self.service_builder = ServiceBuilder(service_registry)

        # 会话状态
        self._session_states: dict = {}

    async def execute(
        self,
        user_input: str,
        intent_result: dict,
        session_id: str = "default",
    ) -> dict:
        """
        执行创建流程

        Args:
            user_input: 用户输入
            intent_result: 意图识别结果
            session_id: 会话ID

        Returns:
            处理结果
        """
        # 获取会话状态
        state = self._session_states.get(session_id, {
            "stage": "initial",
            "requirements": {},
            "sipoc": None,
        })

        stage = state.get("stage", "initial")

        # 根据阶段处理
        if stage == "initial":
            return await self._handle_initial(user_input, intent_result, session_id)
        elif stage == "collecting":
            return await self._handle_collecting(user_input, session_id)
        elif stage == "confirming":
            return await self._handle_confirming(user_input, session_id)
        elif stage == "building":
            return await self._handle_building(user_input, session_id)
        else:
            return await self._handle_initial(user_input, intent_result, session_id)

    async def _handle_initial(
        self,
        user_input: str,
        intent_result: dict,
        session_id: str,
    ) -> dict:
        """处理初始阶段 - 开始需求收集"""
        # 调用流程设计智能体
        result = await self.process_designer.execute({
            "user_input": user_input,
            "session_id": session_id,
            "intent_result": intent_result,
        })

        # 更新会话状态
        self._session_states[session_id] = {
            "stage": result.get("status", "collecting"),
            "requirements": result.get("requirements", {}),
            "sipoc": result.get("sipoc"),
        }

        return result

    async def _handle_collecting(
        self,
        user_input: str,
        session_id: str,
    ) -> dict:
        """处理需求收集阶段"""
        state = self._session_states.get(session_id, {})

        # 继续收集需求
        result = await self.process_designer.execute({
            "user_input": user_input,
            "session_id": session_id,
        })

        # 更新状态
        new_status = result.get("status", "collecting")
        state["stage"] = new_status
        state["requirements"] = result.get("requirements", state.get("requirements", {}))

        if result.get("sipoc"):
            state["sipoc"] = result["sipoc"]

        self._session_states[session_id] = state

        return result

    async def _handle_confirming(
        self,
        user_input: str,
        session_id: str,
    ) -> dict:
        """处理确认阶段"""
        state = self._session_states.get(session_id, {})

        # 检查用户是否确认
        result = await self.process_designer.execute({
            "user_input": user_input,
            "session_id": session_id,
        })

        if result.get("status") == "confirmed":
            # 进入构建阶段
            state["stage"] = "building"
            self._session_states[session_id] = state

            # 立即开始构建
            return await self._handle_building(user_input, session_id)

        # 继续确认流程
        state["stage"] = result.get("status", "confirming")
        if result.get("sipoc"):
            state["sipoc"] = result["sipoc"]
        if result.get("requirements"):
            state["requirements"] = result["requirements"]

        self._session_states[session_id] = state

        return result

    async def _handle_building(
        self,
        user_input: str,
        session_id: str,
    ) -> dict:
        """处理构建阶段"""
        state = self._session_states.get(session_id, {})
        sipoc = state.get("sipoc")
        requirements = state.get("requirements", {})

        if not sipoc:
            return {
                "success": False,
                "message": "缺少SIPOC文档，无法构建服务",
            }

        # 调用服务构建智能体
        build_result = await self.service_builder.build_and_execute(
            sipoc_data=sipoc,
            requirements=requirements,
        )

        # 存储到记忆系统
        await self.memory.store_interaction(
            user_input=f"创建服务: {sipoc.get('title', '未知')}",
            result=build_result,
        )

        # 清理会话状态
        self._clear_session(session_id)

        # 格式化结果消息
        if build_result.get("success"):
            exec_result = build_result.get("execution_result", {})
            if exec_result.get("success"):
                data = exec_result.get("data", {})
                message = f"""**服务创建并执行成功！**

处理结果：
- 处理基金数量: {data.get('processed_count', 0)}
- 分红总金额: ¥{data.get('total_amount', 0):,.2f}

详细信息已记录到系统中。"""
            else:
                message = build_result.get("message", "服务创建成功")
        else:
            message = build_result.get("message", "服务创建失败")

        return {
            "success": build_result.get("success", False),
            "message": message,
            "sipoc": sipoc,
            "build_result": build_result,
        }

    def _clear_session(self, session_id: str):
        """清理会话状态"""
        if session_id in self._session_states:
            del self._session_states[session_id]
        self.process_designer.clear_session(session_id)

    def get_session_stage(self, session_id: str) -> str:
        """获取当前会话阶段"""
        state = self._session_states.get(session_id, {})
        return state.get("stage", "initial")

    def reset_session(self, session_id: str):
        """重置会话"""
        self._clear_session(session_id)
