from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='user')  # 'user', 'admin'
    reputation = db.Column(db.Integer, default=0)
    is_verified = db.Column(db.Boolean, default=False)
    mode = db.Column(db.String(10), default=None)  # 'learn' or 'teach'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    applications = db.relationship('Application', backref='author', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy=True)
    votes = db.relationship('Vote', backref='voter', lazy=True)
    reports = db.relationship('Report', backref='reporter', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_voted(self, application_id):
        return Vote.query.filter_by(user_id=self.id, application_id=application_id).first() is not None


class Domain(db.Model):
    __tablename__ = 'domains'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    icon = db.Column(db.String(50), default='🔬')
    description = db.Column(db.String(300))
    topics = db.relationship('Topic', backref='domain', lazy=True)


class Topic(db.Model):
    __tablename__ = 'topics'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    domain_id = db.Column(db.Integer, db.ForeignKey('domains.id'), nullable=False)
    explanation = db.Column(db.Text)
    applications = db.relationship('Application', backref='topic', lazy=True)


DIFFICULTY_LEVELS = ['Fundamental', 'Intermediate', 'Advanced']

DIFFICULTY_META = {
    'Fundamental': {
        'color': 'var(--diff-fundamental)',
        'bg': 'var(--diff-fundamental-bg)',
        'border': 'var(--diff-fundamental-border)',
        'icon': '🟢',
        'order': 1,
        'tooltip': 'Basic understanding — no prior domain knowledge required.',
    },
    'Intermediate': {
        'color': 'var(--diff-intermediate)',
        'bg': 'var(--diff-intermediate-bg)',
        'border': 'var(--diff-intermediate-border)',
        'icon': '🟡',
        'order': 2,
        'tooltip': 'Moderate complexity — some background knowledge helpful.',
    },
    'Advanced': {
        'color': 'var(--diff-advanced)',
        'bg': 'var(--diff-advanced-bg)',
        'border': 'var(--diff-advanced-border)',
        'icon': '🔴',
        'order': 3,
        'tooltip': 'High complexity — domain-specific or technical depth required.',
    },
}


class Application(db.Model):
    __tablename__ = 'applications'
    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    application_domain = db.Column(db.String(100))
    image_path = db.Column(db.String(300))
    video_url = db.Column(db.String(500))
    tags = db.Column(db.String(300))
    reference = db.Column(db.String(500))
    vote_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_approved = db.Column(db.Boolean, default=True)
    # ── NEW: difficulty classification ──────────────────
    difficulty_level = db.Column(db.String(20), nullable=False, default='Fundamental')

    comments = db.relationship('Comment', backref='application', lazy=True, cascade='all, delete-orphan')
    votes = db.relationship('Vote', backref='application', lazy=True, cascade='all, delete-orphan')
    reports = db.relationship('Report', backref='application', lazy=True, cascade='all, delete-orphan')

    def comment_count(self):
        return Comment.query.filter_by(application_id=self.id, parent_id=None).count()

    def get_tags_list(self):
        if self.tags:
            return [t.strip() for t in self.tags.split(',') if t.strip()]
        return []

    def get_difficulty_meta(self):
        """Return display metadata for this application's difficulty level."""
        return DIFFICULTY_META.get(self.difficulty_level, DIFFICULTY_META['Fundamental'])

    def difficulty_order(self):
        """Numeric sort key: Fundamental=1, Intermediate=2, Advanced=3."""
        return DIFFICULTY_META.get(self.difficulty_level, DIFFICULTY_META['Fundamental'])['order']


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)
    likes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    replies = db.relationship('Comment', backref=db.backref('parent', remote_side='Comment.id'), lazy=True)


class Vote(db.Model):
    __tablename__ = 'votes'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False)
    __table_args__ = (db.UniqueConstraint('user_id', 'application_id'),)


class Report(db.Model):
    __tablename__ = 'reports'
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reason = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, resolved, ignored
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
