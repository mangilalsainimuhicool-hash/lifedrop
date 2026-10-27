# Deploy LifeDrop on Railway

GitHub is the source-code host. GitHub Pages only serves static files and cannot execute Django, process forms, authenticate users, or connect to a Django database. Deploy the application on a Python application host instead.

This repository is configured for Railway with PostgreSQL, Gunicorn, and WhiteNoise. Railway supplies a public HTTPS domain after deployment. Review Railway's current service and database pricing before provisioning resources; prices and free/trial terms can change.

## Deploy from GitHub

1. Sign in to Railway and create a new project from the GitHub repository `mangilalsainimuhicool-hash/lifedrop`, selecting the `main` branch.
2. Add a PostgreSQL service to the project. Keep the database in the same Railway project/environment as the web service.
3. In the Django web service variables, set `DATABASE_URL` to a Railway reference to the PostgreSQL service's `DATABASE_URL`, for example `${{Postgres.DATABASE_URL}}`. Use the exact database service name shown in your project if it differs from `Postgres`.
4. Set `DEBUG` to `False`.
5. Add a `SECRET_KEY` variable using a newly generated value. Generate one locally in PowerShell with:

   ```powershell
   py -c "import secrets; print(secrets.token_urlsafe(50))"
   ```

   Paste the generated value directly into Railway's variable editor. Do not put it in Git, this document, or a committed `.env` file.
6. Deploy the service. Railway reads `railway.json`, installs the packages from `requirements.txt`, collects static assets, runs database migrations at startup, and starts Gunicorn on Railway's assigned port.
7. In the web service's Networking settings, generate a public domain. Railway provides HTTPS. Its `RAILWAY_PUBLIC_DOMAIN` variable is included in Django's allowed hosts and CSRF trusted origins.
8. Open the generated `https://...up.railway.app` URL and confirm the LifeDrop home page loads.

If the generated domain variable is not present in the service, set `ALLOWED_HOSTS` to that hostname and `CSRF_TRUSTED_ORIGINS` to its full `https://` origin in Railway's service variables, then redeploy.

## Windows PowerShell checks

From the project directory, install dependencies, run the checks, and run tests:

```powershell
py -m pip install -r requirements.txt
py manage.py check
py manage.py makemigrations --check --dry-run
py manage.py test lifedrop.tests
py manage.py collectstatic --no-input
```

To publish subsequent changes:

```powershell
git add .
git commit -m "Describe the change"
git push origin main
```

The GitHub Actions workflow runs Django checks, verifies migration state, runs the test suite, and collects static assets on pushes and pull requests targeting `main`.

## Production notes

- Use PostgreSQL for deployment. The local SQLite database is ignored by Git and is not included in production.
- Keep `SECRET_KEY` and the database URL in Railway's private service variables only.
- Do not run `python manage.py seed_data` in production. It creates fictional sample records and is intentionally blocked when `DEBUG=False`.
- This application coordinates donor and requester communications; it is not a clinical blood bank. Review privacy, security, and clinical operations before entering real patient or donor information.
- The GitHub Pages address cannot serve the interactive Django application. Once Railway has generated its public domain, the Pages entrypoint can be changed to link or redirect to that exact URL if desired.