import time
from datetime import datetime

import spotipy

from spotify_to_ytmusic.setup import setup as setup_func
from spotify_to_ytmusic.spotify import Spotify
from spotify_to_ytmusic.ytmusic import YTMusicTransfer
import difflib
import re


def _get_spotify_playlist(spotify:Spotify, playlist_url:str):
    try:
        return spotify.getSpotifyPlaylist(playlist_url)
    except Exception as ex:
        print(
            "Could not get Spotify playlist. Please check the playlist link.\n Error: " + repr(ex)
        )
        return


def _print_success(name, playlistId):
    print(
        f"Success: created playlist '{name}' at\n"
        f"https://music.youtube.com/playlist?list={playlistId}"
    )


def _init():
    """Construct `Spotify` and `YTMusicTransfer` objects. Returned as tuple."""
    return Spotify(), YTMusicTransfer()


def all(args):
    spotify, ytmusic = _init()
    pl = spotify.getUserPlaylists(args.user)
    print(str(len(pl)) + " playlists found. Starting transfer...")
    count = 1
    for p in pl:
        print("Playlist " + str(count) + ": " + p["name"])
        count = count + 1
        try:
            playlist = spotify.getSpotifyPlaylist(p["external_urls"]["spotify"])
            videoIds = ytmusic.search_songs(playlist["tracks"])
            playlist_id = ytmusic.create_playlist(
                p["name"],
                p["description"],
                "PUBLIC" if p["public"] else "PRIVATE",
                videoIds,
            )
            if args.like:
                for id in videoIds:
                    ytmusic.rate_song(id, "LIKE")
            _print_success(p["name"], playlist_id)
        except Exception as ex:
            print(f"Could not transfer playlist {p['name']}. {str(ex)}")


def _create_ytmusic(args, playlist, ytmusic:YTMusicTransfer):
    date = ""
    if args.date:
        date = " " + datetime.today().strftime("%m/%d/%Y")
    name = args.name + date if args.name else playlist["name"] + date
    info = playlist["description"] if (args.info is None) else args.info
    videoIds = ytmusic.search_songs(playlist["tracks"])
    if args.like:
        for id in videoIds:
            ytmusic.rate_song(id, "LIKE")

    playlistId = ytmusic.create_playlist(
        name, info, "PUBLIC" if args.public else "PRIVATE", videoIds
    )
    _print_success(name, playlistId)


def create(args):
    spotify, ytmusic = _init()
    
    playlist = _get_spotify_playlist(spotify, args.playlist)
    _create_ytmusic(args, playlist, ytmusic)


def liked(args):
    spotify, ytmusic = _init()
    if not isinstance(spotify.api.auth_manager, spotipy.SpotifyOAuth):
        raise Exception("OAuth not configured, please run setup and set OAuth to 'yes'")
    playlist = spotify.getLikedPlaylist()
    _create_ytmusic(args, playlist, ytmusic)


def update(args):
    spotify, ytmusic = _init()
    playlist = _get_spotify_playlist(spotify, args.playlist)
    playlistId = ytmusic.get_playlist_id(args.name)
    ytPlaylist =  ytmusic.api.get_playlist(playlistId)
    

    if args.onlynew:
        #create a new playlist for changes
        #see if the songs in the spotify playlist exist in the youtube music playlist, if it doesn't add it to the new playlist
        newSongs = ytmusic.check_songs(playlistId, playlist["tracks"])
        newVideoIds = ytmusic.search_songs(newSongs)
        newIdsSet = set(newVideoIds)
        oldIdsSet = set(track["videoId"] for track in ytPlaylist["tracks"])
        if (newIdsSet - oldIdsSet):
            newIds = list(newIdsSet.difference(oldIdsSet))
            print(newIds)
            newPlaylistId = ytmusic.create_playlist(args.onlynew, "", privacy=ytPlaylist["privacy"], trackIds=newIds)
            print(f"playlist created at {newPlaylistId}")
   # else:    
   #     videoIds = ytmusic.search_songs(playlist["tracks"])
    #    if not args.append:
     #       ytmusic.remove_songs(playlistId)
      #  time.sleep(2)
       # ytmusic.add_playlist_items(playlistId, videoIds)


def remove(args):
    ytmusic = YTMusicTransfer()
    ytmusic.remove_playlists(args.pattern)

def debug(args):
    spotify, yt_music = _init()
    if args.check_diff:
        sp_song_set = spotify.getSpotifyPlaylist(args.playlist)
        if f'https://' in args.yt_playlist or f'music.youtube.com' in args.yt_playlist:
            yt_playlist_id = yt_music.get_playlist_id(url = args.yt_playlist)
        else: 
            yt_playlist_id = yt_music.get_playlist_id(name = args.yt_playlist)
        yt_music.api.get_song(yt_playlist_id)
        yt_items = yt_music.api.get_playlist(yt_playlist_id, 10000)

        if "tracks" in yt_items:
            yt_track_set = {(track["title"].lower(), tuple(artist["name"].lower() for artist in track["artists"])): track for track in yt_items["tracks"]}
            for sp_song in sp_song_set.keys():
                song_matches = difflib.get_close_matches(sp_song, yt_track_set, n = 1, cutoff = 0.4)
                if not song_matches:
                    #TODO do something when there are no matches
                    pass
                print(song_matches)
        else:
            raise Exception("tracks not found in YT Playlist!")
        
        #check pattern for remix or edit
        pattern = r"(\(((?:(?:\w|\:)+\s)?(?:(?:\w|\:)+\s)?(?:[rR]emix|[Ee]dit))\))"
        for track in yt_items["tracks"]:
            re_match = re.sub(pattern, r" \2", track["title"])
            if re_match:
                print(f"match: {re_match[0]}")
       

        #print(diffSongs)
        # return [sp_song_set[song] for song in diffSongs]
        #print(song_matches)

def setup(args):
    setup_func(args.file)
