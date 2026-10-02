# GitHub and Render Deployment

CyberShield 360 is a Flask application that serves its frontend and API from the same service. GitHub stores the source; Render runs Flask; MongoDB Atlas stores persistent application data.

## 1. Publish the source to GitHub

Create an empty repository on GitHub, then run these commands from the project folder in PowerShell. Replace the URL with your repository URL.

```powershell
git init
git add .
git commit -m "Prepare CyberShield 360 deployment"
git branch -M main
git remote add origin https://github.com/YOUR-ACCOUNT/YOUR-REPOSITORY.git
git push -u origin main
```

The root `.gitignore` excludes `.env`, virtual environments, and generated uploads/reports. Do not force-add environment files or credentials.

## 2. Create the Atlas database

Create a MongoDB Atlas cluster and a database user with access to the `cybershield360` database. In Atlas Network Access, allow Render to connect. For a quick initial setup, Atlas may require `0.0.0.0/0`; use a strong, database-only password and restrict network access further when practical.

Copy the Atlas connection string. It will be entered as a Render secret, not committed to GitHub.

## 3. Deploy the Render Blueprint

In Render, choose **New > Blueprint**, connect the GitHub repository, and select `render.yaml`. During setup, provide these private values when prompted:

- `MONGO_URI`: the Atlas connection string
- `ADMIN_EMAIL`: the email to use for the production admin account
- `ADMIN_PASSWORD`: a unique, strong admin password

Render generates separate `SECRET_KEY` and `JWT_SECRET_KEY` values. The first successful connection to a new database creates the admin account and seeds the app's initial content. The known local development admin credentials are not used in production.

## 4. Verify the deployment

After Render reports the service as live, open the service URL and check `/api/health`. The frontend uses that same origin for API calls. Register a user, sign in, and verify the dashboard, learning, quiz, news, and PDF report flows.

The free Render filesystem is temporary. MongoDB data persists in Atlas, but uploaded files and generated files on the service filesystem do not survive an instance replacement. Add a persistent disk or object storage if uploaded files must persist.