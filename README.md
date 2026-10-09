# Music Review Cloud

Music Review Cloud is a Python command-line application for storing album ratings and reviews in Cloud Firestore. Users can add albums, view their collection, search entries, update ratings and reviews, and delete albums.

The application also receives live notifications when album data changes in Firestore.

Demonstration and code walkthrough video: **REPLACE_WITH_VIDEO_LINK**

## Instructions for Build and Use

Steps to build and/or run the software:

1. Install Python and open the project folder in VS Code.
2. Create a Firebase project and a Cloud Firestore database.
3. Generate a service-account JSON key from Firebase project settings. Store this secret file outside the repository.
4. Open a PowerShell terminal in the project folder and create a virtual environment:

   ```powershell
   python -m venv .venv
   ```

5. Install the dependencies:

   ```powershell
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

6. Activate the virtual environment:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, run commands with `.\.venv\Scripts\python.exe` instead of `python`.

7. Configure the connection using your own key file path and Firebase project ID:

   ```powershell
   $env:GOOGLE_APPLICATION_CREDENTIALS = "C:\path\to\your\service-account-key.json"
   $env:FIREBASE_PROJECT_ID = "your-project-id"
   ```

8. Test the connection:

   ```powershell
   python app.py list
   ```

Set the environment variables again whenever you open a new terminal. Never upload your service-account key to GitHub. The Admin SDK uses privileged service-account access through IAM rather than client security rules; run this app on a trusted computer.

Instructions for using the software:

1. Add an album:

   ```powershell
   python app.py add --title "Un Verano Sin Ti" --artist "Bad Bunny" --rating 4.5 --review "One of my favorite summer albums."
   ```

2. View the collection or filter it:

   ```powershell
   python app.py list
   python app.py list --artist "Bad Bunny"
   python app.py list --search "verano"
   ```

   The artist filter runs in Firestore. Substring search filters the retrieved documents locally.

3. Copy an album's document ID from the output. Replace ALBUM_ID below with that ID to update its rating or review:

   ```powershell
   python app.py update ALBUM_ID --rating 5 --review "Updated after listening again."
   ```

4. Delete an album:

   ```powershell
   python app.py delete ALBUM_ID
   ```

   Type DELETE when prompted to confirm removal.

5. Receive live change notifications:

   ```powershell
   python app.py watch
   ```

   Wait for the connection message, then change an album in Firebase Console or another terminal. The application reports additions, modifications, and removals automatically. Existing documents appear in the initial snapshot. Press Ctrl+C to stop watching.

6. View all available commands:

   ```powershell
   python app.py --help
   ```

## Development Environment

To recreate the development environment, you need the following software and/or libraries with the specified versions:

* Windows with PowerShell
* Visual Studio Code
* Python 3.15.0, used during development
* Firebase Admin SDK for Python: `firebase-admin>=6.5,<8`, as specified in requirements.txt
* Google Cloud Firestore client library, installed as a dependency of firebase-admin
* A Firebase project with a Cloud Firestore database

The Firestore database uses an albums collection. Each document contains the album title, artist, normalized artist name for filtering, rating, review, creation timestamp, and update timestamp.

The application uses a service account for database access. It does not implement individual user login. Its stretch challenge is receiving live database change notifications.

## Useful Websites to Learn More

The following websites provide documentation for the tools and database operations used in this project:

* [Cloud Firestore Documentation](https://firebase.google.com/docs/firestore)
* [Firebase Admin SDK Setup](https://firebase.google.com/docs/admin/setup)
* [Add and Update Firestore Data](https://firebase.google.com/docs/firestore/manage-data/add-data)
* [Query Firestore Data](https://firebase.google.com/docs/firestore/query-data/get-data)
* [Delete Firestore Data](https://firebase.google.com/docs/firestore/manage-data/delete-data)
* [Receive Realtime Updates](https://firebase.google.com/docs/firestore/query-data/listen)
* [Python Documentation](https://docs.python.org/3/)

## Future Work

The following items I plan to fix, improve, and/or add to this project in the future:

* [ ] Add a desktop interface with buttons and an album list.
* [ ] Add album artwork.
* [ ] Implement individual user authentication.
* [ ] Improve error messages to make troubleshooting easier.
* [ ] Add pagination for larger album collections.
