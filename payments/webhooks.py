from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import hmac
import hashlib
from django.conf import settings
from .models import Transaction
from accounts.models import VirtualAccount
from django.utils import timezone

@csrf_exempt
@require_POST
def monnify_webhook(request):
    # Verify webhook signature
    signature = request.headers.get('monnify-signature')
    if not verify_webhook_signature(request.body, signature):
        return HttpResponse('Invalid signature', status=400)

    payload = json.loads(request.body)
    event_type = payload.get('eventType')
    
    if event_type == 'SUCCESSFUL_TRANSACTION':
        handle_successful_transaction(payload)
    
    return HttpResponse('Webhook received', status=200)

def verify_webhook_signature(payload, signature):
    from site_core.models import SiteSetting
    site_settings = SiteSetting.get_solo()
    
    computed_signature = hmac.new(
        site_settings.monnify_secret_key.encode(),
        payload,
        hashlib.sha512
    ).hexdigest()
    
    return hmac.compare_digest(computed_signature, signature)

def handle_successful_transaction(payload):
    transaction_data = payload.get('eventData', {})
    
    # Find virtual account
    account_reference = transaction_data.get('destinationAccountInformation', {}).get('accountReference')
    if not account_reference:
        return

    try:
        virtual_account = VirtualAccount.objects.get(reference=account_reference)
        user = virtual_account.user
        
        # Create transaction record
        Transaction.objects.create(
            user=user,
            transaction_type='add_money',
            amount=transaction_data.get('amount', 0),
            currency='NGN',
            status='completed',
            reference=transaction_data.get('transactionReference'),
            description=f"Deposit to virtual account {virtual_account.account_number}",
            metadata=payload,
            completed_at=timezone.now()
        )
        
        # You can also send notification to user here
        
    except VirtualAccount.DoesNotExist:
        pass