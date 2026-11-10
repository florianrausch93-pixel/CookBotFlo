#!/usr/bin/env python3
"""Turn the Cook Bot 2000 artifact into a read-only static site.

Usage: python3 -I build.py ORIG_HTML DB_RECIPES_DIR OUT_DIR
 - ORIG_HTML: the artifact page as read with the Artifact tool
 - DB_RECIPES_DIR: folder of <id>.json files from ArtifactData list (collection "recipes", out_dir)
 - OUT_DIR: the site folder (index.html and recipes.js are written there)
Test recipes (source.name "Cook Bot test recipe") are left out.
Every patch must match exactly once, so a changed artifact fails loudly instead of silently.
"""
import json, glob, os, sys, re

orig, dbdir, out = sys.argv[1:4]
html = open(orig, encoding='utf-8').read()

def sub(old, new, count=1):
    global html
    n = html.count(old)
    if n != count:
        sys.exit(f'PATCH FAILED ({n} matches, wanted {count}): {old[:90]!r}')
    html = html.replace(old, new)

def resub(pattern, new):
    global html
    html, n = re.subn(pattern, new, html, flags=re.S)
    if n != 1:
        sys.exit(f'REGEX PATCH FAILED ({n} matches): {pattern[:90]!r}')

# ---- head: self-hosted fonts (no Google servers), PWA, no search engines ----
resub(r'<link rel="preconnect" href="https://fonts.googleapis.com">.*?display=swap">',
      '<link rel="stylesheet" href="fonts.css">\n'
      '<meta name="robots" content="noindex,nofollow">\n'
      '<meta name="description" content="Flo\'s cookbook: recipes to browse, scale and cook.">\n'
      '<link rel="manifest" href="manifest.webmanifest">\n'
      '<meta name="theme-color" content="#3b1b11">\n'
      '<link rel="icon" href="icon.svg" type="image/svg+xml">\n'
      '<link rel="apple-touch-icon" href="icon-180.png">\n'
      '<meta name="apple-mobile-web-app-capable" content="yes">\n'
      '<meta name="mobile-web-app-capable" content="yes">\n'
      '<meta name="apple-mobile-web-app-title" content="Cook Bot">')
sub('<html><head>', '<html lang="en"><head>')

# ---- tips: written for friends, no Claude features ----
resub(r'const TIPS = \[.*?\];',
      'const TIPS = ["Hi! I\'m Flo\'s dumpling. Tap me for tips.", "The servings button does all the maths for you.", '
      '"Tap a step to follow along while you cook.", "Tick off ingredients as you go.", '
      '"Search by what\'s in your fridge, I\'ll find a match.", "Salt pasta water until it tastes like the sea.", '
      '"Let meat rest a few minutes before slicing. It stays juicier.", "Toast spices in a dry pan first for way more flavour.", '
      '"A squeeze of lemon wakes up almost any dish.", "Brown bananas? That means banana bread time.", '
      '"Add me to your home screen and I\'m always one tap away.", "Freeze soup in portions for lazy evenings."];')

# ---- home ----
sub("recipe${S.recipes.size===1?'':'s'} in your book", "recipe${S.recipes.size===1?'':'s'} in Flo's cookbook")
sub('<h1>Hey Flo, what are we <em>cooking</em> today?</h1>', '<h1>What are we <em>cooking</em> today?</h1>')
sub('      <button class="btn" data-act="nav" data-to="ideas">${ic(\'spark\')}Ask Claude for ideas</button>\n', '')
sub('<h2>Favourites</h2>', "<h2>Flo's favourites</h2>")
resub(r'function emptyBook\(\)\{.*?\n\}\n',
      'function emptyBook(){\n  return `<div class="empty">${mascot()}<h3>No recipes here yet</h3><p>Flo is still filling the book. Check back soon.</p></div>`;\n}\n')

# ---- season / cuisine / chapter / search: drop the Claude buttons ----
resub(r'<button class="btn sm primary" data-act="ideasfor" data-q="\$\{esc\(\'Seasonal \'.*?Seasonal ideas from Claude</button>', '')
sub('<p>Let Claude suggest a few seasonal dishes, then save the ones you like.</p>', '<p>Pick another season above.</p>')
resub(r'<div class="sec-head"><span></span><button class="btn sm" data-act="ideasfor" data-q="\$\{esc\(\'Classic \'.*?ideas</button></div>', '')
resub(r'<p>Paste one in, snap a photo of a page, or let Claude suggest a few.</p><div class="hero-actions">.*?</div></div>`\}',
      '<p>Flo hasn\'t added any yet.</p></div>`}')
resub(r'\n    <button class="btn sm" data-act="ideasfor" data-q="\$\{esc\(\'Something with \'.*?</button></div>', '</div>')
sub('<p>Ask Claude for ideas, or look online and paste what you find into Add.</p>', '<p>Try fewer or different ingredients.</p>')
sub("'Nothing in your book yet'", "'Nothing found'")

# ---- recipe page: share button instead of edit tools ----
sub('<button class="btn sm" data-act="copylist" data-id="${esc(id)}">',
    '<button class="btn sm primary" data-act="share" data-id="${esc(id)}">${ic(\'link\')}Share</button>\n    <button class="btn sm" data-act="copylist" data-id="${esc(id)}">')
sub("case 'askdel':",
    """case 'share': {
      const r = S.recipes.get(id), url = location.href.split('#')[0] + '#r/' + encodeURIComponent(id);
      if (navigator.share){ try { await navigator.share({title: r?.title || 'Cook Bot', url}); } catch {} break; }
      try { await navigator.clipboard.writeText(url); toast('Link copied','link'); } catch { prompt('Copy this link', url); }
      break;
    }
    case 'askdel':""")
sub("<span class=\"eyebrow\">Flo's notes</span>", "<span class=\"eyebrow\">Flo's notes</span>")  # sanity check it exists

# ---- dock: Home, Search, Season. Claude-only routes fall back to home ----
sub("const DOCK = [['home','home','Home'],['search','search','Search'],['ideas','spark','Ideas'],['add','plus','Add']];",
    "const DOCK = [['home','home','Home'],['search','search','Search'],['season','leaf','In season']];")
sub("    case 'ideas': html = vIdeas(); break;\n    case 'add': html = vAdd(); break;\n    case 'edit': html = vEdit(); break;\n", '')

# ---- links that open a recipe, chapter, season or cuisine directly (#r/<id> etc.) ----
sub("function go(route, push=true){\n  S.route = route; S.confirmDel = null;\n  if (push){ S.depth++; try { history.pushState({route, depth:S.depth}, ''); } catch {} }",
    """const HKEY = {recipe:'r', cat:'c', season:'s', cuisine:'k', search:'search'};
const toHash = r => r.name==='home' || !HKEY[r.name] ? location.pathname + location.search : '#' + HKEY[r.name] + (r.id ? '/' + encodeURIComponent(r.id) : '');
function fromHash(){
  const [k, v] = location.hash.slice(1).split('/'); const id = v ? decodeURIComponent(v) : undefined;
  const name = Object.keys(HKEY).find(n => HKEY[n] === k);
  return name ? {name, id} : {name:'home'};
}
S.route = fromHash();
function go(route, push=true){
  S.route = route; S.confirmDel = null;
  if (push){ S.depth++; try { history.pushState({route, depth:S.depth}, '', toHash(route)); } catch {} }""")
sub("try { history.replaceState({route:S.route, depth:0}, ''); } catch {}",
    "try { history.replaceState({route:S.route, depth:0}, ''); } catch {}\naddEventListener('hashchange', () => { S.route = fromHash(); render(true); window.scrollTo(0,0); });")
# in-place route swaps (season chips, cuisine chips, saved edits) keep the address in sync
sub("history.replaceState({route:S.route, depth:S.depth}, ''); } catch {} render(false); } else go({name:'season', id}); break;",
    "history.replaceState({route:S.route, depth:S.depth}, '', toHash(S.route)); } catch {} render(false); } else go({name:'season', id}); break;")
sub("history.replaceState({route:S.route, depth:S.depth}, ''); } catch {} render(false); } else go({name:'cuisine', id}); break;",
    "history.replaceState({route:S.route, depth:S.depth}, '', toHash(S.route)); } catch {} render(false); } else go({name:'cuisine', id}); break;")

# ---- boot: recipes come from recipes.js, nothing can be written ----
resub(r"\(async \(\) => \{\n  const C = window\.claude;.*?\n  render\(false\);\n\}\)\(\);\n",
      """S.recipes = new Map(Object.entries(window.COOKBOOK_RECIPES || {}));
S.canWrite = false; S.mode = 'static'; S.ready = true;
render(false);
if ('serviceWorker' in navigator && location.protocol === 'https:') navigator.serviceWorker.register('sw.js').catch(()=>{});
""")
sub('<script>\n(() => {', '<script src="recipes.js"></script>\n<script>\n(() => {')

for bad in ['window.claude', "data-act=\"nav\" data-to=\"ideas\"", 'Ask Claude']:
    if bad in html:
        sys.exit(f'LEFTOVER: {bad}')

# ---- recipes ----
recipes, skipped = {}, []
for f in sorted(glob.glob(os.path.join(dbdir, '*.json'))):
    d = json.load(open(f, encoding='utf-8'))
    r = d.get('data', d) if isinstance(d.get('data'), dict) else d
    rid = d.get('id') or os.path.splitext(os.path.basename(f))[0]
    if (r.get('source') or {}).get('name') == 'Cook Bot test recipe':
        skipped.append(r.get('title')); continue
    recipes[rid] = r

os.makedirs(out, exist_ok=True)
open(os.path.join(out, 'index.html'), 'w', encoding='utf-8').write(html)
open(os.path.join(out, 'recipes.js'), 'w', encoding='utf-8').write(
    '/* Flo\'s recipes, exported from the Cook Bot 2000 artifact. Generated file. */\n'
    'window.COOKBOOK_RECIPES = ' + json.dumps(recipes, ensure_ascii=False, indent=1) + ';\n')
print(f'{len(recipes)} recipes written, {len(skipped)} test recipes left out: {skipped}')
