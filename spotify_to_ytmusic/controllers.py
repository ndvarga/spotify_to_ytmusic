import time
from datetime import datetime
import os
import spotipy
import json

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
    if args.store_json:
        spotify.saveSpotifyPlaylist()
    _create_ytmusic(args, playlist, ytmusic)


def liked(args):
    spotify, ytmusic = _init()
    if not isinstance(spotify.api.auth_manager, spotipy.SpotifyOAuth):
        raise Exception("OAuth not configured, please run setup and set OAuth to 'yes'")
    playlist = spotify.getLikedPlaylist()
    _create_ytmusic(args, playlist, ytmusic)


def update(args):
    spotify, ytmusic = _init()
    if args.use_local:
        spPlaylistId = spotify.extract_playlist_id_from_url(args.playlist)
        spPlaylistName = spotify.api.playlist(spPlaylistId)["name"]
        with open(f'playlists{os.sep}{spPlaylistName}.json', "r", encoding="utf-8") as spotify_tracks:
            playlist = json.load(spotify_tracks)
            spotify_tracks.close()
    else:
        playlist = _get_spotify_playlist(spotify, args.playlist)
    playlistId = ytmusic.get_playlist_id(args.name)
    ytPlaylist =  ytmusic.api.get_playlist(playlistId)
    

    if args.diff:
        newIds = ytmusic.check_songs(playlist, playlist["tracks"])
        if newIds:
            newPlaylistId = ytmusic.create_playlist(args.diff, "", privacy=ytPlaylist["privacy"], trackIds=newIds)
            print(f"Success! diff playlist created at {newPlaylistId}")
            
    else:    
       videoIds = ytmusic.search_songs(playlist["tracks"])
       if not args.append:
           ytmusic.remove_songs(playlistId)
       time.sleep(2)
       ytmusic.add_playlist_items(playlistId, videoIds)


def remove(args):
    ytmusic = YTMusicTransfer()
    ytmusic.remove_playlists(args.pattern)

def debug(args):
    spotify, yt_music = _init()
    if args.store:
        spotify.getSpotifyPlaylist(args.playlist)
        spotify.saveCurSpotifyPlaylist()
    if args.check_diff:
        spPlaylistId = spotify.extract_playlist_id_from_url(args.playlist)
        playlistName = spotify.api.playlist(spPlaylistId)
        with open(f'playlists{os.sep}{playlistName}.json') as tracks_json:
            spotify_items = json.load(tracks_json)
            tracks_json.close()
        spotify_items = spotify.getSpotifyPlaylist(args.playlist)
        if f'https://' in args.yt_playlist or f'music.youtube.com' in args.yt_playlist:
            yt_playlist_id = yt_music.get_playlist_id(url = args.yt_playlist)
        else: 
            yt_playlist_id = yt_music.get_playlist_id(name = args.yt_playlist)
        
        yt_items = yt_music.api.get_playlist(yt_playlist_id, 10000)

        
        if "tracks" in yt_items:
            yt_music.check_songs(yt_items["tracks"], spotify_items["name"])
            """yt_track_titles = [track['title'].lower() for track in yt_items['tracks']]
            yt_artists = [[artist['name'].lower() for artist in track['artists']] for track in yt_items['tracks']]
            for i, yt_track in enumerate(yt_track_titles):
                
                track_name_matches = difflib.get_close_matches(yt_track, spotify._cur_track_titles, cutoff = 0.65, n = 10)
                if track_name_matches:
                    track_idx = spotify._cur_track_titles.index(track_name_matches[0])
                    artist_name_matches = []
                    for artist in yt_artists[i]:
                        artist_name_matches.append(difflib.get_close_matches(artist, spotify._cur_artist_names[track_idx,:].tolist(), n = 100))    
                    print(f'matched these songs from youtube to spotify: {track_name_matches}')                    
                else:
                    #TODO do something when there are no matches
                    pass
                
                if spotify._cur_track_titles.count(track_name_matches[0]) > 0:
                    print(f'matched these songs from youtube to spotify: {track_name_matches}')
                    # for match in track_name_matches:
                    #     pass
        else:
            raise Exception("tracks not found in YT Playlist!")"""
        
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
