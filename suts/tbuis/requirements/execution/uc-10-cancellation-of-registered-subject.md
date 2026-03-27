# Cancellation of registered subject
ID: UC.10
Actor: teacher

## Preconditions
- Teacher is already logged in to the UIS
- Teacher is on the page My Subjects

## Main flow
1. Teacher clicks on the button Remove located in the row of the subject intended for cancellation
2. UIS will remove the subject from the teacher's subject list
3. Message confirming a successful execution will appear

## Alternative flow
1. 1a. Table has no entries, i.e. the teacher in not teaching any subjects at the moment
2. 1a-1. The UC.10 cannot proceed
3. 1b. Buttons Remove are disabled for every subject that has at least one student enrolled
4. 1b-1. The UC.10 cannot proceed
5. 2a. Internal error occurs in the UIS/DB during the cancellation of the subject in the DB
6. Postcondition: Teacher remains on the page My Subjects
7. Postcondition: Message claiming an unsuccessful execution appears
8. Postcondition: No data are overwritten or changed

## Postconditions
- UIS removes the subject from the teacher's list of subjects and changes the DB and its tables accordingly
- Teacher is still on the page My Subjects
- Message confirming a successful execution appears
- The subject is removed from the list in the menu My Subjects
- The subject is removed from the list in the menu My Exam Dates
- The subject is removed from the list in the menu New Exam Dates
- The subject is removed from the list in the menu Set Evaluation
- The subject is removed from the list in the menu Evaluation Table
- The subject appears on the list in the menu Others' Subjects
- The subject is removed from the teachers' list of subjects in the menu List of All Teachers for the specific teacher
- Student's View: students must not find the removing teacher's name for the subject in the menu Other Subjects
- Student's View: students must not find the removing teacher's name on the list of examining teachers for the selected subject in the menu Other Exam Dates
