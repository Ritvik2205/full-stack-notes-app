from flask import Blueprint, render_template, request, flash, jsonify, session, url_for, redirect
from flask_login import login_required, current_user
from .models import Note
from . import db
import json
from .auth import log_activity

views = Blueprint('views', __name__)

@views.route('/', methods=['GET', 'POST'])
@login_required
def home(): 
    if request.method == 'POST':
        note = request.form.get('note')

        if len(note) < 1:
            flash("Note too short", category="error")
        else:
            new_note = Note(data=note, user_id=current_user.id)
            db.session.add(new_note)
            db.session.commit()
            log_activity("note_added", f"User {current_user.firstName} added a note.")
            flash("Note added", category="success")
        return render_template("home.html", user=current_user)
    # else:
        # if 'user' in session:
    return render_template("home.html", user=current_user)
        # else:
        #     return redirect(url_for("auth.signup"))


@views.route("/delete-note", methods=["POST"])
def delete_note():
    note = json.loads(request.data)
    noteId = note['noteId']
    note = Note.query.get(noteId)
    if note:
        if note.user_id == current_user.id:
            db.session.delete(note)
            db.session.commit()
            log_activity("note_deleted", f"User {current_user.firstName} deleted a note")
    return jsonify({})