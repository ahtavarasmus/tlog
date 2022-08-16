from flask_login import UserMixin
from . import db
import datetime



class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(150))
    in_email_list = db.Column(db.Boolean, default=False)
    phone_number = db.Column(db.String(100))
    
    categories = db.relationship('Category', backref='user', lazy='select')
    trainings = db.relationship(
        'Training', backref='user', lazy='select')
    training_sections = db.relationship('TrainingSection', backref='user', lazy='select')
    years = db.relationship('Year', backref='user')
    months = db.relationship('Month', backref='user')

    def __repr__(self):
        return '<User %r' % self.username


class Training(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    comment = db.Column(db.String(400))


    timeofday = db.Column(db.String(50))
    training_date = db.Column(db.DateTime) 

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    month_id = db.Column(db.Integer, db.ForeignKey('month.id'))
    sections = db.relationship('TrainingSection', backref='training')

    def __repr__(self):
        return '<Training %r>' % self.name

class TrainingSection(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    intensity = db.Column(db.String(100))
    time = db.Column(db.Integer)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    training_id = db.Column(db.Integer, db.ForeignKey('training.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    
    def __repr__(self):
        return '<Year %r>' % self.name



class Category(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    trainingsections = db.relationship('TrainingSection', backref='category')

    def __repr__(self):
        return '<Category %r>' % self.name



class Year(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    num = db.Column(db.Integer, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    months = db.relationship('Month', backref='year')

class Month(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    num = db.Column(db.Integer, nullable=False)
    

    year_id = db.Column(db.Integer, db.ForeignKey('year.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    trainings = db.relationship("Training", backref="month")

    training_categories = db.relationship('MonthsTrainingCategory', backref='month')
    training_intensities = db.relationship('MonthsCategorysIntensity', backref='month')

class MonthsTrainingCategory(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    month_id = db.Column(db.Integer, db.ForeignKey('month.id'), nullable=False)
    intensities = db.relationship('MonthsCategorysIntensity', backref='months_training_category')

class MonthsCategorysIntensity(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    overall_time = db.Column(db.String)

    month_id = db.Column(db.Integer, db.ForeignKey('month.id'))
    months_training_category_id = db.Column(db.Integer, db.ForeignKey('months_training_category.id'))

    
    


""" class Year(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    num = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey(
        'user.id'), nullable=False)
    months = db.relationship('Month', backref='year')
    summary = db.relationship('YearSummary', backref='year')
    
    def __repr__(self):
        return '<Year %r>' % self.name
    
class Month(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    num = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey(
        'user.id'), nullable=False)
    year_id = db.Column(db.Integer, db.ForeignKey('year.id'), nullable=False)
    trainings = db.relationship('Training', backref='month')

class Week(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    weeknum = db.Column(db.Integer, nullable=False,
                        default=int(datetime.now().strftime("%W")))
    user_id = db.Column(db.Integer, db.ForeignKey(
        'user.id', ondelete="CASCADE"), nullable=False)
    trainings = db.relationship('Training', backref='week')

    def __repr__(self):
        return '<Week %r>' % self.name

class WeekSummary(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    huolto = db.Column(db.Integer)
    pk = db.Column(db.Integer)
    vk = db.Column(db.Integer)
    mk = db.Column(db.Integer)
    hypyt = db.Column(db.Integer)
    yht = db.Column(db.Integer)
    comment = db.Column(db.String(300))

    week_id = db.Column(db.Integer, db.ForeignKey('week.id'), nullable=False)
    month_id = db.Column(db.Integer, db.ForeignKey('month.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    year_id = db.Column(db.Integer, db.ForeignKey('year.id'), nullable=False)



class MonthSummary(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    huolto = db.Column(db.Integer)
    pk = db.Column(db.Integer)
    vk = db.Column(db.Integer)
    mk = db.Column(db.Integer)
    hypyt = db.Column(db.Integer)
    yht = db.Column(db.Integer)
    comment = db.Column(db.String(300))

    month_id = db.Column(db.Integer, db.ForeignKey('month.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    year_id = db.Column(db.Integer, db.ForeignKey('year.id'), nullable=False)

class YearSummary(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    huolto = db.Column(db.Integer)
    pk = db.Column(db.Integer)
    vk = db.Column(db.Integer)
    mk = db.Column(db.Integer)
    hypyt = db.Column(db.Integer)
    yht = db.Column(db.Integer)
    comment = db.Column(db.String(300))
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    year_id = db.Column(db.Integer, db.ForeignKey('year.id'), nullable=False) """






