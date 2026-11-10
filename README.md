# Cook Bot 2000 (read-only edition)

Flo's cookbook as a static website for friends: browse recipes, chapters, ingredient search,
servings scaler, cuisine and season labels, "What's in season", macros and the Cook Score.
No logins, no AI features, nothing is saved on a server.

## How updates work
Flo keeps editing recipes in the Cook Bot 2000 artifact on claude.ai. To publish the changes here,
a Claude thread exports the artifact's `recipes` collection and the page, then runs:

    python3 -I tools/build.py <artifact.html> <exported recipes folder> .

That rewrites `index.html` and `recipes.js` (test recipes are left out). Commit and push;
GitHub Pages updates the site within a minute or two. If the design changed, bump `VERSION` in `sw.js`.

## Files
- `index.html`: the app (generated from the artifact, edit tools and Claude features removed)
- `recipes.js`: all recipes (generated)
- `fonts/`, `fonts.css`: fonts served from this site, so no Google servers are contacted
- `manifest.webmanifest`, `sw.js`, `icon*`: "Add to home screen" and offline use
- `robots.txt`: asks search engines to stay away
