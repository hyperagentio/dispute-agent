"""
Cross-validation service using Web3
Integrates Hedera EVM contracts with AI-powered validation
"""
import logging
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

from web3_hedera_helper import HederaWeb3Helper, REGISTRY_MODULE_ABI, JOBS_MODULE_ABI

logger = logging.getLogger(__name__)


@dataclass
class JobDetails:
    """Job details from JobsModule contract"""
    creator: str
    agent_id: int
    budget: int
    description: str
    state: int
    created_at: int
    accept_deadline: int
    complete_deadline: int
    multihop_id: bytes
    step: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "creator": self.creator,
            "agent_id": self.agent_id,
            "budget": self.budget,
            "description": self.description,
            "state": self.state,
            "created_at": self.created_at,
            "accept_deadline": self.accept_deadline,
            "complete_deadline": self.complete_deadline,
            "multihop_id": f"0x{self.multihop_id.hex()}",
            "step": self.step
        }


class ValidationService:
    """Service for cross-validation using Hedera contracts and AI"""
    
    # Contract addresses (EVM addresses)
    REGISTRY_MODULE_EVM = "0xa041ec83d30ef5f7ffc4bc7a62bf1aaeee5544b6"
    
    def __init__(self, web3_helper: HederaWeb3Helper, jobs_module_address: str):
        """
        Initialize validation service
        
        Args:
            web3_helper: Configured HederaWeb3Helper instance
            jobs_module_address: JobsModule contract EVM address (0x...)
        """
        self.w3 = web3_helper
        self.jobs_module_address = jobs_module_address
        
        # Get event signature
        self.cross_validation_event_sig = HederaWeb3Helper.get_event_signature(
            "CrossValidationRequested(bytes32,uint256)"
        )
        
        logger.info(f"Validation service initialized")
        logger.info(f"Registry Module: {self.REGISTRY_MODULE_EVM}")
        logger.info(f"Jobs Module: {jobs_module_address}")
        logger.info(f"Event signature: {self.cross_validation_event_sig}")
    
    def check_event_in_transaction(
        self,
        tx_hash: str,
        job_id: str,
        verifier_agent_id: Optional[int] = None
    ) -> bool:
        """
        Check if CrossValidationRequested event exists in a specific transaction
        
        Args:
            tx_hash: Transaction hash
            job_id: Job ID as hex string (with or without 0x)
            verifier_agent_id: Optional verifier agent ID to match
            
        Returns:
            True if event exists with matching parameters
        """
        logger.info(f"Checking transaction {tx_hash} for CrossValidationRequested")
        
        try:
            # Get logs from transaction
            logs = self.w3.get_logs_from_transaction(
                tx_hash,
                self.cross_validation_event_sig
            )
            
            # Ensure job_id has 0x prefix
            if not job_id.startswith("0x"):
                job_id = f"0x{job_id}"
            
            # Pad to bytes32 if needed
            job_id_padded = job_id.ljust(66, '0')  # 0x + 64 chars
            
            # Check each event
            for log in logs:
                # For CrossValidationRequested(bytes32 jobID, uint256 indexed verifierAgentId)
                # - Topic[0] = event signature
                # - Topic[1] = verifierAgentId (indexed)
                # - Data = jobID (not indexed)
                
                # The jobID should be in the data field
                log_data = log['data']
                if not log_data.startswith("0x"):
                    log_data = f"0x{log_data}"
                
                # Compare job IDs
                if log_data.lower() == job_id_padded.lower():
                    logger.info("Job ID matches!")
                    
                    # If verifier_agent_id specified, check it
                    if verifier_agent_id is not None:
                        # Topic[1] should be the indexed verifierAgentId
                        if len(log['topics']) >= 2:
                            event_verifier_id = int(log['topics'][1], 16)
                            if event_verifier_id == verifier_agent_id:
                                logger.info(f"Verifier agent ID matches: {verifier_agent_id}")
                                return True
                            else:
                                logger.warning(f"Verifier ID mismatch: got {event_verifier_id}, expected {verifier_agent_id}")
                        else:
                            logger.warning("No verifier agent ID in event topics")
                    else:
                        return True
            
            logger.warning("Event not found or parameters don't match")
            return False
            
        except Exception as e:
            logger.error(f"Error checking event: {e}", exc_info=True)
            return False
    
    def get_job_details(self, job_id: str) -> Optional[JobDetails]:
        """
        Fetch job details from JobsModule contract
        
        Args:
            job_id: Job ID as hex string (with or without 0x)
            
        Returns:
            JobDetails object or None if job not found
        """
        logger.info(f"Fetching job details for {job_id}")
        
        try:
            # Convert job_id to bytes32
            job_id_bytes = HederaWeb3Helper.hex_to_bytes32(job_id)
            
            # Call getJob function
            result = self.w3.call_contract_function(
                contract_address=self.jobs_module_address,
                function_name="getJob",
                function_abi=JOBS_MODULE_ABI["getJob_function"],
                args=[job_id_bytes]
            )
            
            # Parse result tuple
            # (address creator, uint256 agentId, uint256 budget, string description,
            #  uint8 state, uint64 createdAt, uint64 acceptDeadline, uint64 completeDeadline,
            #  bytes32 multihopId, uint64 step)
            
            job = JobDetails(
                creator=result[0],
                agent_id=result[1],
                budget=result[2],
                description=result[3],
                state=result[4],
                created_at=result[5],
                accept_deadline=result[6],
                complete_deadline=result[7],
                multihop_id=result[8],
                step=result[9]
            )
            
            logger.info(f"Job details retrieved: agent_id={job.agent_id}")
            return job
            
        except Exception as e:
            logger.error(f"Error fetching job details: {e}", exc_info=True)
            return None
    
    def record_reputation_score(
        self,
        agent_id: int,
        verifier_agent_id: int,
        score: int
    ) -> str:
        """
        Record cross-validation reputation score on RegistryModule
        
        Args:
            agent_id: Agent ID being validated
            verifier_agent_id: Verifier agent ID
            score: Reputation score (0-100)
            
        Returns:
            Transaction hash
        """
        logger.info(f"Recording reputation score: agent={agent_id}, verifier={verifier_agent_id}, score={score}")
        
        # Validate score
        if not 0 <= score <= 100:
            raise ValueError(f"Score must be between 0 and 100, got {score}")
        
        # Execute transaction
        tx_hash = self.w3.execute_contract_function(
            contract_address=self.REGISTRY_MODULE_EVM,
            function_name="recordCrossValidationReputationScore",
            function_abi=REGISTRY_MODULE_ABI["recordCrossValidationReputationScore_function"],
            args=[agent_id, verifier_agent_id, score],
            gas_limit=500000
        )
        
        logger.info(f"Reputation score recorded, tx: {tx_hash}")
        return tx_hash
    
    def build_ai_context(self, job: JobDetails) -> str:
        """
        Build context prompt for AI validation
        
        Args:
            job: Job details
            
        Returns:
            Context string for AI
        """
        context = f"""Job Validation Context:

Job ID: {job.multihop_id.hex()}
Creator: {job.creator}
Agent ID: {job.agent_id}
Budget: {job.budget} (in smallest unit)
Description: {job.description}
State: {job.state}
Created At: {job.created_at} (timestamp)
Accept Deadline: {job.accept_deadline} (timestamp)
Complete Deadline: {job.complete_deadline} (timestamp)
Multihop ID: {job.multihop_id.hex()}
Step: {job.step}

Your task is to evaluate the quality and completion of this job based on the description and context provided.
Provide a reputation score from 0 to 100, where:
- 0-20: Poor quality or incomplete
- 21-40: Below average
- 41-60: Average
- 61-80: Good quality
- 81-100: Excellent quality

Consider factors such as:
1. Job description clarity
2. Completion status (based on state)
3. Budget appropriateness
4. Timeline adherence

Respond with ONLY a number between 0 and 100.
"""
        return context

