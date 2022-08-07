from email.quoprimime import body_check
from re import I
from textwrap import fill
from flask import redirect, url_for, render_template, request, Blueprint, Markup, json, current_app
from flask_login import login_required, current_user
from flask_mail import Message
from .models import MonthsCategorysIntensity, MonthsTrainingCategory, User, Training, TrainingSection, Category, Month, Year
from . import db,mail
import datetime

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



def send_emails():
    today = datetime.date.today()
    mail.init_app(current_app)
    for user in User.query.all():
        if user.in_email_list:
            msg = Message(f'Day {today.day}.{today.month}.{today.year} :D', sender=username,recipients=[user.email])
            msg.body = 'What did you do today?:)'
            mail.send(msg)

def send_email():
    today = datetime.date.today()
    mail.init_app(current_app)
    msg = Message(f'{today.day}.{today.month}.{today.year} fill today:D', sender=username,recipients=[current_user.email])
    msg.body = 'What did you do today?:)'
    mail.send(msg)

def receive_email_body():

    mail = imaplib.IMAP4_SSL(gmail_host)

    #login
    mail.login(username, password)

    #select inbox
    mail.select("INBOX")

    #select specific mails
    _, selected_mails = mail.search(None, f'(FROM {current_user.email})')


    for idx,num in enumerate(selected_mails[0].split()):
        if idx != len(selected_mails[0].split())-1:
           continue 
        _, data = mail.fetch(num , '(RFC822)')
        _, bytes_data = data[0]

        #convert the byte data to message
        email_message = email.message_from_bytes(bytes_data)

        #access data
        for part in email_message.walk():
            if part.get_content_type()=="text/plain" or part.get_content_type()=="text/html":
                message = part.get_payload(decode=True)
                body_text = message.decode()
                list_raw = re.split("\s.{2}\s\d\d",body_text,1)
                message = list_raw[0]
                days_date = re.search(".{2}\s\d\d[.]\s\w+[.]\s\d\d\d\d",body_text).group()
                year = re.search("\d\d\d\d", days_date).group()
                day = re.search("\d\d",days_date,1).group()
                month_raw = re.search("\s\D+[.]",days_date).group()

                if "tammi" in month_raw:
                    month = "1" 
                elif "helmi" in month_raw:
                    month = "2"
                elif "maalis" in month_raw:
                    month = "3"
                elif "huhti" in month_raw:
                    month = "4"
                elif "touko" in month_raw:
                    month = "5"
                elif "kesä" in month_raw:
                    month = "6"
                elif "heinä" in month_raw:
                    month = "7"
                elif "elo" in month_raw:
                    month = "8"
                elif "syys" in month_raw:
                    month = "9"
                elif "loka" in month_raw:
                    month = "10"
                elif "marras" in month_raw:
                    month = "11"
                elif "joulu" in month_raw:
                    month = "12"

                return message,day,month,year
                break

    return 'no messages:('

def add_training_to_db(raw_main,timeofday,day,month,year):

    training_date = day + ' ' + month + ' ' + year 
    date_obj = datetime.date(int(year),int(month),int(day))
    # making the training object
    new_training = Training(user=current_user, name=raw_main, timeofday=timeofday,training_date=training_date)
    try:
        db.session.add(new_training)
        db.session.commit()
    except:
        return 'There was an arror adding training to db'

    # getting existing category objects
    ecategories = current_user.categories
    # if no, redirect to making some categories first
    if ecategories == []:
        return redirect(url_for('routes.settings'))
    
    # making a list of category names
    cat_names = []
    for cat in ecategories:
        cat_names.append(cat.name)

    # checking which section had the most time so i can name the whole training by it
    leading_sec = 0
    # splitting training into parts
    sections = raw_main.split('+')
    for section in sections:
        ttype, intensity, ttime = section.split(',')
        section_obj = TrainingSection(user=current_user,name=ttype)

        if int(ttime) > leading_sec:
            new_training.name = ttype
            leading_sec = int(ttime) 
        # finding the existing category for ttype
        if not ttype in cat_names:
            return 'the category:', ttype, 'not found, create it in settings:)'
        
        # assigning category
        for item in ecategories:
            if ttype == item.name:
                section_obj.category = item
                break

        # assigning intensity

        # assigning intensity
        section_obj.intensity = intensity
        section_obj.time = ttime
        section_obj.training = new_training

        # commiting section_obj
        db.session.add(section_obj)
        db.session.commit()
        # checking if there's an existing year object
        year_found = False
        for item in current_user.years:
            if item.num == int(year):
                year_obj = item
                year_found = True
        if not year_found:
            year_obj = Year(user=current_user, num=int(year))

        db.session.add(year_obj)
        db.session.commit()

        # checking if there's an existing month object
        month_found = False
        for item in current_user.months:
            if item.num == int(month):
                month_obj = item
                month_found = True
        if not month_found:
            month_obj = Month(user=current_user, num=int(month), name=date_obj.strftime("%B"), year=year_obj)


        db.session.add(month_obj)
        db.session.commit()
        
        # adding everything also to Month objects summary
        mtc_found = False
        for c in month_obj.training_categories:
            if c.name == ttype:
                mtc = c
                mtc_found = True
        if not mtc_found:
            mtc = MonthsTrainingCategory(name=ttype,month=month_obj)
            db.session.add(mtc)
            db.session.commit()

        # searching for existing mci
        mci_found = False
        for i in mtc.intensities:
            if i.name == intensity:
                mci = i
                mci_found = True
        if not mci_found:
            mci = MonthsCategorysIntensity(name=intensity, month=month_obj)
            db.session.add(mci)
            db.session.commit()



        if mci.overall_time != None:
            etime = int(mci.overall_time)
        else:
            etime = 0

        etime += int(ttime)
        mci.overall_time = str(etime)
        mci.months_training_category = mtc
        db.session.add(mci)
        db.session.commit()


    try:
        db.session.add(new_training)
        db.session.commit()
    except:
        return "failed adding a new_training to db"


@login_required
@routes.route('/')
@routes.route('/home', methods=['POST', 'GET'])
def home():

    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))

    current_year = session['year']
        # current_year: int
    current_month_int = session['month']
        # current_month_int: int
    current_month_name = calendar.month_name[current_month_int]
        # current_month_name: string
    current_day = datetime.datetime.now().day
    # current_day: int
    days_in_month = monthrange(current_year, current_month_int)[1]
    # days_in_month: int
    list_of_days = [item for item in range(1,days_in_month + 1)]
    firstday_int = datetime.datetime(year=current_year, month=current_month_int, day=1).weekday()
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

    
    # finding right month and year. also cats and ints
    tcats = []
    raw_tints = []
    for mon in current_user.months:
        if mon.year.num == current_year and mon.num == current_month_int:
            tcats = (mon.training_categories)
            raw_tints = (mon.training_intensities)
    # removing duplicates
    tints = list(dict.fromkeys(raw_tints))
    # Category - Time - Chart
    c_times = []
    for tc in tcats:
        time_tracker = 0
        for i in tc.intensities:
            time_tracker += int(i.overall_time)
        c_times.append(time_tracker)
    tc_times = (c_times)
    # Intensity - Time - Chart
    i_times = []

    for i in tints:
        i_times.append(int(i.overall_time))
    ti_times = ( i_times )

    colorpalette = ["#003f5c","#2f4b7c","#665191","#a05195","#d45087","#f95d6a","#ff7c43","#ffa600"]
    cat_colors = ( colorpalette[:len(tcats)] )
    int_colors = ( colorpalette[:len(tints)] )




    if request.method == 'POST':
        year = request.form['year']
        month = datetime.datetime.strptime(request.form['month'], "%B").month
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
    current_day=current_day,
    current_month_int=current_month_int,
    current_month_name=current_month_name,
    current_year=current_year,
    days_in_month=days_in_month,
    list_of_days=list_of_days,
    fill_last_month=fill_last_month,
    fill_next_month=fill_next_month,
    cat_set=zip(tc_times,tcats,cat_colors),
    tc_times=tc_times,
    tcats=tcats,
    cat_colors=cat_colors,
    max=17000,
    int_set=zip(ti_times,tints,int_colors)
    )

@login_required
@routes.route("/training-<timeofday>-<day>-<month>-<year>/", methods=['POST', 'GET'])
def training_day(timeofday, day, month, year):

    # THINK ABOUT DO YOU EVEN NEED THESE MONTH AND YEAR CLASSES OKAY they are useful not having to load up summary everytime you open new month but you could remove them now and 
    # implement those later if needed. RIGHT now figure out if you could just use datetime.date() to sort these trainings on their correct days and daytimes.
    URL = "/training-" + timeofday + "-" + day + "-" + month + "-" + year + "/"

    # how many days ago
    date_obj = datetime.date(int(year),int(month),int(day))
    today = datetime.date.today()
    diff_obj = today - date_obj
    diff_in_days = diff_obj.days

    # constructing a simple date for training object
    training_date = day + ' ' + month + ' ' + year 

    

    # making variables for ap and ip and a list of other trainings for this current day
    plus_trainings = []
    morning_training = 0
    noon_training = 0
    # adding todays trainings to daystrainings
    trainings = current_user.trainings
    for t in trainings:
        if t.training_date == training_date:
            if t.timeofday == 'ap':
                morning_training = t
            elif t.timeofday == 'ip':
                noon_training = t
            else:
                plus_trainings.append(t)

    if request.method == 'POST':
        raw_main = request.form['main']
        add_training_to_db(raw_main,timeofday,day,month,year)
        return redirect(URL)

    return render_template('training_day.html', 
    user=current_user, 
    morning_training=morning_training,
    noon_training=noon_training,
    plus_trainings=plus_trainings,
    trainings=trainings, 
    timeofday=timeofday, 
    diff_in_days=diff_in_days,
    day=day, 
    month=month, 
    year=year)
    

@routes.route("/settings/", methods=['POST','GET'])
def settings():
    ecategories = current_user.categories
    phone_number = current_user.phone_number
    if request.method == 'POST':
        
        """ if request.form['submit'] == 'send':
            send_email()
            return "Sent"
        elif request.form['submit'] == 'receive':
            message, day, month, year = receive_email_body()
            # IAM ONLY DOING AP FOR NOW
            timeofday = "ap"
            add_training_to_db(message,timeofday,day,month,year)
            return "Added to db"
        elif request.form['submit'] == 'ski':
            new_category_obj = Category(user=current_user, name='ski')
            try:
                db.session.add(new_category_obj) 
                db.session.commit()
            except:
                return 'There was an error adding category to the db'
        elif request.form['submit'] == 'run':
            new_category_obj = Category(user=current_user, name='run')
            try:
                db.session.add(new_category_obj) 
                db.session.commit()
            except:
                return 'There was an error adding category to the db'
        elif request.form['submit'] == 'false':
            current_user.in_email_list = False
            db.session.commit()
        elif request.form['submit'] == 'true':
            current_user.in_email_list = True
            db.session.commit() """
        number = request.form['phonenumber']
        current_user.phone_number = number
        db.session.commit()
        """ else:
            new_category = request.form['new_category']
            new_category_obj = Category(user=current_user, name=new_category)
            try:
                db.session.add(new_category_obj) 
                db.session.commit()
            except:
                return 'There was an error adding category to the db'
 """
        return redirect(url_for('routes.settings'))
    return render_template('settings.html', user=current_user, ecategories=ecategories, phone_number=phone_number)

@routes.route("/previous-year-<curryear>/")
def previous_year(curryear):
    curryear = int(curryear)
    session['year'] = curryear - 1
    return redirect(url_for('routes.home'))

@routes.route("/next-year-<curryear>/")
def next_year(curryear):
    curryear = int(curryear)
    session['year'] = curryear + 1
    return redirect(url_for('routes.home'))

@routes.route("previous-month-<currmonth>/")
def previous_month(currmonth):
    currmonth = int(currmonth)
    if (currmonth - 1) < 1:
        session['year'] = session['year'] - 1
        session['month'] = 12
    else:
        session['month'] = currmonth - 1
    return redirect(url_for('routes.home'))

@routes.route("/next-month-<currmonth>/")
def next_month(currmonth):
    currmonth = int(currmonth)
    if (currmonth + 1) > 12:
        session['year'] = session['year'] + 1
        session['month'] = 1
    else:
        session['month'] = currmonth + 1
    return redirect(url_for('routes.home'))

@routes.route("/prevday-<day>-<month>-<year>/")
def prev_day(day,month,year):
    d = datetime.date(int(year),int(month),int(day))
    d_prev = d - datetime.timedelta(days=1)
    p_day,p_month,p_year = d_prev.day,d_prev.month,d_prev.year
    session['year'] = p_year
    session['month'] = p_month
    session['day'] = p_day
    p_url = "/training-ap-" + str(p_day) + "-" + str(p_month) + "-" + str(p_year) + "/"
    return redirect(p_url)


@routes.route("/nextday-<day>-<month>-<year>/")
def next_day(day,month,year):
    d = datetime.date(int(year),int(month),int(day))
    d_next = d + datetime.timedelta(days=1)
    n_day,n_month,n_year = d_next.day,d_next.month,d_next.year
    session['year'] = n_year
    session['month'] = n_month
    session['day'] = n_day
    n_url = "/training-ap-" + str(n_day) + "-" + str(n_month) + "-" + str(n_year) + "/"
    return redirect(n_url)

@ login_required
@ routes.route('/delete-training-<id>-<timeofday>-<day>-<month>-<year>/')
def delete_training(id,timeofday,day,month,year):
    training = Training.query.filter_by(id=id).first()
    for section in training.sections:
        # removing also from the month and it's followers
        for year_obj in current_user.years:
            if year_obj.num == int(year):
                for month_obj in year_obj.months:
                    if month_obj.num == int(month):
                        m_obj = month_obj
                        break
        # looping over training_intensities to find what to delete
        for ti in m_obj.training_intensities:
            # finding the correspondent sections name so they match
            if ti.name == section.intensity:
                # just making sure it's really int 
                etime = int(ti.overall_time)
                etime -= int(section.time)
                ti.overall_time = etime

                # if no time on that intensity obj, let's delete it
                if int(ti.overall_time) <= 0:
                    db.session.delete(ti)
                    db.session.commit()
                else:
                    # saving changes
                    db.session.add(ti)
                    db.session.commit()
        
        # finally deleting the section itself
        db.session.delete(section)
        db.session.commit()


    backurl = '/training-' + timeofday + '-' + day + '-' + month + '-' + year + '/'
    db.session.delete(training)
    db.session.commit()
    return redirect(backurl)


@ login_required
@ routes.route('/training-<id>-<timeofday>-<day>-<month>-<year>/')
def show_training(id,timeofday,day,month,year):
    training = Training.query.filter_by(id=id).first()

    return render_template('training.html', training=training, user=current_user)
