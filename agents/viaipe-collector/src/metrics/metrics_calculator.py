"""
Metrics calculation module
"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class MetricsCalculator:
    """Quality metrics calculator"""
    
    @staticmethod
    def calculate_availability(smoke_data: Dict[str, Any]) -> float:
        """
        Calculates client average availability

        Formula: 100 - avg_loss (based on smoke ping)
        
        Args:
            smoke_data: Client smoke ping data
            
        Returns:
            Availability in percentage (0-100)
        """
        try:
            avg_loss = float(smoke_data.get('avg_loss', 0))
            availability = 100.0 - avg_loss
            return max(0.0, min(availability, 100.0))  # Clamp between 0-100
            
        except Exception as e:
            logger.error(f"Error calculating availability: {e}")
            return 0.0
    
    @staticmethod
    def calculate_bandwidth_stats(interfaces: list) -> Dict[str, float]:
        """
        Calculates bandwidth consumption statistics
                
        Args:
            interfaces: Client interfaces list
            
        Returns:
            Dict with avg_in, avg_out, max_in, max_out in bps
        """
        try:
            if not interfaces:
                return {'avg_in': 0, 'avg_out': 0, 'max_in': 0, 'max_out': 0}
            
            # Sum data from all client interfaces
            total_avg_in = sum(float(iface.get('avg_in', 0)) for iface in interfaces)
            total_avg_out = sum(float(iface.get('avg_out', 0)) for iface in interfaces)
            total_max_in = sum(float(iface.get('max_in', 0)) for iface in interfaces)
            total_max_out = sum(float(iface.get('max_out', 0)) for iface in interfaces)
            
            return {
                'avg_in': total_avg_in,
                'avg_out': total_avg_out,
                'max_in': total_max_in,
                'max_out': total_max_out
            }
            
        except Exception as e:
            logger.error(f"Error calculating bandwidth stats: {e}")
            return {'avg_in': 0, 'avg_out': 0, 'max_in': 0, 'max_out': 0}
    
    @staticmethod
    def calculate_quality_score(
        availability: float,
        smoke_data: Dict[str, Any]
    ) -> float:
        """
        Calculates connection quality score
                
        Formula: Weighted score (0-100)
        - Availability: 50% (100 - avg_loss)
        - Latency: 30% (lower latency = better score)
        - Current Packet Loss: 20% (lower loss = better score)
        
        Args:
            availability: Availability in %
            smoke_data: Smoke ping data (val, loss)
            
        Returns:
            Quality score (0-100)
        """
        try:
            # 1. Availability Score (already normalized 0-100)
            availability_score = availability
            
            # 2. Latency Score
            # val is current latency in ms
            # Assuming: 0-50ms = excellent, 50-100ms = good, >100ms = poor
            latency = float(smoke_data.get('val', 0))
            if latency <= 50:
                latency_score = 100
            elif latency <= 100:
                latency_score = 100 - ((latency - 50) * 2)  # Decays from 100 to 0
            else:
                latency_score = max(0, 100 - latency)
            
            # 3. Current Packet Loss Score
            # loss is current loss in %
            loss = float(smoke_data.get('loss', 0))
            loss_score = max(0, 100 - (loss * 10))  # 10% loss = score 0
            
            # Weights
            weights = {
                'availability': 0.5,
                'latency': 0.3,
                'loss': 0.2
            }
            
            # Final score
            quality_score = (
                availability_score * weights['availability'] +
                latency_score * weights['latency'] +
                loss_score * weights['loss']
            )
            
            return min(quality_score, 100.0)
            
        except Exception as e:
            logger.error(f"Error calculating quality score: {e}")
            return 0.0
