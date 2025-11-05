"""
Pipeline Executor - 5-stage AI orchestration pipeline
Powered by MindsDB agents and enhanced with GETLOOD intelligence
"""

import json
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import logging

from ..adapters.mindsdb_client import MindsDBClient
from ..adapters.agent_adapter import AgentAdapter, AgentResponse
from ..adapters.knowledge_base_adapter import KnowledgeBaseAdapter

logger = logging.getLogger(__name__)


class IntentType(str, Enum):
    """Supported intent types"""
    CREATE_WORKFLOW = "CREATE_WORKFLOW"
    ANALYZE_DATA = "ANALYZE_DATA"
    GENERATE_UI = "GENERATE_UI"
    CHAT = "CHAT"
    OS_CONTROL = "OS_CONTROL"
    CODE_GENERATION = "CODE_GENERATION"
    BROWSER_NAVIGATION = "BROWSER_NAVIGATION"
    COMPUTER_USE = "COMPUTER_USE"
    CLARIFICATION_NEEDED = "CLARIFICATION_NEEDED"


class RoutingMode(str, Enum):
    """Routing modes"""
    WORKFLOW_MODE = "WORKFLOW_MODE"
    REASONING_MODE = "REASONING_MODE"
    STREAMING_CHAT_MODE = "STREAMING_CHAT_MODE"
    DIRECT_AGENT_MODE = "DIRECT_AGENT_MODE"


class ReasoningMethod(str, Enum):
    """Reasoning methods"""
    COT = "CoT"  # Chain of Thought
    TOT = "ToT"  # Tree of Thoughts
    REACT = "ReAct"  # Reasoning + Acting


@dataclass
class Ambiguity:
    """Represents ambiguous intent"""
    is_ambiguous: bool
    candidates: List[Dict[str, Any]] = field(default_factory=list)
    clarification_question: str = ""
    quick_replies: List[str] = field(default_factory=list)


@dataclass
class DetectedIntent:
    """Result of intent detection stage"""
    intent_type: IntentType
    confidence: float
    parameters: Dict[str, Any] = field(default_factory=dict)
    needs_reasoning: bool = False
    ambiguity: Optional[Ambiguity] = None


@dataclass
class RoutingDecision:
    """Result of routing stage"""
    mode: RoutingMode
    reasoning_method: Optional[ReasoningMethod] = None
    rationale: str = ""


@dataclass
class SelectedAgent:
    """Result of agent selection stage"""
    agent_id: str
    agent_name: str
    confidence: float
    capabilities: List[str] = field(default_factory=list)
    selection_rationale: str = ""


@dataclass
class TheoryOfMind:
    """Theory of Mind analysis"""
    user_goal: str
    emotional_context: str  # 'frustrated', 'curious', 'confident', etc.
    next_likely_intent: str
    expertise_level: str  # 'beginner', 'intermediate', 'expert'


@dataclass
class NeuralUI:
    """Neural UI generation"""
    suggested_components: List[str] = field(default_factory=list)
    interaction_patterns: List[str] = field(default_factory=list)
    action_buttons: List[Dict[str, Any]] = field(default_factory=list)
    quick_replies: List[str] = field(default_factory=list)


@dataclass
class ContextAwareness:
    """Context awareness data"""
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    workspace_state: Dict[str, Any] = field(default_factory=dict)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Enhancement:
    """Stage 5 enhancement"""
    theory_of_mind: TheoryOfMind
    neural_ui: NeuralUI
    context: ContextAwareness


@dataclass
class ExecutionContext:
    """Context for pipeline execution"""
    user_id: str
    session_id: str
    project: str = "mindsdb"
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    workspace_state: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineResult:
    """Complete pipeline result"""
    id: str
    message: str
    intent: Optional[DetectedIntent] = None
    routing: Optional[RoutingDecision] = None
    selected_agent: Optional[SelectedAgent] = None
    agent_response: Optional[AgentResponse] = None
    enhancement: Optional[Enhancement] = None
    enhanced_response: str = ""
    needs_clarification: bool = False
    execution_time_ms: float = 0
    tokens_used: int = 0
    cost_usd: float = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class StageBase:
    """Base class for pipeline stages"""

    def __init__(self, name: str):
        self.name = name

    async def process(
        self,
        result: PipelineResult,
        context: ExecutionContext
    ) -> PipelineResult:
        """Process this stage"""
        raise NotImplementedError


class IntentDetectionStage(StageBase):
    """Stage 1: Detect user intent"""

    def __init__(self, client: MindsDBClient, agent_adapter: AgentAdapter):
        super().__init__("IntentDetection")
        self.client = client
        self.agent_adapter = agent_adapter

    async def process(
        self,
        result: PipelineResult,
        context: ExecutionContext
    ) -> PipelineResult:
        """Detect intent using MindsDB agent"""
        logger.info(f"[Stage 1] Detecting intent for: {result.message[:50]}...")

        try:
            # Query intent detection agent
            # This agent is pre-configured with function calling to return structured JSON
            intent_agent_name = "intent_detector"

            # Build prompt with conversation history
            history_context = ""
            if context.conversation_history:
                history_context = "\n".join([
                    f"{msg['role']}: {msg['content']}"
                    for msg in context.conversation_history[-5:]  # Last 5 messages
                ])

            prompt = f"""
Analyze the user's message and detect their intent.

User message: {result.message}

Conversation history:
{history_context}

Return a JSON object with:
- intent_type: One of {[i.value for i in IntentType]}
- confidence: Float between 0 and 1
- parameters: Dict of extracted parameters
- needs_reasoning: Boolean (true if complex reasoning needed)
- ambiguity: Object with is_ambiguous, candidates, clarification_question, quick_replies (if ambiguous)
"""

            response = await self.agent_adapter.query_agent(
                agent_name=intent_agent_name,
                message=prompt,
                session_id=context.session_id,
                project=context.project
            )

            # Parse JSON response
            intent_data = json.loads(response.message)

            # Build DetectedIntent
            ambiguity = None
            if intent_data.get("ambiguity", {}).get("is_ambiguous"):
                amb_data = intent_data["ambiguity"]
                ambiguity = Ambiguity(
                    is_ambiguous=True,
                    candidates=amb_data.get("candidates", []),
                    clarification_question=amb_data.get("clarification_question", ""),
                    quick_replies=amb_data.get("quick_replies", [])
                )

            detected_intent = DetectedIntent(
                intent_type=IntentType(intent_data["intent_type"]),
                confidence=float(intent_data["confidence"]),
                parameters=intent_data.get("parameters", {}),
                needs_reasoning=intent_data.get("needs_reasoning", False),
                ambiguity=ambiguity
            )

            result.intent = detected_intent

            # If ambiguous, mark for clarification
            if ambiguity and ambiguity.is_ambiguous:
                result.needs_clarification = True
                result.enhanced_response = ambiguity.clarification_question

            logger.info(f"[Stage 1] Detected intent: {detected_intent.intent_type} (confidence: {detected_intent.confidence:.2f})")

        except Exception as e:
            logger.error(f"[Stage 1] Intent detection failed: {str(e)}")
            # Fallback to CHAT intent
            result.intent = DetectedIntent(
                intent_type=IntentType.CHAT,
                confidence=0.5,
                needs_reasoning=False
            )

        return result


class RoutingStage(StageBase):
    """Stage 2: Route to appropriate mode"""

    def __init__(self):
        super().__init__("Routing")

    async def process(
        self,
        result: PipelineResult,
        context: ExecutionContext
    ) -> PipelineResult:
        """Route based on intent"""
        logger.info(f"[Stage 2] Routing intent: {result.intent.intent_type}")

        if not result.intent:
            result.routing = RoutingDecision(
                mode=RoutingMode.STREAMING_CHAT_MODE,
                rationale="No intent detected, defaulting to chat"
            )
            return result

        intent = result.intent.intent_type

        # Routing logic
        if intent in [IntentType.CREATE_WORKFLOW, IntentType.GENERATE_UI]:
            mode = RoutingMode.WORKFLOW_MODE
            reasoning = ReasoningMethod.TOT  # Tree of Thoughts for creative tasks
            rationale = "Complex creation task requires workflow orchestration"

        elif intent == IntentType.ANALYZE_DATA:
            mode = RoutingMode.REASONING_MODE
            reasoning = ReasoningMethod.COT  # Chain of Thought for analysis
            rationale = "Data analysis requires step-by-step reasoning"

        elif intent in [IntentType.OS_CONTROL, IntentType.COMPUTER_USE]:
            mode = RoutingMode.DIRECT_AGENT_MODE
            reasoning = ReasoningMethod.REACT  # ReAct for interactive tasks
            rationale = "Direct agent control with real-time feedback"

        elif intent == IntentType.CHAT:
            mode = RoutingMode.STREAMING_CHAT_MODE
            reasoning = None
            rationale = "Simple chat interaction"

        else:
            mode = RoutingMode.REASONING_MODE
            reasoning = ReasoningMethod.COT
            rationale = "Default reasoning mode"

        result.routing = RoutingDecision(
            mode=mode,
            reasoning_method=reasoning,
            rationale=rationale
        )

        logger.info(f"[Stage 2] Routed to: {mode} (reasoning: {reasoning})")

        return result


class AgentSelectionStage(StageBase):
    """Stage 3: Select optimal agent"""

    def __init__(self, agent_adapter: AgentAdapter):
        super().__init__("AgentSelection")
        self.agent_adapter = agent_adapter

    async def process(
        self,
        result: PipelineResult,
        context: ExecutionContext
    ) -> PipelineResult:
        """Select best agent for the task"""
        logger.info(f"[Stage 3] Selecting agent for intent: {result.intent.intent_type}")

        try:
            # Map intent to required capabilities
            required_capabilities = self._map_intent_to_capabilities(result.intent.intent_type)

            # Query available agents with matching capabilities
            agents = await self.agent_adapter.list_agents(project=context.project)

            # Filter by capabilities
            matching_agents = [
                agent for agent in agents
                if any(cap in agent.skills for cap in required_capabilities)
            ]

            if not matching_agents:
                # Use default chat agent
                logger.warning("[Stage 3] No matching agents found, using default")
                result.selected_agent = SelectedAgent(
                    agent_id="default_chat_agent",
                    agent_name="chat",
                    confidence=0.5,
                    capabilities=["chat"],
                    selection_rationale="No specialized agent available"
                )
            else:
                # Select agent with highest performance score
                # (In production, this would use more sophisticated scoring)
                best_agent = matching_agents[0]

                result.selected_agent = SelectedAgent(
                    agent_id=best_agent.id,
                    agent_name=best_agent.name,
                    confidence=0.9,
                    capabilities=best_agent.skills,
                    selection_rationale=f"Agent specialized in {', '.join(required_capabilities)}"
                )

            logger.info(f"[Stage 3] Selected agent: {result.selected_agent.agent_name}")

        except Exception as e:
            logger.error(f"[Stage 3] Agent selection failed: {str(e)}")
            result.selected_agent = SelectedAgent(
                agent_id="default_chat_agent",
                agent_name="chat",
                confidence=0.3,
                capabilities=["chat"],
                selection_rationale="Error in selection, using default"
            )

        return result

    def _map_intent_to_capabilities(self, intent: IntentType) -> List[str]:
        """Map intent to required agent capabilities"""
        mapping = {
            IntentType.CREATE_WORKFLOW: ["workflow_creation", "automation"],
            IntentType.ANALYZE_DATA: ["data_analysis", "statistics"],
            IntentType.GENERATE_UI: ["ui_generation", "react", "frontend"],
            IntentType.CHAT: ["chat", "conversation"],
            IntentType.OS_CONTROL: ["os_control", "composio"],
            IntentType.CODE_GENERATION: ["code_generation", "programming"],
            IntentType.BROWSER_NAVIGATION: ["browser", "web_automation"],
            IntentType.COMPUTER_USE: ["computer_use", "desktop_automation"]
        }
        return mapping.get(intent, ["chat"])


class ExecutionStage(StageBase):
    """Stage 4: Execute selected agent"""

    def __init__(self, agent_adapter: AgentAdapter):
        super().__init__("Execution")
        self.agent_adapter = agent_adapter

    async def process(
        self,
        result: PipelineResult,
        context: ExecutionContext
    ) -> PipelineResult:
        """Execute agent and get response"""
        logger.info(f"[Stage 4] Executing agent: {result.selected_agent.agent_name}")

        start_time = datetime.now()

        try:
            # Build context-aware prompt
            prompt = self._build_contextual_prompt(result, context)

            # Query agent with streaming (collect all chunks)
            chunks = []
            async for chunk in self.agent_adapter.query_agent_stream(
                agent_name=result.selected_agent.agent_name,
                message=prompt,
                session_id=context.session_id,
                project=context.project
            ):
                chunks.append(chunk)

            response_text = ''.join(chunks)

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            result.agent_response = AgentResponse(
                agent_id=result.selected_agent.agent_id,
                agent_name=result.selected_agent.agent_name,
                message=response_text,
                session_id=context.session_id,
                duration_ms=duration_ms
            )

            logger.info(f"[Stage 4] Agent executed in {duration_ms:.0f}ms")

        except Exception as e:
            logger.error(f"[Stage 4] Execution failed: {str(e)}")
            result.agent_response = AgentResponse(
                agent_id=result.selected_agent.agent_id,
                agent_name=result.selected_agent.agent_name,
                message=f"Execution failed: {str(e)}",
                session_id=context.session_id
            )

        return result

    def _build_contextual_prompt(
        self,
        result: PipelineResult,
        context: ExecutionContext
    ) -> str:
        """Build prompt with full context"""
        parts = [result.message]

        # Add conversation history
        if context.conversation_history:
            parts.append("\n--- Recent conversation ---")
            for msg in context.conversation_history[-3:]:
                parts.append(f"{msg['role']}: {msg['content']}")

        # Add intent parameters
        if result.intent and result.intent.parameters:
            parts.append(f"\n--- Extracted parameters ---")
            parts.append(json.dumps(result.intent.parameters, indent=2))

        # Add workspace state
        if context.workspace_state:
            parts.append(f"\n--- Workspace context ---")
            parts.append(f"Active desktop: {context.workspace_state.get('desktop_id', 1)}")
            parts.append(f"Open windows: {len(context.workspace_state.get('windows', []))}")

        return "\n".join(parts)


class EnhancementStage(StageBase):
    """Stage 5: Enhance response with AGI features"""

    def __init__(
        self,
        client: MindsDBClient,
        kb_adapter: KnowledgeBaseAdapter
    ):
        super().__init__("Enhancement")
        self.client = client
        self.kb_adapter = kb_adapter

    async def process(
        self,
        result: PipelineResult,
        context: ExecutionContext
    ) -> PipelineResult:
        """Enhance response with Theory of Mind, Neural UI, and Context Awareness"""
        logger.info(f"[Stage 5] Enhancing response")

        try:
            # Run enhancements in parallel
            tom_task = self._generate_theory_of_mind(result, context)
            ui_task = self._generate_neural_ui(result, context)
            ctx_task = self._gather_context_awareness(context)

            tom, neural_ui, ctx_awareness = await asyncio.gather(
                tom_task,
                ui_task,
                ctx_task
            )

            result.enhancement = Enhancement(
                theory_of_mind=tom,
                neural_ui=neural_ui,
                context=ctx_awareness
            )

            # Build enhanced response
            result.enhanced_response = self._build_enhanced_response(result)

            logger.info(f"[Stage 5] Enhancement complete")

        except Exception as e:
            logger.error(f"[Stage 5] Enhancement failed: {str(e)}")
            # Fallback: use agent response as-is
            result.enhanced_response = result.agent_response.message if result.agent_response else result.message

        return result

    async def _generate_theory_of_mind(
        self,
        result: PipelineResult,
        context: ExecutionContext
    ) -> TheoryOfMind:
        """Generate Theory of Mind analysis"""
        # In production, this would use a specialized ToM model
        # For now, use heuristics based on intent and conversation

        user_goal = "Unknown goal"
        emotional_context = "neutral"
        next_likely_intent = IntentType.CHAT.value
        expertise_level = "intermediate"

        if result.intent:
            intent = result.intent.intent_type

            if intent == IntentType.CREATE_WORKFLOW:
                user_goal = "Automate a complex task"
                emotional_context = "focused"
                next_likely_intent = IntentType.ANALYZE_DATA.value

            elif intent == IntentType.GENERATE_UI:
                user_goal = "Build user interface"
                emotional_context = "creative"
                next_likely_intent = IntentType.CODE_GENERATION.value

            elif intent == IntentType.CHAT:
                user_goal = "Get information or have conversation"
                emotional_context = "curious"
                next_likely_intent = IntentType.CHAT.value

        return TheoryOfMind(
            user_goal=user_goal,
            emotional_context=emotional_context,
            next_likely_intent=next_likely_intent,
            expertise_level=expertise_level
        )

    async def _generate_neural_ui(
        self,
        result: PipelineResult,
        context: ExecutionContext
    ) -> NeuralUI:
        """Generate Neural UI elements"""
        action_buttons = []
        quick_replies = []

        if result.intent:
            intent = result.intent.intent_type

            if intent == IntentType.GENERATE_UI:
                action_buttons = [
                    {
                        "label": "Open in Editor",
                        "action": "OPEN_WINDOW",
                        "payload": {"appId": "code-editor"},
                        "style": "primary"
                    },
                    {
                        "label": "Preview",
                        "action": "OPEN_WINDOW",
                        "payload": {"appId": "browser"},
                        "style": "secondary"
                    }
                ]
                quick_replies = ["Modify colors", "Add animations", "Export code"]

            elif intent == IntentType.CREATE_WORKFLOW:
                action_buttons = [
                    {
                        "label": "Open Workflow Studio",
                        "action": "NAVIGATE",
                        "payload": {"route": "/workflow-studio"},
                        "style": "primary"
                    },
                    {
                        "label": "Execute Now",
                        "action": "EXECUTE_WORKFLOW",
                        "payload": {"workflowId": "auto-generated"},
                        "style": "secondary"
                    }
                ]
                quick_replies = ["Add trigger", "Test workflow", "Save as template"]

        return NeuralUI(
            action_buttons=action_buttons,
            quick_replies=quick_replies
        )

    async def _gather_context_awareness(
        self,
        context: ExecutionContext
    ) -> ContextAwareness:
        """Gather context awareness data"""
        return ContextAwareness(
            conversation_history=context.conversation_history,
            workspace_state=context.workspace_state,
            user_preferences=context.user_preferences,
            performance_metrics={}
        )

    def _build_enhanced_response(self, result: PipelineResult) -> str:
        """Build final enhanced response"""
        if not result.agent_response:
            return result.message

        # Base response from agent
        response = result.agent_response.message

        # Add Theory of Mind insights (subtle)
        if result.enhancement and result.enhancement.theory_of_mind:
            tom = result.enhancement.theory_of_mind
            # Don't add ToM to response, use it for internal optimization

        return response


class PipelineExecutor:
    """
    Main pipeline executor - orchestrates all 5 stages

    Example usage:
        >>> executor = PipelineExecutor(mindsdb_client)
        >>>
        >>> context = ExecutionContext(
        ...     user_id="user_123",
        ...     session_id="session_abc",
        ...     project="user_123"
        ... )
        >>>
        >>> result = await executor.execute(
        ...     user_message="Create a dashboard for sales analytics",
        ...     context=context
        ... )
        >>>
        >>> print(result.enhanced_response)
        >>> print(result.enhancement.neural_ui.action_buttons)
    """

    def __init__(
        self,
        mindsdb_client: MindsDBClient,
        agent_adapter: Optional[AgentAdapter] = None,
        kb_adapter: Optional[KnowledgeBaseAdapter] = None
    ):
        self.client = mindsdb_client

        self.agent_adapter = agent_adapter or AgentAdapter(mindsdb_client)
        self.kb_adapter = kb_adapter or KnowledgeBaseAdapter(mindsdb_client)

        # Initialize stages
        self.stages = [
            IntentDetectionStage(mindsdb_client, self.agent_adapter),
            RoutingStage(),
            AgentSelectionStage(self.agent_adapter),
            ExecutionStage(self.agent_adapter),
            EnhancementStage(mindsdb_client, self.kb_adapter)
        ]

    async def execute(
        self,
        user_message: str,
        context: ExecutionContext
    ) -> PipelineResult:
        """
        Execute full 5-stage pipeline

        Args:
            user_message: User's input message
            context: Execution context

        Returns:
            PipelineResult with enhanced response
        """
        start_time = datetime.now()

        result = PipelineResult(
            id=f"pipeline_{context.session_id}_{int(start_time.timestamp())}",
            message=user_message
        )

        logger.info(f"[Pipeline] Starting execution for: {user_message[:50]}...")

        try:
            for stage in self.stages:
                logger.info(f"[Pipeline] Executing stage: {stage.name}")
                result = await stage.process(result, context)

                # Early exit if clarification needed
                if result.needs_clarification:
                    logger.info("[Pipeline] Clarification needed, stopping early")
                    break

        except Exception as e:
            logger.error(f"[Pipeline] Execution failed: {str(e)}")
            result.enhanced_response = f"Pipeline execution failed: {str(e)}"

        # Calculate metrics
        duration = (datetime.now() - start_time).total_seconds() * 1000
        result.execution_time_ms = duration

        logger.info(f"[Pipeline] Execution complete in {duration:.0f}ms")

        return result


if __name__ == "__main__":
    from ..adapters.mindsdb_client import create_client

    async def main():
        client = create_client()
        executor = PipelineExecutor(client)

        context = ExecutionContext(
            user_id="demo_user",
            session_id="demo_session",
            project="mindsdb"
        )

        # Test message
        result = await executor.execute(
            user_message="Create a dashboard to visualize our sales data",
            context=context
        )

        print("="*60)
        print("PIPELINE RESULT")
        print("="*60)
        print(f"Intent: {result.intent.intent_type if result.intent else 'None'}")
        print(f"Routing: {result.routing.mode if result.routing else 'None'}")
        print(f"Agent: {result.selected_agent.agent_name if result.selected_agent else 'None'}")
        print(f"Execution time: {result.execution_time_ms:.0f}ms")
        print(f"\nEnhanced Response:\n{result.enhanced_response}")

        if result.enhancement and result.enhancement.neural_ui.action_buttons:
            print(f"\nAction Buttons:")
            for btn in result.enhancement.neural_ui.action_buttons:
                print(f"  - {btn['label']} ({btn['style']})")

        await client.close()

    asyncio.run(main())
