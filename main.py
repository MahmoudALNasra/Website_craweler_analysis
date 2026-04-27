import requests
import re
import concurrent.futures
from datetime import datetime

# --- CONFIGURATION ---
SPREADSHEET_NAME = "YOUR EXACT SPREADSHEET NAME HERE" # <--- Change this!

TARGET_COL_INDEX = 14  # Column N
URL_COL_INDEX = 4      # Column D

SHEET_NAMES = [
    'RESTAURANT', 'ELECTRONICS STORE', 'CAR DEALER', 'REAL ESTATE AGENCY', 
    'SUPERMARKET', 'BEAUTY SALON', 'CAFE', 'GYM', 'PHARMACY', 'HOTEL'
]

# --- DETECTION LOGIC (REGEX) ---
def check_regex(pattern, text):
    return bool(re.search(pattern, text, re.IGNORECASE))

def extract_analytics_details(html):
    details = {'hasGA4': False, 'hasUniversalAnalytics': False, 'trackingIds': []}
    if check_regex(r'gtag\s*\(\s*[\'"]config[\'"]\s*,\s*[\'"](G-[A-Z0-9]+)[\'"]', html) or check_regex(r'google-analytics\.com/g/collect', html):
        details['hasGA4'] = True
    if check_regex(r'google-analytics\.com/analytics\.js', html) or check_regex(r'ga\s*\(\s*[\'"]create[\'"]', html):
        details['hasUniversalAnalytics'] = True
        
    ids = re.findall(r'(G-[A-Z0-9]{10}|UA-[A-Z0-9-]+|GTM-[A-Z0-9]{1,7})', html, re.IGNORECASE)
    details['trackingIds'] = list(set(ids))
    return details

def check_meta_tags(html):
    return {
        'desc': check_regex(r'<meta\s+name="description"', html),
        'og': check_regex(r'<meta\s+property="og:', html)
    }

def detect_technologies(html):
    techs = []
    if check_regex(r'wp-content|wordpress', html): techs.append('WordPress')
    if check_regex(r'shopify', html): techs.append('Shopify')
    if check_regex(r'woocommerce', html): techs.append('WooCommerce')
    if check_regex(r'wix', html): techs.append('Wix')
    if check_regex(r'jquery', html): techs.append('jQuery')
    return ', '.join(techs) if techs else 'Unknown'


# --- THE ANALYZER ---
def analyze_website(url):
    clean_url = url.strip()
    if not clean_url.startswith('http'):
        clean_url = 'https://' + clean_url

    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(clean_url, headers=headers, timeout=15, allow_redirects=True)
        html = response.text

        analytics = extract_analytics_details(html)
        
        return {
            'url': clean_url,
            'analytics': analytics,
            'hasGA': analytics['hasGA4'] or analytics['hasUniversalAnalytics'],
            'hasGTM': check_regex(r'googletagmanager\.com/(gtm|gtag)\.js', html),
            'hasFB': check_regex(r'facebook\.com/tr\?|fbq\(', html),
            'hasAds': check_regex(r'googleadservices|gtag\s*\(\s*[\'"]conversion[\'"]', html),
            'hasMeta': check_meta_tags(html),
            'hasStructuredData': check_regex(r'application/ld\+json|schema\.org', html),
            'isMobile': check_regex(r'viewport', html) and not check_regex(r'user-scalable=no', html),
            'hasContact': check_regex(r'<form[^>]*contact|type=["\']email["\']', html),
            'hasChat': check_regex(r'livechatinc|tawk\.to|intercom|zendesk|drift', html),
            'ssl': clean_url.startswith('https'),
            'techs': detect_technologies(html),
            'error': None
        }
    except requests.exceptions.RequestException as e:
        return {'error': str(e).split(':', 1)[0]} # Keep error messages brief


# --- REPORT GENERATOR ---
def generate_detailed_analysis(analysis):
    if analysis.get('error'):
        return f"❌ Analysis failed: {analysis['error']}"

    opportunities = []
    strengths = []

    if not analysis['hasGA']: 
        opportunities.append("Google Analytics missing")
    elif analysis['analytics']['hasUniversalAnalytics'] and not analysis['analytics']['hasGA4']: 
        opportunities.append("Old Universal Analytics - Upgrade to GA4")
    else: 
        strengths.append("GA4 installed")

    if not analysis['hasGTM']: opportunities.append("GTM missing")
    if not analysis['hasFB']: opportunities.append("Facebook Pixel missing")
    if not analysis['hasMeta']['desc']: opportunities.append("Meta description missing")
    if not analysis['hasStructuredData']: opportunities.append("Structured data missing")
    if not analysis['isMobile']: opportunities.append("Mobile optimization issues")
    if not analysis['hasChat']: opportunities.append("No live chat found")

    if analysis['ssl']: strengths.append("SSL Secured")
    if analysis['isMobile']: strengths.append("Mobile Friendly")

    text = f"📊 OPPORTUNITIES: {len(opportunities)}\n"
    text += f"🛠 TECH: {analysis['techs']}\n"
    text += f"✅ STRENGTHS: {', '.join(strengths)}\n\n"
    
    if opportunities:
        text += "Growth Plan:\n• " + "\n• ".join(opportunities)

    return text


def should_skip(cell_value):
    val = str(cell_value)
    return "OPPORTUNITIES:" in val or "🛠 TECH:" in val


# --- SHEET PROCESSOR ---
def process_sheet(sheet_name):
    try:
        ss = gc.open(SPREADSHEET_NAME)
        worksheet = ss.worksheet(sheet_name)
    except Exception as e:
        print(f"❌ Could not open '{sheet_name}'. Skipping.")
        return 0
        
    data = worksheet.get_all_values()
    if len(data) <= 1:
        return 0

    # Ensure header exists
    if len(data[0]) < TARGET_COL_INDEX:
        data[0].extend([""] * (TARGET_COL_INDEX - len(data[0])))
    if data[0][TARGET_COL_INDEX - 1] == "":
        worksheet.update_cell(1, TARGET_COL_INDEX, "Detailed Analysis")

    rows_to_process = []
    skipped = 0

    for i in range(1, len(data)):
        row = data[i]
        while len(row) < TARGET_COL_INDEX:
            row.append("")
            
        url = row[URL_COL_INDEX - 1]
        current_analysis = row[TARGET_COL_INDEX - 1]

        if should_skip(current_analysis):
            skipped += 1
            continue

        if url.strip() != "" and url.strip().lower() != "no website":
            rows_to_process.append({'row_num': i + 1, 'url': url})
        else:
            # Mark invalid URLs instantly
            worksheet.update_cell(i + 1, TARGET_COL_INDEX, 'No valid URL')

    if not rows_to_process:
        print(f"⏭️ {sheet_name}: {skipped} skipped. No new URLs.")
        return 0

    print(f"📊 {sheet_name}: {skipped} skipped. {len(rows_to_process)} URLs ready to analyze.")

    results = []
    processed_count = 0

    # MULTI-THREADING (Analyze 10 sites at once)
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_row = {executor.submit(analyze_website, item['url']): item for item in rows_to_process}
        
        for future in concurrent.futures.as_completed(future_to_row):
            row_info = future_to_row[future]
            try:
                analysis = future.result()
                detailed_output = generate_detailed_analysis(analysis)
            except Exception as e:
                detailed_output = f"❌ Error: {str(e)}"
            
            results.append(gspread.Cell(row=row_info['row_num'], col=TARGET_COL_INDEX, value=detailed_output))
            processed_count += 1
            print(f"  ✅ Analyzed row {row_info['row_num']}: {row_info['url']}")

    # Batch Update Sheet
    if results:
        worksheet.update_cells(results)
        
    return processed_count

# --- PLAYBOOK GENERATOR ---
def create_master_playbook():
    print("\n📝 Compiling Master Playbook...")
    ss = gc.open(SPREADSHEET_NAME)
    
    playbook_content = "# MASTER DIGITAL GROWTH PLAYBOOK\n"
    playbook_content += f"*Generated on: {datetime.now().strftime('%Y-%m-%d')}*\n\n"
    
    for sheet_name in SHEET_NAMES:
        try:
            worksheet = ss.worksheet(sheet_name)
            data = worksheet.get_all_values()
            
            # Remove '_filtered' if it exists for cleaner headers
            clean_title = sheet_name.replace('_filtered', '')
            added_heading = False
            
            for i in range(1, len(data)):
                row = data[i]
                if len(row) >= TARGET_COL_INDEX:
                    url = row[URL_COL_INDEX - 1]
                    analysis = row[TARGET_COL_INDEX - 1]
                    
                    if url and url.lower() != 'no website' and 'OPPORTUNITIES:' in analysis:
                        if not added_heading:
                            playbook_content += f"## 🏢 {clean_title}\n\n"
                            added_heading = True
                            
                        playbook_content += f"### Business: {url}\n"
                        playbook_content += f"```text\n{analysis}\n```\n"
                        playbook_content += "---\n\n"
        except Exception:
            continue
            
    # Save to Colab local file
    with open('Master_Playbook.md', 'w', encoding='utf-8') as f:
        f.write(playbook_content)
    print("✅ Playbook saved as 'Master_Playbook.md' in Colab files!")

# --- MAIN EXECUTION ---
print("🚀 Starting Master Website Analysis...")
total = 0

for sheet_name in SHEET_NAMES:
    print(f"\n{'='*40}\n=== TAB: {sheet_name} ===\n{'='*40}")
    total += process_sheet(sheet_name)

print(f"\n🎉 Analysis Complete! Total websites analyzed: {total}")

create_master_playbook()
