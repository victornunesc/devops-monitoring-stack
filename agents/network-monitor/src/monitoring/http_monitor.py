"""
HTTP monitoring module
"""
import time
import logging
from typing import Dict, Any

import httpx

from src.metrics import MetricsManager

logger = logging.getLogger(__name__)


class HTTPMonitor:
    """HTTP monitor for page load time and return codes"""
    
    def __init__(self, metrics_manager: MetricsManager):
        """
        Initializes the HTTP monitor
        
        Args:
            metrics_manager: Metrics manager
        """
        self.metrics = metrics_manager
    
    async def check(self, target: str, timeout: float = 10.0) -> Dict[str, Any]:
        """
        Performs HTTP check on a target
                
        Args:
            target: Target hostname
            timeout: Request timeout in seconds
            
        Returns:
            Dict with HTTP request information
        """
        url = f"https://{target}"
        
        try:
            start_time = time.time()
            
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                response = await client.get(url)
            
            duration_ms = (time.time() - start_time) * 1000
            
            self.metrics.http_duration.record(
                duration_ms,
                {
                    "target": target,
                    "http.method": "GET",
                    "http.status_code": response.status_code
                }
            )
            
            self.metrics.http_status.add(
                1,
                {
                    "target": target,
                    "http.method": "GET",
                    "http.status_code": response.status_code
                }
            )
            
            logger.info(
                f"HTTP check - Target: {target}, "
                f"Status: {response.status_code}, "
                f"Duration: {duration_ms:.2f}ms"
            )
            
            return {
                "target": target,
                "url": url,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "content_length": len(response.content)
            }
            
        except httpx.TimeoutException:
            logger.error(f"HTTP timeout for {target}")
            return {"target": target, "error": "timeout"}

        except Exception as e:
            logger.error(f"HTTP check error for {target}: {e}")
            return {"target": target, "error": str(e)}
