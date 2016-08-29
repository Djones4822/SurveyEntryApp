#!/usr/bin/env python

import tkinter as tk
from tkinter import messagebox
import queryfuncs as qf
from gui import Main


CREDENTIALS_ERROR = 'Login Unsuccessful.\nPlease check your credentials.'
DATABASE_ERROR = 'Database Error.\nPlease contact the administrator'


class Login:
    def __init__(self, master):
        """
        Login process utilizing an Oracle db for queries and cx_Oracle for query handling. Opens the main GUI if login
        is successful.
        :param master: TK Master root
        :return: None
        """

        self.master = master
        self.master.title("Database Login")
        self.frame = tk.Frame(self.master)
        self.frame.pack()
        self.loginName = tk.StringVar()
        self.loginPw = tk.StringVar()
        self.loginDomain = tk.StringVar()

        tk.Label(self.frame, text='Database Login',  font=("Helvetica", 16, "bold"), pady=5).grid(row = 0, columnspan=2)
        tk.Label(self.frame, text='Username').grid(row=1, sticky='e')
        tk.Label(self.frame, text='Password').grid(row=2, sticky='e')
        tk.Label(self.frame, text='Domain').grid(row=3, sticky='e')

        self.loginNameEntry = tk.Entry(self.frame, textvariable=self.loginName)
        self.loginNameEntry.grid(row=1, column=1, sticky='w')
        self.loginPWEntry = tk.Entry(self.frame, show="*", textvariable=self.loginPw)
        self.loginPWEntry.grid(row=2, column=1, sticky='w')
        self.loginDomainEntry = tk.Entry(self.frame, textvariable=self.loginDomain)
        self.loginDomainEntry.grid(row=3, column=1, sticky='w')

        tk.Button(self.frame, text='Login', width=10, command=self.try_login).grid(row=self.frame.grid_size()[1]+1, columnspan=2, pady=5)
        self.master.bind('<Return>', self.try_login)

    def try_login(self, *args):
        """
        Function used to try to login to the database, if success then the login window is closed and the main GUI
        screen is opened.
        :param args: catchall, not used.
        :return: None
        """
        name = self.loginName.get()
        pw = self.loginPw.get()
        domain = self.loginDomain.get()
        con = qf.connect(name, pw, domain)
        if con == -2:
            messagebox.showerror('Credentials Error', CREDENTIALS_ERROR)
        elif con == -1:
            messagebox.showerror('Database Error', DATABASE_ERROR)
        else:
            self.master.withdraw()
            self.newWindow = tk.Toplevel(self.master)
            self.app = Main(self.newWindow, con)