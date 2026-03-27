# Cancellation of the exam date
ID: UC.12
Actor: teacher

## Preconditions
- Teacher is already logged in to the UIS
- Teacher is on the page My Exam Dates

## Main flow
1. Teacher clicks on the button X in the row of the exam date in the subject's sub-table
2. UIS will remove the exam date from the teacher's list of terms for the selected subject
3. Message confirming a successful execution will appear

## Alternative flow
1. 1a. Table has no entries, i.e. the teacher does not teach any subject at the moment
2. 1a-1. The UC.12 cannot proceed
3. 1b. Subject has empty sub-table i.e. the teacher does teach this subject but no exam dates have not been announced yet
4. 1b-1. The UC.12 cannot proceed
5. 1c. Teacher intends to cancel the exam date that has at least one student attending it
6. 1c-1. Modal JS window will appear claiming that there are students registered in this exam term
7. 1c-2. Teacher will click on the button Cancel/Zrušit
8. Postcondition: The screen of the menu My Exam Dates is still on
9. Postcondition: No data are overwritten or changed
10. 1d. Teacher intends to cancel the exam date that has at least one student attending it
11. 1d-1. A modal JS window will appear claiming that there are students registered in this exam term
12. 1d-2. Teacher will click on the button OK
13. Postcondition: The main success scenario continues from the step 2 onwards
14. 1e. Buttons X are disabled for every exam date that has at least one student attending and at least one student on this exam date was already graded
15. 1e-1. The UC.12 cannot proceed
16. 2a. Internal error occurs in the UIS/DB during the cancellation of the subject's exam date in the DB
17. Postcondition: Page My Exam Dates is still displayed
18. Postcondition: Message claiming an unsuccessful execution appears
19. Postcondition: No data are overwritten or changed

## Postconditions
- Teacher is still on the page My Exam Dates
- UIS removes the exam date from the teacher's list of terms for the selected subject and changes the DB and its tables accordingly
- Message confirming a successful execution appears
- The exam date is removed from the list in the sub-table in the menu My Exam Dates
- The exam date is removed from the list in the menu Set Evaluation
- The exam date is removed from the list in the menu Evaluation Table
- Student's View: for every student with the subject enrolled the teacher and the cancelled term have disappeared on the sub-table of the subject in the menu Other Exam Dates
