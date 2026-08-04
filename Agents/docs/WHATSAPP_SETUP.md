# WhatsApp Setup Guide — MicroLearning Platform

How to run the bot on WhatsApp using the **Meta WhatsApp Cloud API**, end to end:
what to click in Meta's consoles, what to put in `.env`, how to test locally, and
what changes when you go to production.

The channel is controlled by one environment variable:

```bash
MESSAGING_PLATFORM=telegram   # Telegram only (default)
MESSAGING_PLATFORM=whatsapp   # WhatsApp only
MESSAGING_PLATFORM=both       # Both at once
```

---

## Table of contents

1. [What you need before you start](#1-what-you-need-before-you-start)
2. [Meta side — step by step](#2-meta-side--step-by-step)
3. [Application side — configure and run](#3-application-side--configure-and-run)
4. [Test the whole loop](#4-test-the-whole-loop)
5. [The 24-hour window and message templates](#5-the-24-hour-window-and-message-templates)
6. [Publishing videos to WhatsApp](#6-publishing-videos-to-whatsapp)
7. [Going to production](#7-going-to-production)
8. [Troubleshooting](#8-troubleshooting)
9. [Platform differences cheat sheet](#9-platform-differences-cheat-sheet)

---

## 1. What you need before you start

| Requirement | Notes |
|---|---|
| Facebook account | Used to sign in to Meta for Developers |
| Meta Business Account | Free — created at [business.facebook.com](https://business.facebook.com) |
| A phone number | For production. **Must not be registered to the WhatsApp or WhatsApp Business consumer app.** If it is, delete that account first and wait ~24h |
| Public HTTPS endpoint | Meta only delivers webhooks over HTTPS on port 443. For local dev use a tunnel (see [§4](#4-test-the-whole-loop)) |

Meta's **test number** (provided free with every app) needs none of the above and
can message up to **5 verified recipients** — that is enough to complete this
entire guide before you commit a real number.

---

## 2. Meta side — step by step

### Step 1 — Create the app

1. Go to [developers.facebook.com/apps](https://developers.facebook.com/apps) → **Create App**.
2. Use case: **Other** → App type: **Business**.
3. Name it (e.g. `MicroLearning Bot`), pick your Business Account, → **Create app**.

### Step 2 — Add the WhatsApp product

1. In the app dashboard, find **WhatsApp** in the product list → **Set up**.
2. Meta creates a **WhatsApp Business Account (WABA)** and a **test phone number**.

### Step 3 — Collect your identifiers

Go to **WhatsApp → API Setup**. Copy these three values:

| Screen label | `.env` variable | Looks like |
|---|---|---|
| Phone number ID | `WHATSAPP_PHONE_NUMBER_ID` | `123456789012345` |
| WhatsApp Business Account ID | `WHATSAPP_BUSINESS_ACCOUNT_ID` | `987654321098765` |
| Temporary access token | `WHATSAPP_ACCESS_TOKEN` | `EAAG...` (expires in **24 hours**) |

> ⚠️ **Phone number ID is not the phone number.** It is the numeric ID shown
> directly beneath the displayed number. Using the phone number here produces
> error code 100.

### Step 4 — Add your test recipient

Still on **API Setup**, under **To**, click **Manage phone number list** and add
your own WhatsApp number. Confirm the code Meta sends you. Until a number is on
this list the test number cannot message it.

### Step 5 — Create a permanent access token

The token from Step 3 expires in 24 hours. For anything beyond a first test,
create a **System User token**, which never expires:

1. [business.facebook.com/settings](https://business.facebook.com/settings) →
   **Users → System users** → **Add**.
2. Name it (e.g. `microlearning-bot`), role **Admin** → **Create system user**.
3. **Add Assets** → **Apps** → select your app → enable **Full control**.
4. **Add Assets** → **WhatsApp Accounts** → select your WABA → enable **Full control**.
5. Click **Generate new token**:
   - App: your app
   - Expiration: **Never**
   - Permissions: ✅ `whatsapp_business_messaging` ✅ `whatsapp_business_management`
6. **Copy the token now** — Meta shows it exactly once.

This is your `WHATSAPP_ACCESS_TOKEN`.

### Step 6 — Get the app secret

**App Settings → Basic → App Secret → Show**. This is `WHATSAPP_APP_SECRET`.

The app uses it to verify the `X-Hub-Signature-256` header on every inbound
webhook, which is what stops anyone who learns your callback URL from injecting
fake messages. **Set it before production.**

### Step 7 — Configure the webhook

You need the app running and publicly reachable *before* this step, because Meta
calls your URL to verify it. Start the app first ([§3](#3-application-side--configure-and-run)),
expose it ([§4](#4-test-the-whole-loop)), then:

1. **WhatsApp → Configuration → Webhook → Edit**.
2. **Callback URL**: `https://<your-public-domain>/webhook/whatsapp`
3. **Verify token**: exactly the value of `WHATSAPP_VERIFY_TOKEN` in your `.env`
   (any string you choose — treat it like a password).
4. **Verify and save**.

Meta immediately sends a `GET` with `hub.mode`, `hub.verify_token`, and
`hub.challenge`. The app echoes the challenge back and you should see
`WhatsApp webhook verified by Meta` in the logs.

5. Then click **Manage** next to Webhook fields and **subscribe to `messages`**.

> Without the `messages` subscription the webhook saves successfully but you
> never receive anything. This is the single most common setup mistake.

---

## 3. Application side — configure and run

Add to `Agents/.env`:

```bash
MESSAGING_PLATFORM=whatsapp          # or "both" to run Telegram at the same time

WHATSAPP_ACCESS_TOKEN=EAAG...                 # Step 5 (permanent token)
WHATSAPP_PHONE_NUMBER_ID=123456789012345      # Step 3
WHATSAPP_BUSINESS_ACCOUNT_ID=987654321098765  # Step 3
WHATSAPP_VERIFY_TOKEN=some_long_random_string # your choice, used in Step 7
WHATSAPP_APP_SECRET=abc123...                 # Step 6

WEBHOOK_PORT=8000
WHATSAPP_WEBHOOK_PATH=/webhook/whatsapp
```

Install dependencies and start:

```bash
pip install -r requirements.txt
```

```bash
python start_bot.py
```

`start_bot.py` validates the credentials for whichever platforms the flag
enables, then starts the app. Expected output:

```
MESSAGING_PLATFORM -> whatsapp
✅ GEMINI_API_KEY: AIzaSyD...
✅ WHATSAPP_ACCESS_TOKEN: EAAGxxxxx...
✅ WHATSAPP_PHONE_NUMBER_ID: 123456789...
✅ WHATSAPP_VERIFY_TOKEN: some_long_...
✅ WHATSAPP_APP_SECRET: abc123...
   Webhook path: /webhook/whatsapp (port 8000)
...
HTTP server on 0.0.0.0:8000 (health: /health)
WhatsApp callback URL: https://<your-public-domain>/webhook/whatsapp -> 0.0.0.0:8000/webhook/whatsapp
```

---

## 4. Test the whole loop

### Expose your local server

Meta requires public HTTPS, so tunnel to your machine during development:

```bash
ngrok http 8000
```

Use the `https://` forwarding URL from ngrok as your callback base. Alternatives:
`cloudflared tunnel --url http://localhost:8000`, or deploy to any host with TLS.

> The free ngrok URL changes on every restart — update Meta's Callback URL each
> time, or use a reserved domain.

### Verify the app is up

```bash
curl https://<your-public-domain>/health
```

Expect `{"status":"ok","platforms":["whatsapp"],...}`.

### Simulate Meta's verification handshake

```bash
curl "https://<your-public-domain>/webhook/whatsapp?hub.mode=subscribe&hub.verify_token=YOUR_VERIFY_TOKEN&hub.challenge=test123"
```

Expect the literal response `test123`. If you get `403`, your
`WHATSAPP_VERIFY_TOKEN` does not match what you typed into Meta.

### Send a real message

From the WhatsApp number you added in Step 4, message your business number:

| You send | You get back |
|---|---|
| `hi` | The welcome message, and your user row is created |
| `/video` or `video` | Your next learning video |
| `/quiz` or `quiz` | AI-generated questions; your replies are graded 0–10 |
| `/ask what is the leave policy` | A RAG answer with document sources |
| `/progress` | Your stats |
| `/help` | The full command list |

Slash prefixes are optional on WhatsApp — bare `video`, `quiz`, `docs`, `help`,
and `hi` all work, because WhatsApp has no slash-command menu. Mid-quiz, bare
words are treated as answers so a legitimate answer is never swallowed as a
command; an explicit `/video` still works.

### Send a message directly via the API (isolates app problems from Meta problems)

```bash
curl -X POST "https://graph.facebook.com/v21.0/$WHATSAPP_PHONE_NUMBER_ID/messages" -H "Authorization: Bearer $WHATSAPP_ACCESS_TOKEN" -H "Content-Type: application/json" -d '{"messaging_product":"whatsapp","to":"15551234567","type":"text","text":{"body":"Direct API test"}}'
```

If this works but the bot does not, the problem is in your app or webhook. If
this fails, the problem is your Meta configuration.

---

## 5. The 24-hour window and message templates

This is the biggest behavioural difference from Telegram, and it affects the
daily-video feature directly.

**You may only send free-form messages within 24 hours of the learner's last
inbound message.** Outside that window Meta rejects the send with error
**131047** and only a pre-approved **template** may be used. The app records
`users.last_inbound_at` on every inbound message so you can tell which learners
are reachable.

| Scenario | Works? |
|---|---|
| Learner sends `/video`, bot replies | ✅ Always |
| Bot pushes a video 3 hours after their last message | ✅ Inside the window |
| Bot pushes a video 30 hours later | ❌ Requires a template |

### Create the daily-video template

1. [business.facebook.com/wa/manage/message-templates](https://business.facebook.com/wa/manage/message-templates)
   → **Create template**.
2. Category: **Utility** (Utility is cheaper and approves faster than Marketing).
3. Name: `daily_video_ready` — must match `WHATSAPP_TEMPLATE_DAILY_VIDEO`.
4. Language: English (US) — must match `WHATSAPP_TEMPLATE_LANGUAGE` (`en_US`).
5. Body, using positional variables:

   ```
   Hi {{1}}, your micro-learning video "{{2}}" is ready. Reply VIDEO to watch it now.
   ```

6. Provide sample values and submit. Approval usually takes minutes to a few hours.

Send it with:

```python
await client.send_template(
    to="15551234567",
    template_name="daily_video_ready",
    language_code="en_US",
    body_params=["Alice", "Fire Safety Basics"],
)
```

Once the learner replies, the 24-hour window reopens and normal video/quiz
delivery works for the rest of it.

> Template messages are billed per conversation; free-form replies inside the
> window are not. Check Meta's current pricing for your country before scheduling
> daily pushes to a large roster.

---

## 6. Publishing videos to WhatsApp

Each platform issues its own media handle, so a video must be uploaded once per
platform. The handles are cached in the `video_media` table.

```bash
python scripts/publish_videos.py --status
```

```bash
python scripts/publish_videos.py --all
```

```bash
python scripts/publish_videos.py --all --platform whatsapp
```

With `AUTO_UPLOAD_MEDIA=true` (the default) the first learner to request an
unpublished video triggers the upload automatically; every later delivery reuses
the cached id. Pre-publishing simply avoids making that first learner wait.

**WhatsApp media constraints:**

| Constraint | Value |
|---|---|
| Max video size | **16 MB** (Telegram allows 50 MB) |
| Accepted formats | `video/mp4`, `video/3gpp` — H.264 video + AAC audio |
| Caption limit | 1024 characters |
| Media id lifetime | **~30 days** — the app refreshes at 28 |

Videos between 16 MB and 50 MB deliver on Telegram but are rejected by WhatsApp.
Either compress them, or host them publicly and store the URL as the media
reference (the client sends a URL as a `link` automatically).

Refresh expiring ids on a schedule:

```bash
python scripts/publish_videos.py --all --platform whatsapp
```

---

## 7. Going to production

### Add a real phone number

1. **WhatsApp → API Setup → Add phone number**.
2. Enter the display name and business details, verify by SMS or voice call.
3. Meta reviews the display name (usually under 24h).

### Complete Business Verification

Required to lift messaging limits. **Business Settings → Security Centre →
Start Verification**; you will need your business registration documents and a
verifiable address or phone.

### Messaging tiers

New numbers start limited and scale automatically with quality:

| Tier | Unique customers per 24h |
|---|---|
| Unverified | 250 |
| Tier 1 | 1,000 |
| Tier 2 | 10,000 |
| Tier 3 | 100,000 |
| Tier 4 | Unlimited |

### Production checklist

- [ ] `WHATSAPP_ACCESS_TOKEN` is a permanent **system user** token, not a 24h one
- [ ] `WHATSAPP_APP_SECRET` is set so webhook signatures are actually verified
- [ ] `WHATSAPP_VERIFY_TOKEN` is long and random, not `test`
- [ ] Callback URL is HTTPS with a valid certificate on a stable domain
- [ ] Subscribed to the `messages` webhook field
- [ ] App switched from **Development** to **Live** (toggle at the top of the dashboard)
- [ ] Business verification complete
- [ ] `daily_video_ready` template approved
- [ ] All videos published to WhatsApp and under 16 MB
- [ ] Secrets injected from your secret manager — never committed

### Docker

```bash
MESSAGING_PLATFORM=both docker compose up -d
```

Port `8000` is published for the webhook and `/health`; put it behind your TLS
terminator (nginx, Caddy, ALB) and point Meta at the public HTTPS address.

---

## 8. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Webhook won't verify (`403`) | `WHATSAPP_VERIFY_TOKEN` ≠ the value typed into Meta | Make them identical; no stray whitespace |
| Webhook verifies, no messages arrive | Not subscribed to the `messages` field | **Configuration → Webhook fields → Manage → messages** |
| Verification times out | Meta cannot reach your URL | Must be public HTTPS on 443; check the tunnel is alive |
| `403 invalid signature` in logs | `WHATSAPP_APP_SECRET` is wrong | Copy it again from **App Settings → Basic** |
| Error 131047 | 24-hour window closed | Send an approved template; see [§5](#5-the-24-hour-window-and-message-templates) |
| Error 131026 | Recipient not on WhatsApp, or number not in the test list | Add them to the allowed list (test mode) |
| Error 190 | Token expired | Generate a permanent system user token |
| Error 100 | Wrong parameter — usually the phone number in place of the phone number **ID** | Use the numeric ID from API Setup |
| Error 130429 | Throughput limit | The client retries with backoff automatically |
| Error 132001 | Template not found or not approved | Check the name, language code, and approval status |
| Video rejected | Over 16 MB or not H.264 MP4 | Re-encode: `ffmpeg -i in.mp4 -c:v libx264 -c:a aac -b:v 1M out.mp4` |
| Same message handled twice | Meta retried before you acknowledged | Already handled — inbound wamids are deduplicated |
| Nothing happens, no errors | App still in Development mode with an unlisted recipient | Add the number to the test list, or switch the app Live |

**Turn up logging:**

```bash
LOG_LEVEL=DEBUG python start_bot.py
```

**Check what Meta thinks it delivered:** the webhook logs `statuses` callbacks,
including `failed` with the exact error code, at DEBUG/WARNING level.

---

## 9. Platform differences cheat sheet

| | Telegram | WhatsApp Cloud API |
|---|---|---|
| Inbound transport | Long polling | HTTPS webhook (public URL required) |
| Unprompted messages | Any time | Only within 24h of the learner's last message |
| Slash commands | Native menu | Plain text; bare keywords also accepted |
| Max video upload | 50 MB | 16 MB |
| Media handle | `file_id`, permanent | Media id, expires ~30 days |
| Text limit | 4096 chars | 4096 chars |
| Caption limit | 1024 chars | 1024 chars |
| Cost | Free | Per-conversation billing |
| User id | Numeric chat id | `wa_id` (E.164 digits, no `+`) |

In the database, Telegram learners keep a bare chat id in `users.telegram_id`
while WhatsApp learners are stored as `whatsapp:<wa_id>`, so the same phone
number can exist independently on both channels. `users.platform` and
`users.platform_user_id` record the channel and the raw id used for sending.
