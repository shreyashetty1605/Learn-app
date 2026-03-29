from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, Domain, Topic, Application, User, Report
from sqlalchemy import or_

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.mode_select'))
    featured = Application.query.order_by(Application.vote_count.desc()).limit(3).all()
    domains = Domain.query.all()
    return render_template('index.html', featured=featured, domains=domains)


@main_bp.route('/mode', methods=['GET', 'POST'])
@login_required
def mode_select():
    if request.method == 'POST':
        mode = request.form.get('mode')
        if mode in ('learn', 'teach'):
            current_user.mode = mode
            db.session.commit()
            if mode == 'learn':
                return redirect(url_for('main.domains'))
            else:
                return redirect(url_for('app_routes.add_application'))
    return render_template('mode_select.html')


@main_bp.route('/domains')
@login_required
def domains():
    all_domains = Domain.query.all()
    return render_template('domains.html', domains=all_domains)


@main_bp.route('/domain/<int:domain_id>')
@login_required
def domain_detail(domain_id):
    domain = Domain.query.get_or_404(domain_id)
    topics = Topic.query.filter_by(domain_id=domain_id).all()
    return render_template('domain_detail.html', domain=domain, topics=topics)


@main_bp.route('/topic/<int:topic_id>')
@login_required
def topic_detail(topic_id):
    topic = Topic.query.get_or_404(topic_id)
    sort = request.args.get('sort', 'votes')
    difficulty_filter = request.args.get('difficulty', 'all')  # 'all' | 'Fundamental' | 'Intermediate' | 'Advanced'

    # Base query — approved apps for this topic
    query = Application.query.filter_by(topic_id=topic_id, is_approved=True)

    # Apply difficulty filter if set
    if difficulty_filter != 'all':
        query = query.filter(Application.difficulty_level == difficulty_filter)

    # Apply sort
    if sort == 'recent':
        apps = query.order_by(Application.created_at.desc()).all()
    elif sort == 'discussed':
        apps = sorted(query.all(), key=lambda a: a.comment_count(), reverse=True)
    elif sort == 'difficulty':
        # Progression: Fundamental → Intermediate → Advanced
        from models import DIFFICULTY_META
        apps = sorted(query.all(), key=lambda a: a.difficulty_order())
    else:
        apps = query.order_by(Application.vote_count.desc()).all()

    # Build per-difficulty counts for the filter pills (always on the full set)
    all_apps = Application.query.filter_by(topic_id=topic_id, is_approved=True).all()
    from models import DIFFICULTY_LEVELS
    difficulty_counts = {level: 0 for level in DIFFICULTY_LEVELS}
    for a in all_apps:
        if a.difficulty_level in difficulty_counts:
            difficulty_counts[a.difficulty_level] += 1

    return render_template('topic_detail.html',
                           topic=topic,
                           applications=apps,
                           sort=sort,
                           difficulty_filter=difficulty_filter,
                           difficulty_counts=difficulty_counts,
                           difficulty_levels=DIFFICULTY_LEVELS)


@main_bp.route('/search')
@login_required
def search():
    q = request.args.get('q', '').strip()
    if not q:
        return render_template('search.html', results=[], query='')

    topics = Topic.query.filter(Topic.name.ilike(f'%{q}%')).all()
    apps = Application.query.filter(
        or_(
            Application.title.ilike(f'%{q}%'),
            Application.description.ilike(f'%{q}%'),
            Application.tags.ilike(f'%{q}%'),
        ),
        Application.is_approved == True
    ).order_by(Application.vote_count.desc()).all()

    return render_template('search.html', topics=topics, applications=apps, query=q)


@main_bp.route('/api/search-suggest')
@login_required
def search_suggest():
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])
    topics = Topic.query.filter(Topic.name.ilike(f'%{q}%')).limit(4).all()
    apps = Application.query.filter(Application.title.ilike(f'%{q}%'), Application.is_approved == True).limit(4).all()
    results = []
    for t in topics:
        results.append({'type': 'topic', 'text': t.name, 'url': url_for('main.topic_detail', topic_id=t.id)})
    for a in apps:
        results.append({'type': 'application', 'text': a.title, 'url': url_for('app_routes.application_detail', app_id=a.id)})
    return jsonify(results)


@main_bp.route('/dashboard')
@login_required
def dashboard():
    user_apps = Application.query.filter_by(user_id=current_user.id).order_by(Application.created_at.desc()).all()
    total_votes = sum(a.vote_count for a in user_apps)
    return render_template('dashboard.html', user_apps=user_apps, total_votes=total_votes)


@main_bp.route('/switch-mode/<mode>')
@login_required
def switch_mode(mode):
    if mode in ('learn', 'teach'):
        current_user.mode = mode
        db.session.commit()
        if mode == 'learn':
            return redirect(url_for('main.domains'))
        else:
            return redirect(url_for('app_routes.add_application'))
    return redirect(url_for('main.domains'))


# ── Admin ──────────────────────────────────────────────
@main_bp.route('/admin')
@login_required
def admin_panel():
    if current_user.role != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('main.domains'))
    pending_reports = Report.query.filter_by(status='pending').order_by(Report.created_at.desc()).all()
    all_users = User.query.order_by(User.created_at.desc()).all()
    total_apps = Application.query.count()
    total_users = User.query.count()
    pending_count = len(pending_reports)
    return render_template('admin.html',
                           reports=pending_reports,
                           users=all_users,
                           total_apps=total_apps,
                           total_users=total_users,
                           pending_count=pending_count)


@main_bp.route('/admin/report/<int:report_id>/<action>')
@login_required
def handle_report(report_id, action):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    report = Report.query.get_or_404(report_id)
    if action == 'resolve':
        report.status = 'resolved'
    elif action == 'ignore':
        report.status = 'ignored'
    elif action == 'delete':
        app_to_delete = Application.query.get(report.application_id)
        if app_to_delete:
            db.session.delete(app_to_delete)
        report.status = 'resolved'
    db.session.commit()
    flash('Report handled.', 'success')
    return redirect(url_for('main.admin_panel'))


@main_bp.route('/admin/verify/<int:user_id>')
@login_required
def verify_user(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('main.domains'))
    user = User.query.get_or_404(user_id)
    user.is_verified = not user.is_verified
    db.session.commit()
    flash(f'{"Verified" if user.is_verified else "Unverified"} {user.name}.', 'success')
    return redirect(url_for('main.admin_panel'))
