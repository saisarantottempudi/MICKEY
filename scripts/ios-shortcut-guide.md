# MICKEY iOS Shortcut Setup

## Prerequisites
1. Tailscale installed on iPhone/iPad (App Store)
2. Signed into same Tailscale account as MacBook Pro
3. MICKEY backend running on MacBook Pro
4. Auth token (find it: `curl localhost:5050/api/token` on the Mac)

## Shortcut 1: Voice Chat (main shortcut)

Open Shortcuts app → + New Shortcut → Add these actions:

1. **Record Audio** (set duration: 10 seconds, or "Stop on Tap")
2. **Get Contents of URL**
   - URL: `https://YOUR-TAILSCALE-HOSTNAME:5050/api/voice`
   - Method: POST
   - Headers:
     - `Authorization`: `Bearer YOUR_TOKEN`
   - Request Body: Form
     - Key: `audio`, Type: File, Value: (output of Record Audio)
3. **Play Sound** (from step 2 output)

Name it "Hey MICKEY" → Add to Home Screen

## Shortcut 2: Text Chat

1. **Ask for Input** (prompt: "What do you want to ask MICKEY?")
2. **Get Contents of URL**
   - URL: `https://YOUR-TAILSCALE-HOSTNAME:5050/api/chat`
   - Method: POST
   - Headers:
     - `Authorization`: `Bearer YOUR_TOKEN`
     - `Content-Type`: `application/json`
   - Request Body: JSON
     ```json
     {"message": "Provided Input"}
     ```
3. **Get Dictionary Value** (key: `result` from step 2)
4. **Show Result**

## Shortcut 3: System Command

1. **Choose from Menu**: Open Safari, Calendar, System Info
2. **Get Contents of URL** (same as above, message = chosen command)
3. **Show Result**

## Tips
- Replace `YOUR-TAILSCALE-HOSTNAME` with actual Tailscale hostname
- Replace `YOUR_TOKEN` with token from `curl localhost:5050/api/token`
- Voice shortcut works as Siri trigger: "Hey Siri, Hey MICKEY"
- Add shortcuts to Home Screen for quick access
