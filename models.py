from extensions import db, login_manager
from flask_login import UserMixin
from datetime import datetime


# ── User loader cho Flask-Login ───────────────────────────
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ══════════════════════════════════════════════════════════
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id            = db.Column(db.Integer, primary_key=True)
    full_name     = db.Column(db.String(100), nullable=False)
    email         = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    phone         = db.Column(db.String(15))
    role          = db.Column(db.Enum('student', 'tutor', 'admin'), nullable=False, default='student')
    is_active     = db.Column(db.Boolean, default=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    # Quan hệ
    tutor_profile  = db.relationship('TutorProfile', backref='user', uselist=False)
    availabilities = db.relationship('Availability', backref='tutor', lazy='dynamic')
    bookings_as_student = db.relationship('Booking', foreign_keys='Booking.student_id', backref='student', lazy='dynamic')
    bookings_as_tutor   = db.relationship('Booking', foreign_keys='Booking.tutor_id',   backref='tutor_user', lazy='dynamic')

    def is_student(self): return self.role == 'student'
    def is_tutor(self):   return self.role == 'tutor'
    def is_admin(self):   return self.role == 'admin'

    def __repr__(self):
        return f'<User {self.email} [{self.role}]>'


# ══════════════════════════════════════════════════════════
class Subject(db.Model):
    __tablename__ = 'subjects'

    id        = db.Column(db.Integer, primary_key=True)
    name      = db.Column(db.String(100), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    tutor_profiles = db.relationship('TutorProfile', backref='subject', lazy='dynamic')


# ══════════════════════════════════════════════════════════
class TutorProfile(db.Model):
    __tablename__ = 'tutor_profiles'

    id               = db.Column(db.Integer, primary_key=True)
    user_id          = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    subject_id       = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    bio              = db.Column(db.Text)
    experience_years = db.Column(db.Integer, default=0)
    hourly_rate      = db.Column(db.Numeric(10, 2), default=100000)
    rating_avg       = db.Column(db.Numeric(3, 2), default=0.00)
    total_reviews    = db.Column(db.Integer, default=0)
    is_verified      = db.Column(db.Boolean, default=False)


# ══════════════════════════════════════════════════════════
class Availability(db.Model):
    __tablename__ = 'availabilities'

    id         = db.Column(db.Integer, primary_key=True)
    tutor_id   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    avail_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.String(5), nullable=False)   # "08:00"
    end_time   = db.Column(db.String(5), nullable=False)   # "09:00"
    is_booked  = db.Column(db.Boolean, default=False)

    __table_args__ = (
        db.UniqueConstraint('tutor_id', 'avail_date', 'start_time', name='uq_slot'),
    )


# ══════════════════════════════════════════════════════════
class Booking(db.Model):
    __tablename__ = 'bookings'

    id          = db.Column(db.Integer, primary_key=True)
    student_id  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tutor_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    avail_id    = db.Column(db.Integer, db.ForeignKey('availabilities.id'), nullable=False)
    status      = db.Column(db.Enum('pending', 'confirmed', 'completed', 'cancelled'),
                            nullable=False, default='pending')
    note        = db.Column(db.Text)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    availability = db.relationship('Availability', backref='booking', uselist=False)