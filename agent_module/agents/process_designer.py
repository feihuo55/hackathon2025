# -*- coding: utf-8 -*-
"""
流程设计智能体
通过多轮对话收集需求，生成流程设计
"""
import json
from typing import Optional
from .base_agent import BaseAgent
from service_module.sipoc import SIPOCGenerator, SIPOCDocument


PROCESS_DESIGNER_PROMPT = """你是一个专业的业务流程设计师，擅长与用户沟通收集需求，设计托管银行业务流程。

你的任务是：
1. 理解用户的业务需求
2. 通过提问收集必要的信息
3. 设计完整的业务流程
4. 生成SIPOC文档

在收集需求时，你需要了解：
- 流程的目标和范围
- 输入数据来源
- 处理步骤
- 输出结果
- 相关的利益方

请用专业但友好的语气与用户交流。"""


class ProcessDesigner(BaseAgent):
    """流程设计智能体"""

    def __init__(self, bedrock_client=None):
        super().__init__(
            name="ProcessDesigner",
            description="通过多轮对话收集需求，设计业务流程",
            system_prompt=PROCESS_DESIGNER_PROMPT,
        )
        self.sipoc_generator = SIPOCGenerator(bedrock_client)
        self._conversation_state = {}

    async def execute(self, input_data: dict) -> dict:
        """
        执行流程设计

        Args:
            input_data: 包含用户输入和会话状态的字典

        Returns:
            设计结果或下一步问题
        """
        user_input = input_data.get("user_input", "")
        session_id = input_data.get("session_id", "default")
        intent_result = input_data.get("intent_result", {})

        # 获取或初始化会话状态
        state = self._conversation_state.get(session_id, {
            "stage": "initial",
            "requirements": {},
            "questions_asked": 0,
        })

        # 根据阶段处理
        if state["stage"] == "initial":
            return await self._handle_initial(user_input, intent_result, session_id)
        elif state["stage"] == "collecting":
            return await self._handle_collecting(user_input, session_id)
        elif state["stage"] == "confirming":
            return await self._handle_confirming(user_input, session_id)
        else:
            return await self._handle_initial(user_input, intent_result, session_id)

    async def _handle_initial(
        self,
        user_input: str,
        intent_result: dict,
        session_id: str,
    ) -> dict:
        """处理初始阶段"""
        # 提取基本信息
        creation_type = intent_result.get("creation_type", "unknown")

        requirements = {
            "title": "",
            "description": user_input,
            "type": creation_type,
        }

        # 根据类型设置初始问题
        if creation_type == "dividend_processing":
            requirements["title"] = "基金分红处理流程"
            question = """我来帮您设计基金分红处理流程。请告诉我：

1. 需要处理哪些基金的分红？（全部/指定基金）
2. 分红方式是现金分红还是红利再投资？
3. 是否需要生成分红报告？"""
        else:
            question = """请描述您想要创建的业务流程：

1. 这个流程要解决什么问题？
2. 涉及哪些数据或系统？
3. 预期的输出结果是什么？"""

        # 更新状态
        self._conversation_state[session_id] = {
            "stage": "collecting",
            "requirements": requirements,
            "questions_asked": 1,
        }

        return {
            "success": True,
            "status": "collecting",
            "message": question,
            "requirements": requirements,
        }

    async def _handle_collecting(
        self,
        user_input: str,
        session_id: str,
    ) -> dict:
        """处理需求收集阶段"""
        state = self._conversation_state.get(session_id, {})
        requirements = state.get("requirements", {})
        questions_asked = state.get("questions_asked", 0)

        # 使用LLM分析用户回答，提取需求信息
        extracted = await self._extract_requirements(user_input, requirements)
        requirements.update(extracted)

        # 检查是否收集足够信息
        if questions_asked >= 2 or self._has_enough_info(requirements):
            # 生成SIPOC
            sipoc = await self.sipoc_generator.generate_from_requirements(requirements)

            # 更新状态到确认阶段
            self._conversation_state[session_id] = {
                "stage": "confirming",
                "requirements": requirements,
                "sipoc": sipoc,
            }

            sipoc_md = self.sipoc_generator.render_markdown(sipoc)

            return {
                "success": True,
                "status": "confirming",
                "message": f"Based on your requirements, I designed the following process:\n\n{sipoc_md}\n\nPlease confirm if correct (reply 'confirm' to continue, or describe changes needed)",
                "sipoc": sipoc.to_dict(),
                "requirements": requirements,
            }

        # 继续收集
        follow_up = await self._generate_follow_up_question(requirements)

        state["requirements"] = requirements
        state["questions_asked"] = questions_asked + 1
        self._conversation_state[session_id] = state

        return {
            "success": True,
            "status": "collecting",
            "message": follow_up,
            "requirements": requirements,
        }

    async def _handle_confirming(
        self,
        user_input: str,
        session_id: str,
    ) -> dict:
        """处理确认阶段"""
        state = self._conversation_state.get(session_id, {})
        sipoc = state.get("sipoc")
        requirements = state.get("requirements", {})

        # 检查是否确认
        confirm_keywords = ["confirm", "ok", "yes", "correct", "good"]
        if any(kw in user_input.lower() for kw in confirm_keywords):
            # 清理会话状态
            del self._conversation_state[session_id]

            return {
                "success": True,
                "status": "confirmed",
                "message": "Process confirmed! Now creating the corresponding service...",
                "sipoc": sipoc.to_dict() if sipoc else None,
                "requirements": requirements,
            }

        # 用户要求修改
        # 使用LLM理解修改需求
        modified_requirements = await self._extract_requirements(user_input, requirements)
        requirements.update(modified_requirements)

        # 重新生成SIPOC
        new_sipoc = await self.sipoc_generator.generate_from_requirements(requirements)
        state["sipoc"] = new_sipoc
        state["requirements"] = requirements
        self._conversation_state[session_id] = state

        sipoc_md = self.sipoc_generator.render_markdown(new_sipoc)

        return {
            "success": True,
            "status": "confirming",
            "message": f"Process updated based on your feedback:\n\n{sipoc_md}\n\nPlease confirm if correct?",
            "sipoc": new_sipoc.to_dict(),
            "requirements": requirements,
        }

    async def _extract_requirements(
        self,
        user_input: str,
        current_requirements: dict,
    ) -> dict:
        """从用户输入提取需求信息"""
        prompt = f"""Based on user's answer, extract business process requirements.

Current collected requirements:
{json.dumps(current_requirements, ensure_ascii=False, indent=2)}

User answer: "{user_input}"

Please extract and return JSON format requirements including:
- title: Process title (if user provides)
- description: Process description
- supplier: Data source list
- input: Input parameters list
- process_steps: Processing steps
- output: Output results list
- customer: User/consumer list

Only return newly extracted info, don't repeat existing info. Return JSON only."""

        try:
            response = await self._call_llm(prompt, temperature=0.3)
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start != -1 and json_end > json_start:
                return json.loads(response[json_start:json_end])
        except Exception as e:
            print(f"Failed to extract requirements: {e}")

        return {}

    async def _generate_follow_up_question(self, requirements: dict) -> str:
        """生成跟进问题"""
        missing = []
        if not requirements.get("supplier"):
            missing.append("data source")
        if not requirements.get("input"):
            missing.append("input parameters")
        if not requirements.get("output"):
            missing.append("output results")

        if missing:
            return f"Need more info about: {', '.join(missing)}. Please provide details."

        return "Any other details to add?"

    def _has_enough_info(self, requirements: dict) -> bool:
        """检查是否收集了足够的信息"""
        required_fields = ["title", "description"]
        return all(requirements.get(field) for field in required_fields)

    def clear_session(self, session_id: str):
        """清理会话状态"""
        if session_id in self._conversation_state:
            del self._conversation_state[session_id]
