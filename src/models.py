from flask_login import UserMixin
from . import db


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(150))
    in_email_list = db.Column(db.Boolean, default=False)
    phone_number = db.Column(db.String(100))
    year_start = db.Column(db.Integer, default=1)
    year_end = db.Column(db.Integer, default=12)

    categories = db.relationship('Category', backref='user', lazy='select')
    trainings = db.relationship(
        'Training', backref='user', lazy='select')
    training_sections = db.relationship(
            'TrainingSection', backref='user', lazy='select')
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
    jumps = db.Column(db.Integer)
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

    training_categories = db.relationship(
            'MonthsTrainingCategory', backref='month')
    training_intensities = db.relationship(
            'MonthsCategorysIntensity', backref='month')


class MonthsTrainingCategory(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    month_id = db.Column(db.Integer, db.ForeignKey('month.id'), nullable=False)
    intensities = db.relationship('MonthsCategorysIntensity',
                                  backref='months_training_category')


class MonthsCategorysIntensity(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    overall_time = db.Column(db.String)

    month_id = db.Column(db.Integer, db.ForeignKey('month.id'))
    months_training_category_id = db.Column(
            db.Integer, db.ForeignKey('months_training_category.id'))
