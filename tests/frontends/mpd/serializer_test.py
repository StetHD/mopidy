import datetime as dt
import unittest

from mopidy import settings
from mopidy.frontends.mpd import translator, protocol
from mopidy.models import Album, Artist, Playlist, Track

class TrackMpdFormatTest(unittest.TestCase):
    def setUp(self):
        settings.LOCAL_MUSIC_FOLDER = '/dir/subdir'

    def tearDown(self):
        settings.runtime.clear()

    def test_mpd_format_for_empty_track(self):
        result = translator.track_to_mpd_format(Track())
        self.assert_(('file', '') in result)
        self.assert_(('Time', 0) in result)
        self.assert_(('Artist', '') in result)
        self.assert_(('Title', '') in result)
        self.assert_(('Album', '') in result)
        self.assert_(('Track', 0) in result)
        self.assert_(('Date', '') in result)
        self.assertEqual(len(result), 7)

    def test_mpd_format_with_position(self):
        result = translator.track_to_mpd_format(Track(), position=1)
        self.assert_(('Pos', 1) not in result)

    def test_mpd_format_with_cpid(self):
        result = translator.track_to_mpd_format(Track(), cpid=1)
        self.assert_(('Id', 1) not in result)

    def test_mpd_format_with_position_and_cpid(self):
        result = translator.track_to_mpd_format(Track(), position=1, cpid=2)
        self.assert_(('Pos', 1) in result)
        self.assert_(('Id', 2) in result)

    def test_mpd_format_track_uses_uri_to_mpd_relative_path(self):
        track = Track(uri='file:///dir/subdir/song.mp3')
        path = dict(translator.track_to_mpd_format(track))['file']
        correct_path = translator.uri_to_mpd_relative_path(track.uri)
        self.assertEqual(path, correct_path)

    def test_mpd_format_for_nonempty_track(self):
        track = Track(
            uri=u'a uri',
            artists=[Artist(name=u'an artist')],
            name=u'a name',
            album=Album(name=u'an album', num_tracks=13),
            track_no=7,
            date=dt.date(1977, 1, 1),
            length=137000,
        )
        result = translator.track_to_mpd_format(track, position=9, cpid=122)
        self.assert_(('file', 'a uri') in result)
        self.assert_(('Time', 137) in result)
        self.assert_(('Artist', 'an artist') in result)
        self.assert_(('Title', 'a name') in result)
        self.assert_(('Album', 'an album') in result)
        self.assert_(('Track', '7/13') in result)
        self.assert_(('Date', dt.date(1977, 1, 1)) in result)
        self.assert_(('Pos', 9) in result)
        self.assert_(('Id', 122) in result)
        self.assertEqual(len(result), 9)

    def test_mpd_format_artists(self):
        track = Track(artists=[Artist(name=u'ABBA'), Artist(name=u'Beatles')])
        translated = translator.track_artists_to_mpd_format(track)
        self.assertEqual(translated, u'ABBA, Beatles')


class PlaylistMpdFormatTest(unittest.TestCase):
    def test_mpd_format(self):
        playlist = Playlist(tracks=[
            Track(track_no=1), Track(track_no=2), Track(track_no=3)])
        result = translator.playlist_to_mpd_format(playlist)
        self.assertEqual(len(result), 3)

    def test_mpd_format_with_range(self):
        playlist = Playlist(tracks=[
            Track(track_no=1), Track(track_no=2), Track(track_no=3)])
        result = translator.playlist_to_mpd_format(playlist, 1, 2)
        self.assertEqual(len(result), 1)
        self.assertEqual(dict(result[0])['Track'], 2)


class UriToMpdRelativePathTest(unittest.TestCase):
    def setUp(self):
        settings.LOCAL_MUSIC_FOLDER = '/dir/subdir'

    def tearDown(self):
        settings.runtime.clear()

    def test_none_file_returns_empty_string(self):
        uri = 'file:///dir/subdir/music/album/song.mp3'
        result = translator.uri_to_mpd_relative_path(None)
        self.assertEqual('', result)

    def test_file_gets_stripped(self):
        uri = 'file:///dir/subdir/music/album/song.mp3'
        result = translator.uri_to_mpd_relative_path(uri)
        self.assertEqual('/music/album/song.mp3', result)


class TracksToTagCacheFormatTest(unittest.TestCase):
    def setUp(self):
        settings.LOCAL_MUSIC_FOLDER = '/dir/subdir'

    def tearDown(self):
        settings.runtime.clear()

    def check_headers(self, result):
        self.assert_(('info_begin',) in result)
        self.assert_(('mpd_version', protocol.VERSION) in result)
        self.assert_(('fs_charset', protocol.ENCODING) in result)
        self.assert_(('info_end',) in result)
        return result[4:]

    def check_song_list(self, result):
        self.assertEqual(('songList begin',), result[0])
        self.assertEqual(('songList end',), result[-1])
        return result[1:-1]

    def test_empty_tag_cache(self):
        result = translator.tracks_to_tag_cache_format([])
        result = self.check_headers(result)
        result = self.check_song_list(result)
        self.assertEqual(len(result), 0)

    def test_simple_tag_cache_has_header(self):
        track = Track(uri='file:///dir/subdir/song.mp3')
        result = translator.tracks_to_tag_cache_format([track])
        result = self.check_headers(result)
        result = self.check_song_list(result)
        self.assertEqual(len(result), 0)

    def test_simple_tag_cache_has_header(self):
        track = Track(uri='file:///dir/subdir/song.mp3')
        formated = translator.track_to_mpd_format(track)
        formated.insert(0, ('key', 'song.mp3'))

        result = translator.tracks_to_tag_cache_format([track])
        result = self.check_headers(result)
        result = self.check_song_list(result)

        for a, b in zip(result, formated):
            self.assertEqual(a, b)
