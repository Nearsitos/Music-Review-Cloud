# Demonstration and code walkthrough outline

Check the assignment's required video length. This outline takes roughly 4–6 minutes, but the assignment controls the length.

1. Introduce the app and its purpose: a personal music rating/review collection in Cloud Firestore.
2. Show the Firestore database and explain `albums`, documents, fields, and document IDs. Hide private keys and sensitive settings.
3. Add an album in the terminal. Show it in `list` and in Firebase Console.
4. Show an artist-filtered query. Explain that it executes in the cloud; title substring search happens locally.
5. Update the rating/review using the document ID, then query again.
6. Start `watch` in another terminal. Wait for Connected, then change an album. Point out the automatic notification.
7. Delete your demo album after confirmation. Show that it disappears and the listener reports REMOVED.
8. Walk through `connect()` and the five operation branches in `run()`. Explain environment variables and why the private key is outside the repo.
9. Explain what you learned from actually setting up and running the database, and one limitation or future improvement.

Before submitting:
- Create a public GitHub repository and upload the source files, README, dependency file, and .gitignore.
- Review the staged files before committing. Never upload credentials or .venv.
- Record/upload the demonstration and add its URL to README.md.
- Use the instructor's time-log template if one is required; transfer your actual records.
- Submit the public repository URL, video URL, and other requested deliverables.
