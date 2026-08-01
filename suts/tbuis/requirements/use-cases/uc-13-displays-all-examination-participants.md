## UC.13 — Displays all examination participants

**Context of Use**
An overview of all students registered for the date of an examination for a specific subject ("participants")

**Scope**
UIS

**Level**
subfunction

**Primary Actor**
teacher

**Stakeholders and Interests**
- teacher: intends to get a list of participants of the exam date

**Constraints**
N/A

**Preconditions**
1. Teacher is already logged in to the UIS
2. Teacher is on the page My Exam Dates

**Trigger**
Teacher clicks the button

**Main Success Scenario**
1. Teacher clicks on the button

**Postconditions**
1. Modal window Exam Date Participants is displayed with a list of the examination participants
2. No data are overwritten or changed

**Alternative Flows**
- **1a. No student has registered for the exam date**

  Postconditions:
  1. Table in a modal window will display: No participants

**Technology and Data Variations List**
1. Every student has clickable button Grade, which will launch UC.15

**Related Information**
- Modal window can be closed via the button Close
- List sorts students alphabetically by their last name
- Similar to the UC.09 function-wise from the student's side


---
