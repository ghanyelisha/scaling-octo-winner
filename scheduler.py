from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger


def send_reminder_emails(app):
    from extensions import db, mail
    from models import Task, User
    from flask_mail import Message

    with app.app_context():
        now = datetime.now(timezone.utc)

        tasks_24h = Task.query.filter(
            Task.reminder_24h_sent == False,
            Task.status != Task.STATUS_COMPLETED,
            Task.deadline <= now + timedelta(hours=24),
            Task.deadline > now,
        ).all()

        for task in tasks_24h:
            user = db.session.get(User, task.user_id)
            if user and user.email:
                try:
                    msg = Message(
                        subject=f'Reminder: "{task.title}" is due in 24 hours',
                        recipients=[user.email],
                        html=_build_email(user.username, task, '24 hours'),
                    )
                    mail.send(msg)
                except Exception as e:
                    app.logger.warning(f'Failed to send 24h reminder for task {task.id}: {e}')
            task.reminder_24h_sent = True

        tasks_1h = Task.query.filter(
            Task.reminder_1h_sent == False,
            Task.status != Task.STATUS_COMPLETED,
            Task.deadline <= now + timedelta(hours=1),
            Task.deadline > now,
        ).all()

        for task in tasks_1h:
            user = db.session.get(User, task.user_id)
            if user and user.email:
                try:
                    msg = Message(
                        subject=f'Reminder: "{task.title}" is due in 1 hour',
                        recipients=[user.email],
                        html=_build_email(user.username, task, '1 hour'),
                    )
                    mail.send(msg)
                except Exception as e:
                    app.logger.warning(f'Failed to send 1h reminder for task {task.id}: {e}')
            task.reminder_1h_sent = True

        db.session.commit()


def _build_email(username, task, timeframe):
    priority_color = {'high': '#dc3545', 'medium': '#ffc107', 'low': '#28a745'}.get(task.priority, '#6c757d')
    deadline_str = task.deadline.strftime('%A, %B %d, %Y at %I:%M %p')
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px;">
        <div style="background: #4f46e5; color: white; padding: 24px; border-radius: 8px 8px 0 0;">
            <h1 style="margin: 0; font-size: 22px;">Task Reminder</h1>
        </div>
        <div style="background: #f9fafb; padding: 24px; border: 1px solid #e5e7eb; border-radius: 0 0 8px 8px;">
            <p>Hi <strong>{username}</strong>,</p>
            <p>This is a reminder that your task is due in <strong>{timeframe}</strong>.</p>
            <div style="background: white; border-left: 4px solid {priority_color};
                        padding: 16px; margin: 16px 0; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,.1);">
                <h2 style="margin: 0 0 8px; font-size: 18px;">{task.title}</h2>
                <p style="margin: 0 0 8px; color: #6b7280;">{task.description or 'No description provided.'}</p>
                <p style="margin: 0;">
                    <strong>Deadline:</strong> {deadline_str}<br>
                    <strong>Priority:</strong>
                    <span style="color: {priority_color}; text-transform: capitalize;">{task.priority}</span>
                </p>
            </div>
            <p style="color: #6b7280; font-size: 13px; margin-top: 24px;">
                You received this email because you have task reminders enabled.
            </p>
        </div>
    </div>
    """


def init_scheduler(app):
    scheduler = BackgroundScheduler(timezone='UTC')
    scheduler.add_job(
        func=send_reminder_emails,
        args=[app],
        trigger=IntervalTrigger(minutes=5),
        id='email_reminders',
        name='Send task reminder emails',
        replace_existing=True,
    )
    scheduler.start()
    return scheduler
