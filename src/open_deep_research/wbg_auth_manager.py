"""WBG Authentication Manager for Microsoft Entra ID (Azure AD) authentication."""

import msal
from loguru import logger
from pathlib import Path
from typing import Optional, Dict, Any


class WBGAuthManager:
    """Manages authentication tokens for WBG APIs using MSAL with automatic refresh."""
    
    def __init__(
        self,
        # These are standard Microsoft Entra ID details for public clients
        tenant_id: str = "31a2fec0-266b-4c67-b56e-2796d8f59c36",
        client_id: str = "00c104af-b0ae-4557-9787-6e6cfced741e",
        scope: str = "https://cognitiveservices.azure.com/.default",
        token_file: Optional[Path] = None
    ):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.scope = scope
        
        if token_file is None:
            # Store the cache in the project root
            token_file = Path(__file__).parent.parent.parent / ".wbg_token_cache.bin"
        self.token_file = token_file
        
        self.token_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.msal_app = msal.PublicClientApplication(
            client_id=self.client_id,
            authority=f"https://login.microsoftonline.com/{self.tenant_id}",
            token_cache=self._get_token_cache()
        )
        logger.info(f"WBGAuthManager initialized. Cache file: {self.token_file}")

    def _get_token_cache(self) -> msal.SerializableTokenCache:
        cache = msal.SerializableTokenCache()
        if self.token_file.exists():
            try:
                cache.deserialize(open(self.token_file, "r").read())
                logger.debug("Token cache loaded from file.")
            except Exception as e:
                logger.warning(f"Failed to load token cache: {e}")
        return cache

    def _save_token_cache(self) -> None:
        if self.msal_app.token_cache.has_state_changed:
            with open(self.token_file, "w") as f:
                f.write(self.msal_app.token_cache.serialize())
            logger.debug("Token cache saved to file.")

    def get_bearer_token(self) -> str:
        """
        Get a valid bearer token, using silent refresh if possible and falling
        back to interactive flow if necessary.
        """
        accounts = self.msal_app.get_accounts()
        result = None
        
        if accounts:
            logger.info("Account found in cache. Attempting silent token acquisition.")
            result = self.msal_app.acquire_token_silent(scopes=[self.scope], account=accounts[0])
        
        if not result:
            logger.info("Silent acquisition failed. Initiating Device Code Flow for interactive auth.")
            flow = self.msal_app.initiate_device_flow(scopes=[self.scope])
            if "user_code" not in flow:
                raise Exception(f"Failed to create device flow: {flow.get('error_description')}")
            
            print(flow["message"]) # Instruct user to go to a URL and enter a code
            result = self.msal_app.acquire_token_by_device_flow(flow)
            
        if "access_token" in result:
            self._save_token_cache()
            return result["access_token"]
        else:
            raise Exception(f"Failed to acquire token: {result.get('error_description', 'Unknown error')}")