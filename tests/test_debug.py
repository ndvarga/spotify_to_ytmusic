import unittest
from unittest import mock
from io import StringIO
import sys
import os.path as path
sys.path.insert(0, path.abspath(path.join(path.dirname(__file__), '..')))
from spotify_to_ytmusic.main import main

class TestCli(unittest.TestCase):
    def test_debug(self):
        with mock.patch('sys.argv', ['spotify_to_ytmusic', 'debug', '--check-diff', 'https://open.spotify.com/playlist/1uRmhyzZcX3nKUKJzgSLpl', 'https://music.youtube.com/playlist?list=PLQOA3qdxozsNv-t2F1IMwCuJkgm7wlima']):
            with mock.patch('sys.stdout', new=StringIO()) as fake_output:
                main()
                self.assertIn("Success: created playlist", fake_output.getvalue())

    # def test_update_playlist(self):
    #     with mock.patch('sys.argv', ['spotify_to_ytmusic', 'update', 'https://open.spotify.com/playlist/0S0cuX8pnvmF7gA47Eu63M', 'MyPlaylist']):
    #         with mock.patch('sys.stdout', new=StringIO()) as fake_output:
    #             main()
    #             self.assertIn("Success: updated playlist", fake_output.getvalue())

    # def test_liked_songs(self):
    #     with mock.patch('sys.argv', ['spotify_to_ytmusic', 'liked']):
    #         with mock.patch('sys.stdout', new=StringIO()) as fake_output:
    #             main()
    #             self.assertIn("Success: transferred liked songs", fake_output.getvalue())

if __name__ == '__main__':
    unittest.main()