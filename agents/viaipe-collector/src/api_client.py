"""
ViaIpe API client module
"""
import logging
from typing import List, Dict, Any

import httpx

logger = logging.getLogger(__name__)


class ViaIpeClient:
    """Client to consume the ViaIpe API"""
    
    def __init__(self, api_url: str, timeout: int = 30):
        self.api_url = api_url
        self.timeout = timeout
    
    async def fetch_data(self) -> List[Dict[str, Any]]:
        """
        Fetches data from ViaIpe API
        
        Returns:
            List with API data or empty list on error
        """
        try:
            logger.info(f"Fetching data from ViaIpe API: {self.api_url}")
            
            async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
                response = await client.get(self.api_url)
                response.raise_for_status()
            
            data = response.json()
            
            if isinstance(data, list):
                logger.info(f"Successfully fetched ViaIpe data: {len(data)} clients")
            else:
                logger.warning(f"Unexpected data format: {type(data)}")
            return data
            
        except httpx.TimeoutException:
            logger.error("ViaIpe API timeout")
            raise
            
        except httpx.HTTPStatusError as e:
            logger.error(f"ViaIpe API HTTP error: {e.response.status_code}")
            raise
            
        except Exception as e:
            logger.error(f"ViaIpe API error: {e}")
            raise
