"""
TruGrade Photometric Stereo System
=================================

Revolutionary photometric stereo analysis for TruScore grading.
Transferred from RCG with full functionality intact.
"""

from .photometric_stereo import RevolutionaryPhotometricStereo, PhotometricResult
from .photometric_integration import RevolutionaryPhotometricIntegration

__all__ = [
    'RevolutionaryPhotometricStereo',
    'PhotometricResult', 
    'RevolutionaryPhotometricIntegration'
]