"""WBG Authentication Manager for Microsoft Entra ID (Azure AD) authentication."""

import msal
import time
from pathlib import Path
from typing import Optional, Dict, Any
from ..logging_config import logger


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
        logger.info("=== WBG Auth Manager Initialized ===")
        logger.info(f"Tenant ID: {self.tenant_id}")
        logger.info(f"Client ID: {self.client_id}")
        logger.info(f"Scope: {self.scope}")
        logger.info(f"Cache file: {self.token_file}")

    def _get_token_cache(self) -> msal.SerializableTokenCache:
        cache = msal.SerializableTokenCache()
        if self.token_file.exists():
            try:
                logger.debug(f"Loading token cache from {self.token_file}")
                cache_content = open(self.token_file, "r").read()
                cache.deserialize(cache_content)
                logger.info("Token cache loaded successfully")
                logger.debug(f"Cache file size: {len(cache_content)} bytes")
            except Exception as e:
                logger.warning(f"Failed to load token cache: {str(e)}")
                logger.debug(f"Cache file path: {self.token_file}")
                logger.debug(f"Cache file exists: {self.token_file.exists()}")
        else:
            logger.info("No existing token cache found, will create new one")
        return cache

    def _save_token_cache(self) -> None:
        if self.msal_app.token_cache.has_state_changed:
            try:
                logger.debug(f"Saving token cache to {self.token_file}")
                cache_content = self.msal_app.token_cache.serialize()
                with open(self.token_file, "w") as f:
                    f.write(cache_content)
                logger.info("Token cache saved successfully")
                logger.debug(f"Saved cache size: {len(cache_content)} bytes")
            except Exception as e:
                logger.error(f"Failed to save token cache: {str(e)}")
                logger.exception("Cache save error:")
        else:
            logger.debug("Token cache has no changes, skipping save")

    def get_bearer_token(self) -> str:
        """
        Get a valid bearer token, using silent refresh if possible and falling
        back to interactive flow if necessary.
        """
        logger.info("=== WBG Token Acquisition Starting ===")
        start_time = time.time()
        
        accounts = self.msal_app.get_accounts()
        logger.info(f"Found {len(accounts)} cached accounts")
        
        result = None
        
        if accounts:
            logger.info("Attempting silent token acquisition...")
            account = accounts[0]
            logger.debug(f"Using account: {account.get('username', 'N/A')}")
            
            try:
                result = self.msal_app.acquire_token_silent(scopes=[self.scope], account=account)
                if result:
                    logger.info("Silent token acquisition successful")
                    if "expires_in" in result:
                        logger.info(f"Token expires in: {result['expires_in']} seconds")
                else:
                    logger.warning("Silent token acquisition returned None")
            except Exception as e:
                logger.error(f"Silent token acquisition failed: {str(e)}")
                logger.debug("Will fall back to interactive flow")
        else:
            logger.info("No cached accounts found")
        
        if not result or "access_token" not in result:
            logger.info("=== Starting Interactive Authentication ===")
            logger.info("Initiating Device Code Flow...")
            
            try:
                flow = self.msal_app.initiate_device_flow(scopes=[self.scope])
                
                if "user_code" not in flow:
                    error_desc = flow.get('error_description', 'Unknown error')
                    logger.error(f"Failed to create device flow: {error_desc}")
                    logger.error(f"Full flow response: {flow}")
                    raise Exception(f"Failed to create device flow: {error_desc}")
                
                logger.info("Device flow initiated successfully")
                logger.info(f"User code: {flow.get('user_code', 'N/A')}")
                logger.info(f"Verification URL: {flow.get('verification_uri', 'N/A')}")
                logger.info(f"Expires in: {flow.get('expires_in', 'N/A')} seconds")
                
                # Print instructions for user
                print("\n" + "="*60)
                print(flow["message"])
                print("="*60 + "\n")
                
                logger.info("Waiting for user to complete authentication...")
                auth_start = time.time()
                
                result = self.msal_app.acquire_token_by_device_flow(flow)
                
                auth_duration = time.time() - auth_start
                logger.info(f"User authentication completed in {auth_duration:.1f} seconds")
                
            except Exception as e:
                logger.error(f"Device flow authentication failed: {str(e)}")
                logger.exception("Full authentication error:")
                raise
        
        # Process the result
        if "access_token" in result:
            token = result["access_token"]
            logger.info("Token acquired successfully")
            logger.debug(f"Token preview: {token[:20]}...{token[-20:]}")
            logger.debug(f"Token length: {len(token)} characters")
            
            # Log additional token info if available
            if "token_type" in result:
                logger.debug(f"Token type: {result['token_type']}")
            if "expires_in" in result:
                logger.info(f"Token will expire in: {result['expires_in']} seconds")
            if "refresh_token" in result:
                logger.info("Refresh token included in response")
            
            self._save_token_cache()
            
            duration = time.time() - start_time
            logger.info(f"=== Token Acquisition Completed in {duration:.2f} seconds ===")
            
            return token
        else:
            error_desc = result.get('error_description', 'Unknown error')
            error_code = result.get('error', 'Unknown')
            logger.error(f"=== Token Acquisition Failed ===")
            logger.error(f"Error code: {error_code}")
            logger.error(f"Error description: {error_desc}")
            logger.error(f"Full result: {result}")
            raise Exception(f"Failed to acquire token: {error_desc}")