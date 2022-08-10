from routes import * 
from . import db
from datetime import datetime as dt
from models import *

""" def add_to_db():
    raw_main = request.form['main']
    # making a datetime object for this day
    # training_date = datetime.date(int(year),int(month),int(day))
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


    db.session.add(new_training)
    db.session.commit()

 """





def add_training_to_db(raw_main,day,month,year):

    # training_date = day + ' ' + month + ' ' + year 
    training_date = dt(int(year),int(month),int(day))

    # extracting the timeofday from the front
    timeofday, main = raw_main.split()

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
    sections = main.split('+')
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
            month_obj = Month(user=current_user, num=int(month), name=training_date.strftime("%B"), year=year_obj)


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

