# SYNBYTE deployment — Netlify and Python hosting

## Important
The site is a **Flask server-rendered app**. Netlify Drop/static hosting alone cannot
run its Python routes, authentication, SQLite orders or payment verification.
Uploading the project ZIP directly to Netlify will **not** publish a working ordering system.

## Practical deployment route

1. Keep the project in a private repository. Do not commit `instance/`, database files,
   `.env` secrets, or user uploads.
2. Deploy the Python app to a Python web host (for example, Render Web Service).
   Suggested build command: `pip install -r requirements.txt`
   Suggested start command: `gunicorn app:app --workers 1 --threads 4 --timeout 90`
   Select the directory containing `app.py` as the working directory.
3. Add environment variables via hosting dashboard:
   - `SECRET_KEY` = long, random, private value.
   - `SEED_DEMO=0` (avoid creating publicly known demo accounts).
   - `SESSION_COOKIE_SECURE=1` if the service uses HTTPS.
   - `PAYMENT_PROVIDER=razorpay_test` only after correctly configuring test keys/webhook.
4. **State durability matters.** On ephemeral hosting, SQLite data and uploaded photos
   disappear after a restart or redeploy. Do not accept real orders without persistent
   database storage and permanent media storage. To use Render persistent disk for
   SQLite, configure `SYNBYTE_DB` to a disk-mounted path, e.g. `/var/data/synbyte.sqlite3`.
   Vendor-uploaded images currently go to `static/images/food/`, so those files also
   need to be moved to persistent storage before any reliable public launch.
5. Test student sign-up, vendor sign-up, dashboard, order flow, notifications,
   failed payment, duplicate payment callbacks, and token collection on the host.

## Optional: use a Netlify URL in front of the Python host

Once the Python app is running at a real HTTPS URL, Netlify can proxy requests
through a `200` rewrite. A sample is in `NETLIFY_GATEWAY_EXAMPLE/_redirects`.
Edit the placeholder backend URL to YOUR actual deployed hostname, then publish
just that folder as a Netlify static site. Netlify will be a proxy; the Python
backend still runs on your chosen host. Verify login cookies, forms, and payment
callbacks end to end on the final Netlify URL before sharing it.

## What remains before real deployment
- Verify the copyright/license and visual correctness of all 32 food photos.
- Configure and test payment gateway; demo payment does not charge money.
- Move media uploads to persistent storage.
- Perform hosting-specific penetration, security and integration testing.
- Obtain institutional approval if representing an official LPU service.

Useful official docs:
- https://render.com/docs/deploy-flask
- https://docs.netlify.com/manage/routing/redirects/rewrites-proxies/
- https://render.com/docs/disks
