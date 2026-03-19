from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from models import User, Subject

auth_bp = Blueprint('auth', __name__)


# ── Trang chủ: redirect theo role ─────────────────────────
@auth_bp.route('/')
def index():
    if current_user.is_authenticated:
        return _redirect_by_role(current_user)
    return redirect(url_for('auth.login'))


# ── Đăng nhập ─────────────────────────────────────────────
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return _redirect_by_role(current_user)

    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password_hash, password):
            flash('Email hoặc mật khẩu không đúng.', 'danger')
            return render_template('auth/login.html')

        if not user.is_active:
            flash('Tài khoản của bạn đã bị khóa. Liên hệ quản trị viên.', 'danger')
            return render_template('auth/login.html')

        login_user(user)
        flash(f'Chào mừng, {user.full_name}!', 'success')
        return _redirect_by_role(user)

    return render_template('auth/login.html')


# ── Đăng ký ───────────────────────────────────────────────
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return _redirect_by_role(current_user)

    subjects = Subject.query.filter_by(is_active=True).all()

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email     = request.form.get('email', '').strip().lower()
        phone     = request.form.get('phone', '').strip()
        password  = request.form.get('password', '')
        confirm   = request.form.get('confirm_password', '')
        role      = request.form.get('role', 'student')

        # ── Validate chung ────────────────────────────────
        if not full_name or not email or not password:
            flash('Vui lòng điền đầy đủ thông tin bắt buộc.', 'danger')
            return render_template('auth/register.html', subjects=subjects)

        if password != confirm:
            flash('Mật khẩu xác nhận không khớp.', 'danger')
            return render_template('auth/register.html', subjects=subjects)

        if len(password) < 6:
            flash('Mật khẩu phải có ít nhất 6 ký tự.', 'danger')
            return render_template('auth/register.html', subjects=subjects)

        if role not in ('student', 'tutor'):
            role = 'student'

        if User.query.filter_by(email=email).first():
            flash('Email này đã được đăng ký. Vui lòng dùng email khác.', 'danger')
            return render_template('auth/register.html', subjects=subjects)

        # ── Validate riêng cho gia sư ─────────────────────
        if role == 'tutor':
            subject_id    = request.form.get('subject_id', '').strip()
            hourly_rate   = request.form.get('hourly_rate', '').strip()
            exp_years     = request.form.get('experience_years', '0').strip()
            bio           = request.form.get('bio', '').strip()

            if not subject_id:
                flash('Vui lòng chọn môn học bạn muốn dạy.', 'danger')
                return render_template('auth/register.html', subjects=subjects)

            if not hourly_rate:
                flash('Vui lòng nhập giá dạy mỗi giờ.', 'danger')
                return render_template('auth/register.html', subjects=subjects)

            try:
                hourly_rate = float(hourly_rate)
                if hourly_rate < 50000:
                    flash('Giá dạy tối thiểu là 50,000đ/giờ.', 'danger')
                    return render_template('auth/register.html', subjects=subjects)
            except ValueError:
                flash('Giá dạy không hợp lệ.', 'danger')
                return render_template('auth/register.html', subjects=subjects)

            try:
                exp_years = int(exp_years)
            except ValueError:
                exp_years = 0

        # ── Tạo User ──────────────────────────────────────
        user = User(
            full_name=full_name,
            email=email,
            phone=phone if phone else None,
            password_hash=generate_password_hash(password),
            role=role
        )
        db.session.add(user)
        db.session.flush()  # lấy user.id trước khi commit

        # ── Tạo TutorProfile nếu là gia sư ────────────────
        if role == 'tutor':
            from models import TutorProfile
            tp = TutorProfile(
                user_id=user.id,
                subject_id=int(subject_id),
                hourly_rate=hourly_rate,
                experience_years=exp_years,
                bio=bio if bio else None,
                rating_avg=0.00,
                total_reviews=0
            )
            db.session.add(tp)

        db.session.commit()

        if role == 'tutor':
            flash(f'Đăng ký gia sư thành công! Hồ sơ của bạn đã hiển thị trong tìm kiếm.', 'success')
        else:
            flash('Đăng ký thành công! Vui lòng đăng nhập.', 'success')

        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', subjects=subjects)


# ── Đăng xuất ─────────────────────────────────────────────
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Bạn đã đăng xuất.', 'info')
    return redirect(url_for('auth.login'))


# ── Helper ────────────────────────────────────────────────
def _redirect_by_role(user):
    if user.is_admin():  return redirect(url_for('admin.dashboard'))
    if user.is_tutor():  return redirect(url_for('tutor.dashboard'))
    return redirect(url_for('student.dashboard'))