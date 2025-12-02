
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
#Needed because it will create rows and objects
from .models import db, Profile
#Needed to encrypt/decrypt and AWS functions
from .crypto_utils import encrypt
#Basic AWS boto3 functions
from .aws_utils import build_session, list_regions, fetch_instances, bulk_tag_instances
#My curse to parse JSON from form
import json

#Setup the Bluprint that we will use in __init__.py
bp = Blueprint('main', __name__, template_folder='templates', static_folder='static')

#Index.html
#Its doing a query to SQL DB and get the active profile
#You can either navigate to Create Tag or to Create Profile.
@bp.route('/')
def index():
    profiles = Profile.query.all()
    active = Profile.query.filter_by(is_active=True).first()
    return render_template('index.html', profiles=profiles, active=active)


#Get all profiles
#Select the active one.
@bp.route('/profiles')
def profiles():
    items = Profile.query.order_by(Profile.is_active.desc(), Profile.name.asc()).all()
    return render_template('profiles.html', profiles=items)

#Adding a profile 
@bp.route('/profiles/add', methods=['GET','POST'])
def add_profile():
    if request.method == 'POST':
#Gets data from the form and saves to variables
        name = request.form['name'].strip()
        access_key = request.form['access_key'].strip()
        secret_key = request.form['secret_key'].strip()
        region = request.form.get('region','').strip() or None
#Checking if all fields are filled
        if not (name and access_key and secret_key):
            flash('All fields are required.', 'danger')
            return redirect(url_for('main.add_profile'))
#Checking if profile name exists. THIS WILL NOT check access keys and secret access key. A non protera way would be to check the hash of those keys.
        if Profile.query.filter_by(name=name).first():
            flash('Profile name already exists.', 'warning')
            return redirect(url_for('main.add_profile'))
        
#Feature Flag: Store credentials in Secrets Manager or encrypted in DB
        use_sm = current_app.config['FEATURE_FLAGS']['USE_SECRETS_MANAGER']
        if use_sm:
            from .secrets_manager import store_profile_credentials
            from .config import SECRETS_MANAGER_REGION
            store_profile_credentials(name, access_key, secret_key, SECRETS_MANAGER_REGION)
            prof = Profile(
                name=name,
                access_key_id='SECRETS_MANAGER',
                secret_access_key='SECRETS_MANAGER',
                default_region=region,
                use_secrets_manager=True
            )
        else:
#Create the profile object and save to DB
            prof = Profile(
                name=name,
                access_key_id=encrypt(access_key),
                secret_access_key=encrypt(secret_key),
                default_region=region,
                use_secrets_manager=False
            )
#SQLAlchemy add and commit Palo Alto stype with push and commit
        db.session.add(prof)
        db.session.commit()
        flash('Profile added.', 'success')
        return redirect(url_for('main.profiles'))
    return render_template('profile_add.html')

#Activate the profile
#The PID is passed from the form in profiles.html
@bp.route('/profiles/activate/<int:pid>', methods=['POST'])
def activate_profile(pid):
    for p in Profile.query.all():
        p.is_active = (p.id == pid)
    db.session.commit()
    flash('Active profile changed.', 'success')
    return redirect(url_for('main.profiles'))

#Get the profile by ID and delete it
#get_or_404 will return 404 !!!!! We need custom page for that
@bp.route('/profiles/delete/<int:pid>', methods=['POST'])
def delete_profile(pid):
    p = Profile.query.get_or_404(pid)
    if p.use_secrets_manager:
        from .secrets_manager import delete_profile_credentials
        from .config import SECRETS_MANAGER_REGION
        delete_profile_credentials(p.name, SECRETS_MANAGER_REGION)
    db.session.delete(p)
    db.session.commit()
    flash('Profile deleted.', 'info')
    return redirect(url_for('main.profiles'))

#Main page for Tags
@bp.route('/tagger')
def tagger():
    active = Profile.query.filter_by(is_active=True).first()
    if not active:
        flash('Please create and activate a profile first.', 'warning')
        return redirect(url_for('main.profiles'))
#use this to create a boto3 session
    session = build_session(active)
#This will list the regions. It uses boto3 function
    regions = list_regions(session)
#Gets Values from boto and returns to template. 
    return render_template('tagger.html', regions=regions, default_region=active.default_region or 'us-east-1')



@bp.route('/api/instances', methods=['GET','POST'])
def api_instances():
    region = request.values.get('region', 'us-east-1')
    ids_raw = request.values.get('instance_ids', '').strip()
    ids = [x.strip() for x in ids_raw.splitlines() if x.strip()] if ids_raw else None

    active = Profile.query.filter_by(is_active=True).first()
    if not active:
        return jsonify({'error':'No active profile'}), 400
    session = build_session(active)
    try:
        items = fetch_instances(session, region, instance_ids=ids)
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    return jsonify({'instances': items})

@bp.route('/tagger/execute', methods=['POST'])
def tagger_execute():
    active = Profile.query.filter_by(is_active=True).first()
    if not active:
        flash('No active profile.', 'danger')
        return redirect(url_for('main.tagger'))
    region = request.form['region']
    ids = request.form.getlist('selected_ids')
    tags_str = request.form.get('tags_json','{}')
    try:
        tags = json.loads(tags_str) if tags_str else {}
    except Exception:
        tags = {}
    if not tags:
        flash('Please add at least one tag (Key:Value).', 'warning')
        return redirect(url_for('main.tagger'))
    if not ids:
        flash('No instances selected.', 'warning')
        return redirect(url_for('main.tagger'))
    session = build_session(active)
    try:
        count = bulk_tag_instances(session, region, ids, tags)
        flash(f'Added {len(tags)} tag(s) to {count} instance(s) in {region}.', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'danger')
    return redirect(url_for('main.tagger'))

@bp.route('/tagger/upload', methods=['POST'])
def tagger_upload():
    file = request.files.get('file')
    region = request.form.get('region', 'us-east-1')
    if not file:
        flash('No file uploaded.', 'warning')
        return redirect(url_for('main.tagger'))
    content = file.read().decode('utf-8', errors='ignore')
    ids = [x.strip() for x in content.splitlines() if x.strip()]
    active = Profile.query.filter_by(is_active=True).first()
    session = build_session(active)
    try:
        instances = fetch_instances(session, region, instance_ids=ids)
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return redirect(url_for('main.tagger'))
    ids_str = ','.join([i['InstanceId'] for i in instances]) if instances else ''
    return render_template('verify.html', region=region, instances=instances, ids_str=ids_str)
