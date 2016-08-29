#!/usr/bin/env python

import tkinter as tk
import tkinter.messagebox as messagebox
from fuzzywuzzy import fuzz
import queryfuncs as qf
from possible_matches import PossibleMatches

class AddRespondent:
    def __init__(self, master, main_gui, con):
        """
        TK Window Class used for when the user wants to add a respondent. User is constrained to add only respondent types
        2 or 3 (Parents and Mentors) as a design decision. Process gets the name of the respondent and then runs a fuzzy
        string comparison against all other respondents of the same type, if the name has a 50% match to any existing respondent
        then the user is notified and asked to review the existing respondents to ensure that the one they are entering is unique.
        :param master: Master TK Root
        :param main_gui: the main GUI object from gui.py. This is passed so that the main window can be updated upon completion
        :param con: cx_Oracle object
        """
        self.master = master
        self.main_gui = main_gui
        self.con = con
        self.mainframe = tk.Frame(self.master)
        self.mainframe.pack()

        self.master.minsize(400, 130)
        self.master.title("Add Survey Respondent")
        self.mainlabel = tk.Label(self.mainframe, text='Add New Respondent', font=('Times New Roman', 18, 'bold'))
        self.mainlabel.pack(anchor='w')

        self.populate()

    def populate(self):
        """
        Populates the entry window consisting of a header, labels, a tk.Entry() widget, 2 radio buttons to choose the
        respondent type and a tk.Button() widget that performs the fuzzy comparison and subimts the information
        :return:
        """
        self.entryframe = tk.Frame(self.mainframe)
        self.entryframe.pack()
        self.name_var = tk.StringVar()
        self.name_entry = tk.Entry(self.entryframe, textvariable=self.name_var, width=35)
        name_entry_label = tk.Label(self.entryframe, text='Name')
        name_entry_label.grid(row=0, column=0)
        self.name_entry.grid(row=0,column=1, columnspan=2)

        self.respondent_type_var = tk.StringVar()
        self.respondent_type_var.set('')

        parent_radio = tk.Radiobutton(self.entryframe, text='Parent', variable=self.respondent_type_var, value='2')
        mentor_radio = tk.Radiobutton(self.entryframe, text='Mentor', variable=self.respondent_type_var, value='3')

        parent_radio.grid(row=1, column=1)
        mentor_radio.grid(row=1, column=2)

        submit_button = tk.Button(self.entryframe, text='Submit', width=10, command=self.submit)
        submit_button.grid(row=3, column = 0, columnspan=3, sticky='nsew')

    def submit(self, bypass_duplicate=False):
        """
        Method used to fetch the entered name and respondent type to compare against existing database. Uses fuzzywuzzy
        python package to compare the names, if any comparison yields a 50% match or higher then that respondent is added
        to a "review" list that is passed to another window. This can be bypassed by passing "True" as the second argument.
        This is used specifically when the user has completed their review of potential matches and determined that the
        repsondent is unique. NOTE: If the respondent exists exactly then the respondent cannot be added again (database enforced constraint)

        :param bypass_duplicate: Boolean, argument telling whether or not fuzzy matching should be bypassed
        :return: None if error, otherwise the window is destroyed upon completion.
        """
        name = self.name_var.get()
        resp_type = self.respondent_type_var.get()
        if not resp_type:
            messagebox.showerror("Select Type", "Please select the type of the respondent")
            return None
        if not name:
            messagebox.showerror("Empty Name", "Please enter the full name of the respondent")
            return None

        if not bypass_duplicate:
            existing_respondents = qf.get_existing_respondents(self.con, resp_type)
            if name.lower() in [resp[0].lower() for resp in existing_respondents]:
                messagebox.showerror('Already Exists', 'The respondent you are trying to add already exists in the database.\n\nIf you believe this to be an error, please contact the Admin.')
                return None
            possible_matches = []
            for existing_name, id, district in existing_respondents:
                token = fuzz.ratio(name.lower(), existing_name.lower())
                if token >= 50:
                    possible_matches.append((existing_name, id, token, district))

            if possible_matches:
                possible_matches = sorted(possible_matches, key=lambda x: x[2])
                errorstr = 'There are {} possible matches for the name you\'ve entered.\n\nPlease review them to ensure that your entry is unique'.format(len(possible_matches))
                messagebox.showinfo('Possible Duplicate', errorstr)
                self.possiblematchwindow = tk.Toplevel()
                self.app = PossibleMatches(self.possiblematchwindow, self.con, self, possible_matches)
            else:
                result = qf.insert_respondent(self.con, name.title(), resp_type)
                if not result:
                    messagebox.showinfo('Sucess!', 'Respondent added successfully!')
                    self.master.destroy()
                    self.main_gui.respSearchEntry.insert(0, name.title())
                    self.main_gui.respondent_search()
                else:
                    messagebox.showerror('Error!', 'Respondent has not added correctly.\n\nPlease take a screenshot of what you entered and send it to Dave.')
        else:
            result =  qf.insert_respondent(self.con, name.title(), resp_type)
            if not result:
                messagebox.showinfo('Sucess!', 'Respondent added successfully!')
                self.master.destroy()
                self.app.master.destroy()
                self.main_gui.respSearchEntry.insert(0, name.title())
                self.main_gui.respondent_search()
            else:
                messagebox.showerror('Error!', 'Respondent has not added correctly.\n\nPlease take a screenshot of what you entered and send it to Dave.')

