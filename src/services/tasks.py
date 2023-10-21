from celery import Celery
from celery.schedules import crontab
from sqlalchemy.orm import Session

from src.conf.config import settings
from src.services.remove_expired_tokens import check_token


celery = Celery('tasks', broker=settings.broker_url, backend=settings.backend_url)


@celery.task(name='Remove expired tokens of logouted users')
async def remove_tokens(db: Session):
    result = await check_token(db)
    return result


celery.conf.beat_schedule = {
    'remove-tokens': {
        'task': 'src.services.tasks.remove_tokens',
        'schedule': crontab(minute="0", hour='*/6'),
    },
}
