# Cancellation of registered exam date
ID: UC.07
Actor: student

## Preconditions
- Student is already logged in to the UIS
- Student is on the page My Exam Dates

## Main flow
1. Student clicks on the button Unregister in the selected subject's row with an assigned date for an examination
2. UIS will remove the date of examination from the student's list of date for the selected subject
3. Message confirming a successful execution will appear

## Alternative flow
1. 1a. Table has no entries, i.e. student has not assigned any exam date for yet
2. 1a-1. The UC.07 cannot proceed
3. 2a. Internal error occurs in the UIS/DB during cancellation of the subject's exam date registration in the DB
4. Postcondition: Student is still on the page My exam dates
5. Postcondition: Message claiming an unsuccessful execution appears
6. Postcondition: No data are overwritten or changed

## Postconditions
- UIS removes the date of examination from the student's list of exam dates for the selected subject and edits its DB and its tables accordingly
- Student is still on the page My Exam Dates
- Message confirming a successful execution appears
- Subject is removed from the list in the table under the menu My Exam Dates
- The removed date appears in the sub-table under the menu Other Exam Dates
- Teacher's View: the student disappears from the teacher's list of students enrolled on the selected subject's exam from the table located on the menu My Exam Dates
- Teacher's View: the student disappears from the teacher's list of the selected subject's evaluations from the table located on the menu Set Evaluation
- Teacher's View: the student disappears from the teacher's list of the selected subject's evaluations from the table located on the menu Evaluation Table
