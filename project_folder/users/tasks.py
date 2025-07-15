from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth import get_user_model
from users.models import Account

from datetime import timedelta
from celery import shared_task, chain
from celery.result import AsyncResult

import logging, stripe

# The tasks you write will probably live in reusable apps,
# and reusable apps cannot depend on the project itself,
# so you also cannot import your app instance directly.
#
# The @shared_task decorator lets you create tasks without having any concrete app instance


User = get_user_model()
logger = logging.getLogger(__name__)





@shared_task(bind=True, max_retries=3)
def delete_stripe_customer_task(self, account_id):
    """
    Phase 1: Atomic Stripe deletion with:
    - Optimized DB writes
    - Enhanced error context
    - Exponential backoff
    """
    try:
        with transaction.atomic():
            # Note: account instance is locked until
            # transaction.atomic() scope finalizes
            account = Account.objects.select_for_update().get(
                pk=account_id,
                deletion_phase__in=['pending', 'stripe_started']
            )

            # Early return (validate phase)

            if account.deletion_phase == 'stripe_completed':
                return {'status': 'skipped', 'reason': 'already_processed'}

            # Proceed with deletion of Stripe customer
            
            account.deletion_phase = 'stripe_started'
            account.save(update_fields=['deletion_phase'])

            if account.stripe_customer_id:
                stripe.Customer.delete(account.stripe_customer_id)
                account.stripe_customer_id = None
                account.save(update_fields=['stripe_customer_id'])

            account.deletion_phase = 'stripe_completed'
            account.save(update_fields=['deletion_phase'])
            
            # Return success

            logger.info(
                f"Stripe deletion completed | account_id={account.id} "
                f"user_id={account.user.id}"
            )
            return {'status': 'success'}


    # Handle ERRORS

    except Account.DoesNotExist:
        logger.warning(f"Account {account_id} invalid for processing")
        return {'status': 'skipped', 'reason': 'invalid_state'}

    except Exception as e:
        logger.error(
            f"Stripe deletion failed | account_id={account_id} "
            f"error={str(e)}"
        )
        # Exponential backoff with cap
        countdown = min(300, 2 ** self.request.retries * 30)
        self.retry(exc=e, countdown=countdown)




@shared_task(bind=True)
def delete_user_task(self, user_id):
    """
    Phase 2: User deletion with:
    - Atomic phase transition
    - Cascade safety
    - Enhanced diagnostics
    """
    try:
        with transaction.atomic():
            locked_user = User.objects.select_for_update().get(id=user_id)
            locked_account = Account.objects.select_for_update().get(
                user=locked_user,
                deletion_phase='stripe_completed'
            )
            
            # Store for logging before deletion
            account_id = locked_account.id  
            
            locked_account.deletion_phase = 'completed'
            locked_account.save(update_fields=['deletion_phase'])
            locked_user.delete() # Cascades (Hence, removes Account)
            
            logger.info(
                f"User deletion completed | user_id={user_id} "
                f"account_id={account_id}"
            )
            return {'status': 'success', 'user_id': user_id}


    # Handle ERRORS

    except User.DoesNotExist:
        logger.warning(f"User missing | user_id={user_id}")
        return {'status': 'skipped', 'reason': 'missing_user'}

    except Account.DoesNotExist:
        logger.warning(f"Account missing or mismatched phase | user_id={user_id}")
        return {'status': 'skipped', 'reason': 'invalid_phase'}

    except Exception as e:
        logger.error(f"User deletion failed | user_id={user_id} error={str(e)}")
        raise




@shared_task(bind=True)
def pending_deletions_task(self, batch_size=100):
    """
    Activates deletion processes for users with expired deletion_date,
    safely removing them and their associated data from third-party services.
    """
    accounts = Account.objects.filter(
        user__isnull=False,
        deletion_phase='pending',
        deletion_date__lte=timezone.now()
    ).select_related('user')[:batch_size]

    processed = 0
    

    for account in accounts:
        try:
            with transaction.atomic():
                locked_account = Account.objects.select_for_update().get(
                    pk=account.pk,
                    deletion_phase='pending'
                )
                
                locked_account.deletion_phase = 'stripe_started'
                locked_account.save(update_fields=['deletion_phase'])
                
                # Initiate the deletion pipeline:
                # Phase 1: Stripe cleanup → Phase 2: User deletion
                # (Tasks execute sequentially via Celery chain)
                chain(
                    delete_stripe_customer_task.si(locked_account.id),
                    delete_user_task.si(locked_account.user.id)
                ).apply_async()
                
                processed += 1
                logger.info(
                    f"Initiated deletion chain | account_id={locked_account.id} "
                    f"user_id={locked_account.user.id}"
                )


        # Handle ERRORS

        except Account.DoesNotExist:
            continue # Already claimed (processed)

        except Exception as e:
            logger.error(
                f"Initiation failed | account_id={account.id} "
                f"error={str(e)}"
            )

    return {'processed': processed, 'batch_size': batch_size}




@shared_task
def process_stuck_user_deletions_task(batch_size=100):
    """
    Ensures that, users scheduled for deletion, are fully
    removed and their associated data on third party services,
    by finalizing the unfinished deletion processes.
    """

    processed = {
        'users': 0,
        'zombie_accounts': 0,
        'stripe_customers': 0,
    }


    # 1. Renew interrupted Stripe deletions (1h+ stale)
    #
    # Recovers accounts where:
    #   - Stripe deletion was started (deletion_phase='stripe_started')
    #   - But never completed (didn't reach 'stripe_completed')
    #   - Been stuck for >1 hour (deletion_date check)
    #
    # Prevents Orphans:
    #   Without this, accounts could remain indefinitely in a half-deleted state
    #
    stripe_interrupted = Account.objects.filter(
        deletion_phase='stripe_started',
        deletion_date__lte=timezone.now() - timedelta(hours=1)
    ).select_related('user')[:batch_size]

    for account in stripe_interrupted:
        delete_stripe_customer_task.delay(account.id)
        processed['stripe_customers'] += 1


    # 2. Renew User deletions
    #
    # Handles cases where:
    #   - Stripe customer was successfully deleted (deletion_phase='stripe_completed')
    #   - But the subsequent user deletion never executed or failed
    #   - The deletion was scheduled to happen by now (deletion_date__lte=timezone.now())
    #
    user_deletable = Account.objects.filter(
        user__isnull=False,
        deletion_phase='stripe_completed',
        deletion_date__lte=timezone.now()
    ).select_related('user')[:batch_size]

    for account in user_deletable:
        delete_user_task.delay(account.user.id)
        processed['users'] += 1


    # 3. Cleanup zombie states.
    #
    # Fixes two specific edge cases:
    #
    # Ghost Accounts (deletion_phase='stripe_completed', user__isnull=True)
    #   - Accounts where the user was deleted (cascade) but phase wasn't updated to 'completed'
    #   - Example: Worker crashed after user deletion but before phase update
    #
    # Phase Mismatch (deletion_phase='completed', user__isnull=False)
    #   - Accounts marked 'completed' but still have users
    #   - Example: Manual database intervention or race condition
    #
    zombies = Account.objects.filter(
        Q(deletion_phase='stripe_completed', user__isnull=True) |
        Q(deletion_phase='completed', user__isnull=False)
    )
    processed['zombie_accounts'] = zombies.update(deletion_phase='completed')

    logger.info(f"Processed stuck deletions | processed={processed}")


    # Report processed data
    return processed