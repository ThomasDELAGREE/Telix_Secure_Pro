import logging
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)
MICROSOFT_GRAPH_ME = "https://graph.microsoft.com/v1.0/me"


class AzureADService:
    """
    Authentification Azure AD via ROPC flow.
    Recommande uniquement pour portails captifs internes.
    """

    async def authenticate(self, username: str, password: str) -> dict | None:
        token_url = f"https://login.microsoftonline.com/{settings.AZURE_TENANT_ID}/oauth2/v2.0/token"
        data = {
            "grant_type": "password",
            "client_id": settings.AZURE_CLIENT_ID,
            "client_secret": settings.AZURE_CLIENT_SECRET,
            "scope": "openid profile email User.Read",
            "username": username,
            "password": password,
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(token_url, data=data)

        if resp.status_code != 200:
            error = resp.json().get("error_description", "Erreur inconnue")
            logger.warning(f"Azure AD: echec auth pour '{username}' - {error}")
            return None

        access_token = resp.json().get("access_token")

        async with httpx.AsyncClient(timeout=10.0) as client:
            graph_resp = await client.get(
                MICROSOFT_GRAPH_ME,
                headers={"Authorization": f"Bearer {access_token}"},
            )

        if graph_resp.status_code != 200:
            logger.error("Azure AD: impossible de recuperer le profil Graph.")
            return None

        profile = graph_resp.json()
        logger.info(f"Azure AD: auth reussie pour '{username}'.")
        return {
            "username": profile.get("userPrincipalName", username),
            "email": profile.get("mail") or profile.get("userPrincipalName"),
            "display_name": profile.get("displayName", username),
            "groups": [],
        }


azure_ad_service = AzureADService()
