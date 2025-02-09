# Discord Music Bot

A feature-rich Discord music bot with commands for playing, managing, and customizing music playback.

![image](https://github.com/user-attachments/assets/25139aa3-d972-4a72-8e93-d1dd9bfa3aa0)

![image](https://github.com/user-attachments/assets/2302aaa9-5c01-4396-bae7-5c513c746766)

![image](https://github.com/user-attachments/assets/e819eda8-5377-4ee2-bc15-55db7054570d)

![image](https://github.com/user-attachments/assets/b23de99d-daa4-42e1-ac21-1411671dd211)



## Commands

### 🎵 **Basic Voice Commands**
- **Join** (`c, j, connect, summon`) - Connects the bot to a voice channel.
- **Play** (`p, pla`) `<url or yt_search>` - Adds a song to the end of the queue.
- **Playtop** (`pt`) `<url or yt_search>` - Adds a song to the front of the queue.
- **Playskip** (`ps`) `<url or yt_search>` - Skips the current song and plays the new one.
- **Forceskip** (`fs, skip`) - Skips the currently playing song.
- **Pause** (`paus`) - Pauses the song.
- **Resume** (`resum`) - Resumes playback.
- **Rewind** `<seconds>` - Rewinds the song by the specified time.
- **Forward** `<seconds>` - Forwards the song by the specified time.
- **Disconnect** (`leav, dc, leave, stop`) - Disconnects the bot from the voice channel.

### 📜 **Queue Commands**
- **Queue** - Displays the current song queue.
- **Nowplaying** - Shows info about the currently playing song.
- **Move** (`mv`) `<entry 1> <entry 2>` - Swaps positions of two queue entries.
- **Shuffle** (`sh`) - Shuffles the queue.
- **Loop** - Loops the current song.
- **Replay** (`rp`) - Re-queues the currently playing song at position 1.
- **Clear** (`clea, clean`) `<optional: User>` - Clears the queue or entries by a specific user.

### 🔍 **Other Commands**
- **Search** (`search, s`) `<yt_search>` - Searches YouTube and provides a selection.
- **Download** (`dl`) `<url>` - Downloads a song (limited to 15 uses per month).
- **Save** (`sv`) - Sends a message with the song link and info to your DMs.
- **Volume** (`vol`) `<1-250>` - Adjusts the volume.

### ⚙️ **Options**
Use `Opts <setting> <arguments>` to modify playback settings.

- **Speed** (`50-200` or `pog` for 400% speed, or reset to 1).
- **8d** (Apply 8d filter on your song)

## 💡 Installation & Usage
1. Requirements
   
  - Discord Developer Bot setup (API Key required).
  - A device to host on / cloud hosting service (e.g., AWS, Heroku, DigitalOcean, or self-hosting on a VPS).
    
2. Clone the repository:
   ```sh
   git clone https://github.com/AnujanKopu/Discord-Music-Bot.git
   cd Discord-Music-Bot

