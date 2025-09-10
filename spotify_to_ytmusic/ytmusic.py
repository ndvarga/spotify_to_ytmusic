import os
import re
from collections import OrderedDict

from ytmusicapi import YTMusic
import os.path as path
import sys
if __name__ != '__main__':
    from spotify_to_ytmusic.utils.match import get_best_fit_song_id
    from spotify_to_ytmusic.settings import Settings
#maybe change

path = path.dirname(os.path.realpath(__file__)) + os.sep


class YTMusicTransfer:
    def __init__(self):
        settings = Settings()
        headers = settings["youtube"]["headers"]
        assert headers.startswith("{"), "ytmusicapi headers not set or invalid"
        self.api = YTMusic(auth='spotify_to_ytmusic/browser.json')

    def create_playlist(self, name, info, privacy="PRIVATE", tracks=None):
        return self.api.create_playlist(name, info, privacy, video_ids=tracks)

    def rate_song(self, id, rating):
        return self.api.rate_song(id, rating)

    def search_songs(self, tracks):
        videoIds = []
        songs = list(tracks)
        notFound = list()
        print("Searching YouTube...")
        for i, song in enumerate(songs):
            name = re.sub(r" \(feat.*\..+\)", "", song["name"])
            artist_names = ' '.join(song["artists"])
            query = ' '.join([artist_names, name])
            query = query.replace(" &", " ")
            result = self.api.search(query, "songs")
            if len(result) == 0:
                notFound.append(query)
            else:
                targetSong = get_best_fit_song_id(result, song)
                if targetSong is None:
                    notFound.append(query)
                else:
                    videoIds.append(targetSong)

            if i > 0 and i % 10 == 0:
                print(f"YouTube tracks: {i}/{len(songs)}")

        with open(path + "noresults_youtube.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(notFound))
            f.write("\n")
            f.close()

        return videoIds

    def add_playlist_items(self, playlistId, videoIds):
        videoIds = OrderedDict.fromkeys(videoIds)
        self.api.add_playlist_items(playlistId, videoIds)

    def get_playlist_id(self, name:str=None, url:str=None):
        if name:
            pl = self.api.get_library_playlists(10000)
            try:
                playlist = next(x for x in pl if x["title"].find(name) != -1)["playlistId"]
                return playlist
            except:
                raise Exception("Playlist title not found in playlists")
        elif url:
            playlist_id = re.findall(r'list=([\w-]+)\??\&?', url)
            if not playlist_id:
                raise Exception("No playlist found!")
            return playlist_id[0]



    def remove_songs(self, playlistId):
        items = self.api.get_playlist(playlistId, 10000)
        if "tracks" in items:
            self.api.remove_playlist_items(playlistId, items["tracks"])

    def remove_playlists(self, pattern):
        playlists = self.api.get_library_playlists(10000)
        p = re.compile("{0}".format(pattern))
        matches = [pl for pl in playlists if p.match(pl["title"])]
        print("The following playlists will be removed:")
        print("\n".join([pl["title"] for pl in matches]))
        print("Please confirm (y/n):")

        choice = input().lower()
        if choice[:1] == "y":
            [self.api.delete_playlist(pl["playlistId"]) for pl in matches]
            print(str(len(matches)) + " playlists deleted.")
        else:
            print("Aborted. No playlists were deleted.")

    """ Checks songs from a playlist dict returned by YTMusic.get"""
    def check_songs(self, playlist:dict, spotifyTracks):
        playlistSongs = playlist["tracks"]
        playlistIdSet = {song["videoId"] for song in playlistSongs}
        spotifySongIdSet = set(self.search_songs(spotifyTracks))
        newSongIdSet = spotifySongIdSet - playlistIdSet
        return newSongIdSet

if __name__ == '__main__':
    from utils.match import get_best_fit_song_id
    from settings import Settings
    print("Current working directory:", os.getcwd())
    yt_music = YTMusicTransfer()
    print(yt_music.get_playlist_id('new'))
    print(yt_music.check_songs())        
