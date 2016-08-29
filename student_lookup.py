#!/usr/bin/env python

import tkinter as tk
import queryfuncs as qf
from tkinter import messagebox

class StudentLookup:
    def __init__(self, master, widget, con, prev_window):
        """
        TKinter window opened when, during the course of survey entry, the user clicks on the "Student name" field
        in a non-student survey. This field MUST be correctly entered, and as such, requires the user to search through
        and select from the list of students already entered into the DB. This process is performed nearly identically
        to the respondent search process in the main gui class. The window is constructed with a scrollable canvas for
        the search results.

        :param master: TK Root object of the window
        :param widget: the widget object from the survey that this process is filling out
        :param con: cx_Oracle connection object
        :param prev_window: the survey window object that constructed this object
        """
        self.toenter_widget = widget
        self.con = con
        self.master = master
        self.prev_window = prev_window

        self.resp_frame = None
        self.results_frame = None
        self.resp_canvas = None

        self.master.minsize(700,300)
        self.master.title('Student Lookup')
        self.master_frame = tk.Frame(self.master)
        self.master_frame.pack()

        self.search_frame = tk.Frame(self.master_frame)
        self.titleLabel = tk.Label(self.search_frame, text="REACH Student Search", font=("Times New Roman", 16, 'bold'))
        self.titleInstructions = tk.Label(self.search_frame, text="Please Enter any part of the student\'s name or leave blank to search all")
        self.respSearchStr = tk.StringVar()
        self.respSearchEntry = tk.Entry(self.search_frame, textvariable = self.respSearchStr, width=100)
        self.respSearchEntry.bind('<Return>', self.respondent_search)
        self.respSearchButton = tk.Button(self.search_frame, text="Search", width=10, command=self.respondent_search)
        self.titleLabel.pack(anchor='w')
        self.titleInstructions.pack(anchor='w')
        self.respSearchEntry.pack()
        self.respSearchButton.pack()
        self.search_frame.pack()

        self.resp_frame = tk.Frame(self.master_frame)
        tk.Label(self.resp_frame, text='Please click on an ID', font=('Times New Roman', '11', 'bold')).pack(anchor='w', padx=20)
        self.resp_search_canvas = tk.Canvas(self.resp_frame, borderwidth=0, height = 100, width=600)
        self.search_vsb = tk.Scrollbar(self.resp_frame)
        self.resp_results_frame = tk.Frame(self.resp_search_canvas)
        self.resp_search_canvas.config(yscrollcommand=self.search_vsb.set)
        self.search_vsb.pack(side="right", fill='y')
        self.resp_search_canvas.pack(side='left', fill='both', expand=True)
        self.resp_search_canvas.create_window((0, 0), window=self.resp_results_frame, anchor='nw', tags='self.resp_results_frame')
        self.search_vsb.config(command=self.resp_search_canvas.yview)
        self.resp_results_frame.bind("<Configure>", self.onFrameConfigure)
        self.resp_frame.pack(anchor='w', padx=30)
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

        self.selectbutton = tk.Button(self.master_frame, text='Select Student', command=self.select_student, state='disabled')
        self.selectbutton.pack(anchor='c', side='bottom')

    def respondent_search(self, *args):
        """
        Button method used to search the db for the entered respondent. Clears any previous respondent selection as well.
        :param args: catchall for event args
        :return: None, the process calls create_response_table() method that constructs the tk objects
        """
        self.active_resp = {}
        self.active_id = None
        text = self.respSearchStr.get()
        results = qf.search_for_names(self.con, text)
        results = [res for res in results if res[4]=='Student']
        self.create_response_table(results)

    def onFrameConfigure(self, event):
        """
        Reset the scroll region to encompass the inner frame. Since there is only one scrollable object here there
        is no need for the recursive canvas search method.
        """
        cnvs = event.widget.master
        cnvs.configure(scrollregion=cnvs.bbox("all"))

    def create_response_table(self, respondents):
        """
        Method destroys any old response table and then constructs a new table. Table is built using lables aligned in
        the grid. Each label can be clicked on with the left mouse button to "highlight" that row and mark that respondent
        as active. Active respondents have their id stored in the instance variable "active_id" and is passed accordingly.
        :param respondents: List generated from qf.search_for_names which returns respondents that match the given string
        :return: None, constructs tk objects and places them into the window.
        """
        for child in self.created_respondents_table.winfo_children():
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
        Utility method used to simluate the "selecting" of a table row. When a label is clicked, that label is back referenced
        to find all corresponding labels in that row. The default background for each label in that row is stored and the
        backgrounds for each label is set to a light blue. If a row had been previously selected, that row has its default
        background returned and the new row overwrites that saved information.
        :param event: the event widget passed by tkinter
        :return: None, changes the backgrounds and sets self.active_id to the selected student
        """
        # Set previously selected to old color
        selected_widget = event.widget

        if self.active_resp:
            for i in range(len(self.active_resp)):
                self.active_resp[i]['widget'].config(bg = self.active_resp[i]['bg'])

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

        self.active_id = self.resp_widgets[selected_row]['id'].cget('text')
        self.selectbutton.config(state='normal')

    def select_student(self, *args):
        """
        Button method that passes the selected student back to the survey window that constructed this current window.
        If a student is selected then the student information is passed and the window destroyed, otherwise a popup is
        opened that asks the user to select a student.
        :param args: catchall for button arguments passed
        :return: None, passes the information back to the survey window or opens an error-popup.
        """
        if not self.active_id:
            messagebox.showerror('Select Student', 'Please select a student')
            return
        self.prev_window.linked_student = self.active_id
        name = qf.get_student_name_from_id(self.con, self.active_id)
        self.toenter_widget.config(state='normal')
        self.toenter_widget.delete(0,'end')
        self.toenter_widget.insert(0, name)
        self.toenter_widget.config(state='readonly')
        self.master.destroy()
