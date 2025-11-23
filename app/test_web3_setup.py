#!/usr/bin/env python3
"""
Test Web3 setup with Hedera
"""
import os
from dotenv import load_dotenv
from web3_hedera_helper import HederaWeb3Helper

load_dotenv()

PRIVATE_KEY = os.getenv("PRIVATE_KEY", "0x22031d463eda96ebc465b649d31375cd22bd2eefc6c09bcd97da753cbb61e49a")
NETWORK = os.getenv("HEDERA_NETWORK", "testnet")


def main():
    print("=" * 70)
    print("🧪 Testing Web3 Setup for Hedera")
    print("=" * 70)
    
    # Initialize Web3 helper
    print(f"\n📡 Connecting to Hedera {NETWORK}...")
    
    try:
        w3 = HederaWeb3Helper(
            private_key=PRIVATE_KEY,
            network=NETWORK
        )
        
        print(f"✅ Connected successfully!")
        print(f"\n📊 Account Information:")
        print(f"   Address: {w3.address}")
        
        # Get balance
        balance_wei = w3.get_balance()
        balance_hbar = w3.get_balance_hbar()
        
        print(f"   Balance: {balance_hbar:.6f} HBAR")
        print(f"   Balance (wei): {balance_wei}")
        
        # Test event signature generation
        print(f"\n🔍 Testing Event Signature:")
        event_sig = HederaWeb3Helper.get_event_signature(
            "CrossValidationRequested(bytes32,uint256)"
        )
        print(f"   Event: CrossValidationRequested(bytes32,uint256)")
        print(f"   Signature: {event_sig}")
        
        # Test bytes32 conversion
        print(f"\n🔄 Testing bytes32 Conversion:")
        test_hex = "0xabc123"
        test_bytes = HederaWeb3Helper.hex_to_bytes32(test_hex)
        test_hex_back = HederaWeb3Helper.bytes32_to_hex(test_bytes)
        print(f"   Input: {test_hex}")
        print(f"   bytes32: {test_bytes.hex()}")
        print(f"   Output: {test_hex_back}")
        
        print(f"\n{'=' * 70}")
        print(f"✅ All tests passed!")
        print(f"{'=' * 70}")
        
        print(f"\n💡 Next steps:")
        print(f"   1. Set JOBS_MODULE_ADDRESS in .env (EVM address, not Hedera ID)")
        print(f"   2. Start the service: uv run uvicorn main:app --reload")
        print(f"   3. Test /validate endpoint")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

