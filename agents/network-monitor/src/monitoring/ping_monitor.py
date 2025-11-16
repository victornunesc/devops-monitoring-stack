"""
Ping monitoring module
"""
import asyncio
import logging
from typing import Dict, Any

import ping3

from src.metrics import MetricsManager

logger = logging.getLogger(__name__)


class PingMonitor:
    """Ping monitor for latency and packet loss"""
    
    def __init__(self, metrics_manager: MetricsManager):
        """
        Initializes the ping monitor
        
        Args:
            metrics_manager: Metrics manager
        """
        self.metrics = metrics_manager
    
    async def check(self, target: str, ping_count: int = 10, timeout: float = 2.0) -> Dict[str, Any]:
        """
        Performs ping check on a target
                
        Args:
            target: Target hostname or IP
            ping_count: Number of pings to execute
            timeout: Timeout in seconds for each ping
            
        Returns:
            Dict with ping statistics
        """
        try:
            successful_pings = 0
            total_rtt = 0
            
            for _ in range(ping_count):
                try:
                    ping_in_secs = ping3.ping(target, timeout=timeout)
                    
                    if ping_in_secs is not None:
                        successful_pings += 1
                        rtt_ms = ping_in_secs * 1000
                        total_rtt += rtt_ms
                        
                        self.metrics.ping_rtt.record(
                            rtt_ms,
                            {"target": target}
                        )
                    
                    await asyncio.sleep(0.1)  # 100ms
                    
                except Exception as e:
                    logger.warning(f"Ping failed for {target}: {e}")
            
            packet_loss = ((ping_count - successful_pings) / ping_count) * 100
            avg_rtt = total_rtt / successful_pings if successful_pings > 0 else 0
            
            self.metrics.ping_packet_loss.record(
                packet_loss,
                {"target": target}
            )
            
            logger.info(
                f"Ping check - Target: {target}, "
                f"RTT: {avg_rtt:.2f}ms, "
                f"Packet Loss: {packet_loss:.1f}%"
            )
            
            return {
                "target": target,
                "avg_rtt_ms": avg_rtt,
                "packet_loss_percent": packet_loss,
                "successful_pings": successful_pings,
                "total_pings": ping_count
            }
            
        except Exception as e:
            logger.error(f"Ping check error for {target}: {e}")
            return {"target": target, "error": str(e)}
