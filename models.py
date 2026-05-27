from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from extensions import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    tasks = db.relationship('Task', backref='owner', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Task(db.Model):
    __tablename__ = 'tasks'

    STATUS_PENDING = 'pending'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_COMPLETED = 'completed'
    STATUS_OVERDUE = 'overdue'

    PRIORITY_LOW = 'low'
    PRIORITY_MEDIUM = 'medium'
    PRIORITY_HIGH = 'high'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, default='')
    deadline = db.Column(db.DateTime, nullable=False)
    priority = db.Column(db.String(16), default=PRIORITY_MEDIUM)
    status = db.Column(db.String(16), default=STATUS_PENDING)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))
    reminder_24h_sent = db.Column(db.Boolean, default=False)
    reminder_1h_sent = db.Column(db.Boolean, default=False)

    @property
    def deadline_utc(self):
        if self.deadline.tzinfo is None:
            return self.deadline.replace(tzinfo=timezone.utc)
        return self.deadline

    @property
    def is_overdue(self):
        return datetime.now(timezone.utc) > self.deadline_utc and self.status != self.STATUS_COMPLETED

    @property
    def seconds_until_deadline(self):
        delta = self.deadline_utc - datetime.now(timezone.utc)
        return max(0, int(delta.total_seconds()))

    @property
    def priority_class(self):
        return {'low': 'success', 'medium': 'warning', 'high': 'danger'}.get(self.priority, 'secondary')

    @property
    def status_class(self):
        return {
            'pending': 'secondary',
            'in_progress': 'primary',
            'completed': 'success',
            'overdue': 'danger',
        }.get(self.status, 'secondary')

    def __repr__(self):
        return f'<Task {self.title}>'


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
