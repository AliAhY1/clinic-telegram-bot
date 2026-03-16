# utils/photos.py


async def get_user_photo(bot, user_id):
    photos = await bot.get_user_profile_photos(user_id)
    if photos.total_count == 0:
        return None

    file_id = photos.photos[0][-1].file_id
    file = await bot.get_file(file_id)
    return file.file_path
