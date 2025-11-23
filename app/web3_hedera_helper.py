"""
Web3 Helper for Hedera EVM
Utilities for interacting with EVM contracts on Hedera using web3py
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from web3 import Web3
from eth_account import Account
from eth_account.signers.local import LocalAccount

logger = logging.getLogger(__name__)


class HederaWeb3Helper:
    """Helper for interacting with Hedera EVM using web3py"""
    
    # Hedera testnet RPC endpoints
    HEDERA_TESTNET_RPC = "https://testnet.hashio.io/api"
    HEDERA_MAINNET_RPC = "https://mainnet.hashio.io/api"
    
    def __init__(self, private_key: str, network: str = "testnet"):
        """
        Initialize Web3 helper for Hedera
        
        Args:
            private_key: Private key as hex string (with or without 0x)
            network: "testnet" or "mainnet"
        """
        # Get RPC endpoint
        if network == "mainnet":
            rpc_url = self.HEDERA_MAINNET_RPC
        else:
            rpc_url = self.HEDERA_TESTNET_RPC
        
        # Initialize Web3
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        # Setup account
        if not private_key.startswith("0x"):
            private_key = f"0x{private_key}"
        
        self.account: LocalAccount = Account.from_key(private_key)
        self.address = self.account.address
        
        logger.info(f"Web3 initialized for Hedera {network}")
        logger.info(f"Connected: {self.w3.is_connected()}")
        logger.info(f"Account: {self.address}")
    
    def get_balance(self, address: Optional[str] = None) -> int:
        """
        Get HBAR balance in wei (1 HBAR = 10^18 wei)
        
        Args:
            address: Address to check, defaults to account address
            
        Returns:
            Balance in wei
        """
        addr = address or self.address
        return self.w3.eth.get_balance(addr)
    
    def get_balance_hbar(self, address: Optional[str] = None) -> float:
        """
        Get HBAR balance
        
        Args:
            address: Address to check, defaults to account address
            
        Returns:
            Balance in HBAR
        """
        wei = self.get_balance(address)
        return self.w3.from_wei(wei, 'ether')
    
    def call_contract_function(
        self,
        contract_address: str,
        function_name: str,
        function_abi: Dict,
        args: List[Any] = None
    ) -> Any:
        """
        Call a read-only contract function (view/pure)
        
        Args:
            contract_address: Contract address (0x... or 0.0.xxxxx gets converted)
            function_name: Function name
            function_abi: Function ABI (single function from contract ABI)
            args: Function arguments
            
        Returns:
            Function return value
        """
        # Convert Hedera ID to EVM address if needed
        contract_addr = self._to_evm_address(contract_address)
        
        # Build contract instance
        contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(contract_addr),
            abi=[function_abi]
        )
        
        # Get function
        func = contract.functions[function_name]
        
        # Call function
        if args:
            result = func(*args).call()
        else:
            result = func().call()
        
        return result
    
    def execute_contract_function(
        self,
        contract_address: str,
        function_name: str,
        function_abi: Dict,
        args: List[Any] = None,
        gas_limit: int = 500000,
        value: int = 0
    ) -> str:
        """
        Execute a state-changing contract function
        
        Args:
            contract_address: Contract address
            function_name: Function name
            function_abi: Function ABI
            args: Function arguments
            gas_limit: Gas limit
            value: ETH/HBAR value to send (in wei)
            
        Returns:
            Transaction hash
        """
        # Convert address
        contract_addr = self._to_evm_address(contract_address)
        
        # Build contract
        contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(contract_addr),
            abi=[function_abi]
        )
        
        # Get function
        func = contract.functions[function_name]
        
        # Build transaction
        if args:
            transaction = func(*args).build_transaction({
                'from': self.address,
                'gas': gas_limit,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.address),
                'value': value
            })
        else:
            transaction = func().build_transaction({
                'from': self.address,
                'gas': gas_limit,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.address),
                'value': value
            })
        
        # Sign transaction
        signed = self.account.sign_transaction(transaction)
        
        # Send transaction (handle both old and new web3.py versions)
        raw_tx = getattr(signed, 'rawTransaction', None) or getattr(signed, 'raw_transaction', None)
        tx_hash = self.w3.eth.send_raw_transaction(raw_tx)
        
        # Wait for receipt
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        logger.info(f"Transaction executed: {tx_hash.hex()}")
        logger.info(f"Gas used: {receipt['gasUsed']}")
        
        return tx_hash.hex()
    
    def get_transaction_receipt(self, tx_hash: str) -> Dict:
        """
        Get transaction receipt
        
        Args:
            tx_hash: Transaction hash
            
        Returns:
            Transaction receipt
        """
        return dict(self.w3.eth.get_transaction_receipt(tx_hash))
    
    def get_logs(
        self,
        contract_address: str,
        event_abi: Dict,
        from_block: int = 0,
        to_block: str = 'latest',
        argument_filters: Dict = None
    ) -> List[Dict]:
        """
        Get event logs from contract
        
        Args:
            contract_address: Contract address
            event_abi: Event ABI
            from_block: Starting block
            to_block: Ending block
            argument_filters: Filter by indexed arguments
            
        Returns:
            List of event logs
        """
        contract_addr = self._to_evm_address(contract_address)
        
        contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(contract_addr),
            abi=[event_abi]
        )
        
        event = contract.events[event_abi['name']]
        
        logs = event.get_logs(
            fromBlock=from_block,
            toBlock=to_block,
            argument_filters=argument_filters
        )
        
        return [dict(log) for log in logs]
    
    def get_logs_from_transaction(
        self,
        tx_hash: str,
        event_signature: Optional[str] = None
    ) -> List[Dict]:
        """
        Get event logs from a specific transaction
        
        Args:
            tx_hash: Transaction hash
            event_signature: Optional event signature hash to filter
            
        Returns:
            List of parsed event logs
        """
        receipt = self.w3.eth.get_transaction_receipt(tx_hash)
        
        logs = []
        for log in receipt['logs']:
            if event_signature:
                # Check if first topic matches event signature
                if log['topics'] and log['topics'][0].hex() == event_signature:
                    logs.append({
                        'address': log['address'],
                        'topics': [t.hex() for t in log['topics']],
                        'data': log['data'].hex(),
                        'blockNumber': log['blockNumber'],
                        'transactionHash': log['transactionHash'].hex()
                    })
            else:
                logs.append({
                    'address': log['address'],
                    'topics': [t.hex() for t in log['topics']],
                    'data': log['data'].hex(),
                    'blockNumber': log['blockNumber'],
                    'transactionHash': log['transactionHash'].hex()
                })
        
        return logs
    
    def _to_evm_address(self, address: str) -> str:
        """
        Convert Hedera account ID to EVM address or return EVM address as-is
        
        Args:
            address: Hedera ID (0.0.xxxxx) or EVM address (0x...)
            
        Returns:
            EVM address
        """
        # If already EVM address, return as-is
        if address.startswith("0x"):
            return address
        
        # If Hedera account ID format (0.0.xxxxx)
        if "." in address:
            # For now, just return as-is and let the user provide EVM address
            # In production, you'd query mirror node for EVM address
            raise ValueError(
                f"Please provide EVM address instead of Hedera ID: {address}\n"
                "You can get the EVM address from HashScan or mirror node API"
            )
        
        return address
    
    @staticmethod
    def get_event_signature(event_signature_string: str) -> str:
        """
        Get keccak256 hash of event signature
        
        Args:
            event_signature_string: Event signature (e.g., "Transfer(address,address,uint256)")
            
        Returns:
            Event signature hash with 0x prefix
        """
        return Web3.keccak(text=event_signature_string).hex()
    
    @staticmethod
    def bytes32_to_hex(value: bytes) -> str:
        """Convert bytes32 to hex string"""
        if isinstance(value, bytes):
            return f"0x{value.hex()}"
        return value
    
    @staticmethod
    def hex_to_bytes32(hex_str: str) -> bytes:
        """Convert hex string to bytes32"""
        if hex_str.startswith("0x"):
            hex_str = hex_str[2:]
        return bytes.fromhex(hex_str.zfill(64))


# Contract ABIs for the specific contracts
REGISTRY_MODULE_ABI = {
    "CrossValidationRequested_event": {
        "anonymous": False,
        "inputs": [
            {"indexed": False, "name": "jobID", "type": "bytes32"},
            {"indexed": True, "name": "verifierAgentId", "type": "uint256"}
        ],
        "name": "CrossValidationRequested",
        "type": "event"
    },
    "recordCrossValidationReputationScore_function": {
        "inputs": [
            {"name": "agentId", "type": "uint256"},
            {"name": "verifierAgentId", "type": "uint256"},
            {"name": "score", "type": "uint256"}
        ],
        "name": "recordCrossValidationReputationScore",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
}

JOBS_MODULE_ABI = {
    "getJob_function": {
        "inputs": [
            {"name": "jobId", "type": "bytes32"}
        ],
        "name": "getJob",
        "outputs": [{
            "type": "tuple",
            "name": "",
            "components": [
                {"type": "address", "name": "creator"},
                {"type": "uint256", "name": "agentId"},
                {"type": "uint256", "name": "budget"},
                {"type": "string", "name": "description"},
                {"type": "uint8", "name": "state"},
                {"type": "uint64", "name": "createdAt"},
                {"type": "uint64", "name": "acceptDeadline"},
                {"type": "uint64", "name": "completeDeadline"},
                {"type": "bytes32", "name": "multihopId"},
                {"type": "uint64", "name": "step"}
            ]
        }],
        "stateMutability": "view",
        "type": "function"
    }
}

