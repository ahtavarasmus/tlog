from email.quoprimime import body_check
from textwrap import fill
from flask import redirect, url_for, render_template, request, Blueprint, Markup, json, current_app
from flask_login import login_required, current_user
from flask_mail import Message
from .models import MonthsCategorysIntensity, MonthsTrainingCategory, User, Training, TrainingSection, Category, Month, Year
from . import db,mail
from datetime import datetime as dt
import datetime

from twilio.twiml.messaging_response import MessagingResponse

from dotenv import load_dotenv

from calendar import monthrange
from flask import session
import calendar
import email
import imaplib
import os
import re
import time


load_dotenv()

routes = Blueprint('routes', __name__)
username = os.getenv("GMAIL_USER")
password = os.getenv("GMAIL_PASSWORD")

gmail_host = 'imap.gmail.com'


def validate_training(raw):
    if re.search("^..\s", raw) == None:
        return False
    _, raw = raw.split(" ") # removing the "ap "
    sections = raw.split("+") # splitting from + multiple
    for s in sections:
        if re.search(".+\,.+\,\d+", s) == None:
            return False
    
    return True

def add_training_to_db(user, raw_main,day,month,year):

    # training_date = day + ' ' + month + ' ' + year 
    training_date = dt(int(year),int(month),int(day))

    # extracting the timeofday from the front
    timeofday, main = raw_main.split()

    # making the training object
    new_training = Training(user=user, name=raw_main, timeofday=timeofday,training_date=training_date)
    try:
        db.session.add(new_training)
        db.session.commit()
    except:
        return 'There was an arror adding training to db'

    # checking which section had the most time so i can name the whole training by it
    leading_sec = 0
    jumping_training = False

    # splitting training into parts
    sections = main.split('+')
    for section in sections:
        ttype, intensity, ttime = section.split(',')
        section_obj = TrainingSection(user=user,name=ttype)

        if int(ttime) > leading_sec and not jumping_training:
            new_training.name = ttype.capitalize()
            leading_sec = int(ttime)

        if ttype == "jumping":
            jumping_training = True
            new_training.name = ttype.capitalize()

        found = False
        for c in user.categories:
            if c.name == ttype:
                category_obj = c
                found = True
        if not found:
            category_obj = Category(name=ttype,user=user)
            db.session.add(category_obj)
            db.session.commit()

        section_obj.category = category_obj

        # assigning intensity
        if jumping_training:
            section_obj.jumps = int(intensity)
        else:
            section_obj.intensity = intensity
        section_obj.time = ttime
        section_obj.training = new_training

        # commiting section_obj
        db.session.add(section_obj)
        db.session.commit()

    print("-------", user.years, "----------")

    # finding existing year object or making a new
    try:
        year_obj = db.session.execute(db.select(Year).filter_by(num=int(year),
                        user_id=user.id)).scalar_one()
    except:
        year_obj = Year(user=user, num=int(year))
        db.session.add(year_obj)
        db.session.commit()

    new_training.year = year_obj

    # finding existing month object or making a new
    try:
        month_obj = db.session.execute(db.select(Month).filter_by(num=int(month),
                        user_id=user.id,year_id=year_obj.id)).scalar_one()
    except:
        month_obj = Month(user=user, num=int(month), 
                          name=training_date.strftime("%B"),year=year_obj)
        db.session.add(month_obj)
        db.session.commit()

    new_training.month = month_obj

    # finally adding the training
    try:
        db.session.add(new_training)
        db.session.commit()
    except:
        return "failed adding a new_training to db"       


@login_required
@routes.route('/')
@routes.route('/home', methods=['POST', 'GET'])
def home():
    if 'year' not in session or 'month' not in session:
        session['year'] = datetime.datetime.now().year
        session['month'] = datetime.datetime.now().month
        session['day'] = datetime.datetime.now().day

    current_year = session['year']
        # current_year: int
    current_month_int = session['month']
    real_month = (current_month_int == dt.now().month) 
    real_year = (current_year == dt.now().year)
    real_date = (real_month and real_year)
        # current_month_int: int
    current_month_name = calendar.month_name[current_month_int]
        # current_month_name: string
    current_day = dt.now().day
    # current_day: int
    days_in_month = monthrange(current_year, current_month_int)[1]
    # days_in_month: int
    list_of_days = [item for item in range(1,days_in_month + 1)]
    firstday_int = dt(year=current_year, month=current_month_int, day=1).weekday()
    # firstday_int: int, weekday(0-6)
    if (current_month_int - 1) < 1:
        last_mo_year = current_year - 1
        # last_mo_year: int
        last_mo_month = 12
        # last_mo_year: int
    else:
        last_mo_year = current_year
        # last_mo_year: int
        last_mo_month = current_month_int - 1
        # last_mo_year: int

    # fill_last_month: list of ints
    LastMoDays = monthrange(last_mo_year, last_mo_month)[1]
    fill_last_month = [item for item in range(LastMoDays-(firstday_int-1), LastMoDays+1)]  
    # fill_next_month: list of ints
    DaysLeftToFill = 42 - days_in_month - len(fill_last_month)
    fill_next_month = [item for item in range(1, DaysLeftToFill + 1)] 


    # getting dict of day as a key and value as how many trainings at that day
    training_days_marks = set()
    if current_user.is_authenticated:
        for year in current_user.years:
            if year.num == current_year:
                for month in year.months:
                    if month.num == current_month_int:
                        name = month.name
                        for training in month.trainings:
                            training_days_marks.add(training.training_date)
    

    if request.method == 'POST':
        year = request.form['year']
        month = dt.strptime(request.form['month'], "%B").month
        # adding to the session
        session['year'] = year
        session['month'] = month


        # i have to put the current year and month to session always 
        # temporally cause that way i can refresh the page for 
        # next year and remember the selection for that users session.
        return redirect(url_for('routes.home'))


    
    return render_template('home.html',
    user=current_user,
    active_tag='active',
    real_date=real_date,
    current_day=current_day,
    current_month_int=current_month_int,
    current_month_name=current_month_name,
    current_year=current_year,
    days_in_month=days_in_month,
    list_of_days=list_of_days,
    fill_last_month=fill_last_month,
    fill_next_month=fill_next_month,
    )
    

@login_required
@routes.route("/help",methods=['GET'])
def help():
    return render_template("help.html",user=current_user)


@login_required
@routes.route("/month-summary/", methods=['GET'])
def month_summary():
 
    # dict which looks like this {'ski':90,'rh':200}
    categories = {}
    # dict which looks like this {'pk':90,'vk':15}
    intensities = {}
    jumps = 0
    month_overall = 0


    cur_month = session['month']
    cur_year = session['year']
    

    for year in current_user.years:
        if year.num == int(cur_year):
            for month in year.months:
                if month.num == int(cur_month):
                    name = month.name
                    for training in month.trainings:
                        for section in training.sections:
                            if section.category.name != "jumping":
                                month_overall += section.time
                            if section.category.name in categories.keys():
                                print("UPDATING CATEGORY!!!!")
                                categories[section.category.name] += section.time
                            else:
                                categories[section.category.name] = section.time
                                print("FIRST ONE IN CATEGORY!!!!!")

                            if section.category.name == "jumping":
                                jumps += section.jumps
                            else:
                                if section.intensity in intensities.keys():
                                    print("UPDATING INTENSITY!!!!")
                                    intensities[section.intensity] += section.time
                                else:
                                    print("FIRST ONE IN INTENSITY!!!!!")
                                    intensities[section.intensity] = section.time

    for c in categories.keys():
        categories[c] = round(categories[c] / 60, 1)

    for i in intensities.keys():
        intensities[i] = round(intensities[i] / 60, 1)

    name=dt(int(cur_year),int(cur_month),1).strftime("%B") # name of the month


    month_overall = round(month_overall / 60, 1)

    return render_template("month_summary.html",     
            user=current_user,
            intensities=intensities,
            categories=categories,
            jumps=jumps,
            month_overall=month_overall,
            name=name,
            year=cur_year,
            month=cur_month
            )


@login_required
@routes.route("/year-summary/", methods=['POST', 'GET'])
def year_summary():
    
    overall = 0
    categories = {}
    intensities = {}
    jumps = 0
    cur_year = session['year']
    
    
    months_in = {}
    if current_user.year_start > current_user.year_end: # we need two maps
         
        prev_year_months = [*range(current_user.year_start,13)] #includes year_start->13 including start month
        next_year_months = [*range(1,current_user.year_end)] #includes 1->year-end but not including the end month
        clicked_month = session['month']
        c_year = int(cur_year)
        n_year = int(cur_year)+1

        if clicked_month in next_year_months:
            n_year = int(cur_year)
            c_year = int(cur_year)-1
        months_in[c_year] = prev_year_months
        months_in[n_year] = next_year_months 
        season = str(c_year) + "-" + str(n_year)
    else:
        months_in[int(cur_year)] = [*range(current_user.year_start,current_user.year_end)]
        season = cur_year


 
    for year in current_user.years:
        if year.num in months_in.keys():
            for month in year.months:
                if month.num in months_in[year.num]:
                    for training in month.trainings:
                        for section in training.sections:
                            if section.category.name != "jumping":
                                overall += section.time
                            if section.category.name in categories.keys():
                                print("UPDATING CATEGORY!!!!")
                                categories[section.category.name] += section.time
                            else:
                                categories[section.category.name] = section.time
                                print("FIRST ONE IN CATEGORY!!!!!")

                            if section.category.name == "jumping":
                                jumps += section.jumps
                            else:
                                if section.intensity in intensities.keys():
                                    print("UPDATING INTENSITY!!!!")
                                    intensities[section.intensity] += section.time
                                else:
                                    print("FIRST ONE IN INTENSITY!!!!!")
                                    intensities[section.intensity] = section.time

    for c in categories.keys():
        categories[c] = round(categories[c] / 60, 1)

    for i in intensities.keys():
        intensities[i] = round(intensities[i] / 60, 1)

    overall = round(overall / 60, 1)

    return render_template("year_summary.html",     
            user=current_user,
            intensities=intensities,
            categories=categories,
            jumps=jumps,
            overall=overall,
            season=season
            )



@login_required
@routes.route("/training-<day>-<month>-<year>/", methods=['POST', 'GET'])
def training_day(year, month, day):

    URL = "/training-" + day + "-" + month + "-" + year + "/"

    # how many days ago
    date_obj = dt(int(year),int(month),int(day))
    todays_date = dt(int(year),int(month),int(day))
    diff_obj = todays_date - date_obj
    diff_in_days = diff_obj.days


    trainings = []
    # adding todays trainings 
    for t in current_user.trainings:
        if t.training_date == todays_date:
            trainings.append(t)
    
    def get_date(training):
        return training.training_date
    
    trainings.sort(key=get_date)

    if request.method == 'POST':
        raw_main = request.form['main']
        if validate_training(raw_main):
            add_training_to_db(current_user,raw_main,day,month,year)
        return redirect(URL)

    return render_template('training_day.html', 
    user=current_user, 
    trainings=trainings, 
    diff_in_days=diff_in_days,
    day=day, 
    month=month, 
    year=year)
    

@routes.route("/settings/", methods=['POST','GET'])
def settings():
    ecategories = current_user.categories
    phone_number = current_user.phone_number
    y_start = current_user.year_start
    y_end = current_user.year_end
    if request.method == 'POST':
        new_number = request.form['phonenumber']
        year_start = request.form['year_start']
        year_end = request.form['year_end']

        current_user.year_start = year_start
        current_user.year_end = year_end
        current_user.phone_number = new_number
        db.session.commit()
        return redirect(url_for('routes.settings'))
    return render_template('settings.html', user=current_user,
            ecategories=ecategories, 
            phone_number=phone_number,
            year_start=y_start,
            year_end=y_end)
    

@routes.route("/sms-webhook/", methods=['GET','POST'])
def incoming_sms():
    """Respond with the number of text messages sent between two parties."""
    # Sender's phone number
    from_number = request.values.get('From')
    user = User.query.filter_by(phone_number=from_number).first()

    # if user wasn't found return
    #if user is None:
    #    return ('', 204)

    name = "Rasmus"
   
    # Date of the incoming message
    year = dt.today().year
    month = dt.today().month
    day = dt.today().day

    # Body of the message
    body = request.values.get('Body',None)
    print("HELLO")

    add_training_to_db(user, body, day, month, year)


    # Creating the reply
    message = 'Training: "{}" added to {}\'s tlog with date {}.{}.{}'\
            .format(body,name,day,month,year)

    # Put it in a TwiML response
    resp = MessagingResponse()
    resp.message(message)

    return str(resp)





@routes.route("/previous-year-<where>/")
def previous_year(where):
    session['year'] = session['year'] - 1
    return redirect(url_for(where))

@routes.route("/next-year-<where>/")
def next_year(where):
    session['year'] = session['year'] + 1
    return redirect(url_for(where))

@routes.route("previous-month-<where>/")
def previous_month(where):
    currmonth = session['month']
    if (currmonth - 1) < 1:
        session['year'] = session['year'] - 1
        session['month'] = 12
    else:
        session['month'] = currmonth - 1
    return redirect(url_for(where))

@routes.route("/next-month-<where>/")
def next_month(where):
    currmonth = session['month']
    if (currmonth + 1) > 12:
        session['year'] = session['year'] + 1
        session['month'] = 1
    else:
        session['month'] = currmonth + 1
    return redirect(url_for(where))

@routes.route("/prevday-<day>-<month>-<year>/")
def prev_day(day,month,year):
    d = dt(int(year),int(month),int(day))
    d_prev = d - datetime.timedelta(days=1)
    p_day,p_month,p_year = d_prev.day,d_prev.month,d_prev.year
    session['year'] = p_year
    session['month'] = p_month
    session['day'] = p_day
    p_url = "/training-" + str(p_day) + "-" + str(p_month) + "-" + str(p_year) + "/"
    return redirect(p_url)


@routes.route("/nextday-<day>-<month>-<year>/")
def next_day(day,month,year):
    d = datetime.date(int(year),int(month),int(day))
    d_next = d + datetime.timedelta(days=1)
    n_day,n_month,n_year = d_next.day,d_next.month,d_next.year
    session['year'] = n_year
    session['month'] = n_month
    session['day'] = n_day
    n_url = "/training-" + str(n_day) + "-" + str(n_month) + "-" + str(n_year) + "/"
    return redirect(n_url)

@ login_required
@ routes.route('/delete-training-<id>-<day>-<month>-<year>/')
def delete_training(id,day,month,year):
    training = Training.query.filter_by(id=id).first()

    for section in training.sections:
        db.session.delete(section)
        db.session.commit()
    db.session.delete(training)
    db.session.commit()

    backurl = '/training-' + day + '-' + month + '-' + year + '/'
    return redirect(backurl)


@ login_required
@ routes.route('/training-<id>-day>-<month>-<year>/')
def show_training(id,day,month,year):
    training = Training.query.filter_by(id=id).first()

    return render_template('training.html', training=training, user=current_user)

@login_required
@routes.route('/reset-to-home/')
def reset_to_home():
    session['month'] = dt.now().month
    session['year'] = dt.now().year
    session['day'] = dt.now().day
    return redirect(url_for('routes.home'))
