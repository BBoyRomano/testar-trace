# Displays students registered in the subject
ID: UC.11
Actor: teacher

## Preconditions
- Teacher is already logged in to the UIS
- Teacher is on the page My Subjects

## Main flow
1. Teacher clicks on the button Students for the specific subject

## Alternative flow
1. 1a. No student attends the subject
2. Postcondition: The message in the table from the modal window shows the No students message

## Postconditions
- The modal window List of students appears
- No data are overwritten or changed
