#!/usr/bin/env python

import tkinter as tk
import queryfuncs as qf

class PossibleMatches:
    def __init__(self, master, con, previous_window, matches):
        """
        TK Window opened when the user attempted to add a new respondent that had a fuzzy string comparison match of 50%
        or more to an existing respondent. Includes a scrollable table that displays the existing respondent's information
        for comparison.

        :param master: TK window root
        :param con: cx_oracle connection object
        :param previous_window: the "add_respondent" window that opened this window
        :param matches: the list of potential matches from the fuzzywuzzy comparison
        """
        self.master = master
        self.con = con
        self.previous_window = previous_window
        self.matches = matches

        self.masterframe = tk.Frame(self.master)
        self.masterframe.pack()
        tk.Label(self.masterframe, text='Possible Respondent Matches', font=('Times New Roman', 18, 'bold')).pack(anchor='w')
        self.canvasframe = tk.Frame(self.masterframe)
        self.canvasframe.pack()

        self.canvas = tk.Canvas(self.canvasframe, width=600, borderwidth=0, bg='#ffffff')
        self.vsb = tk.Scrollbar(self.canvasframe)
        self.results_frame = tk.Frame(self.canvas)
        self.canvas.config(yscrollcommand=self.vsb.set)
        self.vsb.pack(side="right", fill='y')
        self.canvas.pack(side='left', fill='both', expand=True)
        self.canvas.create_window((4, 4), window=self.results_frame, anchor='nw', tags='self.results_frame')
        self.vsb.config(command=self.canvas.yview)
        self.results_frame.bind("<Configure>", self.onFrameConfigure)
        self.master.bind_all("<MouseWheel>", self.onMouseWheel)


        tk.Label(self.results_frame, text='ID', width=5, font=('Times New Roman', 11, 'bold')).grid(row=0, column=0, sticky='nsew')
        tk.Label(self.results_frame, text='Name', width=15, font=('Times New Roman', 11, 'bold')).grid(row=0, column=1, sticky='nsew')
        tk.Label(self.results_frame, text='District', width=15, font=('Times New Roman', 11, 'bold')).grid(row=0, column=2, sticky='nsew')
        tk.Label(self.results_frame, text='Match Percent', width=5, font=('Times New Roman', 11, 'bold')).grid(row=0, column=3, sticky='nsew')
        tk.Label(self.results_frame, text='Linked Students', font=('Times New Roman', 11, 'bold')).grid(row=0, column=4, sticky='nsw')

        currow = 1
        print(self.matches)
        for res in self.matches:
            previous_matched_students = qf.get_given_students(self.con, res[1])
            prev_resp_string = ', '.join(str(i) for i in previous_matched_students)
            label1 = tk.Label(self.results_frame, text=res[1], width=5)
            label2 = tk.Label(self.results_frame, text=res[0], width=15)
            label3 = tk.Label(self.results_frame, text=res[3], width=15)
            label4 = tk.Label(self.results_frame, text='{}%'.format(res[2]), width=15)
            label5 = tk.Label(self.results_frame, text=prev_resp_string, wraplength=150, justify='left')

            label1.grid(row=currow, column=0)
            label2.grid(row=currow, column=1)
            label3.grid(row=currow, column=2)
            label4.grid(row=currow, column=3)
            label5.grid(row=currow, column=4, sticky='nsw')

            currow += 1

        self.buttonframe = tk.Frame(self.masterframe)
        self.buttonframe.pack(anchor='c')
        self.select_button = tk.Button(self.masterframe, text='My Respondent Is New', command=self.addnew)
        self.addnew_button = tk.Button(self.masterframe, text='Cancel', command=self._cancel)
        self.select_button.pack( anchor='c', padx=5, pady=5)
        self.addnew_button.pack(anchor='c', padx=5, pady=5)

    def _cancel(self):
        """
        Button method used when the user determines that their respondent already exists, does not add the respondent
        and closes both this and the previous window.
        :return:
        """
        self.master.destroy()
        self.previous_window.master.destroy()

    def addnew(self):
        """
        Button method used when the user determines that their respondent is unique. Calls the submit() method from the
        previous window with the bypass_duplicate argument set to True.
        """
        self.previous_window.submit(bypass_duplicate=True)

    def onFrameConfigure(self, event):
        """
        Method used to configure the potential matches frame to scroll
        :param event: the event information passed by tkinter
        :return: None
        """
        '''Reset the scroll region to encompass the inner frame'''
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def onMouseWheel(self, event):
        """
        Method used to scroll using the mousewheel. First finds whether or not the mouse is sitting over a canvas
        and if so performs the scroll behavior.
        :param event: the event information passed by tkinter
        :return: None
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
        "pressed," Tkinter automatically assocaites it with the top-most widget. This function checks to see if that widget
        is a canvas, and if so, returns the widget object. Otherwise the fuction recursively calls itself again with the
        widget.parent() as the argument. This is performed until the widget is the master as set during the __init__() method
        at which point it is determined that the mouse is definitely NOT over a canvas.

        :param widget: The widget of the current recursion step that we're on.
        :return: False if the mouse is not over a canvas, True otherwise.
        """
        if widget == self.master:
            return False
        elif isinstance(widget, tk.Canvas):
            return widget
        else:
            return self.findCanvas(widget.master)