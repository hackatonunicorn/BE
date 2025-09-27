"""
LinkedIn integration for prospect research and outreach
"""
from typing import Dict, Any, List
import httpx
from app.core.config import settings


class LinkedInIntegration:
    """LinkedIn API integration for prospect research"""
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://api.linkedin.com/v2"
        self.client = httpx.AsyncClient()
    
    async def search_people(self, keywords: str, company: str = None) -> List[Dict[str, Any]]:
        """Search for people on LinkedIn"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Note: This is a simplified example. LinkedIn's actual People Search API
            # requires special partnership access and has different endpoints
            url = f"{self.base_url}/people"
            params = {
                "keywords": keywords,
                "facet": "network"
            }
            
            if company:
                params["company"] = company
            
            response = await self.client.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            return response.json().get("elements", [])
            
        except Exception as e:
            return {"error": f"LinkedIn people search failed: {str(e)}"}
    
    async def get_company_info(self, company_id: str) -> Dict[str, Any]:
        """Get company information from LinkedIn"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            url = f"{self.base_url}/companies/{company_id}"
            
            response = await self.client.get(url, headers=headers)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            return {"error": f"LinkedIn company lookup failed: {str(e)}"}
    
    async def get_profile_info(self, person_id: str) -> Dict[str, Any]:
        """Get person's profile information"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            url = f"{self.base_url}/people/{person_id}"
            params = {
                "projection": "(id,firstName,lastName,headline,summary,positions)"
            }
            
            response = await self.client.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            return {"error": f"LinkedIn profile lookup failed: {str(e)}"}


class LinkedInProspectResearcher:
    """Helper class for prospect research using LinkedIn data"""
    
    def __init__(self, linkedin_integration: LinkedInIntegration):
        self.linkedin = linkedin_integration
    
    async def research_vc_contacts(self, vc_name: str) -> List[Dict[str, Any]]:
        """Research potential contacts at a VC firm"""
        try:
            # Search for people at the VC firm
            prospects = await self.linkedin.search_people(
                keywords="partner investor",
                company=vc_name
            )
            
            enriched_prospects = []
            for prospect in prospects[:5]:  # Limit to top 5 results
                profile_info = await self.linkedin.get_profile_info(prospect.get("id"))
                
                enriched_prospect = {
                    "name": f"{profile_info.get('firstName', '')} {profile_info.get('lastName', '')}",
                    "headline": profile_info.get("headline", ""),
                    "summary": profile_info.get("summary", ""),
                    "positions": profile_info.get("positions", []),
                    "linkedin_id": prospect.get("id"),
                    "company": vc_name
                }
                
                enriched_prospects.append(enriched_prospect)
            
            return enriched_prospects
            
        except Exception as e:
            return {"error": f"VC contact research failed: {str(e)}"}
    
    async def analyze_investment_focus(self, vc_name: str) -> Dict[str, Any]:
        """Analyze VC's investment focus based on LinkedIn data"""
        try:
            # Get company information
            # Note: This would require company search first to get company_id
            company_info = await self.linkedin.get_company_info("mock_company_id")
            
            # Analyze description and recent posts for investment themes
            analysis = {
                "company_name": vc_name,
                "description": company_info.get("description", ""),
                "specialties": company_info.get("specialties", []),
                "industry": company_info.get("industry", ""),
                "focus_areas": [],  # Would be extracted using NLP
                "stage_preference": "",  # Would be inferred from portfolio
                "geographic_focus": ""  # Would be extracted from location data
            }
            
            return analysis
            
        except Exception as e:
            return {"error": f"Investment focus analysis failed: {str(e)}"}
