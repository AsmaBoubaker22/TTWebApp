from flask import Blueprint, render_template
from flask import flash , request, url_for, redirect
from flask_login import login_user, login_required, logout_user, current_user
from .models import db, User, UsageHistory, Balance, Recharge, MonetaryRechargePlan, MobileDataPlan, AgencyLocation, Question, Answer
from werkzeug.security import generate_password_hash, check_password_hash
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
import pandas as pd
import numpy as np
from geopy.distance import geodesic

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


# Web app main routes-------------------------------------------------------------------------------------------------------------------------
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

# Route for the prediction page
@blp.route('/predict', methods=['POST'])
@login_required
def predict():
    # Fetch user's usage history----------------------------------------------------------------------------------------------------------------
    usage_history = UsageHistory.query.filter_by(userId=current_user.id).all()

    # If no usage history exists, show a message
    if not usage_history:
        return render_template("prediction.html", message="No usage history available for prediction.")

    # Prepare data for linear regression
    data = pd.DataFrame([{
        'usageTimestamp': record.usageTimestamp,
        'callsMinutes': record.callsMinutes,
        'smsCount': record.smsCount,
        'dataUsageMB': record.dataUsageMB
    } for record in usage_history])

    # Convert the timestamp to numeric (e.g., days since the first record)
    data['days_since_first'] = (data['usageTimestamp'] - data['usageTimestamp'].min()).dt.days

    # Set the target variable (usage)
    X = data[['days_since_first']]  # Features (days since first usage)
    y_calls = data['callsMinutes']  # Target: Calls
    y_sms = data['smsCount']  # Target: SMS
    y_data = data['dataUsageMB']  # Target: Data Usage

    # Fit Linear Regression models
    model_calls = LinearRegression().fit(X, y_calls)
    model_sms = LinearRegression().fit(X, y_sms)
    model_data = LinearRegression().fit(X, y_data)

    # Predict next usage based on the most recent data point
    next_day = data['days_since_first'].max() + 1  # Predict the next day
    predicted_calls = model_calls.predict([[next_day]])[0]
    predicted_sms = model_sms.predict([[next_day]])[0]
    predicted_data = model_data.predict([[next_day]])[0]

    # Round the predicted data to 3 decimal places
    predicted_sms = round(predicted_sms, 3)
    predicted_calls = round(predicted_calls, 3)
    predicted_data = round(predicted_data, 3)
    
    # Fetch user's recharge history---------------------------------------------------------------------------------------------------------
    recharge_history = Recharge.query.filter_by(userId=current_user.id).all()

    # If no recharge history exists, show a message
    if not recharge_history:
        return render_template("prediction.html", message="No recharge history available for prediction.",
                               user=current_user,
                               predicted_calls=predicted_calls,
                               predicted_sms=predicted_sms,
                               predicted_data=predicted_data)

    # Prepare data for Random Forest (recharge prediction)
    recharge_data = pd.DataFrame([{
        'rechargeDate': record.rechargeDate,
        'rechargeAmount': record.rechargeAmount,
        'bonusAdded': record.bonusAdded,
        'dataAddedMB': record.dataAddedMB
    } for record in recharge_history])

    # Convert rechargeDate to datetime if it is not already
    recharge_data['rechargeDate'] = pd.to_datetime(recharge_data['rechargeDate'])

    # Convert rechargeDate to numeric (e.g., days since the first recharge)
    recharge_data['days_since_first_recharge'] = (recharge_data['rechargeDate'] - recharge_data['rechargeDate'].min()).dt.days

    # Set the target variables (monetary recharge and data recharge)
    X_recharge = recharge_data[['days_since_first_recharge']]  # Features (days since first recharge)
    y_recharge_monetary = recharge_data['rechargeAmount']  # Target: Recharge Amount (Monetary)
    y_recharge_data = recharge_data['dataAddedMB']  # Target: Data Recharge Amount

    # Fit Random Forest models for recharge prediction
    rf_model_monetary = RandomForestRegressor(n_estimators=100).fit(X_recharge, y_recharge_monetary)
    rf_model_data = RandomForestRegressor(n_estimators=100).fit(X_recharge, y_recharge_data)

    # Predict next recharge values
    next_recharge_day = recharge_data['days_since_first_recharge'].max() + 1  # Predict the next recharge day
    predicted_recharge_monetary = rf_model_monetary.predict([[next_recharge_day]])[0]
    predicted_recharge_data = rf_model_data.predict([[next_recharge_day]])[0]

    # Round the predicted recharge values to 3 decimal places
    predicted_recharge_monetary = round(predicted_recharge_monetary, 3)
    predicted_recharge_data = round(predicted_recharge_data, 3)

    # Fetch the user's bonus plan
    user = User.query.filter_by(id=current_user.id).first()
    bonus_plan = user.bonusPlan if user else 0  # Default to 0 if no bonus plan
    # Calculate the bonus prediction (predicted recharge * bonus plan)
    bonus_prediction = predicted_recharge_monetary * bonus_plan
    bonus_prediction = round(bonus_prediction, 3)  # Round to 3 decimal places

     # Define prices for SMS and calls
    sms_price = 0.025  # Price per SMS
    call_price = 0.035  # Price per minute of call

    # Fetch the user's current balance details from the Balance table
    user_balance = Balance.query.filter_by(userId=current_user.id).first()

    if not user_balance:
        return render_template("prediction.html", message="Balance information not available for the user.")

    # Get the current balance details from the Balance table
    monetary_balance = user_balance.monetaryBalance  # Monetary balance (TDN)
    bonus_balance = user_balance.bonusBalance  # Bonus balance (TDN)
    data_balance = user_balance.dataBalanceMB  # Data balance in MB

    # Calculate the cost of predicted SMS and call usage
    sms_cost = predicted_sms * sms_price
    call_cost = predicted_calls * call_price

    # Deduct the SMS and call costs from the bonus balance, then from the monetary balance if needed
    remaining_bonus_balance = bonus_balance - sms_cost - call_cost

    if remaining_bonus_balance >= 0:
        # If bonus balance is sufficient, use bonus balance
        predicted_balance_bonus = remaining_bonus_balance
        predicted_balance_monetary = monetary_balance  # No change to monetary balance
        predicted_balance_data = data_balance - predicted_data  # Subtract predicted data from the data balance
    else:
        # If bonus balance is not enough, use the monetary balance
        predicted_balance_bonus = 0  # All bonus balance used
        remaining_monetary_balance = monetary_balance + remaining_bonus_balance  # Remaining monetary balance after bonus depletion
        if remaining_monetary_balance >= 0:
            # If monetary balance is sufficient, use monetary balance
            predicted_balance_monetary = remaining_monetary_balance
            predicted_balance_data = data_balance - predicted_data  # Subtract predicted data from the data balance
        else:
            # If both bonus and monetary balances are not enough, set them to zero
            predicted_balance_monetary = 0
            predicted_balance_data = 0  # If both balances are insufficient, no data balance left

    # Add recharge prediction to balances
    predicted_balance_monetary += predicted_recharge_monetary
    predicted_balance_bonus += bonus_prediction
    predicted_balance_data += predicted_recharge_data

    # Recommend plans-----------------------------------------------------------------------------------------------------------------------------  
    # Predict usage for 7 days
    predicted_week_sms = predicted_sms * 7
    predicted_week_calls = predicted_calls * 7
    predicted_week_data = predicted_data * 7

    # Fetch monetary plans from the database
    monetary_plans = MonetaryRechargePlan.query.all()

    # Calculate total predicted cost for SMS and calls over the next week
    total_sms_cost = predicted_week_sms * sms_price
    total_call_cost = predicted_week_calls * call_price
    total_cost = total_sms_cost + total_call_cost

    # Find the best monetary plan from the database
    best_monetary_plan = None
    for plan in monetary_plans:
        if plan.rechargeAmount >= total_cost:
            if not best_monetary_plan or plan.rechargeAmount < best_monetary_plan.rechargeAmount:
                best_monetary_plan = plan

    # Fetch data plans from the database
    data_plans = MobileDataPlan.query.all()

    # Find the best data plan from the database
    best_data_plan = None
    for plan in data_plans:
        if plan.dataAmountMB >= predicted_week_data:
            if not best_data_plan or plan.dataAmountMB < best_data_plan.dataAmountMB:
                best_data_plan = plan
    
    # Convert the timestamp to datetime and calculate daily usage
    data['usageTimestamp'] = pd.to_datetime(data['usageTimestamp'])
    data['date'] = data['usageTimestamp'].dt.date  # Extract only the date part

    # Group data by date to calculate daily statistics
    daily_stats = data.groupby('date').agg({
        'callsMinutes': ['mean', 'std', 'median', lambda x: pd.Series.mode(x).iloc[0] if not x.mode().empty else np.nan],
        'smsCount': ['mean', 'std', 'median', lambda x: pd.Series.mode(x).iloc[0] if not x.mode().empty else np.nan],
        'dataUsageMB': ['mean', 'std', 'median', lambda x: pd.Series.mode(x).iloc[0] if not x.mode().empty else np.nan]
    }).reset_index()

    # Rename the mode column for clarity
    daily_stats.columns = ['date', 'calls_mean', 'calls_std', 'calls_median', 'calls_mode',
                           'sms_mean', 'sms_std', 'sms_median', 'sms_mode',
                           'data_usage_mean', 'data_usage_std', 'data_usage_median', 'data_usage_mode']

    # Calculate daily monetary recharge and data recharge
    recharge_history = Recharge.query.filter_by(userId=current_user.id).all()
    recharge_data = pd.DataFrame([{
        'rechargeDate': record.rechargeDate,
        'rechargeAmount': record.rechargeAmount,
        'dataAddedMB': record.dataAddedMB
    } for record in recharge_history])

    recharge_data['rechargeDate'] = pd.to_datetime(recharge_data['rechargeDate'])
    recharge_data['date'] = recharge_data['rechargeDate'].dt.date
    daily_recharge_stats = recharge_data.groupby('date').agg({
        'rechargeAmount': ['mean', 'std', 'median', lambda x: pd.Series.mode(x).iloc[0] if not x.mode().empty else np.nan],
        'dataAddedMB': ['mean', 'std', 'median', lambda x: pd.Series.mode(x).iloc[0] if not x.mode().empty else np.nan]
    }).reset_index()

    # Rename the mode column for clarity
    daily_recharge_stats.columns = ['date', 'recharge_mean', 'recharge_std', 'recharge_median', 'recharge_mode',
                                    'data_recharge_mean', 'data_recharge_std', 'data_recharge_median', 'data_recharge_mode']

    # Get the statistics for the most recent day or use averages
    latest_daily_usage = daily_stats.iloc[-1] if len(daily_stats) > 0 else None
    latest_daily_recharge = daily_recharge_stats.iloc[-1] if len(daily_recharge_stats) > 0 else None

    # Pass predictions to the prediction page
    return render_template("prediction.html",  user=current_user,
                           predicted_calls=predicted_calls,
                           predicted_sms=predicted_sms,
                           predicted_data= predicted_data,
                           predicted_recharge_monetary=predicted_recharge_monetary,
                           predicted_recharge_data=predicted_recharge_data,
                           bonus_prediction=bonus_prediction,
                           predicted_balance_monetary=round(predicted_balance_monetary, 3),
                           predicted_balance_bonus=round(predicted_balance_bonus, 3),
                           predicted_balance_data=round(predicted_balance_data, 3),
                           best_monetary_plan=best_monetary_plan,
                           best_data_plan=best_data_plan,
                           daily_stats=latest_daily_usage,
                           daily_recharge_stats=latest_daily_recharge)


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



@blp.route('/find', methods=['GET', 'POST'])
@login_required
def findAgency():
    user_lat = None
    user_lng = None
    closest_agency = None

    if request.method == 'POST':
        # Get user's location from the form
        user_lat = float(request.form.get('latitude'))
        user_lng = float(request.form.get('longitude'))

        # Fetch all agencies from the database
        agencies = AgencyLocation.query.all()

        closest_distance = float('inf')

        # Calculate the shortest distance between the user and all agencies
        for agency in agencies:
            agency_location = (agency.latitude, agency.longitude)
            user_location = (user_lat, user_lng)
            distance = geodesic(user_location, agency_location).meters  # Get distance in meters

            if distance < closest_distance:
                closest_distance = distance
                closest_agency = agency

    # Fetch all agencies for map rendering
    agencies = AgencyLocation.query.all()

    return render_template("findAgency.html", 
                           user=current_user, 
                           agencies=agencies, 
                           closest_agency=closest_agency,
                           user_lat=user_lat,
                           user_lng=user_lng)
