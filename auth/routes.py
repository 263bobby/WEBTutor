from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from models import User

auth_bp = Blueprint('auth', __name__)


# ── Trang chủ: redirect theo role ────────────────────────
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

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email     = request.form.get('email', '').strip().lower()
        phone     = request.form.get('phone', '').strip()
        password  = request.form.get('password', '')
        confirm   = request.form.get('confirm_password', '')
        role      = request.form.get('role', 'student')

        # Validate cơ bản
        if not full_name or not email or not password:
            flash('Vui lòng điền đầy đủ thông tin.', 'danger')
            return render_template('auth/register.html')

        if password != confirm:
            flash('Mật khẩu xác nhận không khớp.', 'danger')
            return render_template('auth/register.html')

        if len(password) < 6:
            flash('Mật khẩu phải có ít nhất 6 ký tự.', 'danger')
            return render_template('auth/register.html')

        if role not in ('student', 'tutor'):
            role = 'student'

        if User.query.filter_by(email=email).first():
            flash('Email này đã được đăng ký.', 'danger')
            return render_template('auth/register.html')

        user = User(
            full_name=full_name,
            email=email,
            phone=phone,
            password_hash=generate_password_hash(password),
            role=role
        )
        db.session.add(user)

        # Nếu đăng ký làm gia sư, tạo profile trống
        if role == 'tutor':
            from models import TutorProfile, Subject
            db.session.flush()
            subj = Subject.query.first()
            tp = TutorProfile(user_id=user.id,
                              subject_id=subj.id if subj else 1,
                              hourly_rate=100000)
            db.session.add(tp)

        db.session.commit()
        flash('Đăng ký thành công! Vui lòng đăng nhập.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


# ── Đăng xuất ─────────────────────────────────────────────
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Bạn đã đăng xuất.', 'info')
    return redirect(url_for('auth.login'))


# ── Helper ────────────────────────────────────────────────
def _redirect_by_role(user):
    if user.is_admin():   return redirect(url_for('admin.dashboard'))
    if user.is_tutor():   return redirect(url_for('tutor.dashboard'))
    return redirect(url_for('student.search'))