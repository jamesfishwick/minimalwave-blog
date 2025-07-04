from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from blog.models import Entry, LinkedInCredentials, LinkedInPost, LinkedInSettings
from blog.linkedin_service import LinkedInService, LinkedInAPIException


class Command(BaseCommand):
    help = 'Manage LinkedIn integration: post entries, retry failed posts, check status'

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(dest='action', help='Available actions')
        
        # Post entry command
        post_parser = subparsers.add_parser('post', help='Post a specific entry to LinkedIn')
        post_parser.add_argument('entry_id', type=int, help='ID of the entry to post')
        post_parser.add_argument('--force', action='store_true', help='Force posting even if already posted')
        
        # Retry failed posts command
        retry_parser = subparsers.add_parser('retry', help='Retry failed LinkedIn posts')
        retry_parser.add_argument('--max-age', type=int, default=24, 
                                help='Maximum age of failed posts to retry (in hours)')
        
        # Status command
        subparsers.add_parser('status', help='Check LinkedIn integration status')
        
        # Failed posts summary command
        summary_parser = subparsers.add_parser('failed', help='Show summary of failed posts')
        summary_parser.add_argument('--days', type=int, default=7,
                                  help='Number of days to look back for failed posts')
        
        # Bulk post command
        bulk_parser = subparsers.add_parser('bulk-post', help='Post multiple published entries')
        bulk_parser.add_argument('--limit', type=int, default=10,
                               help='Maximum number of entries to post')
        bulk_parser.add_argument('--skip-posted', action='store_true', default=True,
                               help='Skip entries that have already been posted')

    def handle(self, *args, **options):
        action = options['action']
        
        if action == 'post':
            self.post_entry(options['entry_id'], options['force'])
        elif action == 'retry':
            self.retry_failed_posts(options['max_age'])
        elif action == 'status':
            self.show_status()
        elif action == 'failed':
            self.show_failed_summary(options['days'])
        elif action == 'bulk-post':
            self.bulk_post_entries(options['limit'], options['skip_posted'])
        else:
            self.stdout.write(self.style.ERROR('Please specify an action: post, retry, status, failed, or bulk-post'))

    def post_entry(self, entry_id, force=False):
        """Post a specific entry to LinkedIn"""
        try:
            entry = Entry.objects.get(id=entry_id)
        except Entry.DoesNotExist:
            raise CommandError(f'Entry with ID {entry_id} does not exist')
        
        if not entry.is_published:
            raise CommandError(f'Entry "{entry.title}" is not published')
        
        # Check if already posted
        if not force and LinkedInPost.objects.filter(entry=entry, status='posted').exists():
            self.stdout.write(
                self.style.WARNING(f'Entry "{entry.title}" has already been posted to LinkedIn. Use --force to post anyway.')
            )
            return
        
        if not entry.linkedin_enabled:
            self.stdout.write(
                self.style.WARNING(f'LinkedIn posting is disabled for entry "{entry.title}"')
            )
            return
        
        try:
            linkedin_service = LinkedInService()
            
            if not linkedin_service.is_authenticated():
                raise CommandError('LinkedIn is not authenticated. Please authenticate via the admin interface.')
            
            self.stdout.write(f'Posting entry "{entry.title}" to LinkedIn...')
            
            response = linkedin_service.post_entry_to_linkedin(entry)
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully posted "{entry.title}" to LinkedIn')
            )
            
            if 'id' in response:
                self.stdout.write(f'LinkedIn Post ID: {response["id"]}')
                
        except LinkedInAPIException as e:
            raise CommandError(f'Failed to post to LinkedIn: {str(e)}')
        except Exception as e:
            raise CommandError(f'Unexpected error: {str(e)}')

    def retry_failed_posts(self, max_age_hours):
        """Retry failed LinkedIn posts"""
        try:
            linkedin_service = LinkedInService()
            
            if not linkedin_service.is_authenticated():
                raise CommandError('LinkedIn is not authenticated. Please authenticate via the admin interface.')
            
            self.stdout.write(f'Retrying failed posts from the last {max_age_hours} hours...')
            
            results = linkedin_service.retry_failed_posts(max_age_hours)
            
            self.stdout.write(f'Retry Results:')
            self.stdout.write(f'  Attempted: {results["attempted"]}')
            self.stdout.write(f'  Succeeded: {results["succeeded"]}')
            self.stdout.write(f'  Still Failed: {results["still_failed"]}')
            
            if results['errors']:
                self.stdout.write(self.style.WARNING('\nErrors:'))
                for error in results['errors']:
                    self.stdout.write(f'  - {error}')
            
            if results['succeeded'] > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'\nSuccessfully retried {results["succeeded"]} posts')
                )
            elif results['attempted'] == 0:
                self.stdout.write('No failed posts found to retry')
            else:
                self.stdout.write(
                    self.style.WARNING('No posts were successfully retried')
                )
                
        except LinkedInAPIException as e:
            raise CommandError(f'Failed to retry posts: {str(e)}')
        except Exception as e:
            raise CommandError(f'Unexpected error: {str(e)}')

    def show_status(self):
        """Show LinkedIn integration status"""
        try:
            linkedin_service = LinkedInService()
            credentials = linkedin_service.credentials
            settings = LinkedInSettings.get_settings()
            
            self.stdout.write(self.style.SUCCESS('LinkedIn Integration Status:'))
            self.stdout.write('=' * 40)
            
            # Authentication status
            if linkedin_service.is_authenticated():
                self.stdout.write(self.style.SUCCESS('✓ Authenticated'))
                if credentials:
                    self.stdout.write(f'  User: {credentials.authorized_user}')
                    self.stdout.write(f'  Token expires: {credentials.token_expires_at}')
            else:
                self.stdout.write(self.style.ERROR('✗ Not authenticated'))
            
            # Settings
            self.stdout.write(f'\nSettings:')
            self.stdout.write(f'  Global enabled: {settings.enabled}')
            self.stdout.write(f'  Auto-post entries: {settings.auto_post_entries}')
            self.stdout.write(f'  Auto-post blogmarks: {settings.auto_post_blogmarks}')
            self.stdout.write(f'  Include URL: {settings.include_url}')
            
            # Recent activity
            recent_posts = LinkedInPost.objects.order_by('-posted_at')[:5]
            if recent_posts:
                self.stdout.write(f'\nRecent Posts:')
                for post in recent_posts:
                    status_symbol = '✓' if post.status == 'posted' else '✗'
                    self.stdout.write(f'  {status_symbol} {post.entry.title} ({post.status})')
            
            # Failed posts count
            failed_count = LinkedInPost.objects.filter(status='failed').count()
            if failed_count > 0:
                self.stdout.write(self.style.WARNING(f'\n⚠ {failed_count} failed posts'))
            
        except Exception as e:
            raise CommandError(f'Error checking status: {str(e)}')

    def show_failed_summary(self, days):
        """Show summary of failed posts"""
        try:
            linkedin_service = LinkedInService()
            summary = linkedin_service.get_failed_posts_summary(days)
            
            self.stdout.write(self.style.WARNING('Failed Posts Summary:'))
            self.stdout.write('=' * 30)
            
            self.stdout.write(f'Total failed posts (last {days} days): {summary["total_failed"]}')
            
            if summary['error_types']:
                self.stdout.write('\nError Types:')
                for error_type, count in summary['error_types'].items():
                    self.stdout.write(f'  {error_type}: {count}')
            
            if summary['recent_failures']:
                self.stdout.write('\nRecent Failures:')
                for failure in summary['recent_failures']:
                    self.stdout.write(f'  - {failure["entry_title"]} ({failure["failed_at"]})')
                    self.stdout.write(f'    Error: {failure["error"][:100]}...')
            
            if summary['total_failed'] == 0:
                self.stdout.write(self.style.SUCCESS('No failed posts found'))
                
        except Exception as e:
            raise CommandError(f'Error getting failed posts summary: {str(e)}')

    def bulk_post_entries(self, limit, skip_posted):
        """Post multiple published entries to LinkedIn"""
        try:
            linkedin_service = LinkedInService()
            
            if not linkedin_service.is_authenticated():
                raise CommandError('LinkedIn is not authenticated. Please authenticate via the admin interface.')
            
            # Get published entries that are LinkedIn-enabled
            entries_query = Entry.objects.filter(
                status='published',
                linkedin_enabled=True
            ).order_by('-created')
            
            if skip_posted:
                # Exclude entries that have already been successfully posted
                posted_entry_ids = LinkedInPost.objects.filter(
                    status='posted'
                ).values_list('entry_id', flat=True)
                entries_query = entries_query.exclude(id__in=posted_entry_ids)
            
            entries = entries_query[:limit]
            
            if not entries:
                self.stdout.write('No entries found to post')
                return
            
            self.stdout.write(f'Found {len(entries)} entries to post to LinkedIn')
            
            success_count = 0
            error_count = 0
            
            for entry in entries:
                try:
                    self.stdout.write(f'Posting: {entry.title}')
                    linkedin_service.post_entry_to_linkedin(entry)
                    success_count += 1
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Posted successfully'))
                    
                except LinkedInAPIException as e:
                    error_count += 1
                    self.stdout.write(self.style.ERROR(f'  ✗ Failed: {str(e)}'))
                    
                except Exception as e:
                    error_count += 1
                    self.stdout.write(self.style.ERROR(f'  ✗ Unexpected error: {str(e)}'))
            
            self.stdout.write(f'\nBulk posting complete:')
            self.stdout.write(f'  Successful: {success_count}')
            self.stdout.write(f'  Failed: {error_count}')
            
        except Exception as e:
            raise CommandError(f'Error in bulk posting: {str(e)}')