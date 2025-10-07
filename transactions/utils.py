from payments.models import Transaction

def mask_email(email):
    """
    Mask email address for display in transaction tables.
    Example: 'abcdef@gmail.com' -> 'abc***@gm...om'
    """
    if not email or '@' not in email:
        return email
    
    local_part, domain = email.split('@')
    
    # Mask local part - show first 3 characters
    if len(local_part) > 3:
        masked_local = local_part[:3] + '***'
    else:
        masked_local = local_part + '***'
    
    # Mask domain - show first 2 and last 2 characters
    domain_parts = domain.split('.')
    if len(domain_parts) >= 2:
        main_domain = '.'.join(domain_parts[:-1])
        tld = domain_parts[-1]
        
        if len(main_domain) > 2:
            masked_domain = main_domain[:2] + '...' + main_domain[-1:] if len(main_domain) > 3 else main_domain
        else:
            masked_domain = main_domain
            
        masked_domain += '.' + tld
    else:
        masked_domain = domain[:2] + '...' + domain[-2:] if len(domain) > 4 else domain
    
    return f"{masked_local}@{masked_domain}"

def to_display_currency(amount, currency, currency_rate=1):
    """
    Convert amount to display currency using currency rate.
    """
    if currency.upper() == 'USD':
        return amount * currency_rate
    return amount


def get_user_balance(user):
    """
    Get user's available balance from completed transactions.
    """
  
    
    # Get all completed transactions for the user
    transactions = Transaction.objects.filter(
        user=user, 
        status='completed'
    )
    
    balance = 0
    for transaction in transactions:
        if transaction.transaction_type in ['deposit', 'credit', 'refund']:
            balance += transaction.amount
        elif transaction.transaction_type in ['withdrawal', 'debit', 'purchase']:
            balance -= transaction.amount
    
    return balance


def can_afford_purchase(user, amount):
    """
    Check if user can afford a purchase.
    """
    return get_user_balance(user) >= amount


def create_purchase_transaction(user, amount, description, reference=None):
    """
    Create a purchase transaction that deducts from user balance.
    """

    
    transaction = Transaction.objects.create(
        user=user,
        amount=amount,
        transaction_type='purchase',
        description=description,
        reference=reference,
        status='completed'  # Immediately complete since it's from balance
    )
    return transaction


def create_sale_transaction(user, amount, description, reference=None, admin_fee=0):
    """
    Create a sale transaction that adds to seller balance (minus admin fee).
    """

    
    net_amount = amount - admin_fee
    
    # Create credit transaction for seller
    transaction = Transaction.objects.create(
        user=user,
        amount=net_amount,
        transaction_type='credit',
        description=description,
        reference=reference,
        status='completed'
    )
    
    # Create admin fee transaction if there's a fee
    if admin_fee > 0:
        Transaction.objects.create(
            user=user,
            amount=admin_fee,
            transaction_type='fee',
            description=f"Admin fee for: {description}",
            reference=reference,
            status='completed'
        )
    
    return transaction