from flask import Blueprint, render_template
from flask import flash , request, url_for, redirect
from flask_login import login_user, login_required, logout_user, current_user
from .models import db, User, UsageHistory, Balance, Recharge, MonetaryRechargePlan, MobileDataPlan, AgencyLocation, Question, Answer
from werkzeug.security import generate_password_hash, check_password_hash

blp = Blueprint('blp', __name__)

# these are the web application routes handling the views and web pages and connected to the front end
# Authentication routes----------------------------------------------
@blp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phoneNumber = request.form.get('phoneNumber')
        password = request.form.get('password')

        user = User.query.filter_by(phoneNumber=phoneNumber).first()
        if user:
            if user.passwordHash is None:
                flash('No account exists for this phone number. Please create an account first.', category='E')
            elif check_password_hash(user.passwordHash, password):
                flash('Logged in successfully!', category='S')
                login_user(user, remember=True)
                return redirect(url_for('blp.home'))
            else:
                flash('Password is incorrect! Try again.', category='E')
        else:
            flash('Phone number does not exist.', category='E')


    return render_template("login.html",user=current_user)


@blp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        phoneNumber = request.form.get('phoneNumber')
        username = request.form.get('username')
        password = request.form.get('password')
        passwordC = request.form.get('passwordC')

        user = User.query.filter_by(phoneNumber=phoneNumber).first()
        if not user:
            flash('your phone number does not exist!', category='E')
        elif user.username:
            flash('This account already exists !', category='E')
        elif len(username) < 3:
            flash('Username too short!', category='E')
        elif len(password) < 10:
            flash('Password too short! at least 10 characters please.', category='E')
        elif password != passwordC:
            flash('Passwords don\'t match.', category='E')
        else:
            user.username = username
            user.passwordHash = generate_password_hash(password, method='pbkdf2:sha256')  # Ensure to hash the password
            db.session.commit()
            login_user(user, remember=True)
            flash('your Account is successfully created!', category='S')
            return redirect(url_for('blp.home'))
            
    return render_template("signup.html", user=current_user)


@blp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('blp.login'))


# Web app main routes-----------------------------------------------
@blp.route('/')
@login_required
def home():
    # Get the current user's balance data
    balance = Balance.query.filter_by(userId=current_user.id).first()  # Get user's balance record
    
    # If no balance exists for the user, set default values
    if not balance:
        balance = {
            'monetaryBalance': 0,
            'monetaryExpiryDate': None,
            'bonusBalance': 0,
            'bonusExpiryDate': None,
            'dataBalanceMB': 0,
            'dataExpiryDate': None
        }
    else:
        balance = {
            'monetaryBalance': round(balance.monetaryBalance, 3),  # Round to 3 decimal places
            'monetaryExpiryDate': balance.monetaryExpiryDate,
            'bonusBalance': round(balance.bonusBalance, 3),  # Round to 3 decimal places
            'bonusExpiryDate': balance.bonusExpiryDate,
            'dataBalanceMB': round(balance.dataBalanceMB, 3),  # Round to 3 decimal places
            'dataExpiryDate': balance.dataExpiryDate
        }

    return render_template("home.html", user=current_user, balance=balance)


@blp.route('/subscriptions')
@login_required
def subscriptions():
    return render_template("subscriptions.html", user=current_user)


@blp.route('/questions', methods=['GET', 'POST'])
@login_required
def questions():
    keyword = request.args.get('keyword', '')
    questions = []
    
    if request.method == 'POST': 
        question = request.form.get('question')  # Gets the question from the HTML

        if len(question) < 10:
            flash('The question is too short to be submitted!', category='E') 
        else:
            new_question = Question(content=question, userId=current_user.id)  # Creating the new question
            db.session.add(new_question)  # Adding the question to the database
            db.session.commit()
            flash('Your Question is submitted successfully!', category='S')

        return redirect(url_for('blp.questions'))  # Redirect to the main questions page after submit

    # Search functionality
    if keyword:
        questions = Question.query.filter(Question.content.ilike(f'%{keyword}%')).all()

    return render_template("questions.html", user=current_user, questions=questions, keyword=keyword)

@blp.route('/question/<int:question_id>', methods=['GET', 'POST'])
@login_required
def answers(question_id):
    # Get the question by ID
    question = Question.query.get_or_404(question_id)
    
    # Handle the POST request to add an answer
    if request.method == 'POST':
        answer_content = request.form.get('answer')
        
        if answer_content:
            # Create a new answer linked to the question
            new_answer = Answer(content=answer_content, questionId=question_id, userId=current_user.id)
            db.session.add(new_answer)
            db.session.commit()
            flash('Your answer has been added successfully!', category='S')
            return redirect(url_for('blp.answers', question_id=question.id))

    return render_template("answers.html", user=current_user, question=question)


@blp.route('/find')
@login_required
def findAgency():
    return render_template("findAgency.html", user=current_user)