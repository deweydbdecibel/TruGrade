"""
TruGrade Core Systems
The foundational components of the TruGrade Professional Platform
"""

__version__ = "1.0.0"
__author__ = "TruGrade Technologies"
__description__ = "Revolutionary Professional Card Grading Platform"

# Core system imports
from .models import GradingResult, PhotometricResult, CornerResult

# Import revolutionary modules if available
try:
    from .grading_engine import RevolutionaryGradingEngine
    GRADING_ENGINE_AVAILABLE = True
except ImportError:
    GRADING_ENGINE_AVAILABLE = False

# Legacy imports (commented out until system module is created)
# from .trugrade_platform import TruGradePlatform
# from .truscore_engine import TruScoreEngine

__all__ = [
    "GradingResult",
    "PhotometricResult", 
    "CornerResult"
]

if GRADING_ENGINE_AVAILABLE:
    __all__.append("RevolutionaryGradingEngine")