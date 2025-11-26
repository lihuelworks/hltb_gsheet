# HLTB Google Sheets API

A Flask API that fetches game playtime data from HowLongToBeat and integrates with Google Sheets.

## How It Works

This API extracts HowLongToBeat data by searching **"howlongtobeat GAMENAME"** on Google via SerpAPI and parsing the playtime information from the search results (featured snippets and organic results).

**Why not use the HLTB library directly?** The official HowLongToBeat website has aggressive bot protection that blocks all direct programmatic access from Python. Instead, we leverage Google search results which include HLTB data in a structured format.

## Features

- 🎮 Fetches game completion times (Main Story, Main + Extra, Completionist)
- 📊 Google Sheets integration via custom Apps Script
- ⚡ 7-day caching to minimize API calls
- 🔍 Smart search with Wikipedia fallback for game name corrections
- 🛡️ API key authentication
- 📝 Comprehensive logging

## API Response Format

```json
{
  "game_name": "Halo: Combat Evolved",
  "main_story": 10.0,
  "main_extra": 13.5,
  "completionist": 18.0,
  "all_styles": null
}
```

All time values are in **hours** (float) or `null` if not available.

## Setup & Deployment

### 1. Get API Keys

**SerpAPI Key** (required for searching):
1. Sign up at https://serpapi.com/
2. Get your API key from the dashboard
3. Free tier: 100 searches/month

**Custom API Key** (for Google Sheets auth):
- Create your own secret key (e.g., `"mySecretKey123"`)
- This prevents unauthorized access to your API

### 2. Deploy to Render

#### Option A: Deploy via GitHub (Recommended)

1. **Fork/Clone this repo** to your GitHub account

2. **Create new Web Service** on [Render](https://render.com):
   - Connect your GitHub repository
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Instance Type:** Free

3. **Set Environment Variables** in Render dashboard:
   ```
   SERP_API_KEY=your_serpapi_key_here
   GSHEET_API_KEY=your_custom_secret_key_here
   ```

4. **Deploy!** Render will auto-deploy on every git push to main

#### Option B: Manual Deploy

1. Install [Render CLI](https://render.com/docs/cli)
2. Run: `render deploy`

### 3. Configure Google Sheets

#### Step 1: Add the Apps Script

1. Open your Google Sheet
2. Go to **Extensions > Apps Script**
3. Copy the code from [`google_sheet_script.js`](https://github.com/lihuelworks/hltb_gsheet/blob/main/../google_sheet_script.js) (in parent directory)
4. Update these constants in the script:
   ```javascript
   const HOWLONGTOBEAT_GSHEET_API_KEY = 'your_custom_secret_key_here'; // Match your GSHEET_API_KEY
   const API_URL = 'https://your-render-app.onrender.com/search-game';
   ```

#### Step 2: Set Up Your Sheet

Create columns like this:

| TITLE | HOWLONGTOBEAT |
|-------|---------------|
| Celeste | *(auto-filled)* |
| Halo 1 | *(auto-filled)* |

The script automatically fills the **HOWLONGTOBEAT** column when you enter a game title.

#### Step 3: Add Trigger (Optional)

For automatic updates on sheet edits:

1. **Create the trigger function** in your Apps Script:
   ```javascript
   // Configuration
   const BACKLOG_SHEET = "📃🎮 backlog";
   const TITLE_COLUMN = 3;  // Column C
   const HOWLONGTOBEAT_COLUMN = 5;  // Column E
   
   function onSheetEdit(e) {
     const { range, value, oldValue } = e;
     const sheet = range.getSheet();
     const column = range.getColumn();
     const row = range.getRow();
     
     // Only process edits in the backlog sheet
     if (sheet.getName() !== BACKLOG_SHEET) return;
     
     // Auto-fill playtime when a game title is entered
     if (column === TITLE_COLUMN && row > 1 && value && value !== oldValue) {
       const hltbCell = sheet.getRange(row, HOWLONGTOBEAT_COLUMN);
       hltbCell.setValue('Loading...');
       
       const playTime = getGamePlayTimeHandler(value);
       hltbCell.setValue(playTime);
     }
     
     // Handle manual "gettime" command
     if (column === HOWLONGTOBEAT_COLUMN && row > 1 && 
         value && value.toLowerCase() === 'gettime') {
       const gameTitle = sheet.getRange(row, TITLE_COLUMN).getValue();
       if (!gameTitle) return;
       
       const hltbCell = sheet.getRange(row, HOWLONGTOBEAT_COLUMN);
       hltbCell.setValue('Loading...');
       
       const playTime = getGamePlayTimeHandler(gameTitle);
       hltbCell.setValue(playTime);
     }
   }
   ```

2. **Set up the trigger**:
   - In Apps Script editor, click **Triggers** (clock icon on left sidebar)
   - Click **+ Add Trigger** (bottom right)
   - Configure:
     - Function to run: `onSheetEdit`
     - Deployment: Head
     - Event source: From spreadsheet
     - Event type: On edit
   - Click **Save**

3. **Authorize** the script when prompted

**How it works:**
- When you type a game name in the TITLE column, it automatically fetches and fills the playtime
- Type `gettime` in the HOWLONGTOBEAT column to manually refresh the data
- Shows "Loading..." while fetching from the API

## API Endpoints

### `POST /search-game`

Search for a game's playtime data.

**Request:**
```json
{
  "GSHEET_API_KEY": "your_custom_secret_key_here",
  "game_name": "Celeste"
}
```

**Response (200 OK):**
```json
{
  "game_name": "Celeste",
  "main_story": 8.0,
  "main_extra": 11.5,
  "completionist": 38.0,
  "all_styles": null
}
```

**Error Responses:**
- `401`: Invalid API key
- `404`: Game not found
- `500`: Server error

### `GET /health`

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-26T12:34:56.789Z"
}
```

## Example: Using with Google Sheets

1. **Enter game title** in TITLE column: `Hollow Knight`
2. **Script auto-fetches** playtime from API
3. **Displays formatted time**: `27h 0m` (converted from 27.0 hours)

## Development

### Local Testing

```bash
# Clone the repo
git clone https://github.com/lihuelworks/hltb_gsheet.git
cd hltb_gsheet

# Create .env file
echo "SERP_API_KEY=your_key" > .env
echo "GSHEET_API_KEY=your_key" >> .env

# Install dependencies
pip install -r requirements.txt

# Run locally
python app.py
# Or with gunicorn
gunicorn app:app
```

API runs on `http://localhost:10000`

### Test the API

```bash
curl -X POST http://localhost:10000/search-game \
  -H "Content-Type: application/json" \
  -d '{"GSHEET_API_KEY": "your_key", "game_name": "Celeste"}'
```

## Technical Details

### Search Strategy

1. **Direct HLTB Search**: Searches "howlongtobeat GAMENAME" via SerpAPI
2. **Wikipedia Fallback**: If no results, searches Wikipedia to find correct game name
3. **Retry with Corrected Name**: Uses Wikipedia result to search HLTB again

### Data Extraction

The API uses regex patterns to extract times from Google snippets:
- Matches: `"8 Hours"`, `"10.5 Hours"`, `"10-12 Hours"`
- Averages ranges: `"10-12 Hours"` → `11.0`
- Searches both **answer_box** (featured snippets) and **organic_results**

### Caching

- **7-day TTL** for search results
- **In-memory storage** (resets on server restart - free tier limitation)
- Reduces SerpAPI quota usage

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SERP_API_KEY` | Yes | SerpAPI key for Google searches |
| `GSHEET_API_KEY` | Yes | Your custom secret key for auth |
| `PORT` | No | Server port (default: 10000) |

## Dependencies

- **Flask 3.1.2** - Web framework
- **Flask-CORS 5.0.1** - CORS support for Google Sheets
- **google-search-results 2.4.2** - SerpAPI client
- **gunicorn 23.0.0** - Production WSGI server
- **python-dotenv 1.0.1** - Environment variable management

## Limitations

- **Free Render Tier**: Server sleeps after 15min inactivity (first request may be slow)
- **SerpAPI Free Tier**: 100 searches/month
- **Cache Storage**: In-memory (resets on server restart)
- **No HLTB "All Styles"**: This field is not available from Google snippets

## Troubleshooting

### "API unavailable (405)" in Google Sheets
- Check that your Render deployment is running
- Verify the API URL in `google_sheet_script.js`

### "Error: 401"
- `GSHEET_API_KEY` in Google Sheets doesn't match your Render environment variable

### "No results found"
- Game name may be incorrect (try different spelling)
- HLTB might not have data for that game
- SerpAPI quota exhausted

### Server takes forever on first request
- Render free tier: server sleeps after 15min inactivity
- First request "wakes up" the server (~30-60 seconds)

## Why Not Use HLTB Library Directly?

The `howlongtobeatpy` library is currently broken due to HLTB's bot protection:
- All requests return `403 Forbidden` or "Session expired"
- HLTB uses aggressive bot detection (likely Cloudflare)
- Python's requests library is fingerprinted and blocked

**Our solution**: Extract HLTB data from Google search results instead, which works reliably.

For more details, see the [GitHub issue on HowLongToBeat-PythonAPI](https://github.com/ScrappyCocco/HowLongToBeat-PythonAPI/issues/52).

## License

MIT

## Author

Created for integrating HowLongToBeat data with Google Sheets workflow.
