# Story: Test login

As a User, I want to log in with my email and password so that 
I can access my profile page.

## Acceptance criteria
- Valid credentials redirect to /launchpad and after Account selection to /copilot
- After successful login and Account selection, profile page shows the User's name and 'Workspace' and 'Huddles' buttons are visible.
- Invalid credentials show an error message toaster "The user credentials were incorrect"