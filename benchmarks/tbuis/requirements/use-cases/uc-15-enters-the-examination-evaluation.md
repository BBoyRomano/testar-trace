## UC.15 — Enters the examination evaluation

**Context of Use**
Teacher enters the examination evaluation of the selected student for the selected exam date he/she teaches

**Scope**
UIS

**Level**
user goal

**Primary Actor**
teacher

**Stakeholders and Interests**

- teacher: intends to enter the examination evaluation of a student

**Constraints**
N/A

**Preconditions**

1. Teacher is already logged in to the UIS
2. Teacher is on the page Set Evaluation

**Trigger**
Teacher enters values and entries to the form

**Main Success Scenario**

1. Teacher selects the desired subject and exam date from the menu
2. Teacher selects the desired student from the dropdown menu
3. Teacher selects the desired evaluation from the dropdown menu
4. Teacher clicks on the button Save evaluation
5. UIS will enter the student's result for the selected subject
6. Message confirming a successful execution will appear

**Postconditions**

1. UIS adds the results to the student for the selected subject and edits its DB and its tables accordingly
2. Teacher is still on page Set Evaluation
3. Message confirming a successful execution appears
4. Appropriate subject and the exam date remain selected in the dropdown menu
5. The student disappears from the list in the dropdown menu
6. Evaluation A is predefined in the dropdown menu
7. If the student scored A-E (i.e. he/she passed), he/she is removed from the list in the menu My Subjects
8. If the student scored F (i.e. he/she did not pass), he/she remains on the list in the menu My Subjects
9. The student disappears from the list of examination participans in the menu My Exam Dates
10. The evaluation will appear by the student in the menu Evaluation Table with the filter Includes students with already set grade turned on
11. Student's View: regardless on the evaluation, the subject disappears from the table in the menu My Exam Dates
12. Student's View: if the student scored A-E (i.e. he/she passed), the subject is removed from the table Enrolled Subjects in he menu My Subjects
13. Student's View: if the student scored A-E (i.e. he/she passed), credits are added to the amount in the header of the table Completed Subjects in the menu My Subjects
14. Student's View: if the student scored A-E (i.e. he/she passed), the subject appears with the achieved score in the table Completed Subjects in the menu My Subjects
15. Student's View: if the student scored A-E (i.e. he/she passed), the subject disappears from the table in the menu Other Exam Dates
16. Student's View: if the student scored F (i.e. he/she did not pass), the subject remains in the table Enrolled Subjects in the menu My Subjects
17. Student's View: if the student scored F (i.e. he/she did not pass), the subject remains in the table in the menu Other Exam Dates

**Alternative Flows**

- **1a. No entry form is displayed and instead there is a message reading: Warning! No exam dates, i.e. teacher does not have any announced exam dates at the moment**
  - 1a-1. UC.15 cannot proceed

- **1b. Teacher chooses an exam date without any students registered**

  Postconditions:
  1. Teacher is still on page Set Evaluation
  2. Entry form displays: No student is registered on this exam date!
  3. The button Save evaluation is disabled

- **4a. If the evaluated student is the last student registered on this exam date**

  Postconditions:
  1. Conditions 1-4 and 6-16 of the main postcondition list are now enforced
  2. Entry form displays: No student is registered on this exam date!
  3. Button Save evaluation is disabled

**Technology and Data Variations List**

1. Teacher accessed this page from the menu My Exam Dates of the modal window Participants by clicking the button Grade (see UC.13); in the selection list there is a predefined (disabled) subject and the exam date and the evaluated student, the program proceeds with step 3 of main scenario onwards

**Related Information**

- One subject can be taught by up to two teachers and each one of them can announce up to 3 exam dates. Teacher can only evaluate students registered on the exam date announced by him/her.
- After selecting the item from the menu Set Evaluation the entry form has predefined entries
- One of the taught subject (selected randomly) will appear with a exam date
- The first of the participans is selected (in order of the date of registration on exam date)
- Score A is selected

---
