from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Entry
import logging

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Entry)
def entry_pre_save(sender, instance, **kwargs):
    """
    Track status changes and log image upload operations for Azure storage debugging.
    """
    if instance.pk:
        try:
            old_instance = Entry.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
            instance._old_publish_date = old_instance.publish_date
        except Entry.DoesNotExist:
            instance._old_status = None
            instance._old_publish_date = None
    else:
        instance._old_status = None
        instance._old_publish_date = None

    if instance.image:
        try:
            logger.info(f"========== PRE-SAVE Entry Image ==========")
            logger.info(f"Entry: {instance.title}")
            logger.info(f"Image name: {instance.image.name if instance.image else 'None'}")
            if hasattr(instance.image, 'file'):
                logger.info(f"New file upload detected")
                try:
                    logger.info(f"File size: {instance.image.size}")
                except Exception as size_error:
                    logger.warning(f"Could not get file size: {size_error}")
            else:
                logger.info(f"Existing image reference")
            logger.info("===========================================")
        except Exception as e:
            logger.error(f"Error logging image info: {e}")


@receiver(post_save, sender=Entry)
def entry_post_save(sender, instance, created, **kwargs):
    """
    Log image storage operations for debugging Azure storage.
    """
    if instance.image:
        logger.info(f"========== POST-SAVE Entry Image ==========")
        logger.info(f"Entry: {instance.title}, Created: {created}")
        logger.info(f"Image name: {instance.image.name}")
        try:
            logger.info(f"Image URL: {instance.image.url}")
            storage = instance.image.storage
            logger.info(f"Storage class: {storage.__class__.__name__}")
            exists = storage.exists(instance.image.name)
            logger.info(f"File exists in storage: {exists}")
            if hasattr(storage, 'account_name'):
                logger.info(f"Azure account: {storage.account_name}")
            if hasattr(storage, 'azure_container'):
                logger.info(f"Azure container: {storage.azure_container}")
        except Exception as e:
            logger.error(f"Error checking storage: {e}", exc_info=True)
        logger.info("===========================================")
