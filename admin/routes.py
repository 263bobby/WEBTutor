from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from extensions import db
from models import User, Booking, TutorProfile

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Trang này chỉ dành cho quản trị viên.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


# ── Dashboard ─────────────────────────────────────────────
@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total_users    = User.query.filter(User.role != 'admin').count()
    total_tutors   = User.query.filter_by(role='tutor').count()
    total_students = User.query.filter_by(role='student').count()
    total_bookings = Booking.query.count()
    pending_count  = Booking.query.filter_by(status='pending').count()

    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(10).all()

    return render_template('admin/dashboard.html',
                           total_users=total_users,
                           total_tutors=total_tutors,
                           total_students=total_students,
                           total_bookings=total_bookings,
                           pending_count=pending_count,
                           recent_bookings=recent_bookings)


# ── Danh sách người dùng ──────────────────────────────────
@admin_bp.route('/users')
@login_required
@admin_required
def users():
    role_filter = 'tutor'  # mặc định xem gia sư
    all_tutors   = User.query.filter_by(role='tutor').order_by(User.created_at.desc()).all()
    all_students = User.query.filter_by(role='student').order_by(User.created_at.desc()).all()
    return render_template('admin/users.html',
                           tutors=all_tutors,
                           students=all_students)


# ── Khóa / Mở tài khoản ───────────────────────────────────
@admin_bp.route('/users/toggle/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_admin():
        flash('Không thể thay đổi trạng thái tài khoản admin.', 'danger')
        return redirect(url_for('admin.users'))

    user.is_active = not user.is_active
    db.session.commit()
    status = 'mở khóa' if user.is_active else 'khóa'
    flash(f'Đã {status} tài khoản {user.full_name}.', 'success')
    return redirect(url_for('admin.users'))


# ── Tất cả đơn booking ────────────────────────────────────
@admin_bp.route('/bookings')
@login_required
@admin_required
def bookings():
    status_filter = 'all'
    query = Booking.query.order_by(Booking.created_at.desc())
    bookings = query.all()
    return render_template('admin/bookings.html', bookings=bookings)