# Displays all examination participants
ID: UC.13
Actor: teacher

## Preconditions
- Teacher is already logged in to the UIS
- Teacher is on the page My Exam Dates

## Main flow
1. Teacher clicks on the button

## Alternative flow
1. 1a. No student has registered for the exam date
2. Postcondition: Table in a modal window will display: No participants

## Postconditions
- Modal window Exam Date Participants is displayed with a list of the examination participants
- No data are overwritten or changed
