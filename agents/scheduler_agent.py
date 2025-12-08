"""
Scheduler Agent - Manages post scheduling and execution
"""
from datetime import datetime, timedelta
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SchedulerAgent:
    """Agent responsible for scheduling and executing posts"""
    
    # Optimal posting times by platform (24h format)
    DEFAULT_SCHEDULES = {
        'instagram': {'times': ['11:00', '21:00'], 'days': 'daily'},
        'x': {'times': ['09:00', '12:00', '17:00'], 'days': 'daily'},
        'linkedin': {'times': ['07:30', '12:00'], 'days': 'weekdays'},
        'meta': {'times': ['09:00', '13:00', '19:00'], 'days': 'daily'},
        'tiktok': {'times': ['12:00', '19:00', '22:00'], 'days': 'daily'},
        'reddit': {'times': ['10:00', '19:00'], 'days': 'daily'},
        'youtube': {'times': ['15:00'], 'days': 'daily'},
        'threads': {'times': ['09:00', '18:00'], 'days': 'daily'},
        'pinterest': {'times': ['14:00', '21:00'], 'days': 'daily'}
    }
    
    def __init__(self, scheduler, platform_manager):
        self.scheduler = scheduler
        self.platform_manager = platform_manager
        self.job_registry = {}
    
    def get_default_schedule(self, platform: str) -> Dict:
        """Get default schedule for a platform"""
        return self.DEFAULT_SCHEDULES.get(platform, {'times': ['12:00'], 'days': 'daily'})
    
    def schedule_campaign(
        self,
        campaign_id: str,
        posts: List[Dict],
        schedule_config: Dict
    ) -> List[Dict]:
        """Schedule posts for a campaign"""
        
        scheduled_jobs = []
        schedule_type = schedule_config.get('type', 'optimal')
        
        if schedule_type == 'immediate':
            scheduled_jobs = self._schedule_immediate(campaign_id, posts)
        elif schedule_type == 'optimal':
            scheduled_jobs = self._schedule_optimal(campaign_id, posts)
        elif schedule_type == 'spread':
            scheduled_jobs = self._schedule_spread(campaign_id, posts, schedule_config)
        elif schedule_type == 'custom':
            scheduled_jobs = self._schedule_custom(campaign_id, posts, schedule_config)
        
        self.job_registry[campaign_id] = scheduled_jobs
        return scheduled_jobs
    
    def _schedule_immediate(self, campaign_id: str, posts: List[Dict]) -> List[Dict]:
        """Schedule all posts immediately with small delays"""
        from apscheduler.triggers.date import DateTrigger
        
        jobs = []
        for i, post in enumerate(posts):
            delay = timedelta(seconds=i * 30)
            run_time = datetime.now() + delay
            
            job = self.scheduler.add_job(
                self._execute_post,
                trigger=DateTrigger(run_date=run_time),
                args=[campaign_id, post],
                id=f"{campaign_id}_{post['platform']}_{i}",
                name=f"Post to {post['platform']}"
            )
            
            jobs.append({
                'job_id': job.id,
                'platform': post['platform'],
                'scheduled_time': run_time.isoformat(),
                'status': 'scheduled'
            })
        
        return jobs
    
    def _schedule_optimal(self, campaign_id: str, posts: List[Dict]) -> List[Dict]:
        """Schedule posts at platform-optimal times"""
        from apscheduler.triggers.date import DateTrigger
        
        jobs = []
        now = datetime.now()
        
        for post in posts:
            platform = post['platform']
            schedule = self.DEFAULT_SCHEDULES.get(platform, {'times': ['12:00']})
            
            # Find next available time slot
            for time_str in schedule['times']:
                hour, minute = map(int, time_str.split(':'))
                scheduled_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                if scheduled_time > now:
                    break
            else:
                # All times passed today, schedule for tomorrow
                hour, minute = map(int, schedule['times'][0].split(':'))
                scheduled_time = (now + timedelta(days=1)).replace(
                    hour=hour, minute=minute, second=0, microsecond=0
                )
            
            job = self.scheduler.add_job(
                self._execute_post,
                trigger=DateTrigger(run_date=scheduled_time),
                args=[campaign_id, post],
                id=f"{campaign_id}_{platform}_optimal",
                name=f"Optimal post to {platform}"
            )
            
            jobs.append({
                'job_id': job.id,
                'platform': platform,
                'scheduled_time': scheduled_time.isoformat(),
                'status': 'scheduled'
            })
        
        return jobs
    
    def _schedule_spread(self, campaign_id: str, posts: List[Dict], config: Dict) -> List[Dict]:
        """Spread posts evenly over time"""
        from apscheduler.triggers.date import DateTrigger
        
        jobs = []
        start = datetime.fromisoformat(config.get('start_date', datetime.now().isoformat()))
        interval = config.get('interval_hours', 4)
        
        for i, post in enumerate(posts):
            scheduled_time = start + timedelta(hours=interval * i)
            
            job = self.scheduler.add_job(
                self._execute_post,
                trigger=DateTrigger(run_date=scheduled_time),
                args=[campaign_id, post],
                id=f"{campaign_id}_{post['platform']}_spread_{i}",
                name=f"Spread post to {post['platform']}"
            )
            
            jobs.append({
                'job_id': job.id,
                'platform': post['platform'],
                'scheduled_time': scheduled_time.isoformat(),
                'status': 'scheduled'
            })
        
        return jobs
    
    def _schedule_custom(self, campaign_id: str, posts: List[Dict], config: Dict) -> List[Dict]:
        """Schedule at custom specified times"""
        from apscheduler.triggers.date import DateTrigger
        
        jobs = []
        custom_times = config.get('times', [])
        
        for i, post in enumerate(posts):
            if i < len(custom_times):
                scheduled_time = datetime.fromisoformat(custom_times[i])
            else:
                scheduled_time = datetime.now() + timedelta(hours=i + 1)
            
            job = self.scheduler.add_job(
                self._execute_post,
                trigger=DateTrigger(run_date=scheduled_time),
                args=[campaign_id, post],
                id=f"{campaign_id}_{post['platform']}_custom_{i}",
                name=f"Custom post to {post['platform']}"
            )
            
            jobs.append({
                'job_id': job.id,
                'platform': post['platform'],
                'scheduled_time': scheduled_time.isoformat(),
                'status': 'scheduled'
            })
        
        return jobs
    
    def _execute_post(self, campaign_id: str, post: Dict):
        """Execute a scheduled post"""
        logger.info(f"Executing post for campaign {campaign_id} to {post['platform']}")
        
        try:
            result = self.platform_manager.post(
                platform=post['platform'],
                content=post['content'],
                hashtags=post.get('hashtags', [])
            )
            logger.info(f"Posted to {post['platform']}: {result}")
            return result
        except Exception as e:
            logger.error(f"Failed to post to {post['platform']}: {e}")
            return {'success': False, 'error': str(e)}
    
    def cancel_campaign(self, campaign_id: str) -> bool:
        """Cancel all scheduled jobs for a campaign"""
        if campaign_id not in self.job_registry:
            return False
        
        for job_info in self.job_registry[campaign_id]:
            try:
                self.scheduler.remove_job(job_info['job_id'])
            except Exception as e:
                logger.warning(f"Could not remove job {job_info['job_id']}: {e}")
        
        del self.job_registry[campaign_id]
        return True
    
    def get_campaign_schedule(self, campaign_id: str) -> List[Dict]:
        """Get schedule for a campaign"""
        return self.job_registry.get(campaign_id, [])
