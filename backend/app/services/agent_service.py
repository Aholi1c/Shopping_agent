from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
import asyncio
import json
import uuid
from ..models.models import Agent, AgentTask, AgentCollaboration
from ..models.schemas import (
    AgentCreate, AgentResponse, TaskCreate, TaskResponse, TaskStatus,
    AgentCollaborationCreate, AgentCollaborationResponse, CollaborationType
)
from ..services.llm_service import get_llm_service
from ..services.memory_service import MemoryService
import logging

logger = logging.getLogger(__name__)

class BaseAgent:
    """基础Agent类"""
    def __init__(self, agent_id: int, config: Dict[str, Any]):
        self.agent_id = agent_id
        self.config = config
        self.capabilities = config.get("capabilities", [])

    async def execute_task(self, task_data: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行任务的具体实现"""
        raise NotImplementedError

    def can_handle_task(self, task_type: str) -> bool:
        """检查是否能处理特定类型的任务"""
        return task_type in self.capabilities

class ResearcherAgent(BaseAgent):
    """研究员Agent - 专门处理信息收集和分析任务"""
    async def execute_task(self, task_data: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        query = task_data.get("query", "")
        search_type = task_data.get("search_type", "general")
        depth = task_data.get("depth", "basic")

        # 构建研究员提示
        research_prompt = f"""
        You are a research agent. Conduct thorough research on the following query:

        Query: {query}
        Search Type: {search_type}
        Research Depth: {depth}

        Provide a comprehensive research report including:
        1. Key findings
        2. Data sources
        3. Analysis and insights
        4. Recommendations
        5. References

        Format your response as a structured JSON report.
        """

        llm_service = get_llm_service()
        response = await llm_service.chat_completion([
            {"role": "system", "content": "You are an expert research agent."},
            {"role": "user", "content": research_prompt}
        ])

        return {
            "type": "research",
            "query": query,
            "report": response["content"],
            "sources": ["LLM Knowledge Base"],
            "timestamp": datetime.utcnow().isoformat()
        }

class AnalystAgent(BaseAgent):
    """分析师Agent - 专门处理数据分析和洞察任务"""
    async def execute_task(self, task_data: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        data = task_data.get("data", [])
        analysis_type = task_data.get("analysis_type", "general")
        objective = task_data.get("objective", "analyze the data")

        # 构建分析师提示
        analysis_prompt = f"""
        You are a data analysis expert. Analyze the following data:

        Data: {json.dumps(data, indent=2)}
        Analysis Type: {analysis_type}
        Objective: {objective}

        Provide detailed analysis including:
        1. Data summary
        2. Key patterns and trends
        3. Statistical insights
        4. Recommendations
        5. Visualizations suggestions

        Format your response as a structured analysis report.
        """

        llm_service = get_llm_service()
        response = await llm_service.chat_completion([
            {"role": "system", "content": "You are an expert data analyst."},
            {"role": "user", "content": analysis_prompt}
        ])

        return {
            "type": "analysis",
            "analysis_type": analysis_type,
            "insights": response["content"],
            "timestamp": datetime.utcnow().isoformat()
        }

class WriterAgent(BaseAgent):
    """写作Agent - 专门处理内容创作任务"""
    async def execute_task(self, task_data: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        content_type = task_data.get("content_type", "general")
        topic = task_data.get("topic", "")
        style = task_data.get("style", "professional")
        length = task_data.get("length", "medium")

        # 构建写作提示
        writing_prompt = f"""
        You are a professional writer. Create {content_type} content on the following topic:

        Topic: {topic}
        Style: {style}
        Length: {length}

        Context from previous work: {json.dumps(context or {})}

        Write engaging and informative content that:
        1. Addresses the topic comprehensively
        2. Maintains the specified style
        3. Is appropriate for the target audience
        4. Provides unique insights
        """

        llm_service = get_llm_service()
        response = await llm_service.chat_completion([
            {"role": "system", "content": f"You are a professional {style} writer."},
            {"role": "user", "content": writing_prompt}
        ])

        return {
            "type": "writing",
            "content_type": content_type,
            "topic": topic,
            "content": response["content"],
            "style": style,
            "timestamp": datetime.utcnow().isoformat()
        }

class CoordinatorAgent(BaseAgent):
    """协调Agent - 专门处理多Agent协调任务"""
    def __init__(self, agent_id: int, config: Dict[str, Any], agent_service: 'AgentService'):
        super().__init__(agent_id, config)
        self.agent_service = agent_service

    async def execute_task(self, task_data: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        collaboration_type = task_data.get("collaboration_type", "sequential")
        participants = task_data.get("participants", [])
        workflow = task_data.get("workflow", {})
        main_task = task_data.get("main_task", {})

        results = {}

        if collaboration_type == "sequential":
            results = await self._execute_sequential_workflow(participants, workflow, main_task)
        elif collaboration_type == "parallel":
            results = await self._execute_parallel_workflow(participants, workflow, main_task)
        elif collaboration_type == "hierarchical":
            results = await self._execute_hierarchical_workflow(participants, workflow, main_task)

        return {
            "type": "coordination",
            "collaboration_type": collaboration_type,
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def _execute_sequential_workflow(self, participants: List[int], workflow: Dict[str, Any], main_task: Dict[str, Any]) -> Dict[str, Any]:
        """执行顺序工作流"""
        results = {}
        context_data = main_task.get("context", {})

        for i, agent_id in enumerate(participants):
            agent_task = workflow.get(f"agent_{i+1}", {})
            agent_task.update({"context": context_data})

            result = await self.agent_service.execute_agent_task(agent_id, agent_task)
            results[f"agent_{agent_id}"] = result

            # 更新上下文
            if result.get("success"):
                context_data.update(result.get("output", {}))

        return results

    async def _execute_parallel_workflow(self, participants: List[int], workflow: Dict[str, Any], main_task: Dict[str, Any]) -> Dict[str, Any]:
        """执行并行工作流"""
        tasks = []

        for i, agent_id in enumerate(participants):
            agent_task = workflow.get(f"agent_{i+1}", {})
            agent_task.update({"context": main_task.get("context", {})})

            task = asyncio.create_task(
                self.agent_service.execute_agent_task(agent_id, agent_task)
            )
            tasks.append((f"agent_{agent_id}", task))

        # 等待所有任务完成
        results = {}
        for agent_name, task in tasks:
            try:
                result = await task
                results[agent_name] = result
            except Exception as e:
                logger.error(f"Error in parallel task {agent_name}: {e}")
                results[agent_name] = {"error": str(e)}

        return results

    async def _execute_hierarchical_workflow(self, participants: List[int], workflow: Dict[str, Any], main_task: Dict[str, Any]) -> Dict[str, Any]:
        """执行层级工作流"""
        # 简化的层级工作流实现
        coordinator_id = participants[0]
        worker_ids = participants[1:]

        # 先执行协调任务
        coordinator_result = await self.agent_service.execute_agent_task(
            coordinator_id,
            workflow.get("coordinator_task", {})
        )

        # 根据协调结果执行工作任务
        worker_tasks = []
        for worker_id in worker_ids:
            worker_task = workflow.get(f"worker_task_{worker_id}", {})
            worker_task.update({"coordination_result": coordinator_result.get("output", {})})

            task = asyncio.create_task(
                self.agent_service.execute_agent_task(worker_id, worker_task)
            )
            worker_tasks.append((f"worker_{worker_id}", task))

        results = {"coordinator": coordinator_result}
        for worker_name, task in worker_tasks:
            try:
                result = await task
                results[worker_name] = result
            except Exception as e:
                logger.error(f"Error in hierarchical task {worker_name}: {e}")
                results[worker_name] = {"error": str(e)}

        return results

class AgentService:
    """Agent服务管理类"""
    def __init__(self, db: Session):
        self.db = db
        self.agent_instances: Dict[int, BaseAgent] = {}
        self._initialize_agents()

    def _initialize_agents(self):
        """初始化所有Agent实例"""
        agents = self.db.query(Agent).filter(Agent.is_active == True).all()

        for agent in agents:
            agent_instance = self._create_agent_instance(agent)
            if agent_instance:
                self.agent_instances[agent.id] = agent_instance

    def _create_agent_instance(self, agent: Agent) -> Optional[BaseAgent]:
        """根据Agent类型创建实例"""
        try:
            if agent.agent_type == "researcher":
                return ResearcherAgent(agent.id, agent.config)
            elif agent.agent_type == "analyst":
                return AnalystAgent(agent.id, agent.config)
            elif agent.agent_type == "writer":
                return WriterAgent(agent.id, agent.config)
            elif agent.agent_type == "coordinator":
                return CoordinatorAgent(agent.id, agent.config, self)
            else:
                logger.warning(f"Unknown agent type: {agent.agent_type}")
                return None
        except Exception as e:
            logger.error(f"Error creating agent instance: {e}")
            return None

    async def create_agent(self, agent_data: AgentCreate) -> AgentResponse:
        """创建新的Agent"""
        try:
            agent = Agent(
                name=agent_data.name,
                description=agent_data.description,
                agent_type=agent_data.agent_type,
                capabilities=agent_data.capabilities,
                config=agent_data.config or {},
                is_active=True
            )

            self.db.add(agent)
            self.db.commit()
            self.db.refresh(agent)

            # 创建Agent实例
            agent_instance = self._create_agent_instance(agent)
            if agent_instance:
                self.agent_instances[agent.id] = agent_instance

            return AgentResponse.from_orm(agent)

        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to create agent: {e}")

    async def create_task(self, task_data: TaskCreate) -> TaskResponse:
        """创建任务"""
        try:
            task = AgentTask(
                task_id=str(uuid.uuid4()),
                agent_id=task_data.agent_id,
                session_id=task_data.session_id,
                task_type=task_data.task_type,
                task_data=task_data.task_data,
                status=TaskStatus.PENDING
            )

            self.db.add(task)
            self.db.commit()
            self.db.refresh(task)

            # 异步执行任务
            asyncio.create_task(self._execute_task(task.id))

            return TaskResponse.from_orm(task)

        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to create task: {e}")

    async def execute_agent_task(self, agent_id: int, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """直接执行Agent任务"""
        agent_instance = self.agent_instances.get(agent_id)
        if not agent_instance:
            raise Exception(f"Agent {agent_id} not found or not active")

        try:
            result = await agent_instance.execute_task(task_data)
            return {"success": True, "output": result}
        except Exception as e:
            logger.error(f"Error executing agent task: {e}")
            return {"success": False, "error": str(e)}

    async def _execute_task(self, task_id: int):
        """异步执行任务"""
        try:
            task = self.db.query(AgentTask).filter(AgentTask.id == task_id).first()
            if not task:
                return

            # 更新任务状态
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.utcnow()
            self.db.commit()

            # 执行任务
            agent_instance = self.agent_instances.get(task.agent_id)
            if agent_instance:
                result = await agent_instance.execute_task(task.task_data)

                task.result = {"success": True, "output": result}
                task.status = TaskStatus.COMPLETED
            else:
                task.result = {"success": False, "error": "Agent not found"}
                task.status = TaskStatus.FAILED

            task.completed_at = datetime.utcnow()
            self.db.commit()

        except Exception as e:
            logger.error(f"Error executing task {task_id}: {e}")
            # 更新任务状态为失败
            task = self.db.query(AgentTask).filter(AgentTask.id == task_id).first()
            if task:
                task.status = TaskStatus.FAILED
                task.error_message = str(e)
                task.completed_at = datetime.utcnow()
                self.db.commit()

    async def create_collaboration(self, collaboration_data: AgentCollaborationCreate) -> AgentCollaborationResponse:
        """创建Agent协作"""
        try:
            collaboration = AgentCollaboration(
                session_id=collaboration_data.session_id,
                collaboration_type=collaboration_data.collaboration_type,
                participants=collaboration_data.participants,
                workflow=collaboration_data.workflow,
                status="active"
            )

            self.db.add(collaboration)
            self.db.commit()
            self.db.refresh(collaboration)

            # 异步执行协作
            asyncio.create_task(self._execute_collaboration(collaboration.id))

            return AgentCollaborationResponse.from_orm(collaboration)

        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to create collaboration: {e}")

    async def _execute_collaboration(self, collaboration_id: int):
        """异步执行协作"""
        try:
            collaboration = self.db.query(AgentCollaboration).filter(
                AgentCollaboration.id == collaboration_id
            ).first()

            if not collaboration:
                return

            # 创建协调任务
            coordinator_task = TaskCreate(
                agent_id=1,  # 假设ID为1的是协调Agent
                session_id=collaboration.session_id,
                task_type="collaboration",
                task_data={
                    "collaboration_type": collaboration.collaboration_type,
                    "participants": collaboration.participants,
                    "workflow": collaboration.workflow,
                    "main_task": collaboration.workflow.get("main_task", {})
                }
            )

            result = await self.execute_agent_task(coordinator_task.agent_id, coordinator_task.task_data)

            collaboration.result = result
            collaboration.status = "completed"
            collaboration.completed_at = datetime.utcnow()
            self.db.commit()

        except Exception as e:
            logger.error(f"Error executing collaboration {collaboration_id}: {e}")
            collaboration = self.db.query(AgentCollaboration).filter(
                AgentCollaboration.id == collaboration_id
            ).first()
            if collaboration:
                collaboration.status = "failed"
                collaboration.result = {"error": str(e)}
                collaboration.completed_at = datetime.utcnow()
                self.db.commit()

    def get_agent_tasks(self, session_id: str, limit: int = 50) -> List[TaskResponse]:
        """获取会话的任务列表"""
        tasks = self.db.query(AgentTask).filter(
            AgentTask.session_id == session_id
        ).order_by(AgentTask.created_at.desc()).limit(limit).all()

        return [TaskResponse.from_orm(task) for task in tasks]

    def get_active_agents(self) -> List[AgentResponse]:
        """获取活跃的Agent列表"""
        agents = self.db.query(Agent).filter(Agent.is_active == True).all()
        return [AgentResponse.from_orm(agent) for agent in agents]

# 全局Agent服务实例（需要通过依赖注入使用）
def get_agent_service(db: Session) -> AgentService:
    return AgentService(db)