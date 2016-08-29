#!/usr/bin/env python

import tkinter as tk
from tkinter import messagebox
import datetime
import queryfuncs as qf
from enter_survey import SurveyEntry
from add_respondent import AddRespondent

class Main:
    def __init__(self, master, con):
        """
        This is the main GUI of the entire app. Users are directed here after logging in and this window stays open during
        the duration of use. In this window, the user searches for respondents, can add a new parent/mentor respondent if
        one is not already entered, can view and select previously entered surveys to edit, or add a new survey administrations.

        :param master: TK root object that this window is created in.
        :param con: cx_Oracle connection object created during login process
        """
        self.CON = con
        self.master = master

        # initialize future attributes
        self.resp_frame = None
        self.resp_search_canvas = None
        self.resp_search_vsb = None
        self.taken_surveys_frame = None
        self.available_surveys_frame = None
        self.active_toadd_survey = None
        self.active_id = None
        self.resp_widgets = None
        self.active_resp = None
        self.taken_surveys_widgets = None
        self.add_survey_button = None
        self.toadd_survey_name = None
        self.available_surveys_widgets = None
        self.taken_surveys_canvas = None
        self.taken_surveys_vsb = None
        self.resp_results_frame = None
        self.search_vsb = None
        self.taken_surveys_results_frame = None
        self.active_taken_survey = None
        self.active_taken_survey_widgets = None

        #Set Window information, in particular, bind the "return" key to search for respondents given the text entered
        self.master.protocol("WM_DELETE_WINDOW", self.exit_program)
        self.master.title("Respondent Search and Survey Entry")
        self.master.minsize(width=850, height=525)
        #self.master.maxsize(width=850, height=525)
        self.master.bind("<Return>", self.respondent_search)
        self.master.bind_all("<MouseWheel>", self.onMouseWheel)

        # Respondent Search outline widget construction
        self.respSearchFrame = tk.Frame(self.master)
        self.titleLabel = tk.Label(self.respSearchFrame, text="REACH Respondent Search", font=("Times New Roman", 16, 'bold'))
        self.titleInstructions = tk.Label(self.respSearchFrame, text="Please Enter any part of the respondents name or leave blank to search all")
        self.respSearchStr = tk.StringVar()
        self.respSearchEntry = tk.Entry(self.respSearchFrame, textvariable = self.respSearchStr, width=100)
        self.respSearchEntry.bind('<Return>', self.respondent_search)
        self.respSearchButton = tk.Button(self.respSearchFrame, text="Search", width=10, command=self.respondent_search)
        self.respSearchFrame.pack()
        self.titleLabel.pack(anchor='w')
        self.titleInstructions.pack(anchor='w')
        self.respSearchEntry.pack()
        self.respSearchButton.pack()

        #Respondent Search Results frames and canvas construction
        self.resp_frame = tk.Frame(self.master)
        tk.Label(self.resp_frame, text='Please click on an ID', font=('Times New Roman', '11', 'bold')).pack(anchor='w', padx=20)
        self.resp_search_canvas = tk.Canvas(self.resp_frame, borderwidth=0, height = 200, width=580, bg='#ffffff', bd=1)
        self.search_vsb = tk.Scrollbar(self.resp_frame)
        self.resp_add = tk.Button(self.resp_frame, text="Add New Respondent", command=self.add_respondent)
        self.resp_add.pack(side='bottom', anchor='c')
        self.resp_results_frame = tk.Frame(self.resp_search_canvas)
        self.resp_search_canvas.config(yscrollcommand=self.search_vsb.set)
        self.search_vsb.pack(side="right", fill='y')
        self.resp_search_canvas.pack(side='left', fill='both', expand=True)
        self.resp_search_canvas.create_window((0, 0), window=self.resp_results_frame, anchor='nw', tags='self.resp_results_frame')
        self.search_vsb.config(command=self.resp_search_canvas.yview)
        self.resp_results_frame.bind("<Configure>", self.onFrameConfigure)
        self.resp_frame.pack(anchor='w', padx=120)
        self.resp_labels_frame = tk.Frame(self.resp_results_frame)
        tk.Label(self.resp_labels_frame, text='ID', font=('Times New Roman', 10, 'bold'), width=7, bd=1).grid(row=2, column=0, sticky='nsew')
        tk.Label(self.resp_labels_frame, text='Name', font=('Times New Roman', 10, 'bold'), width=25, bd=1).grid(row=2, column=1, sticky='nsew')
        tk.Label(self.resp_labels_frame, text='District', font=('Times New Roman', 10, 'bold'), width=25, bd=1).grid(row=2, column=2, sticky='nsew')
        tk.Label(self.resp_labels_frame, text='Cohort', font=('Times New Roman', 10, 'bold'), width=10, bd=1).grid(row=2, column=3, sticky='nsew')
        tk.Label(self.resp_labels_frame, text='Type', font=('Times New Roman', 10, 'bold'), width=20, bd=1).grid(row=2, column=4, sticky='nsew')
        self.resp_labels_frame.pack(anchor='w')
        self.created_respondents_table = tk.Frame(self.resp_results_frame)
        tk.Label(self.created_respondents_table, text='Search for Respondents Above', font=('Times New Roman', 10, 'italic'), width=75, bd=1).grid(row=1, column=0, columnspan=4, sticky='nsew')
        self.created_respondents_table.pack(anchor='w')

        #Taken Surveys construction, frames and canvas construction
        self.taken_surveys_frame = tk.Frame(self.master)
        tk.Label(self.taken_surveys_frame, text='Surveys Previously Entered', font=('Times New Roman', 11, 'bold')).pack(anchor='w')
        self.edit_survey_button = tk.Button(self.taken_surveys_frame, text='Edit Survey', width=12, command=self.edit_survey, state='disabled')
        self.edit_survey_button.pack(anchor='c',side='bottom')
        self.taken_surveys_canvas = tk.Canvas(self.taken_surveys_frame, borderwidth=0, height = 125, width=450)
        self.taken_surveys_vsb = tk.Scrollbar(self.taken_surveys_frame)
        self.taken_surveys_results_frame = tk.Frame(self.taken_surveys_canvas, bg='#ffffff')
        self.taken_surveys_canvas.config(yscrollcommand=self.taken_surveys_vsb.set)
        self.taken_surveys_vsb.pack(side="right", fill='y')
        self.taken_surveys_canvas.pack(side='left',fill='both', expand=True)
        self.taken_surveys_canvas.create_window((0, 0), window=self.taken_surveys_results_frame, anchor='nw', tags='self.taken_surveys_results_frame')
        self.taken_surveys_vsb.config(command=self.taken_surveys_canvas.yview)
        self.taken_surveys_results_frame.bind("<Configure>", self.onFrameConfigure)
        self.taken_surveys_frame.pack(side='left',anchor='nw', pady=15, padx=10)
        self.taken_surveys_labels = tk.Frame(self.taken_surveys_results_frame)
        tk.Label(self.taken_surveys_labels, text='Survey Name', font=('Times New Roman', 10, 'bold'), width=15, bd=1, bg='#ffffff').grid(row=0, column=0, sticky='nsew')
        tk.Label(self.taken_surveys_labels, text='Date Taken', font=('Times New Roman', 10, 'bold'), width=15, bd=1, bg='#ffffff').grid(row=0, column=1, sticky='nsew')
        tk.Label(self.taken_surveys_labels, text='Date Entered', font=('Times New Roman', 10, 'bold'), width=15, bd=1, bg='#ffffff').grid(row=0, column=2, sticky='nsew')
        tk.Label(self.taken_surveys_labels, text='Last Updated', font=('Times New Roman', 10, 'bold'), width=15, bd=1, bg='#ffffff').grid(row=0, column=3, sticky='nsew')
        self.taken_surveys_labels.grid(row=0, sticky='nw')
        self.taken_surveys_table = tk.Frame(self.taken_surveys_results_frame)
        tk.Label(self.taken_surveys_table, text='No Surveys Found', font=('Times New Roman', 10, 'italic'), width=75, bd=1).grid(row=0, column=0, columnspan=4, sticky='nsew')
        self.taken_surveys_table.grid(row=1, sticky='nw')

        #Available surveys construction frames and canvas construction
        self.available_surveys_frame = tk.Frame(self.master, height=625, width = 300)
        self.add_survey_button = tk.Button(self.available_surveys_frame, text='Add Survey', width=12, command=self.add_survey, state='disabled')
        self.add_survey_button.pack(anchor='s', side='bottom')
        self.available_surveys_frame.pack(side='left', anchor='nw', pady=15, padx=10)
        self.available_surveys_labels = tk.Frame(self.available_surveys_frame)
        tk.Label(self.available_surveys_labels, text='Available Surveys: Please Select a Survey', font=('Times New Roman', 11, 'bold')).grid(row=0, columnspan=2, sticky='w')
        tk.Label(self.available_surveys_labels, text='Survey Name', font=('Times New Roman', 10, 'bold'), width=15, bd=1).grid(row=1, column=0, sticky='w')
        tk.Label(self.available_surveys_labels, text='Description', font=('Times New Roman', 10, 'bold'), width=10, bd=1).grid(row=1, column=1, sticky='w')
        self.available_surveys_labels.pack(anchor='w')
        self.available_surveys_table = tk.Frame(self.available_surveys_frame)
        tk.Label(self.available_surveys_table, text='No Surveys Found', font=('Times New Roman', 10, 'italic'), bd=1).grid(row=0, column=0, columnspan=2, sticky='nsew')
        self.available_surveys_table.pack(anchor='w')

    def add_respondent(self):
        """
        Button method used open the AddRespondent window and begin that process (see add_respondent.py)
        :return: None, opens a new window.
        """
        self.addrespondentwindow = tk.Toplevel(self.master)
        self.app = AddRespondent(self.addrespondentwindow, self, self.CON)

    def onMouseWheel(self, event):
        """
        Takens the widget that called this method and recursively searches its parents to see if there is a scrollable
        canvas somewhere underneath using the findCanvas() method. If so, it performs the scroll, otherwise does nothing.
        :param event: Widget that the scrollwheel button was activated over.
        :return: None, performs a scrolling effect on the canvas.
        """
        widget = event.widget.winfo_containing(event.x_root, event.y_root)
        #print(widget.winfo_parent())
        widget = self.findCanvas(widget)
        if widget:
            pass
            widget.yview_scroll(-1*event.delta//120, 'units')

    def findCanvas(self, widget):
        """
        Utility method that recursively checks if the mouse is sitting on top of a canvas. When the scrollbutton is
        "pressed," Tkinter automatically associates it with the top-most widget. This function checks to see if that widget
        is a canvas, and if so, returns the widget object. Otherwise the fuction recursively calls itself again with the
        widget.parent() as the argument. This is performed until the widget passed is the master as set during the __init__()
        method at which point it is determined that the mouse is NOT over a canvas.

        :param widget: The widget of the current recursion step that we're on.
        :return: False if the mouse is not over a canvas, True otherwise.
        """
        #print(widget)
        if widget == self.master:
            return False
        elif isinstance(widget, tk.Canvas):
            return widget
        else:
            return self.findCanvas(widget.master)

    def onFrameConfigure(self, event):
        """
        Method called to configure the canvas to scroll through the entire frame contained within.
        :param event: catch for event passed by tkinter.
        :return: None, sets the canvas scroll region to the entire bounded box.
        """
        cnvs = event.widget.master
        cnvs.configure(scrollregion=cnvs.bbox("all"))

    def exit_program(self):
        """
        Method called when the window is closed using the window manager "X" to ensure that the connection is disconnected.
        :return: None, destroys all windows and quits the application.
        """
        if messagebox.askyesno('Logoff', 'Are you sure you want to log off?'):
            self.con_disconnect()
            self.master.destroy()
            self.master.quit()

    def respondent_search(self, *args):
        """
        Method used to search the database for any respondent whose name contains the fragments entered
        :param args: catchall for the arguments passed by tkinter, currently unused.
        :return: None, calls "create_respondents_table()" to generate a tkinter table
        """
        self.active_resp = {}
        self.active_id = None
        text = self.respSearchStr.get()
        results = qf.search_for_names(self.CON, text)
        print(results)
        #print(results)
        self.create_respondents_table(results)

    def create_respondents_table(self, respondents):
        """
        Method for creating the table that displays all potential respondents that match the search field for which
        surveys can be edited or entered. First deletes all previous respondent information (their taken and available surveys)
        along with the existing created_respondents_table. Then it loops through the list of respondents passed and generates
        a new row for each respondent. Each row is selectable by clicking on any of the labels which stores that respondent's
        ID for use.
        :param respondents: a list of respondents as generated from the qf.search_for_names() function.
        :return: None, creates a set of tkinter objects and places them into the window.
        """
        for child in self.created_respondents_table.winfo_children():
            child.destroy()
        if self.taken_surveys_table:
            for child in self.taken_surveys_table.winfo_children():
                child.destroy()
        if self.available_surveys_table:
            for child in self.available_surveys_table.winfo_children():
                child.destroy()

        if not respondents:
            tk.Label(self.created_respondents_table, text='No Respondents Found', font=('Times New Roman', '10', 'bold italic'), width = 75).grid(row=1, column=0, columnspan = 4, sticky = 'nsew')

        else:
            self.resp_widgets = {}
            for rowid, row in enumerate(respondents):
                if rowid % 2 == 0:
                    bgcol = '#ffffcc'
                else:
                    bgcol = '#ffffff'
                self.resp_widgets[rowid] = {
                    'rowid':rowid,
                    'id': tk.Label(self.created_respondents_table, text=row[0], bg=bgcol, width=7, bd=1),
                    'name': tk.Label(self.created_respondents_table, text=row[1], bg=bgcol, width=25, bd=1),
                    'district': tk.Label(self.created_respondents_table, text=row[2], bg=bgcol, width=25, bd=1),
                    'cohort': tk.Label(self.created_respondents_table, text=row[3], bg=bgcol, width=10, bd=1),
                    'type': tk.Label(self.created_respondents_table, text=row[4], bg=bgcol, width=20, bd=1)
                }

                self.resp_widgets[rowid]['id'].grid(row=rowid, column=0, sticky='nsew')
                self.resp_widgets[rowid]['id'].bind('<Button-1>', self.highlight_respondent)
                self.resp_widgets[rowid]['name'].grid(row=rowid, column=1, sticky='nsew')
                self.resp_widgets[rowid]['name'].bind('<Button-1>', self.highlight_respondent)
                self.resp_widgets[rowid]['district'].grid(row=rowid, column=2, sticky='nsew')
                self.resp_widgets[rowid]['district'].bind('<Button-1>', self.highlight_respondent)
                self.resp_widgets[rowid]['cohort'].grid(row=rowid, column=3, sticky='nsew')
                self.resp_widgets[rowid]['cohort'].bind('<Button-1>', self.highlight_respondent)
                self.resp_widgets[rowid]['type'].grid(row=rowid, column=4, sticky='nsew')
                self.resp_widgets[rowid]['type'].bind('<Button-1>', self.highlight_respondent)

        self.created_respondents_table.pack(anchor='w')

    def highlight_respondent(self, event):
        """
        Utility method used to simulate the "selecting" of a table row. When a label is clicked, that label is back referenced
        to find the row and all corresponding labels in that row. The default background for each label in that row is stored
        and the backgrounds for each label is set to a light blue. If a row had been previously selected, that old row has
        its default background returned and the new row overwrites the saved information. A new respondent also necessitates
        that the frames containing the taken and available surveys are rebuilt and the old information deselected.
        :param event: the event widget passed by tkinter
        :return: None, changes the backgrounds and sets self.active_id to the selected student and populates other frames
        """
        # Set previously selected to old color
        selected_widget = event.widget

        #clear all selections
        if self.active_resp:
            for i in range(len(self.active_resp)):
                self.active_resp[i]['widget'].config(bg = self.active_resp[i]['bg'])
        for child in self.taken_surveys_table.winfo_children():
            child.destroy()
        for child in self.available_surveys_table.winfo_children():
            child.destroy()

        self.active_toadd_survey = None
        self.active_taken_survey_widgets = None
        self.active_taken_survey = None
        self.edit_survey_button.config(state='disabled')
        self.add_survey_button.config(state='disabled')

        self.active_resp= []
        selected_row = None

        for i in range(len(self.resp_widgets)):
            rowwidgets = self.resp_widgets[i]
            for widget in rowwidgets.values():
                #print(widget)
                if widget == selected_widget:
                    if widget in [widg['widget'] for widg in self.active_resp]:
                        return
                    selected_row = self.resp_widgets[i]['rowid']
                    break

        for key, widget in self.resp_widgets[selected_row].items():
            #print(widget)
            if key != 'rowid':
                self.active_resp.append({
                    'widget':widget,
                    'bg':widget.cget('bg')
                })
                widget.config(bg='lightblue')

        resp_id = self.resp_widgets[selected_row]['id'].cget('text')
        self.active_taken_survey_widgets= []
        self.active_id = resp_id
        self.active_toadd_survey = {}
        self.get_taken_surveys()
        self.get_available_surveys()

    def get_taken_surveys(self, *args):
        """
        Method used to populate the frame that displays all surveys previously entered for a selected respondent. This frame
        is displayed as a table, is scrollable, and rows are selectable. Selecting a row here necessarily deselects any
        row in the "available surveys" frame. Selecting a new respondent deselects any row here as well.
        :param args: catch-all for passed arguments. Unused.
        :return: None, constructs a frame and places it into the master window.
        """
        print('getting taken surveys')
        if self.taken_surveys_table.winfo_children():
            for child in self.taken_surveys_table.winfo_children():
                child.destroy()

        self.active_taken_survey_widgets = {}

        surveys = qf.get_taken_surveys(self.CON, self.active_id)

        if not surveys:
            tk.Label(self.taken_surveys_table, text='No Surveys Found').grid()

        else:
            self.taken_surveys_widgets = {}
            for rowid, row in enumerate(surveys):
                #print('Last updated: {}'.format(row[5]))
                self.taken_surveys_widgets[rowid] = {
                    'rowid':rowid,
                    'id': row[3],
                    'survey_id': row[4],
                    'survey': tk.Label(self.taken_surveys_table, text=row[0], width=15, bg='#ffffff'),
                    'taken': tk.Label(self.taken_surveys_table, text=datetime.datetime.date(row[1]), width=15, bg='#ffffff'),
                    'entered': tk.Label(self.taken_surveys_table, text=row[2], width=15, bg='#ffffff'),
                    'updated':tk.Label(self.taken_surveys_table, text=row[5], width=15, bg='#ffffff')
                }

                self.taken_surveys_widgets[rowid]['survey'].grid(row=rowid, column=0, sticky='nsew')
                self.taken_surveys_widgets[rowid]['survey'].bind("<Button-1>", self.highlight_taken_survey)
                self.taken_surveys_widgets[rowid]['taken'].grid(row=rowid, column=1, sticky='nsew')
                self.taken_surveys_widgets[rowid]['taken'].bind("<Button-1>", self.highlight_taken_survey)
                self.taken_surveys_widgets[rowid]['entered'].grid(row=rowid, column=2, sticky='nsew')
                self.taken_surveys_widgets[rowid]['entered'].bind("<Button-1>", self.highlight_taken_survey)
                self.taken_surveys_widgets[rowid]['updated'].grid(row=rowid, column=3, sticky='nsew')
                self.taken_surveys_widgets[rowid]['updated'].bind("<Button-1>", self.highlight_taken_survey)

        self.taken_surveys_table.grid(row=1)

    def highlight_taken_survey(self, event):
        """
        Utility method used to simulate "selection" of a taken survey. The user can select a taken survey of a respondent
        and edit the responses. Selection is done by left-mouse clicking any row after selecting a respondent. This necessarily
        deselects any selection made in the "Available Surveys" frame.
        :param event: event catch passed by tkinter.
        :return: None, passes the administration_id of the selected survey to the class to be used during the edit process.
        """
        selected_widget = event.widget
        #erase taken survey highlighting
        if self.active_taken_survey_widgets:
            for i in range(len(self.active_taken_survey_widgets)):
                self.active_taken_survey_widgets[i]['widget'].config(bg ='#ffffff')

        #erase new survey highlighting
        if self.active_toadd_survey:
            for i in range(len(self.active_toadd_survey)):
                self.active_toadd_survey[i]['widget'].config(bg = self.active_toadd_survey[i]['bg'])

        self.active_toadd_survey= []
        self.add_survey_button.config(state='disabled')
        self.active_taken_survey_widgets= []
        selected_row = None

        for i in range(len(self.taken_surveys_widgets)):
            rowwidgets = self.taken_surveys_widgets[i]
            for widget in rowwidgets.values():
                #print(widget)
                if widget == selected_widget:
                    if widget in [widg['widget'] for widg in self.active_taken_survey_widgets]:
                        return
                    selected_row = self.taken_surveys_widgets[i]['rowid']
                    break

        for key, widget in self.taken_surveys_widgets[selected_row].items():
            #print(widget)
            if key not in ('rowid', 'id', 'survey_id'):
                self.active_taken_survey_widgets.append({
                    'widget':widget,
                    'bg':widget.cget('bg')
                })
                widget.config(bg='lightblue')

        active_survey = self.taken_surveys_widgets[selected_row]['id']

        self.active_taken_survey = active_survey
        self.active_survey_id = self.taken_surveys_widgets[selected_row]['survey_id']
        self.edit_survey_button.config(state='normal')

    def edit_survey(self):
        """
        Method used to open the SurveyEntry window while passing the necessary information to enable editing.
        :return: None, opens a new tkinter window.
        """
        self.newwindow = tk.Toplevel(self.master)
        self.app = SurveyEntry(self.newwindow, self.CON, self.active_survey_id, self.active_id, self.active_taken_survey, True, self )

    def get_available_surveys(self):
        """
        Method used to generate a frame that contains the possible surveys a respondent can have entered. This is generated
        from a list returned by qf.get_available_surveys() and is presented in table format. User can select a survey to
        enter, this necessarily deselects any survey selected in the "Taken Surveys" frame. This frame is regenerated if a
        new respondent is selected.
        :return: None, generates a frame and places it in the master window.
        """
        surveys = qf.get_available_surveys(self.CON, self.active_id)
        self.available_surveys_widgets = {}
        for rowid, row in enumerate(surveys):
            self.available_surveys_widgets[rowid] = {
                'rowid': rowid,
                'id': row[0],
                'name': tk.Label(self.available_surveys_table, text=row[1]),
                'description': tk.Label(self.available_surveys_table, text=row[2], anchor='w')
            }

            self.available_surveys_widgets[rowid]['name'].grid(row=rowid, column=0, sticky='nsew')
            self.available_surveys_widgets[rowid]['name'].bind('<Button-1>', self.unlock_add_survey)
            self.available_surveys_widgets[rowid]['description'].grid(row=rowid, column=1, sticky='nsew')
            self.available_surveys_widgets[rowid]['description'].bind('<Button-1>', self.unlock_add_survey)

        self.available_surveys_table.pack(anchor='nw')

    def add_survey(self):
        """
        Button method used to enter a new survey. This button is only pressable when a survey is selected in the
        "Available surveys" frame. If the available surveys selection is deselected (either through the selection/search
        for a new respondent, or by selecting a "taken survey") then the button is disabled.
        :return: None, opens a new tkinter window using the SurveyEntry class.
        """
        survey_id = qf.get_survey_id(self.CON, self.toadd_survey_name)
        self.newwindow = tk.Toplevel(self.master)
        self.app = SurveyEntry(self.newwindow, self.CON, survey_id, self.active_id, parentwindow=self)

    def unlock_add_survey(self, event):
        """
        Utility method used to enable the "add survey" button. This method is only called when a selection is made from
        "available surveys"
        :param event: tkinter event object
        :return: None, changes the status of the "add_survey" button widget.
        """
        if self.active_taken_survey_widgets:
            for i in range(len(self.active_taken_survey_widgets)):
                self.active_taken_survey_widgets[i]['widget'].config(bg ='#ffffff')
            self.active_taken_survey_widgets= []

        #erase new survey highlighting
        if self.active_toadd_survey:
            for i in range(len(self.active_toadd_survey)):
                self.active_toadd_survey[i]['widget'].config(bg = self.active_toadd_survey[i]['bg'])
            self.active_toadd_survey= []

        self.edit_survey_button.config(state='disabled')

        selected_widget = event.widget

        self.edit_survey_button.config(state='disabled')
        self.active_taken_survey = None
        self.active_taken_survey_widgets = []

        if self.active_toadd_survey:
            for i in range(len(self.active_toadd_survey)):
                self.active_toadd_survey[i]['widget'].config(bg = self.active_toadd_survey[i]['bg'])

        self.active_toadd_survey= []
        selected_row = None

        for i in range(len(self.available_surveys_widgets)):
            rowwidgets = self.available_surveys_widgets[i]
            for widget in rowwidgets.values():
                #print(widget)
                if widget == selected_widget:
                    selected_row = self.available_surveys_widgets[i]['rowid']
                    break

        for key, widget in self.available_surveys_widgets[selected_row].items():
            #print(widget)
            if key not in ('rowid', 'id'):
                self.active_toadd_survey.append({
                    'widget':widget,
                    'bg':widget.cget('bg')
                })
                widget.config(bg='lightblue')

        self.add_survey_button.config(state='normal')
        self.toadd_survey_name = self.available_surveys_widgets[selected_row]['name'].cget('text')

    def con_disconnect(self):
        """
        Utility method used to disconnect from the oracle db
        :return: None
        """
        if self.CON:
            self.CON.close()
            #print('closed connection')
        self.master.destroy()
