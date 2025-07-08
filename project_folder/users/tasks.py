from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from users.models import Account

import logging
from celery import shared_task

# The tasks you write will probably live in reusable apps,
# and reusable apps cannot depend on the project itself,
# so you also cannot import your app instance directly.
#
# The @shared_task decorator lets you create tasks without having any concrete app instance

User = get_user_model()
logger = logging.getLogger(__name__)  # Creates a logger specific to this module





@shared_task(bind=True, max_retries=3)
def delete_user_by_id_task(user_id):
    try:
        user_instance = User.objects.get(id=user_id)
        user_instance.delete()
        logger.info(f"Successfully deleted User with ID: '{user_id}'")
        return {'status': 'success', 'user_id': user_id}

    except User.DoesNotExist:
        logger.warning(f"User with ID: '{user_id}' not found")
        return {'status': 'skipped', 'reason': 'missing_user'}

    except Exception as e:
        logger.error(
            f"Failed to delete User with ID: '{user_id}'. "
            f"Error: {str(e)}"
        )
        self.retry(exc=e, countdown=60) # Retry after 60 seconds



@shared_task
def pending_deletions_task(batch_size=100):
    """
    Continuously processes accounts scheduled for deletion in batches.
    Uses transaction.atomic() to ensure consistency.
    """

    while True:
        # Fetch the next batch of deletable accounts
        accounts = Account.objects.filter(
            deletion_task_id__isnull=True,
            deletion_date__isnull=False,
            deletion_date__lte=timezone.now()
        ).select_related('user')[:batch_size]

        # If no accounts left, break the loop
        if not accounts:
            logger.info('No more accounts pending deletion.')
            break

        for account in accounts:
            try:
                with transaction.atomic():
                    task = delete_user_by_id_task.delay(account.user.id)
                    account.deletion_task_id = task.id
                    account.save(update_fields=['deletion_task_id'])
                    logger.info(f"Scheduled deletion for User with ID: '{account.user.id}'")     

            except Exception as e:
                logger.error(
                    f"Failed processing User with ID: '{account.user.id}'. "
                    f"Error: {str(e)}"
                )
