from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from models import db, Application, Comment, Vote, Report, Topic, Domain, DIFFICULTY_LEVELS
from werkzeug.utils import secure_filename
import os
import uuid

app_bp = Blueprint('app_routes', __name__)

ALLOWED_IMAGE = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_VIDEO = {'mp4', 'mov', 'avi', 'webm'}


def allowed_file(filename, allowed_set):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_set


def save_file(file, folder=''):
    ext = file.filename.rsplit('.', 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    upload_dir = current_app.config['UPLOAD_FOLDER']
    if folder:
        upload_dir = os.path.join(upload_dir, folder)
        os.makedirs(upload_dir, exist_ok=True)
    path = os.path.join(upload_dir, unique_name)
    file.save(path)
    return os.path.join(folder, unique_name).replace('\\', '/') if folder else unique_name


@app_bp.route('/application/add', methods=['GET', 'POST'])
@login_required
def add_application():
    domains = Domain.query.all()
    topics = Topic.query.all()
    if request.method == 'POST':
        topic_id = request.form.get('topic_id')
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        application_domain = request.form.get('application_domain', '').strip()
        tags = request.form.get('tags', '').strip()
        reference = request.form.get('reference', '').strip()
        video_url = request.form.get('video_url', '').strip()
        difficulty_level = request.form.get('difficulty_level', '').strip()

        # Validation
        errors = []
        if not topic_id:
            errors.append('Please select a concept/topic.')
        if not title:
            errors.append('Title is required.')
        if not description:
            errors.append('Description is required.')
        if len(description.split()) > 200:
            errors.append('Description must be under 150 words.')
        if difficulty_level not in DIFFICULTY_LEVELS:
            errors.append('Please select a valid difficulty level.')

        # Image (required)
        image_file = request.files.get('image')
        image_path = None
        if image_file and image_file.filename:
            if not allowed_file(image_file.filename, ALLOWED_IMAGE):
                errors.append('Image must be PNG, JPG, JPEG, GIF or WEBP.')
            else:
                image_path = save_file(image_file)
        else:
            errors.append('An image is required.')

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('add_application.html', domains=domains, topics=topics,
                                   difficulty_levels=DIFFICULTY_LEVELS)

        # Optional video
        video_path = None
        video_file = request.files.get('video')
        if video_file and video_file.filename:
            if allowed_file(video_file.filename, ALLOWED_VIDEO):
                video_path = save_file(video_file, 'videos')
            else:
                flash('Invalid video format. Accepted: mp4, mov, avi, webm', 'warning')

        final_video = video_path or video_url or None

        new_app = Application(
            topic_id=int(topic_id),
            user_id=current_user.id,
            title=title,
            description=description,
            application_domain=application_domain,
            image_path=image_path,
            video_url=final_video,
            tags=tags,
            reference=reference,
            difficulty_level=difficulty_level,
        )
        db.session.add(new_app)
        current_user.reputation += 10
        db.session.commit()
        flash('Application submitted successfully! 🎉', 'success')
        return redirect(url_for('app_routes.application_detail', app_id=new_app.id))

    return render_template('add_application.html', domains=domains, topics=topics,
                           difficulty_levels=DIFFICULTY_LEVELS)


@app_bp.route('/application/<int:app_id>')
@login_required
def application_detail(app_id):
    application = Application.query.get_or_404(app_id)
    top_comments = Comment.query.filter_by(application_id=app_id, parent_id=None).order_by(Comment.created_at.desc()).all()
    user_voted = current_user.has_voted(app_id)
    related = Application.query.filter(
        Application.topic_id == application.topic_id,
        Application.id != app_id,
        Application.is_approved == True
    ).order_by(Application.vote_count.desc()).limit(3).all()
    return render_template('application_detail.html',
                           application=application,
                           comments=top_comments,
                           user_voted=user_voted,
                           related=related)


@app_bp.route('/application/<int:app_id>/vote', methods=['POST'])
@login_required
def vote(app_id):
    application = Application.query.get_or_404(app_id)
    existing = Vote.query.filter_by(user_id=current_user.id, application_id=app_id).first()
    if existing:
        db.session.delete(existing)
        application.vote_count = max(0, application.vote_count - 1)
        voted = False
    else:
        new_vote = Vote(user_id=current_user.id, application_id=app_id)
        db.session.add(new_vote)
        application.vote_count += 1
        application.author.reputation += 2
        voted = True
    db.session.commit()
    return jsonify({'vote_count': application.vote_count, 'voted': voted})


@app_bp.route('/application/<int:app_id>/comment', methods=['POST'])
@login_required
def add_comment(app_id):
    content = request.form.get('content', '').strip()
    parent_id = request.form.get('parent_id')
    if not content:
        flash('Comment cannot be empty.', 'error')
        return redirect(url_for('app_routes.application_detail', app_id=app_id))
    comment = Comment(
        application_id=app_id,
        user_id=current_user.id,
        content=content,
        parent_id=int(parent_id) if parent_id else None
    )
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('app_routes.application_detail', app_id=app_id) + '#comments')


@app_bp.route('/comment/<int:comment_id>/like', methods=['POST'])
@login_required
def like_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    comment.likes += 1
    db.session.commit()
    return jsonify({'likes': comment.likes})


@app_bp.route('/application/<int:app_id>/report', methods=['POST'])
@login_required
def report_application(app_id):
    reason = request.form.get('reason', '').strip()
    details = request.form.get('details', '').strip()
    if not reason:
        flash('Please select a reason.', 'error')
        return redirect(url_for('app_routes.application_detail', app_id=app_id))
    existing = Report.query.filter_by(application_id=app_id, user_id=current_user.id).first()
    if existing:
        flash('You have already reported this application.', 'warning')
        return redirect(url_for('app_routes.application_detail', app_id=app_id))
    report = Report(application_id=app_id, user_id=current_user.id, reason=reason, details=details)
    db.session.add(report)
    db.session.commit()
    flash('Report submitted. Our team will review it.', 'success')
    return redirect(url_for('app_routes.application_detail', app_id=app_id))


@app_bp.route('/api/topics-by-domain/<int:domain_id>')
@login_required
def topics_by_domain(domain_id):
    topics = Topic.query.filter_by(domain_id=domain_id).all()
    return jsonify([{'id': t.id, 'name': t.name} for t in topics])
