from .dbInitialization import db
from flask_login import UserMixin
from sqlalchemy.sql import func

# Users data -------------------------------------------------------------------------------------------------------------------
# this table will contain pre-existing data that the company TT provides
class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    phoneNumber = db.Column(db.String(15), unique=True, nullable=False)  # Pre-existing
    username = db.Column(db.String(120), unique=True, nullable=True)   # Added during signup
    passwordHash = db.Column(db.String(128), nullable=True)         # Added during signup
    bonusPlan = db.Column(db.Integer, nullable=False)          # Pre-existing
    
    # Relationships
    usageHistory = db.relationship('UsageHistory', back_populates='user', cascade='all, delete-orphan')
    balance = db.relationship('Balance', uselist=False, back_populates='user', cascade='all, delete-orphan') 
    rechargeHistory = db.relationship('Recharge', back_populates='user', cascade='all, delete-orphan') 
    questions = db.relationship('Question', back_populates='user', cascade='all, delete-orphan')  
    answers = db.relationship('Answer', back_populates='user', cascade='all, delete-orphan') 


# history of usage, this also should be provided by the company
class UsageHistory(db.Model):
    __tablename__ = 'usageHistory'    
    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Foreign key to User table
   # Timestamp for hourly tracking 
    usageTimestamp = db.Column(db.DateTime, nullable=False) # Date and time of the usage
    callsMinutes = db.Column(db.Integer, nullable=False)
    smsCount = db.Column(db.Integer, nullable=False)
    dataUsageMB = db.Column(db.Float, nullable=False)  
    
    # Relationships
    user = db.relationship('User', back_populates='usageHistory')


# this table also provided by the company, stores users balance
class Balance(db.Model):
    __tablename__ = 'balance' 
    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    # Balances
    monetaryBalance = db.Column(db.Float, nullable=False, default=0)  # Money available
    bonusBalance = db.Column(db.Float, nullable=False, default=0)     # Bonus units available
    dataBalanceMB = db.Column(db.Float, nullable=False, default=0)    # Mobile data in MB
    # Expiration dates
    monetaryExpiryDate = db.Column(db.Date, nullable=True)
    bonusExpiryDate = db.Column(db.Date, nullable=True)
    dataExpiryDate = db.Column(db.Date, nullable=True)
    
    # Relationships
    user = db.relationship('User', back_populates='balance')


# this table is also provided by the company but since the user can purchase using this webservice, we can also add contribute to this table 
class Recharge(db.Model):
    __tablename__ = 'recharge' 
    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # Recharge Details
    rechargeAmount = db.Column(db.Float, nullable=True)  # Amount recharged
    rechargeDate = db.Column(db.Date, nullable=True)     # Date of recharge
    bonusAdded = db.Column(db.Float, nullable=True)      # Bonus units added
    dataAddedMB = db.Column(db.Float, nullable=True)     # Mobile data added in MB
    # Expiration Dates
    monetaryExpiryDate = db.Column(db.Date, nullable=True)  # Expiration for monetary balance
    bonusExpiryDate = db.Column(db.Date, nullable=True)     # Expiration for bonus balance
    dataExpiryDate = db.Column(db.Date, nullable=True)      # Expiration for data balance

    # Relationships
    user = db.relationship('User', back_populates='rechargeHistory')


# Subscription plans data--------------------------------------------------------------------------------------------------------------------------------
# this table contains plans data that are provided by the company, and the webservice will display
class MonetaryRechargePlan(db.Model):
    __tablename__ = 'monetaryRechargePlan'   
    id = db.Column(db.Integer, primary_key=True)
    price = db.Column(db.Float, nullable=False)  # Price of the plan
    rechargeAmount = db.Column(db.Float, nullable=False)  # Recharge value
    rechargeExpDays = db.Column(db.Integer, nullable=False)  # Validity of recharge in days
    bonusExpDays = db.Column(db.Integer, nullable=False)  # Validity of bonus in days


# same as the previous table, but this one will deal with mobile data plans
class MobileDataPlan(db.Model):
    __tablename__ = 'mobileDataPlan'   # Custom table name
    id = db.Column(db.Integer, primary_key=True)
    price = db.Column(db.Float, nullable=False)  # Price of the plan
    dataAmountMB = db.Column(db.Float, nullable=False)  # Data amount in MB
    expDays = db.Column(db.Integer, nullable=False)  # Validity of data in days



# questions and answers data-----------------------------------------------------------------------------------------------------------------------------------------
# this table will store questions submitted by the users
class Question(db.Model):
    __tablename__ = 'question'  
    id = db.Column(db.Integer, primary_key=True) 
    userId = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Foreign Key to User table
    content = db.Column(db.Text, nullable=False)  # Detailed question content
    submittedAt = db.Column(db.DateTime, default=func.now(), nullable=False)  # when the question was submitted

    # Relationships
    user = db.relationship('User', back_populates='questions') 
    answers = db.relationship('Answer', back_populates='question', cascade='all, delete-orphan') 


# this table will stores the answers related to each question if exist
class Answer(db.Model):
    __tablename__ = 'answer' 
    id = db.Column(db.Integer, primary_key=True)  
    questionId = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)  # Foreign Key to Questions table
    userId = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Foreign Key to User table
    content = db.Column(db.Text, nullable=False)  # Content of the answer
    submittedAt = db.Column(db.DateTime, default=func.now(), nullable=False)  # when the answer was submitted

    # Relationships
    question = db.relationship('Question', back_populates='answers')  
    user = db.relationship('User', back_populates='answers') 


# Agencies location data ------------------------------------------------------------------------------------------------------------------------------------
# this table will stores the locations for all TT agencies
class AgencyLocation(db.Model):
    __tablename__ = 'agencyLocation'  
    id = db.Column(db.Integer, primary_key=True)  
    name = db.Column(db.String(100), nullable=False) 
    address = db.Column(db.String(255), nullable=False)  
    phoneNumber = db.Column(db.String(20), nullable=False)  
    latitude = db.Column(db.Float, nullable=False) 
    longitude = db.Column(db.Float, nullable=False)
     

