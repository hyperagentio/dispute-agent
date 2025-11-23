#!/usr/bin/env python3
"""Test script to verify Hedera Agent Kit setup"""
import asyncio
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.client.network import Network
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.account.account_id import AccountId
from hedera_agent_kit_py import HederaAgentAPI, Configuration, ToolDiscovery
from hedera_agent_kit_py.shared.configuration import Context

# Your credentials
ACCOUNT_ID = "0.0.7306947"
PRIVATE_KEY = "0x22031d463eda96ebc465b649d31375cd22bd2eefc6c09bcd97da753cbb61e49a"
HEDERA_NETWORK = "testnet"  # Change to "mainnet" if needed


async def test_hedera_setup():
    """Test basic Hedera Agent Kit functionality"""
    
    print("🔧 Setting up Hedera Client...")
    
    # Create network
    network = Network(network=HEDERA_NETWORK)
    
    # Create client
    client = Client(network=network)
    
    # Set operator (your account credentials)
    private_key = PrivateKey.from_string_ecdsa(PRIVATE_KEY)
    account_id = AccountId.from_string(ACCOUNT_ID)
    client.set_operator(account_id, private_key)
    
    print(f"✅ Connected to {HEDERA_NETWORK}")
    print(f"📋 Account ID: {ACCOUNT_ID}")
    print(f"🔑 Private Key: {PRIVATE_KEY[:10]}...")
    
    # Create context
    context = Context(
        account_id=ACCOUNT_ID,
        account_public_key=private_key.public_key().to_string_raw()
    )
    
    # Discover available tools
    print("\n🔍 Discovering available tools...")
    config = Configuration(context=context)
    tool_discovery = ToolDiscovery.create_from_configuration(config)
    tools = tool_discovery.get_all_tools(context, config)
    
    print(f"✅ Found {len(tools)} tools:")
    for tool in tools[:10]:  # Show first 10
        print(f"  - {tool.method}: {tool.description[:80]}...")
    
    if len(tools) > 10:
        print(f"  ... and {len(tools) - 10} more tools")
    
    # Create agent API
    agent = HederaAgentAPI(client=client, context=context, tools=tools)
    
    print("\n✅ Hedera Agent Kit is ready!")
    print("\nAvailable tool categories:")
    categories = set()
    for tool in tools:
        category = tool.method.split('_')[0]
        categories.add(category)
    for cat in sorted(categories):
        print(f"  - {cat}")
    
    # Test a simple query (get account balance)
    print("\n🧪 Testing account balance query...")
    try:
        result = await agent.run("getAccountBalance", {"accountId": ACCOUNT_ID})
        print(f"✅ Balance check successful!")
        print(f"   Result: {result}")
    except Exception as e:
        print(f"❌ Balance check failed: {e}")
    
    return agent, tools


if __name__ == "__main__":
    asyncio.run(test_hedera_setup())

