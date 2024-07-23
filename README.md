## Features
 
### Moderation
  `!kick <user> <reason>`: Kicks the specified user from the server.
  `!ban <user> <reason>`: Bans the specified user from the server.
  `!unban <user_ID> <reason>`: Unbans the specified user.
  `!silence <user> <time>`: Mutes the specified user.
  `!unsilence <user> <time>`: Unmutes the specified user.
  `!lockdown` locksdown the server and prevents anyone from sending messages
  `!unlock` unlocks the server and users may send messages again
  Note: You need to make a Member role that has regular permissions and can send messages, you also need to take away send message privelage from the @everyone role, and you need to make 2 muted roles, one called Muted and the other called Muted_Lockdown

### Miscellaneous 
  Note: most of these commands require an API key from `https://api-ninjas.com`
  `/ninja_api_key <api_key>` to set the API key for the commands below, admin only.
  `!trivia <catagory>` asks a trivia question
  `!answer <answer>` answer the trivia question
  `!motivate` gives you a motivational quote
  `!dadjoke` gives you a dad joke
  `!remindme <reminder> <time>`  Set a reminder. Time format: <number><unit> (e.g. 10s, 5m, 1h, 2d)
  `/qrcode <url>` generate a QR code for a URL
  `!whatsthismean <word>` look up a word in the dictionary
  `!ping` tests the bot to see if it's working

## Installation

  To run this bot, you'll need to have Python and the discord.py, requests, apscheduler, yt-dlp, PyNaCl, and asyncio library installed which you can do by going to command prompt and running `pip install <library_name>`. 
  Download the repository and extract the folder called Discord_Bot from the zip file
  Go to `https://discord.com/developers/`, make an application and get your bot token, then, make a text file called auth_token.txt with your bot token in it and put it in the Discord_Bot folder.
  Download ffmpeg (built versions available at `https://www.gyan.dev/ffmpeg/builds/`) and put the `ffmpeg.exe`, `ffplay.exe`, and `ffprobe.exe` in the Discord_Bot folder.
  Use `https://discord.com/oauth2/authorize?client_id=1260569414764331030` to install the bot in your server
  Then open commmand prompt and use `cd <your_Discord_Bot_folder_location>` and run `python main.py`

## Contributing
  Feel free to fork this repository and submit pull requests. For major changes, please open an issue first to discuss what you would like to change.

## License
  This project is licensed under the MIT License.
