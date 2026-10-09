"""Music reviews stored in Cloud Firestore. Run python app.py --help."""

import argparse
import math
import os
import sys
from threading import Event


def rating_value(value):
    try:
        number = float(value)
    except (ValueError, TypeError):
        raise argparse.ArgumentTypeError(
            "Rating must be a number from 0 to 5."
        )

    if not math.isfinite(number) or not 0 <= number <= 5:
        raise argparse.ArgumentTypeError(
            "Rating must be a number from 0 to 5."
        )

    return number


def nonempty(value):
    value = value.strip()

    if not value:
        raise argparse.ArgumentTypeError("This field cannot be empty.")

    return value


def document_id(value):
    value = nonempty(value)

    if "/" in value or value in (".", ".."):
        raise argparse.ArgumentTypeError(
            "Use a single album document ID, not a path."
        )

    return value


def parser():
    p = argparse.ArgumentParser(
        description="Music Review Cloud: album ratings in Firestore"
    )
    sub = p.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="Save a new album review")
    add.add_argument("--title", required=True, type=nonempty)
    add.add_argument("--artist", required=True, type=nonempty)
    add.add_argument("--rating", required=True, type=rating_value)
    add.add_argument("--review", default="")

    listing = sub.add_parser("list", help="Query the collection")
    listing.add_argument(
        "--artist",
        type=nonempty,
        help="Exact artist match, ignoring case",
    )
    listing.add_argument(
        "--search",
        type=nonempty,
        help="Title/artist substring (local filtering)",
    )

    update = sub.add_parser(
        "update", help="Update only the fields you specify"
    )
    update.add_argument("id", type=document_id)
    update.add_argument("--title", type=nonempty)
    update.add_argument("--artist", type=nonempty)
    update.add_argument("--rating", type=rating_value)
    update.add_argument(
        "--review", help="Use --review= to clear the review"
    )

    delete = sub.add_parser(
        "delete", help="Delete an album after confirmation"
    )
    delete.add_argument("id", type=document_id)

    sub.add_parser(
        "watch",
        help="Receive live change notifications; Ctrl+C to stop",
    )

    return p


def connect():
    import firebase_admin
    from firebase_admin import credentials, firestore

    key_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    project = os.environ.get("FIREBASE_PROJECT_ID")

    if not key_path or not project:
        raise ValueError(
            "Set GOOGLE_APPLICATION_CREDENTIALS and FIREBASE_PROJECT_ID."
        )

    if not os.path.isfile(key_path):
        raise ValueError("The credentials file was not found.")

    firebase_app = firebase_admin.initialize_app(
        credentials.Certificate(key_path),
        {"projectId": project},
    )

    return firestore.client(app=firebase_app)


def display(doc):
    data = doc.to_dict() or {}

    rating = data.get("rating", "?")
    rating_text = (
        f"{rating:g}"
        if isinstance(rating, (int, float))
        else str(rating)
    )

    print(f"\nID: {doc.id}")
    print(
        f"{data.get('title', '(untitled)')} — "
        f"{data.get('artist', '(unknown)')}"
    )
    print(f"Rating: {rating_text}/5")
    print(f"Review: {data.get('review', '')}")


def run(args, db):
    from firebase_admin import firestore
    from google.cloud.firestore_v1.base_query import FieldFilter

    albums = db.collection("albums")

    if args.command == "add":
        # The first document write automatically creates the collection.
        doc = albums.document()

        doc.create(
            {
                "title": args.title,
                "artist": args.artist,
                "artist_key": args.artist.casefold(),
                "rating": args.rating,
                "review": args.review,
                "created_at": firestore.SERVER_TIMESTAMP,
                "updated_at": firestore.SERVER_TIMESTAMP,
            },
            timeout=15,
        )

        print(f"Saved album. ID: {doc.id}")

    elif args.command == "list":
        query = albums

        if args.artist:
            # This filter runs in Firestore.
            query = query.where(
                filter=FieldFilter(
                    "artist_key", "==", args.artist.casefold()
                )
            )

        docs = list(query.stream(timeout=15))

        if args.search:
            # Substring search runs locally on the retrieved documents.
            term = args.search.casefold()
            matches = []

            for doc in docs:
                data = doc.to_dict() or {}
                searchable = (
                    f"{data.get('title', '')} "
                    f"{data.get('artist', '')}"
                ).casefold()

                if term in searchable:
                    matches.append(doc)

            docs = matches

        docs.sort(
            key=lambda doc: str(
                (doc.to_dict() or {}).get("title", "")
            ).casefold()
        )

        for doc in docs:
            display(doc)

        print(f"\n{len(docs)} album(s) found.")

    elif args.command == "update":
        updates = {
            key: getattr(args, key)
            for key in ("title", "artist", "rating", "review")
            if getattr(args, key) is not None
        }

        if not updates:
            raise ValueError("Specify at least one field to update.")

        if "artist" in updates:
            updates["artist_key"] = updates["artist"].casefold()

        updates["updated_at"] = firestore.SERVER_TIMESTAMP

        # update() fails if the document does not exist.
        albums.document(args.id).update(updates, timeout=15)

        print("Album updated.")

    elif args.command == "delete":
        doc = albums.document(args.id)
        snapshot = doc.get(timeout=15)

        if not snapshot.exists:
            raise ValueError("Album not found.")

        display(snapshot)

        confirmation = input(
            "Type DELETE to remove this album: "
        ).strip()

        if confirmation != "DELETE":
            print("Deletion cancelled.")
            return

        doc.delete(timeout=15)
        print("Album deleted.")

    elif args.command == "watch":
        ready = Event()

        def on_snapshot(snapshot, changes, read_time):
            if not ready.is_set():
                print(
                    f"Connected. Initial collection: "
                    f"{len(snapshot)} album(s).",
                    flush=True,
                )
                ready.set()
                return

            for change in changes:
                data = change.document.to_dict() or {}

                print(
                    f"{change.type.name}: "
                    f"{data.get('title', '(untitled)')} "
                    f"[{change.document.id}]",
                    flush=True,
                )

        watch = albums.on_snapshot(on_snapshot)

        try:
            if not ready.wait(20):
                raise ValueError(
                    "Listener did not connect within 20 seconds."
                )

            print(
                "Watching cloud changes. Edit an album in another "
                "terminal or Firebase Console.",
                flush=True,
            )

            while watch.is_active:
                Event().wait(1)

            raise ValueError("Listener stopped unexpectedly.")

        except KeyboardInterrupt:
            print("\nStopped watching.")

        finally:
            watch.unsubscribe()


def main(argv=None):
    args = parser().parse_args(argv)

    if args.command == "update" and all(
        getattr(args, key) is None
        for key in ("title", "artist", "rating", "review")
    ):
        print(
            "Error: specify at least one field to update.",
            file=sys.stderr,
        )
        return 1

    db = None

    try:
        db = connect()
        run(args, db)
        return 0

    except ImportError:
        print(
            "Install dependencies: "
            "python -m pip install -r requirements.txt",
            file=sys.stderr,
        )

    except (ValueError, OSError):
        print(
            "Setup or input error. Check environment variables, "
            "credentials, and document ID. See README.md.",
            file=sys.stderr,
        )

    except KeyboardInterrupt:
        print("\nCancelled.")

    except Exception as error:
        # Avoid printing credential objects or sensitive tracebacks.
        print(
            f"Operation failed ({type(error).__name__}). "
            "Check Firestore setup, permissions, network, and album ID.",
            file=sys.stderr,
        )

    finally:
        if db is not None:
            db.close()

    return 1


if __name__ == "__main__":
    raise SystemExit(main())