from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Entry, Blogmark
import logging

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Entry)
def entry_pre_save(sender, instance, **kwargs):
    """
    Track status changes before save to detect when entries are published.
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


@receiver(post_save, sender=Entry)
def entry_published(sender, instance, created, **kwargs):
    """
    Detect when an Entry is published and trigger LinkedIn posting.
    
    This signal fires when:
    1. Entry status changes to 'published'
    2. Entry is saved with status 'published' and publish_date in the past
    """
    if not instance.is_published:
        return
    
    # Check if this is a new publication
    is_newly_published = False
    
    if created:
        # New entry created as published
        is_newly_published = True
    else:
        # Check if status changed to published
        old_status = getattr(instance, '_old_status', None)
        if old_status != 'published' and instance.status == 'published':
            is_newly_published = True
        
        # Check if publish_date changed to past (scheduled post becoming active)
        old_publish_date = getattr(instance, '_old_publish_date', None)
        if (old_publish_date and old_publish_date > timezone.now() and 
            instance.publish_date and instance.publish_date <= timezone.now()):
            is_newly_published = True
    
    if is_newly_published:
        logger.info(f"Entry '{instance.title}' was published, LinkedIn posting temporarily disabled")
        
        # TODO: Re-enable LinkedIn posting after migration issue is resolved
        # # Import here to avoid circular imports
        # from .linkedin_service import LinkedInService
        # 
        # # Check if LinkedIn posting is enabled for this entry
        # if getattr(instance, 'linkedin_enabled', True):
        #     try:
        #         linkedin_service = LinkedInService()
        #         linkedin_service.post_entry_to_linkedin(instance)
        #         logger.info(f"LinkedIn posting initiated for entry: {instance.title}")
        #     except Exception as e:
        #         logger.error(f"Failed to post entry '{instance.title}' to LinkedIn: {str(e)}")
        # else:
        #     logger.info(f"LinkedIn posting disabled for entry: {instance.title}")


@receiver(pre_save, sender=Blogmark)
def blogmark_pre_save(sender, instance, **kwargs):
    """
    Track status changes before save to detect when blogmarks are published.
    """
    if instance.pk:
        try:
            old_instance = Blogmark.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
            instance._old_publish_date = old_instance.publish_date
        except Blogmark.DoesNotExist:
            instance._old_status = None
            instance._old_publish_date = None
    else:
        instance._old_status = None
        instance._old_publish_date = None


@receiver(post_save, sender=Blogmark)
def blogmark_published(sender, instance, created, **kwargs):
    """
    Detect when a Blogmark is published and trigger LinkedIn posting.
    
    This signal fires when:
    1. Blogmark status changes to 'published'
    2. Blogmark is saved with status 'published' and publish_date in the past
    """
    if not instance.is_published:
        return
    
    # Check if this is a new publication
    is_newly_published = False
    
    if created:
        # New blogmark created as published
        is_newly_published = True
    else:
        # Check if status changed to published
        old_status = getattr(instance, '_old_status', None)
        if old_status != 'published' and instance.status == 'published':
            is_newly_published = True
        
        # Check if publish_date changed to past (scheduled post becoming active)
        old_publish_date = getattr(instance, '_old_publish_date', None)
        if (old_publish_date and old_publish_date > timezone.now() and 
            instance.publish_date and instance.publish_date <= timezone.now()):
            is_newly_published = True
    
    if is_newly_published:
        logger.info(f"Blogmark '{instance.title}' was published, LinkedIn posting temporarily disabled")
        
        # TODO: Re-enable LinkedIn posting after migration issue is resolved
        # # Import here to avoid circular imports
        # from .linkedin_service import LinkedInService
        # 
        # # Check LinkedIn settings for blogmarks (default disabled)
        # try:
        #     from .models import LinkedInSettings
        #     settings = LinkedInSettings.get_settings()
        #     if settings.auto_post_blogmarks:
        #         linkedin_service = LinkedInService()
        #         linkedin_service.post_blogmark_to_linkedin(instance)
        #         logger.info(f"LinkedIn posting initiated for blogmark: {instance.title}")
        #     else:
        #         logger.info(f"LinkedIn posting disabled for blogmarks")
        # except Exception as e:
        #     logger.error(f"Failed to post blogmark '{instance.title}' to LinkedIn: {str(e)}")