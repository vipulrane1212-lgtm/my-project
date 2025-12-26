# 📱 How to Get Your Telegram Chat ID

## Quick Method (Recommended)

1. **Add @userinfobot to your group/channel**
   - Open your Telegram group/channel
   - Add @userinfobot as a member
   - Send any message in the group
   - @userinfobot will reply with the chat ID

2. **Copy the chat ID**
   - Look for a number like `-1001234567890`
   - That's your `ALERT_CHAT_ID`

3. **Update telegram_monitor_new.py**
   ```python
   ALERT_CHAT_ID = -1001234567890  # Your chat ID here
   ```

## Alternative Method (API)

1. **Add your bot to the group/channel**
   - Make sure your bot is an admin (for channels) or member (for groups)

2. **Send a test message in the group/channel**

3. **Visit this URL in your browser:**
   ```
   https://api.telegram.org/bot8276826313:AAH2vOYZmqDfmvflNwtz3FimjMsg3gtgqjs/getUpdates
   ```

4. **Look for the chat ID:**
   - Search for `"chat":{"id":-1001234567890}`
   - The number after `"id":` is your chat ID

5. **Update telegram_monitor_new.py:**
   ```python
   ALERT_CHAT_ID = -1001234567890  # Your chat ID here
   ```

## Notes

- **Group IDs** are negative numbers (e.g., `-1001234567890`)
- **Channel IDs** are also negative numbers
- **Private chat IDs** are positive numbers (but you probably want a group/channel)

## Test It

After setting `ALERT_CHAT_ID`, run:
```bash
python telegram_monitor_new.py
```

When an auto-buy signal is detected, you should see:
```
✅ Alert sent to Telegram (chat: -1001234567890)
```

If you see an error, make sure:
1. Bot is added to the group/channel
2. Bot has permission to send messages
3. Chat ID is correct (negative number for groups/channels)

