from bot.songs_collector import SongCollector

collector = SongCollector()
collector.save_songs_data_to_json('songs_data.json')