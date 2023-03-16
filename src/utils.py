from flask import session,render_template
from flask_login import current_user 
from .models import User,Training,Category,TrainingSection,Year,Month
from . import db
from datetime import datetime
import calendar
import re

def load_trainings_view():
    current_year = session.get('year',default=datetime.now().year)
    days = dict() 
    for month in range(1,13):
        for day in range(1,calendar.monthrange(1,month)[1] + 1):
            trainings = db.session.execute(db.select(Training)
                            .filter_by(training_date=
                            datetime(current_year,month,day))).scalar_one()
            days[f"{current_year}.{month}.{day}"] = trainings



    trainings = current_user.trainings
    
    if current_user.year_start > current_user.year_end: # we need two maps
    def all_dates_in_year(year=2019):
        for month in range(1, 13): # Month is always 1..12
            for day in range(1, calendar.monthrange(year, month)[1] + 1):
            yield Date(year, month, day)
         
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


    return trainings


def load_month_view():
    if 'year' not in session or 'month' not in session:
        session['year'] = datetime.now().year
        session['month'] = datetime.now().month
        session['day'] = datetime.now().day

    current_year = session['year']
        # current_year: int
    current_month_int = session['month']
    real_month = (current_month_int == datetime.now().month) 
    real_year = (current_year == datetime.now().year)
    real_date = (real_month and real_year)
        # current_month_int: int
    current_month_name = calendar.month_name[current_month_int]
        # current_month_name: string
    current_day = datetime.now().day
    # current_day: int
    days_in_month = calendar.monthrange(current_year, current_month_int)[1]
    # days_in_month: int
    list_of_days = [item for item in range(1,days_in_month + 1)]
    firstday_int = datetime(year=current_year, month=current_month_int, day=1).weekday()
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
    LastMoDays = calendar.monthrange(last_mo_year, last_mo_month)[1]
    fill_last_month = [item for item in range(LastMoDays-(firstday_int-1), LastMoDays+1)]  
    # fill_next_month: list of ints
    DaysLeftToFill = 42 - days_in_month - len(fill_last_month)
    fill_next_month = [item for item in range(1, DaysLeftToFill + 1)] 

    return (real_date,current_day,current_month_int,current_month_name,
            current_year,days_in_month,list_of_days,fill_last_month,
            fill_next_month)
 



def validate_training(raw):
    if re.search("^..\s", raw) == None:
        return False
    parts = raw.split(" ")
    if len(parts) == 2:
        # no comment
        _, raw = parts # removing the "ap "
    elif len(parts) == 3:
        # comment
        _, raw, _= parts # removing "ap " and comment
    else:
        # if more than max two spaces
        return False
    sections = raw.split("+") # splitting from + multiple
    for s in sections:
        if re.search(".+\,.+\,\d+", s) == None:
            return False
    return True

def add_training_to_db(user, raw_main,day,month,year):

    if not validate_training(raw_main):
        return False
    try:
        training_date = datetime(int(year),int(month),int(day))
    except:
        return False

    # extracting the timeofday from the front, and possible comment
    parts = raw_main.split()
    # just so code checker don't complain
    timeofday = "" 
    comment = ""
    main = ""
    if len(parts) == 2:
        timeofday, main = parts
    elif len(parts) == 3:
        timeofday, main, comment = parts

    # making the training object
    new_training = Training(user=user, name=raw_main, comment=comment, timeofday=timeofday,training_date=training_date)
    db.session.add(new_training)
    db.session.commit()

    # checking which section had the most time so i can name the whole training by it
    leading_sec = 0
    jumping_training = False

    # splitting training into parts
    sections = main.split('+')
    for section in sections:
        training_type, intensity, training_time = section.split(',')
        section_obj = TrainingSection(user=user,name=training_type)

        if int(training_time) > leading_sec and not jumping_training:
            new_training.name = training_type.capitalize()
            leading_sec = int(training_time)

        if training_type == "jumping":
            jumping_training = True
            new_training.name = training_type.capitalize()

        try:
            category_obj = db.session.execute(db.select(Category).filter_by(
                name=training_type,user_id=user.id)).scalar_one()
        except:
            category_obj = Category(user=user, name=training_type)
            db.session.add(category_obj)
            db.session.commit()


        """

        found = False

        for c in user.categories:
            if c.name == ttype:
                category_obj = c
                found = True
        if not found:
            category_obj = Category(name=ttype,user=user)
            db.session.add(category_obj)
            db.session.commit()
            """

        section_obj.category = category_obj

        # assigning intensity or number of jumps if jumping training
        if jumping_training:
            section_obj.jumps = int(intensity)
        else:
            section_obj.intensity = intensity
        section_obj.time = training_time
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


