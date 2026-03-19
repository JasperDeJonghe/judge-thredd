# Discord Leaderboard Bot

A Discord bot that tracks the most active members in specific channels, shows a daily top 5 leaderboard, and automatically awards a role to the top helper.

---

## Setup

### 1. Install dependencies

Make sure you have Python installed, then run:

```
pip install -r requirements.txt
```

### 2. Configure the bot

Rename `config_example.json` to `config.json` and fill in all the values.

```json
{
    "api_key": "YOUR_BOT_TOKEN_HERE",
    "channels": [
        CHANNEL_ID_1,
        CHANNEL_ID_2
    ],
    "output_channel": CHANNEL_ID_WHERE_LEADERBOARD_IS_POSTED,
    "role": "NAME_OF_THE_ROLE_TO_AWARD",
    "reset_hour": HOUR,
    "reset_min": MINUTES,
    "reset_day": DAY
}
```

| Field            | Description                                                     |
| ---------------- | --------------------------------------------------------------- |
| `api_key`        | Your Discord bot token from the Discord Developer Portal        |
| `channels`       | A list of channel IDs the bot will count messages in            |
| `output_channel` | The channel ID where the leaderboard will be posted             |
| `role`           | The exact name of the role that gets awarded to the top helper  |
| `reset_hour`     | The hour the leaderboard resets and role is awarded (UTC, 0-23) |
| `reset_min`      | The minute the leaderboard resets (0-59)                        |
| `reset_day`      | The day the leaderboard resets (0=Monday, 1=Tuesday...)         |

> **Note:** `reset_hour` and `reset_min` use UTC time.

### 3. Run the bot

```
python bot.py
```

---

## How it works

- The bot counts every message sent in the configured channels
- Every day at the configured time, it automatically posts the top 5 leaderboard and awards the configured role to the top user
- The leaderboard resets after the role is awarded

---

Requirements
For the bot to be able to assign and remove the role, the bot's own role must be above the role you want to award in the server's role list. You can change this in Server Settings → Roles by dragging the bot's role higher than the role specified in config.json.

---

## How to get IDs

To get a channel ID, server ID, or role ID in Discord: go to **Settings → Advanced** and enable **Developer Mode**. Then right-click any channel, server, or role and click **Copy ID**.
