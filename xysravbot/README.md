# Xysravbot (Telegram CS2 AI banter)
Deploy with Render Blueprint from this branch: render.yaml.
Required Render environment variables:
- TELEGRAM_BOT_TOKEN (new token from BotFather, not previously shared)
- OPENAI_API_KEY (create in OpenAI Platform and enter in Render; never commit)
Commands: /on /off /chance 0-100 /status.
Disable group privacy via BotFather to allow occasional contextual replies.
Do not run multiple polling instances of the same bot.
Chat history and group settings are currently in memory; reset on restart.
