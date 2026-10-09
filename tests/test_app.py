import argparse
import contextlib
import io
import unittest
from unittest.mock import MagicMock, patch
import app

class InputTests(unittest.TestCase):
    def test_rating_bounds_and_nonfinite(self):
        for value in ('-1', '6', 'nan', 'inf', 'abc'):
            with self.subTest(value=value), self.assertRaises(argparse.ArgumentTypeError):
                app.rating_value(value)
        for value in ('0', '4.5', '5'):
            self.assertEqual(app.rating_value(value), float(value))

    def test_title_and_document_validation(self):
        with self.assertRaises(argparse.ArgumentTypeError): app.nonempty('   ')
        for value in ('albums/abc', '.', '..'):
            with self.assertRaises(argparse.ArgumentTypeError): app.document_id(value)

    def test_noop_update_does_not_connect(self):
        with patch('app.connect') as connect, contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(app.main(['update', 'missing']), 1)
            connect.assert_not_called()

class DatabaseBehaviorTests(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.collection = self.db.collection.return_value
        self.output = io.StringIO()

    def run_command(self, argv):
        with contextlib.redirect_stdout(self.output):
            app.run(app.parser().parse_args(argv), self.db)

    def test_update_preserves_unspecified_fields_and_accepts_zero(self):
        self.run_command(['update', 'abc', '--rating', '0', '--review='])
        fields = self.collection.document.return_value.update.call_args.args[0]
        self.assertEqual(fields['rating'], 0)
        self.assertEqual(fields['review'], '')
        self.assertNotIn('title', fields)
        self.assertNotIn('artist', fields)
        self.assertIn('updated_at', fields)

    def test_missing_update_propagates_without_creating(self):
        from google.api_core.exceptions import NotFound
        doc = self.collection.document.return_value
        doc.update.side_effect = NotFound('Missing')
        with self.assertRaises(NotFound):
            self.run_command(['update', 'missing', '--rating', '3'])
        doc.create.assert_not_called()
        doc.set.assert_not_called()

    def test_delete_cancellation(self):
        snapshot = self.collection.document.return_value.get.return_value
        snapshot.exists = True
        snapshot.to_dict.return_value = {'title': 'Test', 'artist': 'Artist', 'rating': 3}
        with patch('builtins.input', return_value='no'):
            self.run_command(['delete', 'abc'])
        self.collection.document.return_value.delete.assert_not_called()

    def test_delete_confirmation(self):
        snapshot = self.collection.document.return_value.get.return_value
        snapshot.exists = True
        snapshot.to_dict.return_value = {}
        with patch('builtins.input', return_value='DELETE'):
            self.run_command(['delete', 'abc'])
        self.collection.document.return_value.delete.assert_called_once_with(timeout=15)

    def test_artist_filter_sent_to_firestore(self):
        self.collection.where.return_value.stream.return_value = []
        self.run_command(['list', '--artist', 'BAD BUNNY'])
        filtering = self.collection.where.call_args.kwargs['filter']
        self.assertEqual(filtering.field_path, 'artist_key')
        self.assertEqual(filtering.value, 'bad bunny')

    def test_listener_releases_watch_on_interrupt(self):
        class ImmediateEvent:
            ready = False
            def is_set(self): return self.ready
            def set(self): self.ready = True
            def wait(self, timeout):
                if timeout == 20: return self.ready
                raise KeyboardInterrupt
        watch = MagicMock()
        watch.is_active = True
        def subscribe(callback):
            callback([], [], None)
            added = MagicMock()
            added.type.name = 'ADDED'
            added.document.id = 'abc'
            added.document.to_dict.return_value = {'title': 'Test'}
            callback([], [added], None)
            return watch
        self.collection.on_snapshot.side_effect = subscribe
        with patch('app.Event', ImmediateEvent): self.run_command(['watch'])
        watch.unsubscribe.assert_called_once()
        self.assertIn('ADDED: Test [abc]', self.output.getvalue())

if __name__ == '__main__': unittest.main()
