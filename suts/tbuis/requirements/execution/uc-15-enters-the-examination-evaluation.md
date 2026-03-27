# Enters the examination evaluation
ID: UC.15
Actor: teacher

## Preconditions
- Teacher is already logged in to the UIS
- Teacher is on the page Set Evaluation

## Main flow
1. Teacher selects the desired subject and exam date from the menu
2. Teacher selects the desired student from the dropdown menu
3. Teacher selects the desired evaluation from the dropdown menu
4. Teacher clicks on the button Save evaluation
5. UIS will enter the student's result for the selected subject
6. Message confirming a successful execution will appear

## Alternative flow
1. 1a. No entry form is displayed and instead there is a message reading: Warning! No exam dates, i.e. teacher does not have any announced exam dates at the moment
2. 1a-1. UC.15 cannot proceed
3. 1b. Teacher chooses an exam date without any students registered
4. Postcondition: Teacher is still on page Set Evaluation
5. Postcondition: Entry form displays: No student is registered on this exam date!
6. Postcondition: The button Save evaluation is disabled
7. 4a. If the evaluated student is the last student registered on this exam date
8. Postcondition: Conditions 1-4 and 6-16 of the main postcondition list are now enforced
9. Postcondition: Entry form displays: No student is registered on this exam date!
10. Postcondition: Button Save evaluation is disabled

## Postconditions
- UIS adds the results to the student for the selected subject and edits its DB and its tables accordingly
- Teacher is still on page Set Evaluation
- Message confirming a successful execution appears
- Appropriate subject and the exam date remain selected in the dropdown menu
- The student disappears from the list in the dropdown menu
- Evaluation A is predefined in the dropdown menu
- If the student scored A-E (i.e. he/she passed), he/she is removed from the list in the menu My Subjects
- If the student scored F (i.e. he/she did not pass), he/she remains on the list in the menu My Subjects
- The student disappears from the list of examination participans in the menu My Exam Dates
- The evaluation will appear by the student in the menu Evaluation Table with the filter Includes students with already set grade turned on
- Student's View: regardless on the evaluation, the subject disappears from the table in the menu My Exam Dates
- Student's View: if the student scored A-E (i.e. he/she passed), the subject is removed from the table Enrolled Subjects in he menu My Subjects
- Student's View: if the student scored A-E (i.e. he/she passed), credits are added to the amount in the header of the table Completed Subjects in the menu My Subjects
- Student's View: if the student scored A-E (i.e. he/she passed), the subject appears with the achieved score in the table Completed Subjects in the menu My Subjects
- Student's View: if the student scored A-E (i.e. he/she passed), the subject disappears from the table in the menu Other Exam Dates
- Student's View: if the student scored F (i.e. he/she did not pass), the subject remains in the table Enrolled Subjects in the menu My Subjects
- Student's View: if the student scored F (i.e. he/she did not pass), the subject remains in the table in the menu Other Exam Dates
