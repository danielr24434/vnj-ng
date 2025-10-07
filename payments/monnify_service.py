import requests
import json
import logging
from django.conf import settings
from django.utils import timezone
from site_core.models import SiteSetting


logger = logging.getLogger(__name__)

class MonnifyService:
    def __init__(self):
        try:
            # Load from .env (via settings.py)
            self.base_url = getattr(settings, 'MONNIFY_BASE_URL', None)
            self.api_key = getattr(settings, 'MONNIFY_API_KEY', None)
            self.secret_key = getattr(settings, 'MONNIFY_SECRET_KEY', None)
            self.contract_code = getattr(settings, 'MONNIFY_CONTRACT_CODE', None)

            # Optionally still load SiteSetting for prefix/default bank
            self.site_settings = SiteSetting.get_solo() if SiteSetting.objects.exists() else None

            self.access_token = None
            self.token_expiry = None

            # 🔍 Debug output to trace configuration loading
            logger.info("🔍 [Monnify Config Check]")
            logger.info(f"Base URL: {self.base_url or '❌ Missing'}")
            logger.info(f"API Key: {self.api_key[:6] + '****' if self.api_key else '❌ Missing'}")
            logger.info(f"Secret Key: {self.secret_key[:6] + '****' if self.secret_key else '❌ Missing'}")
            logger.info(f"Contract Code: {self.contract_code or '❌ Missing'}")

            # Validate configuration early
            if not all([self.base_url, self.api_key, self.secret_key, self.contract_code]):
                raise ValueError("Missing Monnify environment variables. Please check your .env file.")

        except Exception as e:
            logger.exception(f"🚨 Error initializing Monnify service: {str(e)}")
            raise


    def _get_access_token(self):
        """Authenticate with Monnify API"""
        if self.access_token and self.token_expiry and timezone.now() < self.token_expiry:
            logger.info("✅ Using cached Monnify token.")
            return self.access_token

        url = f"{self.base_url}/api/v1/auth/login"
        logger.info(f"🔑 Requesting Monnify token from {url}")

        try:
            response = requests.post(
                url,
                auth=(self.api_key, self.secret_key),
                headers={'Content-Type': 'application/json'},
                timeout=30
            )

            logger.info(f"📡 [Monnify Auth] Response Code: {response.status_code}")
            logger.debug(f"📡 [Monnify Auth] Raw Response: {response.text}")

            if response.status_code == 200:
                data = response.json()
                if data.get('requestSuccessful'):
                    self.access_token = data['responseBody']['accessToken']
                    self.token_expiry = timezone.now() + timezone.timedelta(minutes=55)
                    logger.info("✅ Monnify access token obtained successfully.")
                    return self.access_token
                else:
                    logger.error(f"❌ Auth failed: {data.get('responseMessage')}")
                    return None
            else:
                logger.error(f"❌ HTTP error: {response.status_code} - {response.text}")
                return None

        except requests.exceptions.RequestException as e:
            logger.exception(f"🚨 Auth request failed: {str(e)}")
            return None

    def create_reserved_account(self, user, kyc_data, preferred_banks=None):
        """Create virtual account for user with comprehensive error handling"""
        access_token = self._get_access_token()
        if not access_token:
            return None, "Failed to authenticate with Monnify. Please check API configuration."

        url = f"{self.base_url}/api/v2/bank-transfer/reserved-accounts"
        
        # Generate unique reference
        from django.utils.crypto import get_random_string
        reference = f"{self.site_settings.account_reference_prefix}_{user.id}_{get_random_string(8).upper()}"
        
        # Get preferred banks or use default
        if not preferred_banks and self.site_settings.default_bank_code:
            preferred_banks = [self.site_settings.default_bank_code]
        
        # Prepare account name (Monnify has character limits)
        account_name = f"{kyc_data['legal_first_name']} {kyc_data['legal_last_name'][:1]}".strip()
        if len(account_name) > 150:  # Monnify limit
            account_name = account_name[:147] + "..."
        
        payload = {
            "accountReference": reference,
            "accountName": account_name,
            "currencyCode": "NGN",
            "contractCode": self.contract_code,
            "customerEmail": user.email,
            "customerName": f"{kyc_data['legal_first_name']} {kyc_data['legal_last_name']}",
            "getAllAvailableBanks": True,
            "preferredBanks": []
        }

        try:
            logger.info(f"Creating Monnify account for user {user.username} with reference {reference}")
            
            response = requests.post(
                url,
                json=payload,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {access_token}'
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('requestSuccessful'):
                    logger.info(f"Monnify account created successfully for user {user.username}")
                    return data['responseBody'], None
                else:
                    error_msg = data.get('responseMessage', 'Account creation failed')
                    logger.error(f"Monnify account creation failed for {user.username}: {error_msg}")
                    return None, f"Monnify error: {error_msg}"
            else:
                logger.error(f"Monnify HTTP error for {user.username}: {response.status_code} - {response.text}")
                return None, f"HTTP error {response.status_code}: Please try again later"
                
        except requests.exceptions.Timeout:
            logger.error(f"Monnify request timeout for user {user.username}")
            return None, "Request timeout. Please try again."
        except requests.exceptions.RequestException as e:
            logger.error(f"Monnify request failed for {user.username}: {str(e)}")
            return None, f"Network error: {str(e)}"

    def get_banks(self):
        """Get list of available banks from Monnify"""
        access_token = self._get_access_token()
        if not access_token:
            return None

        url = f"{self.base_url}/api/v1/banks"
        
        try:
            response = requests.get(
                url,
                headers={
                    'Authorization': f'Bearer {access_token}'
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('requestSuccessful'):
                    return data['responseBody']
                else:
                    logger.error(f"Monnify banks fetch failed: {data}")
                    return None
            else:
                logger.error(f"Monnify banks HTTP error: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Monnify banks request failed: {str(e)}")
            return None

    def verify_transaction(self, transaction_reference):
        """Verify transaction status"""
        access_token = self._get_access_token()
        if not access_token:
            return None

        url = f"{self.base_url}/api/v2/transactions/{transaction_reference}"
        
        try:
            response = requests.get(
                url,
                headers={
                    'Authorization': f'Bearer {access_token}'
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('requestSuccessful'):
                    return data['responseBody']
                else:
                    return None
            else:
                return None
                
        except requests.exceptions.RequestException:
            return None

    def sync_banks_to_database(self):
        """Sync available banks from Monnify to database"""
        banks = self.get_banks()
        if not banks:
            return False, "Failed to fetch banks from Monnify"

        try:
            for bank in banks:
                MonnifyBank.objects.update_or_create(
                    bank_code=bank['code'],
                    defaults={
                        'bank_name': bank['name'],
                        'is_active': True
                    }
                )
            logger.info("Successfully synced banks from Monnify")
            return True, "Banks synced successfully"
        except Exception as e:
            logger.error(f"Error syncing banks: {str(e)}")
            return False, f"Error syncing banks: {str(e)}"