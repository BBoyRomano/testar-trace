# Cancelling the registration (enrollment) to a subject
ID: UC.04
Actor: student

## Preconditions
- Student is logged in to the UIS
- User is located on the My Subjects page

## Main flow
1. Student will click on the X button located in the row of the subject intended for cancellation in the Enrolled subjects table
2. Modal window Unenroll subject will appear with a preselected subject intended for cancellation
3. Student will click on the Unenroll subject button
4. UIS will remove subject from the student's list of subjects
5. Message confirming successful execution will appear

## Alternative flow
1. 1a. Table has no values in it, i.e. the student is not enrolled on any subject
2. 1a-1. The UC.04 cannot proceed
3. 2a. Student sees a modal window Unenroll subject with a preselected subject intended for cancellation
4. 2a-1. Student will choose a different subject for cancellation
5. 2a-2. Student will continue from the 3rd step of the main success scenario onwards
6. 3a. Student sees a modal window Unenroll subject with a preselected subject intended for cancellation
7. 3a-1. Student clicks on the Cancel button
8. Postcondition: The menu My Subjects appears
9. Postcondition: No data are overwritten or changed
10. 4a. Internal error occurs in the UIS/DB during the cancellation of the subject's registration in the DB
11. Postcondition: Menu My Subjects appears
12. Postcondition: Message claiming an unsuccessful execution will appear
13. Postcondition: No data are overwritten or changed

## Postconditions
- UIS removes the subject from the student's list of subjects and changes tables of the DB accordingly
- Student is still on the My Subjects page
- Message confirming successful execution appears
- The subject is removed from the table Enrolled subjects from the My Subjects menu
- The subject appears on the list in the table of the Other Subjects menu
- The subject is removed from the list in the table My Exam Dates
- The subject is removed from the list in the table Other Exam Dates
- Teacher's View: the student disappears from the teacher's list of students enrolled on the selected subject from the table located on the menu My Subjects
- Teacher's View: the student must not appear on the teacher's list of students enrolled on the selected subject's exam from the table located on the menu My Exam Dates
- Teacher's View: the student must not appear on the teacher's list of the selected subject's evaluations from the table located on the menu Set Evaluation
- Teacher's View: the student must not appear on the teacher's list of the selected subject's evaluations from the table located on the menu Evaluation Table
