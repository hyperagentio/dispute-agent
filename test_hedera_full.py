#!/usr/bin/env python3
"""Test script to verify Hedera Agent Kit with all plugins"""
import asyncio
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.client.network import Network
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.account.account_id import AccountId
from hedera_agent_kit_py import HederaAgentAPI, Configuration, ToolDiscovery
from hedera_agent_kit_py.shared.configuration import Context

# Import all available plugins
from hedera_agent_kit_py.plugins.core_account_plugin import core_account_plugin
from hedera_agent_kit_py.plugins.core_account_query_plugin import core_account_query_plugin
from hedera_agent_kit_py.plugins.core_consensus_plugin import core_consensus_plugin
from hedera_agent_kit_py.plugins.core_consensus_query_plugin import core_consensus_query_plugin
from hedera_agent_kit_py.plugins.core_token_plugin import core_token_plugin
from hedera_agent_kit_py.plugins.core_token_query_plugin import core_token_query_plugin
from hedera_agent_kit_py.plugins.core_evm_plugin import core_evm_plugin
from hedera_agent_kit_py.plugins.core_evm_query_plugin import core_evm_query_plugin
from hedera_agent_kit_py.plugins.core_transaction_plugin import core_transaction_plugin
from hedera_agent_kit_py.plugins.core_misc_query_plugin import core_misc_query_plugin

# Your credentials
ACCOUNT_ID = "0.0.7306947"
PRIVATE_KEY = "0x22031d463eda96ebc465b649d31375cd22bd2eefc6c09bcd97da753cbb61e49a"
HEDERA_NETWORK = "testnet"  # Change to "mainnet" if needed


async def test_hedera_full_setup():
    """Test Hedera Agent Kit with all available plugins"""
    
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
    
    # List of all available plugins
    all_plugins = [
        core_account_plugin,
        core_account_query_plugin,
        core_consensus_plugin,
        core_consensus_query_plugin,
        core_token_plugin,
        core_token_query_plugin,
        core_evm_plugin,
        core_evm_query_plugin,
        core_transaction_plugin,
        core_misc_query_plugin,
    ]
    
    # Discover available tools with all plugins
    print("\n🔍 Discovering available tools...")
    config = Configuration(context=context, plugins=all_plugins)
    tool_discovery = ToolDiscovery.create_from_configuration(config)
    tools = tool_discovery.get_all_tools(context, config)
    
    print(f"✅ Found {len(tools)} tools total!")
    
    # Group tools by category
    categories = {}
    for tool in tools:
        category = tool.method.split('_tool')[0].replace('_', ' ').title()
        if category not in categories:
            categories[category] = []
        categories[category].append(tool.method)
    
    print("\n📦 Available tool categories:")
    for cat, tool_list in sorted(categories.items()):
        print(f"  {cat} ({len(tool_list)} tools)")
    
    print("\n📋 All available tools:")
    for i, tool in enumerate(tools, 1):
        desc = tool.description.split('\n')[0][:60]
        print(f"  {i:2}. {tool.method:40} - {desc}...")
    
    # Create agent API
    agent = HederaAgentAPI(client=client, context=context, tools=tools)
    
    print("\n✅ Hedera Agent Kit is fully configured and ready!")
    
    return agent, tools


if __name__ == "__main__":
    asyncio.run(test_hedera_full_setup())

