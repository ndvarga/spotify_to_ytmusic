import unittest
from unittest import mock
from io import StringIO
import sys
import os.path as path
import time
sys.path.insert(0, path.abspath(path.join(path.dirname(__file__), '..')))
from spotify_to_ytmusic.main import main

TEST_SPOTIFY_PLAYLIST = 'https://open.spotify.com/playlist/3mIXvAn4ZkPjf7aN0S1y9N?si=6808a06bfc6d42c0'
TEST_YTMUSIC_PLAYLIST = 'https://music.youtube.com/playlist?list=PLQOA3qdxozsNv-t2F1IMwCuJkgm7wlima'
class TestCli(unittest.TestCase):
    def test_debug(self):
        # with mock.patch('sys.argv', ['spotify_to_ytmusic', 'debug', '-s', '--check-diff', TEST_SPOTIFY_PLAYLIST, TEST_YTMUSIC_PLAYLIST]):
        #     with mock.patch('sys.stdout', new=StringIO()) as fake_output:
        #         main()
        #         self.assertIn("Success: created new playlist at", fake_output.getvalue())
        # time.sleep(2)

        with mock.patch('sys.argv', ['spotify_to_ytmusic', 'create', TEST_SPOTIFY_PLAYLIST]):
            main()
        time.sleep(2)
if __name__ == '__main__':
    unittest.main()