#!/usr/bin/env python3
"""
TruGrade Desktop API Client
Professional API communication for the revolutionary desktop app

COPY TO: /home/dewster/TruGrade/desktop_app/api_client.py
"""

import aiohttp
import asyncio
import json
import base64
from typing import Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class TruGradeAPIClient:
    """
    Professional API client for TruGrade Desktop App
    Handles all communication with the revolutionary backend
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if TruGrade backend is running"""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"status": "error", "message": f"HTTP {response.status}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        try:
            async with self.session.get(f"{self.base_url}/api/system/status") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"status": "error", "message": f"HTTP {response.status}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def load_card(self, image_path: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Load Card API call - preserves revolutionary_card_manager.py functionality
        """
        try:
            # Read image file
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # Encode image as base64
            image_b64 = base64.b64encode(image_data).decode('utf-8')
            
            payload = {
                "image_data": image_b64,
                "image_path": str(image_path),
                "options": options or {}
            }
            
            async with self.session.post(
                f"{self.base_url}/api/card/load",
                json=payload
            ) as response:
                return await response.json()
                
        except Exception as e:
            logger.error(f"Load card failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def calibrate_border(self, calibration_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Border Calibration API call - preserves revolutionary_border_calibration.py functionality
        """
        try:
            async with self.session.post(
                f"{self.base_url}/api/calibration/border",
                json=calibration_data
            ) as response:
                return await response.json()
                
        except Exception as e:
            logger.error(f"Border calibration failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def full_analysis(self, card_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Full Analysis API call - preserves enhanced_revo_card_manager.py functionality
        """
        try:
            async with self.session.post(
                f"{self.base_url}/api/analysis/full",
                json=card_data
            ) as response:
                return await response.json()
                
        except Exception as e:
            logger.error(f"Full analysis failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def grade_card(self, image_data: bytes, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Revolutionary card grading with TruScore engine
        """
        try:
            # Encode image as base64
            image_b64 = base64.b64encode(image_data).decode('utf-8')
            
            payload = {
                "image_data": image_b64,
                "metadata": metadata or {}
            }
            
            async with self.session.post(
                f"{self.base_url}/api/grade/card",
                json=payload
            ) as response:
                return await response.json()
                
        except Exception as e:
            logger.error(f"Card grading failed: {e}")
            return {"status": "error", "message": str(e)}

# Synchronous wrapper for desktop app
class TruGradeAPI:
    """Synchronous wrapper for desktop app usage"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    def _run_async(self, coro):
        """Run async function synchronously"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(coro)
    
    async def _execute_with_client(self, func, *args, **kwargs):
        """Execute function with API client"""
        async with TruGradeAPIClient(self.base_url) as client:
            return await func(client, *args, **kwargs)
    
    def health_check(self) -> Dict[str, Any]:
        """Synchronous health check"""
        return self._run_async(
            self._execute_with_client(lambda client: client.health_check())
        )
    
    def system_status(self) -> Dict[str, Any]:
        """Synchronous system status"""
        return self._run_async(
            self._execute_with_client(lambda client: client.system_status())
        )
    
    def load_card(self, image_path: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Synchronous load card"""
        return self._run_async(
            self._execute_with_client(lambda client: client.load_card(image_path, options))
        )
    
    def calibrate_border(self, calibration_data: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous border calibration"""
        return self._run_async(
            self._execute_with_client(lambda client: client.calibrate_border(calibration_data))
        )
    
    def full_analysis(self, card_data: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous full analysis"""
        return self._run_async(
            self._execute_with_client(lambda client: client.full_analysis(card_data))
        )
    
    def grade_card(self, image_path: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Synchronous card grading"""
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        return self._run_async(
            self._execute_with_client(lambda client: client.grade_card(image_data, metadata))
        )