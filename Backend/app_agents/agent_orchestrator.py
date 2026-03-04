"""
Agent Orchestrator

This module manages the creation and orchestration of all agents in the test case generation system.
It uses Microsoft Agent Framework with Azure AI Foundry to create and coordinate multiple specialized agents.
"""

import os
import asyncio
from typing import List, Optional
from dotenv import load_dotenv
from azure.identity import AzureCliCredential
from azure.ai.agents import AgentsClient
from agent_framework.azure import AzureAIAgentClient
from agent_framework.orchestrations import HandoffBuilder
from agent_framework.orchestrations import HandoffAgentUserRequest
from agent_framework import MCPStreamableHTTPTool, AgentResponse, AgentResponseUpdate

# Import agent definitions
from . import master_agent
from . import reqreviewer_agent
from . import testcasegenerator_agent
from . import enhance_agent
from . import migration_agent

MASTER_AGENT_NAME = master_agent.AGENT_NAME
MASTER_INSTRUCTIONS = master_agent.AGENT_INSTRUCTIONS
REQREVIEWER_AGENT_NAME = reqreviewer_agent.AGENT_NAME
REQREVIEWER_INSTRUCTIONS = reqreviewer_agent.AGENT_INSTRUCTIONS
TESTGEN_AGENT_NAME = testcasegenerator_agent.AGENT_NAME
TESTGEN_INSTRUCTIONS = testcasegenerator_agent.AGENT_INSTRUCTIONS
ENHANCE_AGENT_NAME = enhance_agent.AGENT_NAME
ENHANCE_INSTRUCTIONS = enhance_agent.AGENT_INSTRUCTIONS
MIGRATION_AGENT_NAME = migration_agent.AGENT_NAME
MIGRATION_INSTRUCTIONS = migration_agent.AGENT_INSTRUCTIONS


class AgentOrchestrator:
    """
    Orchestrator for managing all agents in the test case generation workflow.
    
    This class handles:
    - Creating/retrieving agents in Azure AI Foundry
    - Setting up the GroupChat workflow
    - Running the workflow with different inputs
    
    Each instance can run independently in different threads/sessions.
    """
    
    def __init__(self):
        """Initialize the orchestrator with Azure credentials and configuration."""
        load_dotenv()
        
        self.credential = AzureCliCredential()
        self.project_endpoint = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
        self.model_deployment_name = os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME")
        
        if not self.project_endpoint or not self.model_deployment_name:
            raise ValueError(
                "Missing required environment variables: "
                "AZURE_AI_PROJECT_ENDPOINT and AZURE_AI_MODEL_DEPLOYMENT_NAME"
            )
        
        # Initialize AgentsClient for Foundry operations
        self.agents_client = AgentsClient(
            endpoint=self.project_endpoint,
            credential=self.credential
        )
        
        # Store agent references
        self.foundry_agents = {}
        self.workflow = None
        self.foundry_client = None
        
        # Load Jira MCP configuration (mandatory)
        self.jira_mcp_url = os.getenv("JIRA_MCP_SERVER_URL", "http://localhost:8002/mcp")
        print(f"Initializing Jira MCP tool: {self.jira_mcp_url}")
        
        # Initialize Jira MCP tool
        self.jira_mcp_tool = MCPStreamableHTTPTool(
            name="jira-mcp-server",
            description="Jira MCP server to create, update and search Jira Issues.",
            url=self.jira_mcp_url
        )
        
        print(f"✓ AgentOrchestrator instance created")
    
    async def get_or_create_agent(self, name: str, instructions: str):
        """
        Check if agent exists in Foundry, if not create it.
        
        Args:
            name: Agent name
            instructions: Agent instructions
            
        Returns:
            Agent object from Azure AI Foundry
        """
        print(f"Checking if agent '{name}' exists in Foundry...")
        
        # List all agents (run in thread pool to avoid blocking)
        existing_agents = await asyncio.to_thread(self.agents_client.list_agents)
        
        # Check if agent with this name already exists
        for agent in existing_agents:
            if agent.name == name:
                if os.getenv("UPDATE_AGENT_INSTRUCTIONS", "true").lower() == "true":
                    print(f"  ✓ Found existing agent: {agent.name} (ID: {agent.id}) — updating instructions...")
                    updated = await asyncio.to_thread(
                        self.agents_client.update_agent,
                        agent.id,
                        instructions=instructions
                    )
                    return updated
                else:
                    print(f"  ✓ Found existing agent: {agent.name} (ID: {agent.id})")
                    return agent
        
        # Agent doesn't exist, create it
        print(f"  Creating new agent '{name}'...")
        new_agent = await asyncio.to_thread(
            self.agents_client.create_agent,
            model=self.model_deployment_name,
            name=name,
            instructions=instructions,
        )
        print(f"  ✓ Created agent: {new_agent.name} (ID: {new_agent.id})")
        return new_agent
    
    async def setup_agents(self):
        """
        Set up all agents in Azure AI Foundry.
        Creates agents if they don't exist, or retrieves existing ones.
        """
        print("\n" + "="*60)
        print("SETTING UP AGENTS IN AZURE AI FOUNDRY")
        print("="*60 + "\n")
        
        # Create/get all agents in Foundry
        self.foundry_agents['master'] = await self.get_or_create_agent(
            name=MASTER_AGENT_NAME,
            instructions=MASTER_INSTRUCTIONS
        )
        
        self.foundry_agents['reqreviewer'] = await self.get_or_create_agent(
            name=REQREVIEWER_AGENT_NAME,
            instructions=REQREVIEWER_INSTRUCTIONS
        )
        
        # Create testgenerator agent with Jira integration instructions
        print(f"  Jira MCP tool will be attached to {TESTGEN_AGENT_NAME}")
        testgen_instructions = TESTGEN_INSTRUCTIONS + "\n\nJIRA INTEGRATION: You have access to Jira tools to create, update, and search Jira issues. Use them when appropriate for test case management."
        
        self.foundry_agents['testgenerator'] = await self.get_or_create_agent(
            name=TESTGEN_AGENT_NAME,
            instructions=testgen_instructions
        )
        
        self.foundry_agents['enhance'] = await self.get_or_create_agent(
            name=ENHANCE_AGENT_NAME,
            instructions=ENHANCE_INSTRUCTIONS
        )
        
        self.foundry_agents['migration'] = await self.get_or_create_agent(
            name=MIGRATION_AGENT_NAME,
            instructions=MIGRATION_INSTRUCTIONS
        )
        
        print(f"\n✓ All {len(self.foundry_agents)} agents ready in Foundry")
    
    async def initialize_workflow(self):
        """
        Initialize the GroupChat workflow with all agents.
        The master_agent serves as the orchestrator.
        """
        print("\n" + "="*60)
        print("INITIALIZING GROUPCHAT WORKFLOW")
        print("="*60 + "\n")
        
        # Create AzureAIAgentClient as context manager
        self.foundry_client = AzureAIAgentClient(
            credential=self.credential,
            project_endpoint=self.project_endpoint,
            model_deployment_name=self.model_deployment_name
        )
        
        await self.foundry_client.__aenter__()
        
        # Wrap all agents for the workflow
        print("Wrapping agents for workflow...")
        
        master_agent = self.foundry_client.as_agent(
            agent_id=self.foundry_agents['master'].id,
            name=self.foundry_agents['master'].name
        )
        
        reqreviewer_agent = self.foundry_client.as_agent(
            agent_id=self.foundry_agents['reqreviewer'].id,
            name=self.foundry_agents['reqreviewer'].name
        )
        
        # Wrap testgenerator agent with Jira MCP tool
        testgenerator_agent = self.foundry_client.as_agent(
            agent_id=self.foundry_agents['testgenerator'].id,
            name=self.foundry_agents['testgenerator'].name
            ,tools=[self.jira_mcp_tool]
        )
        print(f"  ✓ Attached Jira MCP tool to {self.foundry_agents['testgenerator'].name}")
        
        enhance_agent = self.foundry_client.as_agent(
            agent_id=self.foundry_agents['enhance'].id,
            name=self.foundry_agents['enhance'].name
        )
        
        migration_agent = self.foundry_client.as_agent(
            agent_id=self.foundry_agents['migration'].id,
            name=self.foundry_agents['migration'].name
        )
        
        # Build Handoff workflow with master_agent as start agent
        print(f"Building Handoff workflow with {MASTER_AGENT_NAME} as start agent...")
        self.workflow = (
            HandoffBuilder(
                name="testcasegenerator",
                participants=[
                    master_agent,
                    reqreviewer_agent,
                    testgenerator_agent,
                    enhance_agent,
                    migration_agent
                ],
            )
            .with_start_agent(master_agent)
            .build()
        )
        
        print("✓ Workflow initialized successfully\n")
    
    async def run_workflow(self, user_input: str) -> List:
        """
        Run the Handoff workflow with the given input using streaming events.

        Args:
            user_input: The user's request or input to process

        Returns:
            List of message dicts {'agent': str, 'content': str}
        """
        if not self.workflow:
            raise RuntimeError(
                "Workflow not initialized. Call initialize_workflow() first."
            )

        print("\n" + "="*60)
        print("RUNNING WORKFLOW")
        print("="*60)
        print(f"\nUser Input: {user_input}\n")
        print("Executing workflow (streaming)...")

        messages: List[dict] = []
        handoff_trace: List[str] = []
        current_agent: str = "Master"
        text_buffer: dict = {}   # agent_name → accumulated text
        got_streaming_text = False
        events = []

        def clean_name(raw: str) -> str:
            """Convert agent ID to a display name."""
            return (
                raw.replace('testcasegenerator_', '')
                   .replace('_agent', '')
                   .replace('_', ' ')
                   .title()
            )

        async for event in self.workflow.run(user_input, stream=True):
            events.append(event)

            # Track handoff routing
            if event.type == "handoff_sent":
                source = clean_name(getattr(event.data, 'source', 'unknown'))
                target = clean_name(getattr(event.data, 'target', 'unknown'))
                handoff_trace.append(f"{source} → {target}")
                current_agent = target
                print(f"  🔀 Handoff: {source} → {target}")

            # Streaming text chunk from an agent
            elif event.type == "output" and isinstance(event.data, AgentResponseUpdate):
                if event.data.text:
                    text_buffer.setdefault(current_agent, "")
                    text_buffer[current_agent] += event.data.text
                    got_streaming_text = True

            # Non-streaming full agent response
            elif event.type == "output" and isinstance(event.data, AgentResponse):
                for msg in event.data.messages:
                    text = getattr(msg, 'text', None)
                    if text and text.strip():
                        text_buffer.setdefault(current_agent, "")
                        text_buffer[current_agent] += text
                        got_streaming_text = True

        # Flush buffered streaming text into messages
        for agent_name, content in text_buffer.items():
            content = content.strip()
            if content:
                messages.append({'agent': agent_name, 'content': content})

        # Fallback: specialist answer may be in request_info → HandoffAgentUserRequest
        if not got_streaming_text:
            for event in events:
                if event.type == "request_info" and isinstance(
                    event.data, HandoffAgentUserRequest
                ):
                    resp = event.data.agent_response
                    if resp:
                        agent_name = clean_name(
                            getattr(event.data, 'agent_name', None)
                            or getattr(resp, 'executor_id', current_agent)
                        )
                        for msg in resp.messages:
                            text = getattr(msg, 'text', None)
                            if text and text.strip():
                                messages.append({'agent': agent_name, 'content': text.strip()})

        print("✓ Workflow execution completed")
        if handoff_trace:
            print(f"  Routing: {' → '.join(handoff_trace)}")

        return messages
    
    async def cleanup(self):
        """Clean up resources."""
        if self.foundry_client:
            await self.foundry_client.__aexit__(None, None, None)
            print("✓ Resources cleaned up")


# Convenience function for simple workflow execution
async def run_agent_testcase_workflow(user_request: str) -> List:
    """
    Convenience function to run the test case generation workflow.
    
    This function:
    1. Creates the orchestrator
    2. Sets up all agents
    3. Initializes the workflow
    4. Runs the workflow with the user request
    5. Cleans up resources
    
    Args:
        user_request: User's input/request
        
    Returns:
        List of messages from workflow execution
        
    Example:
        >>> messages = await run_testcase_workflow(
        ...     "Review these requirements and generate test cases: ..."
        ... )
    """
    orchestrator = AgentOrchestrator()
    
    
    # Setup
    await orchestrator.setup_agents()
    await orchestrator.initialize_workflow()
    
    # Run workflow
    messages = await orchestrator.run_workflow(user_request)
    
    return messages    


async def get_orchestrator() -> AgentOrchestrator:
    """
    Create and initialize a new orchestrator instance.
    
    Returns:
        AgentOrchestrator: Initialized orchestrator instance
        
    Example:
        >>> orchestrator = await get_orchestrator()
        >>> await orchestrator.run_workflow("Request 1")
        >>> await orchestrator.cleanup()
    """
    orchestrator = AgentOrchestrator()
    await orchestrator.setup_agents()
    await orchestrator.initialize_workflow()
    return orchestrator


