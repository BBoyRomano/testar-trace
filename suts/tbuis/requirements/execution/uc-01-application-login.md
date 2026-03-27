# Application login
ID: UC.01
Actor: Unlogged user

## Preconditions
- User is on the UIS homepage
- No other user is logged in - the upper bar has a black colour and on the right side there is a visible Login option of the menu

## Main flow
1. User will select the Login option from the menu located on the right side of the upper bar
2. Specific Login Page form will appear
3. User will fill his/her login name that already exists (=is registered in the UIS)
4. User will enter `pass` in the password field - the universal password for all users
5. User will press the Login button

## Alternative flow
1. 5a. Selected login name does not exist in the UIS
2. Postcondition: User is not redirected from the Login Page
3. Postcondition: Error message regarding an unsuccessful login attempt appears
4. 5b. User enters other password than a `pass`
5. Postcondition: User is not redirected from the Login Page
6. Postcondition: Error message regarding an unsuccessful login attempt appears

## Postconditions
- UIS determines whether the user is either a student or a teacher by checking the users' login name
- Login option disappears from the top bar menu
- Clickable first and last name of the logged-in user appear in the upper bar on the right
- Logout option appears in the upper bar on the right
- User with student's status sees a Student's view menu, the upper bar is orange
- User with teacher's status sees a Teacher's view menu, the upper bar is dark green
- Overview page appears to both Student and Teacher
