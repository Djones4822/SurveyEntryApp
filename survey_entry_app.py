#!/usr/bin/env python

"""
This is a Tkinter GUI. This GUI is used for the entry of Surveys and is custom built to a set of requirements and
a specific survey design. This tool was designed to fill the need for a method to convert a large collection of surveys
adminstered on paper into a meaningful database. Survey respondents can be either students, parents, or mentors,
and have a set of potential surveys available to each. The surveys were preprocess and loaded into an oracle database
and that database is heavily utilized for a variety of tasks within this application. Concretely, the database contains
respondent information, survey information (questions, orders, answers) and the responses entered by the user.
The surveys necessitated certain unique constraints and checks, which are performed
according to the requirements set at the beginning of the project.

Future revisions should seek to make it more generalizable since it currently requires specific knowledge
of the surveys to correctly function. Changes in the surveys will undoubtedly necessitate changes to this code.

IMPORTANT: This app necessarily relies on an Oracle Database.
"""

import tkinter as tk
from login import Login

__author__ = "David Jones"
__copyright__ = "Copyright 2016, David Jones"
__license__ = "MIT"
__version__ = "3.5"
__maintainer__ = "David Jones"
__email__ = "david.jones4822@gmail.com"
__status__ = "Production"

def main():
    root = tk.Tk()
    app = Login(root)
    root.mainloop()

if __name__ == '__main__':
    main()