from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_wtf import CSRFProtect
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms import ValidationError
from wtforms.validators import DataRequired
from flask_migrate import Migrate

from flask_debugtoolbar import DebugToolbarExtension

app = Flask(__name__, static_url_path='/static', static_folder='static')
app.config.from_pyfile('../instance/config.py')
app.config["WTF_CSRF_ENABLED"] = False

secret_key = app.config['SECRET_KEY']

# Enable the Debug Toolbar
app.debug = False

toolbar = DebugToolbarExtension(app)


# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///names.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Define database model

class Name(db.Model):
    
    name_id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    grade = db.Column(db.Integer, nullable=True)
    choices = db.relationship('Choices', back_populates='name')

class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(100), nullable=False)
    choices = db.relationship('Choices', back_populates='user')

class Choices(db.Model):
    choice_id = db.Column(db.Integer, primary_key=True)
    name_id = db.Column(db.Integer, db.ForeignKey('name.name_id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    video_url = db.Column(db.String(100), nullable=False)
    attribute = db.Column(db.String(255), nullable=False)
    name = db.relationship('Name', back_populates='choices')
    user = db.relationship('User', back_populates='choices')

#insert users
def insert_users(user_name):
    if not User.query.filter_by(user_name=user_name).first():
         new_user = User(user_name=user_name)
         db.session.add(new_user)
         db.session.commit()
         print(f"User {user_name} inserted into the database.")
    else:
        print(f'{user_name} already in database')
        

# Create the database tables

with app.app_context():
     db.create_all()

##handle forms 

def validateName(form, field):
    name = field.data.split()
    if len(name) < 2:
        raise ValidationError('Please enter your full name (first name and last name).')

class lowerCaseStringField(StringField):
    def process_formdata(self, valuelist):
        if valuelist:
            self.data = valuelist[0].lower()

class nameForm(FlaskForm):
    name = lowerCaseStringField('Input First And Last Name:', validators=[DataRequired(), validateName])
    submit = SubmitField('Play')

# Clear session on visiting index page 
@app.before_request
def clear_session():
    if request.method == 'GET' and request.endpoint == 'index':
        session.clear()
        print("session-cleared")

##handle routes

@app.route('/', methods=['GET','POST'])
def index():
    #insert users

    insert_users('Patrick')
    insert_users('Cara')
    insert_users('Nate')
    insert_users('Ruth')
    insert_users('Jeremy')

    #process form data
    form = nameForm()
    if form.validate_on_submit():
        name = form.name.data
        grade = request.form.get('grade')  # Get the selected grade

        new_name = Name(full_name=name, grade=grade)  # Create a new Name instance
        db.session.add(new_name)
        db.session.commit()
        session['full_name'] = name
        #initialize user and screen number
        session['user_id'] = 1
        session['screen_number'] = 0
        ##debug
        for name in Name.query.all():
            print (name.full_name)

        return redirect(url_for('screen1'))
    else:
        print(form.errors)
    return render_template('index.html', form=form, options=[6,7,8])

@app.route('/screen1',  methods=['GET','POST'])
def screen1():
    name = session.get('full_name')
    user_name = session.get('user_name')
    vidSet = session.get('screen_number')
    

    return render_template('screen1.html', name=name, vidSet=vidSet, user_name=user_name)

@app.route('/update_screen_number', methods=['GET', 'POST'])
def update_screen_number():
    session['screen_number'] += 1
    screen_number = session.get('screen_number')

    return jsonify({'screen_number': screen_number})

@app.route('/go_to_results_screen', methods=['GET'])
def go_to_results_screen():

    return redirect(url_for('user_results'))

@app.route('/update_current_video', methods=['POST'])
def update_current_video():
    data = request.json
    session['url'] = data.get('url')
    session['attribute'] = data.get('attribute')
    url = session.get('url')
    attribute = session.get('attribute')

    return jsonify({
        'message': 'Current Video updated successfully',
        'url': url,
        'attribute': attribute
    })
    
@app.route('/update_choice', methods=['POST'])
def update_choice():
    
    full_name = session.get('full_name')
    user_id = session.get('user_id')
    name_instance = Name.query.filter_by(full_name=full_name).first()
    user_instance = User.query.filter_by(user_id=user_id).first()
    video_url = session.get('url')
    attribute = session.get('attribute')

    new_choice = Choices(name=name_instance, user=user_instance, video_url=video_url, attribute=attribute)
    db.session.add(new_choice)
    db.session.commit()

    return jsonify({
        'message': 'Choice updated successfully',
        'full_name': full_name,
        'user_id': user_id,
        'video_url': video_url,
        'attribute': attribute
    })

@app.route('/check_user_image')
def check_user_image():
    user_id = session.get('user_id')
    return jsonify ({'user_id': user_id})

@app.route('/check_user_name')
def check_user_name():
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    return jsonify ({'user_name': user.user_name if user else None})

@app.route('/check_screen_number')
def check_screen_number():
    screen_number = session.get('screen_number')
    return jsonify ({'screen_number': screen_number})

@app.route('/increment_user_id', methods=['POST'])
def increment_user_id():
    session['user_id'] += 1
    if session['user_id'] == 6:
        session['user_id'] = 1
    user_id = session.get('user_id')
    
    return jsonify({'user_id': user_id})

@app.route('/decrement_user_id', methods=['POST'])
def decrement_user_id():
    session['user_id'] -= 1
    if session['user_id'] == 0:
        session['user_id'] = 5
    user_id = session.get('user_id')
    
    return jsonify({'user_id': user_id})

@app.route('/query_sql', methods=['get'])
def query_sql():
    full_name = session['full_name']
    user_id = session['user_id']
    name = db.session.query(Name).filter(Name.full_name == full_name).first()
    name_id = name.name_id

    total_choices = db.session.query(func.count(Choices.choice_id)).\
    filter(Choices.name_id == name_id).\
    filter(Choices.user_id == user_id).\
    scalar()

    attribute_counts = db.session.query(Choices.attribute, func.count(Choices.choice_id)).\
    filter(Choices.name_id == name_id).\
    filter(Choices.user_id == user_id).\
    group_by(Choices.attribute).all()

    attribute_counts_dict = [{'attribute': attr, 'count': count} for attr, count in attribute_counts] ## for debug logging

    attribute_percentages = [(attr, count / total_choices * 100) for attr, count in attribute_counts]
    
    attribute_percentages_dict = {}
    for attr, count in attribute_counts:
        percentage = count / total_choices * 100
        percentage = round(percentage, 2)
        attribute_percentages_dict[attr] = percentage

    return jsonify({'attribute_percentages_dict': attribute_percentages_dict})

@app.route('/query_sql_combined', methods=['get'])
def query_sql_combined():
    user_id = session['user_id']

    attribute_counts = db.session.query(Choices.attribute, func.count(Choices.choice_id)).\
    filter(Choices.user_id == user_id).\
    group_by(Choices.attribute).all()

    total_choices = sum(count for _, count in attribute_counts)

    average_attribute_percentages = {}
    for attr, count in attribute_counts:
        percentage = count / total_choices * 100
        percentage = round(percentage, 2)
        average_attribute_percentages[attr] = percentage

    return jsonify({'average_attribute_percentages':average_attribute_percentages})

@app.route('/user-results')
def user_results():
    return render_template('user-results.html')

@app.route('/final-results')
def final_results():
    return render_template('final-results.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
    
    
    
    
       
    
