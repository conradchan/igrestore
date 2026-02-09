import csv
import re
from html import unescape

with open('/Users/conradchan/repos/personal/igrestore/data.xml', 'r', encoding='utf-8') as f:
    html = f.read()

try:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    
    accounts = []
    # Find all anchor tags with _a6hd class
    for a_tag in soup.find_all('a', class_=re.compile(r'_a6hd')):
        href = a_tag.get('href', '')
        username_match = re.match(r'^/([^/]+)/$', href)
        if not username_match:
            continue
        username = username_match.group(1)
        
        # Display name: span with those specific classes
        display_span = a_tag.find_next('span', class_=re.compile(r'x1lliihq.*x193iq5w.*x6ikm8r.*x10wlt62.*xlyipyv.*xuxw1ft'))
        display_name = display_span.get_text(strip=True) if display_span else username
        
        # Profile pic: img with alt containing username's profile picture
        img = soup.find('img', alt=re.compile(re.escape(username) + r".*profile picture", re.IGNORECASE))
        pic_url = unescape(img['src']) if img and img.get('src') else ''
        
        profile_url = f'https://instagram.com/{username}'
        accounts.append((username, display_name, profile_url, pic_url))
    
except ImportError:
    # Fallback to regex
    pattern = re.compile(
        r'<a[^>]*class="[^"]*_a6hd[^"]*"[^>]*href="/([^/]+)/"[^>]*>',
        re.DOTALL
    )
    # Also try href before class
    pattern2 = re.compile(
        r'<a[^>]*href="/([^/]+)/"[^>]*class="[^"]*_a6hd[^"]*"[^>]*>',
        re.DOTALL
    )
    
    usernames = pattern.findall(html) + pattern2.findall(html)
    # dedupe preserving order
    seen = set()
    unique = []
    for u in usernames:
        if u not in seen:
            seen.add(u)
            unique.append(u)
    
    accounts = []
    for username in unique:
        # display name
        dn_pat = re.compile(
            r'<span[^>]*class="[^"]*x1lliihq x193iq5w x6ikm8r x10wlt62 xlyipyv xuxw1ft[^"]*"[^>]*>(.*?)</span>',
            re.DOTALL
        )
        # Find display name near this username - search after the username anchor
        pos = html.find(f'href="/{username}/"')
        display_name = username
        if pos != -1:
            chunk = html[pos:pos+2000]
            m = dn_pat.search(chunk)
            if m:
                display_name = unescape(re.sub(r'<[^>]+>', '', m.group(1)).strip())
        
        # profile pic
        pic_pat = re.compile(
            r'<img[^>]*alt="' + re.escape(username) + r'[^"]*profile picture[^"]*"[^>]*src="([^"]+)"',
            re.DOTALL | re.IGNORECASE
        )
        pic_pat2 = re.compile(
            r'<img[^>]*src="([^"]+)"[^>]*alt="' + re.escape(username) + r'[^"]*profile picture',
            re.DOTALL | re.IGNORECASE
        )
        pic_m = pic_pat.search(html) or pic_pat2.search(html)
        pic_url = unescape(pic_m.group(1)) if pic_m else ''
        
        profile_url = f'https://instagram.com/{username}'
        accounts.append((username, display_name, profile_url, pic_url))

# Write CSV
outpath = '/Users/conradchan/repos/personal/igrestore/following.csv'
with open(outpath, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f, quoting=csv.QUOTE_ALL)
    writer.writerow(['username', 'display_name', 'profile_url', 'profile_pic_url'])
    writer.writerows(accounts)

print(f"Total accounts: {len(accounts)}\n")
print("First 5 rows:")
for row in accounts[:5]:
    print(f"  {row[0]} | {row[1]} | {row[2]} | {row[3][:80]}...")
