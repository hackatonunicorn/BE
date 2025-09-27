"""
CRM integrations for syncing startup and VC data
"""
from typing import Dict, Any, List
import httpx
from app.core.config_simple import settings


class CRMIntegration:
    """Base class for CRM integrations"""
    
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def sync_contacts(self) -> List[Dict[str, Any]]:
        """Sync contacts from CRM"""
        raise NotImplementedError
    
    async def create_contact(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new contact in CRM"""
        raise NotImplementedError
    
    async def update_contact(self, contact_id: str, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing contact in CRM"""
        raise NotImplementedError


class HubSpotIntegration(CRMIntegration):
    """HubSpot CRM integration"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key, "https://api.hubapi.com")
    
    async def sync_contacts(self) -> List[Dict[str, Any]]:
        """Sync contacts from HubSpot"""
        try:
            url = f"{self.base_url}/crm/v3/objects/contacts"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            response = await self.client.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            return data.get("results", [])
            
        except Exception as e:
            return {"error": f"HubSpot sync failed: {str(e)}"}
    
    async def create_contact(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new contact in HubSpot"""
        try:
            url = f"{self.base_url}/crm/v3/objects/contacts"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {"properties": contact_data}
            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            return {"error": f"HubSpot contact creation failed: {str(e)}"}


class SalesforceIntegration(CRMIntegration):
    """Salesforce CRM integration"""
    
    def __init__(self, client_id: str, client_secret: str, username: str, password: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password
        super().__init__("", "https://login.salesforce.com")
        self.access_token = None
    
    async def authenticate(self) -> bool:
        """Authenticate with Salesforce"""
        try:
            auth_url = f"{self.base_url}/services/oauth2/token"
            data = {
                "grant_type": "password",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "username": self.username,
                "password": self.password
            }
            
            response = await self.client.post(auth_url, data=data)
            response.raise_for_status()
            
            auth_data = response.json()
            self.access_token = auth_data.get("access_token")
            self.base_url = auth_data.get("instance_url")
            
            return True
            
        except Exception as e:
            print(f"Salesforce authentication failed: {str(e)}")
            return False
    
    async def sync_contacts(self) -> List[Dict[str, Any]]:
        """Sync contacts from Salesforce"""
        if not self.access_token:
            await self.authenticate()
        
        try:
            url = f"{self.base_url}/services/data/v58.0/query"
            headers = {"Authorization": f"Bearer {self.access_token}"}
            params = {
                "q": "SELECT Id, Name, Email, Company FROM Contact LIMIT 100"
            }
            
            response = await self.client.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            return data.get("records", [])
            
        except Exception as e:
            return {"error": f"Salesforce sync failed: {str(e)}"}
