#!/usr/bin/env python

import tkinter as tk
from tkinter import messagebox
import time
import datetime
import queryfuncs as qf
import student_lookup as sl


class SurveyEntry:
    def __init__(self, master, con, survey_id, resp_id, admin_id = None, edit=False, parentwindow = None):
        """
        This class is initialized as a TK window for survey entry. The Window is a large canvas laid onto the master, inisde
        that canvas is a frame that the canvas scrolls through. The frame is populated with widgets proceedurally based on
        queries to the Oracle db.
        :param master: TK root that the window exists in
        :param con: cx_oracle connection object
        :param survey_id: ID of the survey to be completed
        :param resp_id: ID of the respondent
        :param admin_id: ID of the administration, given only if editing
        :param edit: Boolean, True if editting an old survey
        :param parentwindow: GUI object, used for updating certain fields based on actions taken in this window
        :return:
        """
        self.master = master
        self.con = con
        self.survey_id = survey_id
        self.admin_id = admin_id
        self.respondent = resp_id
        self.toedit = edit
        self.parentwindow = parentwindow
        self.questions = qf.get_survey_questions(self.con, self.survey_id)
        self.answers = []
        self.questionwidgets = {}
        self.survey_title = qf.get_survey_name(self.con, self.survey_id)
        self.survey_widgets = {}
        self.master.protocol("WM_DELETE_WINDOW", self.close_window)
        self.master.minsize(1200,800)
        self.master.title('{} Entry'.format(self.survey_title))
        self.lookupwindow = None
        self.linked_student = None

        # Initialize The Canvas info
        self.canvas = tk.Canvas(self.master, borderwidth=0)
        self.vsb = tk.Scrollbar(self.master)
        self.master_frame = tk.Frame(self.canvas)
        self.canvas.config(yscrollcommand=self.vsb.set)
        self.vsb.pack(side="right", fill='y')
        self.canvas.pack(side='left', fill='both', expand=True)
        self.canvas.create_window((4, 4), window=self.master_frame, anchor='nw', tags='self.master_frame')
        self.vsb.config(command=self.canvas.yview)
        self.master_frame.bind("<Configure>", self.onFrameConfigure)

        #Add Header information
        tk.Label(self.master_frame, text=self.survey_title, font=("Helvetica", 16, "bold italic"), padx=10, pady=6).grid(
            sticky='w', column=0, columnspan=8)
        tk.Label(self.master_frame, text='Please enter the data exactly as it appears on the survey', padx=10, pady=6).grid(
            sticky='w', column=0, columnspan=8)

        #Populate Survey
        self.populate()

        #Populate previously given answers if editing
        if self.toedit:
            old_answers = qf.get_given_answers(self.con, self.admin_id)
            self.input_answers(old_answers)

    def close_window(self):
        """
        Special confirmation popup if the window is closed using the window manager "X" button, answers are not saved
        :return: None
        """
        if messagebox.askyesno('Close', 'Are you sure you want to close?\nThis survey will not be saved.'):
            self.master.destroy()

    def student_lookup(self, event):
        """
        Opens a window for the student lookup if one is not already open.
        :param event: catch for event argument
        :return: None
        """
        try:
             self.lookupwindow.deiconify()
        except:
            self.lookupwindow = tk.Toplevel(self.master)
            self.app = sl.StudentLookup(self.lookupwindow, event.widget, self.con, self)

    def onFrameConfigure(self, event):
        """
        Method for setting the master frame to scroll through the canvas.
        :param event:
        :return:
        """
        '''Reset the scroll region to encompass the inner frame'''
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def populate(self):
        """ Build Question Widgets. Loops through the questions twice, once to generate all the widget information, and then
        a second time to place the widgets. This was done because some placement decisions depend on the widget information
        of other answers. It was easier this way than trying to place at the same time which would require fancy logic.
        :returns None. The class is edited in place
        """
        for quid, qtext, num in self.questions:
            qtype = int(qf.get_question_type(self.con, quid)[0])
            #print(num, qtype)
            if qtype == 1:  # short_string
                qlabel = tk.Label(self.master_frame, text='{}. {}'.format(num, qtext), wraplength=700, justify='left')
                qstrvar = tk.StringVar()
                qentry = tk.Entry(self.master_frame, textvariable=qstrvar, width=50)
                if quid == 97:
                    if self.survey_id in (1,2,3):
                        name = qf.get_student_name_from_id(self.con, self.respondent)
                        qentry.delete(0,'end')
                        qentry.insert(0, name)
                    else:
                        qentry.bind("<Button-1>", self.student_lookup)
                    qentry.config(state='readonly')
                elif quid in (99, 100):
                    name = qf.get_student_name_from_id(self.con, self.respondent)
                    qentry.delete(0,'end')
                    qentry.insert(0, name)
                    qentry.config(state='readonly')
                self.survey_widgets[num] = {
                    'quid': quid,
                    'type': qtype,
                    'label': qlabel,
                    'response': qentry,
                    'response_var': qstrvar
                }

            elif qtype == 2:  # long_string
                qlabel = tk.Label(self.master_frame, text='{}. {}'.format(num, qtext), wraplength=700, justify='left')
                qentry = tk.Text(self.master_frame, wrap='word', height=4)
                self.survey_widgets[num] = {
                    'quid': quid,
                    'type': qtype,
                    'label': qlabel,
                    'response': qentry,
                    'response_var': ''
                }

            elif qtype == 3:  # single_choice
                qlabel = tk.Label(self.master_frame, text='{}. {}'.format(num, qtext), wraplength=700, justify='left')
                qanswers = qf.get_question_responses(self.con, quid)
                answervar = tk.StringVar()
                answervar.set(None)
                buttons = []
                for a_id, ans in qanswers:
                    buttons.append(tk.Radiobutton(
                        self.master_frame, text=ans, variable=answervar, value=ans
                    ))
                self.survey_widgets[num] = {
                    'quid': quid,
                    'type': qtype,
                    'label': qlabel,
                    'response': buttons,
                    'response_var': answervar
                }

            elif qtype == 4:  # table_single_choice
                # these need to reference the previous question to see if the same frame should be used
                qlabel = '{}. {}'.format(num, qtext)
                qanswers = qf.get_question_responses(self.con, quid)
                answervar = tk.StringVar()
                buttons = []
                for a_id, ans in qanswers:
                    buttons.append(tk.Radiobutton(
                        self.master_frame, text=ans, variable=answervar, value=ans, indicatoron=0, width=0, height=2
                    ))
                self.survey_widgets[num] = {
                    'quid': quid,
                    'type': qtype,
                    'label': qlabel,
                    'response': buttons,
                    'response_var': answervar,
                    'answers': [ans[1] for ans in qanswers]
                }

            elif qtype == 5:  # table_multiple_choice
                # these need to reference the previous question to see if the same frame should be used
                qlabel = '{}. {}'.format(num, qtext)
                qanswers = qf.get_question_responses(self.con, quid)
                buttons = []
                answervars = []
                for a_id, ans in qanswers:
                    ansvar = tk.StringVar()
                    box = tk.Checkbutton(self.master_frame, text='', variable=ansvar, onvalue=ans, offvalue='', width=7)
                    buttons.append(box)
                    answervars.append(ansvar)
                self.survey_widgets[num] = {
                    'quid': quid,
                    'type': qtype,
                    'label': qlabel,
                    'response': buttons,
                    'response_var': answervars,
                    'answers': [ans[1] for ans in qanswers]
                }

            elif qtype == 6:  # multiple_choice
                qlabel = tk.Label(self.master_frame, text='{}. {}'.format(num, qtext), wraplength=700, justify='left')
                qanswers = qf.get_question_responses(self.con, quid)
                buttons = []
                answervars = []
                for a_id, ans in qanswers:
                    ansvar = tk.StringVar()
                    box = tk.Checkbutton(self.master_frame, text=ans, variable=ansvar, onvalue=ans, offvalue='')
                    buttons.append(box)
                    answervars.append(ansvar)
                self.survey_widgets[num] = {
                    'quid': quid,
                    'type': qtype,
                    'label': qlabel,
                    'response': buttons,
                    'response_var': answervars
                }

        placerow = 3    # When placing the survey widgets, the first 2 rows are the header and instructions

        for i in range(1, len(self.survey_widgets)+1):
            label = self.survey_widgets[i]['label']
            qtype = self.survey_widgets[i]['type']
            answers = self.survey_widgets[i].get('answers')

            if qtype in (1,2):  # short entry answers
                response = self.survey_widgets[i]['response']
                label.grid(row=placerow, column=0, columnspan=8, sticky='w')
                placerow += 1
                response.grid(row=placerow, column=0, columnspan=8, sticky='w', padx=20)
                placerow += 1

            elif qtype in (4, 5):  # horizontal table answers
                prev_q = i-1
                prev_q_ans = [ans[1] for ans in
                              qf.get_question_responses(self.con, self.survey_widgets[prev_q]['quid'])]
                if [ans.lower() for ans in answers] != [ans.lower() for ans in prev_q_ans] and qtype == 5:
                    col = 8
                    for answer in answers[::-1]:
                        tk.Label(self.master_frame, text=answer, wraplength=100).grid(
                                row=placerow, column=col, sticky='nsew')
                        col -= 1
                    placerow += 1

                label_size = 8-len(answers)
                tk.Label(self.master_frame, text=self.survey_widgets[i]['label'], wraplength=500, justify='left').grid(
                        row=placerow, column=0, columnspan=label_size, sticky='w')
                buttons = self.survey_widgets[i]['response']
                col = 8
                for button in buttons[::-1]:
                    button.grid(row=placerow, column=col, sticky='nsew')
                    col -= 1
                placerow += 1

            elif qtype in (3, 6):  # vertical choice answers
                responses = self.survey_widgets[i]['response']
                label.grid(row=placerow, column=0, columnspan=8, sticky='w')
                placerow += 1
                for resp in responses:
                    resp.grid(row=placerow, column=0, sticky='w', padx=10)
                    try:
                        resp.deslect()
                    except:
                        pass
                        #print(i)
                    placerow += 1

            # Add a blank line between questions unless the question is a "table" type in which case only add
            # a blank row if the next question utilizes a different set of answers
            if qtype in (1,2,3,6):
                tk.Label(self.master_frame, text='', font=('Times new Roman', 3)).grid(row=placerow, columnspan=8)
                placerow += 1
            else:
                next_q = i+1
                next_q_ans = [ans[1] for ans in
                              qf.get_question_responses(self.con, self.survey_widgets[next_q]['quid'])]
                if [ans.lower() for ans in answers] != [ans.lower() for ans in next_q_ans]:
                    tk.Label(self.master_frame, text='', font=('Times new Roman', 3)).grid(row=placerow, columnspan=8)
                    placerow += 1


        self.submitbutton = tk.Button(self.master_frame, text='Submit', command=self.submitanswers, width=20, bg='green')
        self.submitbutton.grid()

    def input_answers(self, old_answers):
        """
        Method used when the user has selected an old survey to edit. Queries the database for the previously given answers
        and inserts them into their appropriate widgets. Text entry fields are inputted, and buttons are selected.
        :param old_answers: a list generated from the qf.get_given_answers() method
        :return: None
        """
        #format old answers
        old_ans_dict = {}
        #print(old_answers)
        for ans in old_answers:
            if not old_ans_dict.get(ans[2], None):
                old_ans_dict[ans[2]] = {'quid':ans[0],
                                        'ans':[ans[1]]}
            else:
                old_ans_dict[ans[2]]['ans'].append(ans[1])
        #print(old_ans_dict)

        for num, widget_dict in self.survey_widgets.items():
            quid = widget_dict['quid']
            type = widget_dict['type']

            old_num_dict = old_ans_dict.get(num)
            if not old_num_dict:
                #print('no answer for {}'.format(num))
                continue

            old_ans = old_num_dict['ans']

            if quid != old_ans_dict.get(num)['quid']:
                messagebox.showerror('','quids dont match')

            if type == 1:
                widget_dict['response'].config(state='normal')
                widget = widget_dict['response']
                widget.delete(0,'end')
                widget.insert(0, old_ans[0])
                # Special handling of fields that are filled through another window
                if quid in (97, 99, 100):
                    widget_dict['response'].config(state='readonly')

            elif type == 2:
                widget = widget_dict['response']
                widget.insert(1.0, old_ans[0])

            if type in (3, 4):
                responsevar = widget_dict['response_var']
                responsevar.set(old_ans[0])

            if type in (5,6):
                buttons = widget_dict['response']
                for but in buttons:
                    but_ans = but.cget('onvalue')
                    if but_ans in old_ans:
                        but.select()

    def submitanswers(self):
        """
        This method reviews all of the survey widgets, extracts their entered information, ensures certain requirements are met,
        creates or fetches the administration id (fetching occurs if this is an edit) and then batch inserts them into the
        response database.
        :return: returns 'None' if process failed, otherwise the top level window is destroyed upon successful completion.
        """
        if not messagebox.askokcancel('Submit Answers?', 'Are you sure you want to submit these answers?'):
            return
        else:
            #Grab the date information, on surveys this is the "date taken" field, which is important for identifying the order of administrations, in the student application
            #quid 116 is the "Date of Birth" field which is important because it is a field we'll be matching on in the future.
            date_widget = {}
            for widget in self.survey_widgets.values():
                if widget['quid'] in (96,116):
                    date_widget = widget

            if date_widget.get('quid', None) not in (96,116):
                messagebox.showerror('Fatal Error', 'The date could not be retrieved, something went VERY wrong. \nCall Dave. Take a break. There\'s nothing you can do.')
                return

            # Confirm that both the date has been entered and is of the format MM/DD/YYYY
            try:
                date = date_widget['response_var'].get()
                if not date:
                    if self.survey_id == 7:
                        messagebox.showerror('Date Error', 'You haven\'t entered a date of birth.\nPlease enter one in the format of MM/DD/YYYY')
                        return
                    else:
                        messagebox.showerror('Date Error', 'You haven\'t entered a date.\nPlease enter one in the format of MM/DD/YYYY')
                        return
                print(date)
                time.strptime(date, '%m/%d/%Y')    # Will raise an error if the date is not formatted correctly

            except ValueError:
                messagebox.showerror('Date Error', 'You\'ve entered a date that is not in correct format\nPlease change to MM/DD/YYYY format')
                return

            #The "date taken" field doesn't exist on the student application, so we are going to just set it to the day the application was entered into the survey
            if self.survey_id == 7:
                date = datetime.date.today().strftime('%m/%d/%Y')

            insert_list = []
            for index in range(1,len(self.survey_widgets)+1):
                quid = self.survey_widgets[index]['quid']
                qtype = self.survey_widgets[index]['type']
                #long answer (tk.Text) fields have a different way of getting the inputted information
                if qtype == 2:
                    resp =self.survey_widgets[index]['response']
                else:
                    resp = self.survey_widgets[index]['response_var']

                #Handling multiple choice requires iterating through a list of response widgets
                if isinstance(resp, list):
                    for response in resp:
                        text = response.get()
                        if text:
                            insert_list.append([0, quid, self.respondent, text])
                else:
                    if resp: # Check to make sure we have a response variable
                        if qtype == 2:
                            text = resp.get(0.0, 'end')   #Special handling of tk.Text widget
                        else:
                            text = resp.get()
                        if text:   # Don't add null responses to the database
                            insert_list.append([0, quid, self.respondent, text])
                        else:
                            if quid in (91,92,93,94,95,96) or self.survey_id == 7:    #Required answers, cannot be null, application must be completely filled out
                                if self.survey_id == 7:
                                    messagebox.showerror("Empty Fields", 'Student Applications must be completely filled out, if an answer is left blank by the student or parents please enter \"None\"')
                                else:
                                    messagebox.showerror("Empty Fields", "You haven't answered the required questions\n\nPlease answer all questions marked with an \"*\"")
                                return

            # If we're editing an old survey, update the survey administration details, otherwise create a new
            # administration. Set self.admin_id to the generated or given admin_id
            if self.toedit:
                admin_id = self.admin_id
                update_result = qf.update_survey_response(self.con, admin_id)
                if update_result:
                    messagebox.showerror('', 'Could not update the survey data. Call Dave')
            else:
                if self.valid_entry(date):
                    admin_id = qf.insert_new_survey_response(self.con, self.survey_id, self.respondent, date)
                else:
                    messagebox.showerror('Invalid Entry', 'You\'re trying to enter a survey for a student that\'s already been entered.\nPlease double check the respondent\'ts name, the survey type, and the date you\'ve entered above')
                    return

            #add the admin id to all the incoming response rows
            for row in insert_list:
                row[0] = admin_id

            #If updating, delete all old responses (less error prone than trying to update and add new responses if old were left blank)
            if self.toedit:
                delete_result = qf.delete_old_responses(self.con, admin_id)
                if delete_result:
                    messagebox.showerror('Error', 'Could not delete the old answers')
                    return

            #Add responses
            insert_result = qf.insert_responses(self.con, insert_list)

            #check to see if batch insert failed
            if not insert_result:
                messagebox.showinfo('Success', 'Survey Responses Added Successfully!')
                self.parentwindow.get_taken_surveys()
                if self.survey_id in (4,5,6) and not self.toedit:
                    result = self.update_district()
                    if result:
                        messagebox.showerror('Error', 'Tried to update the respondents given district but failed. Please let Dave know.')
                self.parentwindow.respondent_search()
                self.master.destroy()

            else:
                messagebox.showerror('Error', 'One of the answers could not be saved, please check to make sure no field is incorrectly entered')

    def valid_entry(self, date):
        """
        Utility function for ensuring that the survey administration is not a duplicate.
        A unique administration is defined as a distinct student id, survey id, and "date taken" for surveys
        while applications can only be entered once.
        :param date: a string formatted as MM/DD/YYYY, this format is verified in submit_answers(). If called outside of
        this method then an error will be raised if formatted incorrectly.
        :return: False if the survey information is a duplicate of an already entered survey, True otherwise.
        """
        results = qf.get_taken_surveys(self.con, self.respondent)
        date2 = time.strptime(date, '%m/%d/%Y')
        checkdate = time.strftime('%Y-%m-%d', date2) + ' 00:00:00'
        #print(self.survey_id, checkdate, self.respondent, '\n')
        for row in results:
            if self.survey_id == 7:   #If the response is an application then return false since it's already been entered for this student
                if row[4] == 7:
                    return False
            else:
                if int(row[4]) == int(self.survey_id) and str(row[1])==str(checkdate) and int(row[6])==int(self.respondent):
                    return False
        else:
            return True

    def update_district(self):
        """
        When a parent/mentor has a survey added, they must associate with a student. That student's most recent district
        is then associated with the parent as well.
        :return: None if the update is successful, -1 otherwise.
        """
        respondent_id = self.respondent
        student_id = self.linked_student
        student_district = qf.get_student_district(self.con, student_id)
        print(student_district, student_id, respondent_id)
        result = qf.update_district(self.con, respondent_id, student_district)
        return result
