"""
Tests for ViaIpe API client
"""
import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock

from src.api_client import ViaIpeClient


@pytest.mark.asyncio
class TestViaIpeClient:
    """Test suite for ViaIpeClient"""

    @pytest.fixture
    def client(self):
        """Create a ViaIpe client instance"""
        return ViaIpeClient(
            api_url="https://test-api.example.com/api",
            timeout=30
        )

    @pytest.fixture
    def sample_api_data(self):
        """Sample API response data"""
        return [
            {
                "id": "client1",
                "name": "Client 1",
                "data": {
                    "smoke": {
                        "val": 25.5,
                        "loss": 0.5,
                        "avg_loss": 1.2
                    },
                    "interfaces": [
                        {
                            "name": "eth0",
                            "avg_in": 1000000,
                            "avg_out": 500000,
                            "max_in": 2000000,
                            "max_out": 1000000
                        }
                    ]
                }
            },
            {
                "id": "client2",
                "name": "Client 2",
                "data": {
                    "smoke": {
                        "val": 15.0,
                        "loss": 0.1,
                        "avg_loss": 0.5
                    },
                    "interfaces": []
                }
            }
        ]

    async def test_fetch_data_success(self, client, sample_api_data):
        """Test successful data fetch"""
        mock_response = MagicMock()
        mock_response.json.return_value = sample_api_data
        mock_response.status_code = 200
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            result = await client.fetch_data()
            
            assert result == sample_api_data
            assert len(result) == 2
            assert result[0]["id"] == "client1"
            mock_client.get.assert_called_once_with(client.api_url)

    async def test_fetch_data_timeout(self, client):
        """Test API timeout handling"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get.side_effect = httpx.TimeoutException("Timeout")
            mock_client_class.return_value = mock_client
            
            with pytest.raises(httpx.TimeoutException):
                await client.fetch_data()

    async def test_fetch_data_http_error(self, client):
        """Test HTTP error handling"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server Error",
            request=MagicMock(),
            response=mock_response
        )
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            with pytest.raises(httpx.HTTPStatusError):
                await client.fetch_data()

    async def test_fetch_data_unexpected_error(self, client):
        """Test unexpected error handling"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get.side_effect = Exception("Unexpected error")
            mock_client_class.return_value = mock_client
            
            with pytest.raises(Exception):
                await client.fetch_data()

    async def test_fetch_data_empty_response(self, client):
        """Test empty API response"""
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.status_code = 200
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            result = await client.fetch_data()
            
            assert result == []
            assert len(result) == 0

    async def test_fetch_data_non_list_response(self, client):
        """Test non-list API response"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"error": "Not a list"}
        mock_response.status_code = 200
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            result = await client.fetch_data()
            
            assert result == {"error": "Not a list"}

    def test_client_initialization(self):
        """Test client initialization with custom parameters"""
        client = ViaIpeClient(
            api_url="https://custom-api.example.com",
            timeout=60
        )
        
        assert client.api_url == "https://custom-api.example.com"
        assert client.timeout == 60

    def test_client_default_timeout(self):
        """Test client initialization with default timeout"""
        client = ViaIpeClient(api_url="https://test.example.com")
        
        assert client.timeout == 30
