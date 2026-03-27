# Displays all examination participants - classmates
ID: UC.09
Actor: student

## Preconditions
- Student is already logged in to the UIS
- Student is either on the Other Exam Dates page or the My Exam Dates page

## Main flow
1. Student clicks on the button Participants for the selected subject

## Alternative flow
1. 1a. No student is registered for the exam date
2. Postcondition: Table of the modal window shows the No participants message

## Postconditions
- Modal window Exam Date Participants is displayed with a list of participants of an examination
- No data are overwritten or changed
