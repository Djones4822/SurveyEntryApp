from cx_Freeze import setup, Executable
import sys

base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
        name='Survey Entry',
        version='3.5',
        url='',
        license='MIT',
        author='David Jones',
        author_email='davidj@gsfc.org',
        description='GUI For entering survey data from surveys',
        executables= [Executable(".\Survey Entry.py", base=base)],
        options={"build_exe":{"packages":['tkinter','cx_Oracle','datetime','time','enter_survey','student_lookup',
                                          'queryfuncs','login','gui', 'datetime', 'add_respondent', 'possible_matches',
                                          'fuzzywuzzy', 'Levenshtein']}}
)
