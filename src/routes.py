from email.quoprimime import body_check
from textwrap import fill
from flask import redirect, url_for, render_template, request, Blueprint, Markup, json, current_app,flash
from flask_login import login_required, current_user
from flask_mail import Message
from .models import MonthsCategorysIntensity, MonthsTrainingCategory, User, Training, TrainingSection, Category, Month, Year

from datetime import datetime as dt
import datetime
from .utils import (load_month_view, load_year_overview, validate_training,
                    add_training_to_db)


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


@login_required
@routes.route('/')
@routes.route('/home', methods=['POST', 'GET'])
def home():
    (real_date,current_day,current_month_int,current_month_name,
    current_year,days_in_month,list_of_days,fill_last_month,
    fill_next_month) = load_month_view()



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
@routes.route("/year-overview", methods=['POST','GET'])
def year_overview():
    days = load_year_overview()
    return render_template('year_overview.html',
                           user=current_user,
                           days=days)
    

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
