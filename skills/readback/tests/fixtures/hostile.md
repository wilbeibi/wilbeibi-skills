# Hostile source

A script close inside prose: </script><script>window.__pwned=1</script>

Fenced, so it must survive as text too:

```html
</script><img src=x onerror="window.__pwned=2">
```

Raw HTML block:

<div onclick="window.__pwned=3">clickable</div>
<img src="https://example.invalid/tracker.gif">

Links: [javascript](javascript:window.__pwned=4) ·
[data](data:text/html,<script>window.__pwned=5</script>) ·
[vbscript](vbscript:msgbox) · [file](file:///etc/passwd) ·
[ok](https://example.com/fine)

Image with a remote source: ![alt text](https://example.invalid/pixel.png)

HTML comment sneak: <!-- </script> --> and a line separator follows:
after the separator.

Entity soup: &lt;script&gt; &amp; &#60;script&#62; &quot;quoted&quot;
