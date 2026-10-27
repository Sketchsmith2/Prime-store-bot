# PRIME STORE BOT — CONTEXT

## GitHub
- Repo: https://github.com/Sketchsmith2/Prime-store-bot
- Branch: main

## Deployment
- Host: Render (free tier)
- URL: https://prime-store-bot-hs2f.onrender.com
- UptimeRobot: 5 min interval

## Rules
- ❌ Termux/PC pe `python bot.py` NAHI chalana (409 conflict)
- ✅ Sirf edit + git push karo
- ✅ Bot sirf Render pe chalega

## Files
- bot.py — main code
- store_data.json — products & stock
- orders.json — order history
- requirements.txt

## Current Products (Last update: [date])
| Product | Stock | Price |
|---------|-------|-------|
| Bigbasket JSON | 9 | ₹15 |
| Flipkart JSON | 0 | ₹15 |
| Meesho 120 OFF | 5 | ₹10 |
| Meesho 170 OFF | 22 | ₹18 |
| Bigbasket Coupon | 0 | ₹5 |
| Amazon 10rs Giftcard | 0 | ₹5 |

## Delivery System
- JSON category: pura JSON as it is (file + caption + admin copy)
- Coupon category: sirf codes (no file)
- Admin approve button → auto delivery

## Common Commands
- Stock check: `python -c "import json; d=json.load(open('store_data.json')); [print(p['name'],':',p.get('stock',0),'stock, Rs.',p['price']) for p in d['products']['json_files']]"`
- Push: `git add . ; git commit -m "Update" ; git push origin main`
- Termux bot kill: `pkill -9 -f python`