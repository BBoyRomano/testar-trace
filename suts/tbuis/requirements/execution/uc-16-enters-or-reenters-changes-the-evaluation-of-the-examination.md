# Enters or reenters (changes) the evaluation of the examination
ID: UC.16
Actor: teacher

## Preconditions
- Teacher is already logged in to the UIS
- Teacher is on the page Evaluation Table

## Main flow
1. Teacher chooses a subject from the dropdown menu of entry form Filter
2. If teacher wants only to enter new evaluations, he/she will keep the checkbox Includes students with already set grade unchecked
3. If teacher wants to search or change already entered evaluations, he/she will check the checkbox Includes students with already set grade.
4. Teacher clicks on the button Filter
5. Teacher chooses the desired evaluation of the student for a specific exam date from the dropdown menu
6. Teacher clicks on the button Submit
7. UIS enters the student's examination result for the selected subject
8. Message confirming a successful execution will appear

## Alternative flow
1. 1a. Dropdown menu in the entry form Filter does not show any subject, i.e. Teacher does not teach any subject at the moment
2. 1a-1. The UC.16 cannot proceed
3. 5a. If there is no exam date for the selected subject and the table Evaluation Table displays: No exam dates for this subject
4. 5a-1. The UC.16 cannot proceed
5. 6a. If the evaluated student is the last student registered on this term and the checkbox Includes students with already set grade. is unchecked
6. Postcondition: Conditions 1-17 of the main postcondition list are now enforced
7. Postcondition: Selected term in the table Evaluation table in the menu Evaluation table displays: No students on this exam date

## Postconditions
- UIS enters the subject's evaluation to the student and changes the DB and its tables accordingly
- Teacher is still on the page Evaluation Table
- Message confirming a successful execution appears
- The subject and its exam dates remain visible in the table Evaluation table
- If the checkbox Includes students with already set grade is checked, the student and his/her evaluation remain visible in the table
- If the checkbox Includes students with already set grade is not checked, the student is removed from the table
- If the student scored A-E (i.e. he/she passed), he/she is removed from the list in the menu My Subjects
- If the student scored F (i.e. he/she did not pass), he/she remains on the list in the menu My Subjects
- Student is removed from the list of examination participans in the menu My Exam Dates
- Student is removed from the list of examination participans in the menu Set Evaluation
- Student's View: regardless of the evaluation the subject disappears from the table in the menu My Exam Dates
- Student's View: if the student scored A-E (i.e. he/she passed), the subject is removed from the table Enrolled Subjects in the menu My Subjects
- Student's View: if the student scored A-E (i.e. he/she passed), the credits are added to the amount in the header of the table Completed Subjects in the menu My Subjects
- Student's View: if the student scored A-E (i.e. he/she passed), the subject appears with the achieved score in the table Completed Subjects in the menu My Subjects
- Student's View: if the student scored A-E (i.e. he/she passed), the subject disappears from the table in the menu Other Exam Dates
- Student's View: if the student scored F (i.e. he/she did not pass), the subject remains in the table Enrolled Subjects in the menu My Subjects
- Student's View: if the student scored F (i.e. he/she did not pass), the subject remains in the table in the menu Other Exam Dates
