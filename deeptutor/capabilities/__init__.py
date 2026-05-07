"""
Capabilities Package
==================

Each module wraps an existing agent pipeline behind the ``BaseCapability`` protocol.
Capabilities represent deep modes: multi-step agent pipelines that take over
the conversation when selected.
"""

# Import built-in capabilities
from .chat import ChatCapability
from .deep_solve import DeepSolveCapability
from .deep_question import DeepQuestionCapability
from .llamaindex_agent import LlamaIndexAgentCapability
from .forensics_investigation import ForensicsInvestigationCapability
from .deep_coding import DeepCodingCapability

# Built-in capability types
BUILTIN_CAPABILITIES = {
    "chat": ChatCapability,
    "deep_solve": DeepSolveCapability,
    "deep_question": DeepQuestionCapability,
    "llamaindex_agent": LlamaIndexAgentCapability,
    "forensics_investigation": ForensicsInvestigationCapability,
    "deep_coding": DeepCodingCapability,
}

# Conditionally import EvidenceAnalysisCapability
try:
    from .evidence_analysis import EvidenceAnalysisCapability
    BUILTIN_CAPABILITIES["evidence_analysis"] = EvidenceAnalysisCapability
    _has_evidence_analysis = True
except ImportError:
    _has_evidence_analysis = False

__all__ = ["BUILTIN_CAPABILITIES", "ChatCapability", "DeepSolveCapability", 
           "DeepQuestionCapability", "LlamaIndexAgentCapability", 
           "ForensicsInvestigationCapability"]

if _has_evidence_analysis:
    __all__.append("EvidenceAnalysisCapability")
