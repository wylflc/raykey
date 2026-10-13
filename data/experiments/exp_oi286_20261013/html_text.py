import re, sys, html
raw = open(sys.argv[1], 'rb').read()
for enc in ('utf-8', 'gb18030'):
    try:
        text = raw.decode(enc); break
    except UnicodeDecodeError:
        continue
else:
    text = raw.decode('utf-8', 'replace')
text = re.sub(r'(?is)<(script|style|noscript)[^>]*>.*?</\1>', ' ', text)
text = re.sub(r'(?i)<br\s*/?>|</p>|</div>|</h\d>|</li>', '\n', text)
text = html.unescape(re.sub(r'<[^>]+>', ' ', text))
lines = [re.sub(r'[ \t　]+', ' ', l).strip() for l in text.split('\n')]
minimum = int(sys.argv[2]) if len(sys.argv) > 2 else 1
lines = [l for l in lines if len(l) >= minimum]
print('\n'.join(lines))
