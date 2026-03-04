"""
Simple Agent Test Script

Tests each agent individually to verify they work correctly before testing the full workflow.
"""

import os
import asyncio
from dotenv import load_dotenv
from azure.identity import AzureCliCredential
from azure.ai.agents import AgentsClient
from agent_framework.azure import AzureAIAgentClient


async def test_individual_agent(agent_name: str, agent_id: str, test_input: str):
    """
    Test a single agent with a specific input.
    
    Args:
        agent_name: Name of the agent
        agent_id: Agent ID in Foundry
        test_input: Input text to test the agent with
    """
    print(f"\n{'='*60}")
    print(f"TESTING: {agent_name}")
    print(f"Agent ID: {agent_id}")
    print(f"{'='*60}")
    print(f"Input: {test_input}\n")
    
    load_dotenv()
    project_endpoint = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
    model_deployment_name = os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME")
    
    try:
        # Create AzureAIAgentClient
        async with AzureAIAgentClient(
            credential=AzureCliCredential(),
            project_endpoint=project_endpoint,
            model_deployment_name=model_deployment_name
        ) as client:
            
            # Wrap the agent
            agent = client.as_agent(
                agent_id=agent_id,
                name=agent_name
            )
            
            # Run the agent and get the result
            print("Running agent...")
            result = await agent.run(test_input)
            
            # Display results
            print(f"\n{'-'*60}")
            print("RESPONSE:")
            print(f"{'-'*60}\n")
            
            # Extract the response text
            if hasattr(result, 'messages'):
                for message in result.messages:
                    if hasattr(message, 'content'):
                        if isinstance(message.content, str):
                            print(message.content)
                        elif isinstance(message.content, list):
                            for item in message.content:
                                if hasattr(item, 'text'):
                                    print(item.text)
                                else:
                                    print(str(item))
                    elif hasattr(message, 'text'):
                        print(message.text)
            elif hasattr(result, 'content'):
                print(result.content)
            elif hasattr(result, 'text'):
                print(result.text)
            else:
                print(f"Result type: {type(result)}")
                print(f"Result: {result}")
            
            print(f"\n{'-'*60}")
            print(f"✓ {agent_name} test completed successfully")
            print(f"{'-'*60}\n")
            
            return True
            
    except Exception as e:
        print(f"\n❌ ERROR testing {agent_name}:")
        print(f"   {type(e).__name__}: {str(e)}")
        print(f"{'-'*60}\n")
        return False


async def test_all_agents():
    """Test all agents individually."""
    
    print("\n" + "="*60)
    print("SIMPLE AGENT TEST SUITE")
    print("="*60)
    
    # Load environment
    load_dotenv()
    
    # Get existing agents from Foundry
    print("\nRetrieving agent IDs from Azure AI Foundry...")
    
    project_endpoint = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
    agents_client = AgentsClient(
        endpoint=project_endpoint,
        credential=AzureCliCredential()
    )
    
    # List all agents and find ours
    all_agents = agents_client.list_agents()
    agent_map = {}
    
    for agent in all_agents:
        if agent.name in [
            'testcasegenerator_master_agent',
            'testcasegenerator_requirement_reviewer_agent',
            'testcasegenerator_testcasegenerator_agent',
            'testcasegenerator_enhance_agent',
            'testcasegenerator_migration_agent'
        ]:
            agent_map[agent.name] = agent.id
            print(f"  Found: {agent.name} (ID: {agent.id})")
    
    if not agent_map:
        print("\n❌ No agents found. Please run agent_orchestrator.py first to create agents.")
        return
    
    print(f"\n✓ Found {len(agent_map)} agents to test\n")
    
    # Test cases for each agent
    test_cases = {
        'testcasegenerator_requirement_reviewer_agent': """
        Please review this requirement:
        "Users should be able to login with email and password. Password must be at least 8 characters."
        """,
        
        'testcasegenerator_testcasegenerator_agent': """
        Generate 3 test cases for this requirement:
        "Users should be able to login with email and password"
        """,
        
        'testcasegenerator_enhance_agent': """
        Enhance this basic test case:
        Test Case: User Login
        Steps: 1. Enter email 2. Enter password 3. Click login
        Expected: User is logged in
        """,
        
        'testcasegenerator_migration_agent': """
        Convert this test case to Jira format:
        Test Case ID: TC001
        Title: User Login Test
        Steps: Enter credentials and click login
        Expected: Successful login
        """,
        
        'testcasegenerator_master_agent': """
        I need help creating a test plan for a login feature.
        The requirements are: email/password authentication with 8 character minimum password.
        """
    }
    
    # Test each agent
    results = {}
    
    for agent_name, test_input in test_cases.items():
        if agent_name in agent_map:
            success = await test_individual_agent(
                agent_name=agent_name,
                agent_id=agent_map[agent_name],
                test_input=test_input
            )
            results[agent_name] = success
        else:
            print(f"⚠️  Skipping {agent_name} - not found in Foundry")
            results[agent_name] = False
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for agent_name, success in results.items():
        status = "✓ PASS" if success else "❌ FAIL"
        print(f"{status}: {agent_name}")
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    
    print(f"\nTotal: {passed_tests}/{total_tests} tests passed")
    print("="*60 + "\n")


async def test_single_agent_quick():
    """Quick test of a single agent for debugging."""
    
    print("\n" + "="*60)
    print("QUICK SINGLE AGENT TEST")
    print("="*60 + "\n")
    
    load_dotenv()
    
    # Get requirement reviewer agent
    project_endpoint = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
    agents_client = AgentsClient(
        endpoint=project_endpoint,
        credential=AzureCliCredential()
    )
    
    print("Finding requirement_reviewer_agent...")
    all_agents = agents_client.list_agents()
    
    reqreviewer_agent = None
    for agent in all_agents:
        if agent.name == 'testcasegenerator_requirement_reviewer_agent':
            reqreviewer_agent = agent
            break
    
    if not reqreviewer_agent:
        print("❌ requirement_reviewer_agent not found. Run agent_orchestrator.py first.")
        return
    
    print(f"✓ Found agent: {reqreviewer_agent.name} (ID: {reqreviewer_agent.id})\n")
    
    # Test the agent
    await test_individual_agent(
        agent_name=reqreviewer_agent.name,
        agent_id=reqreviewer_agent.id,
        test_input="Review this requirement: Users can login with email and password"
    )


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        # Quick test mode
        print("Running in QUICK TEST mode (single agent)")
        asyncio.run(test_single_agent_quick())
    else:
        # Full test mode
        print("Running in FULL TEST mode (all agents)")
        print("Use --quick flag for single agent test\n")
        asyncio.run(test_all_agents())
