# Vendored browser assets

Generated review pages inline these files. No download or Node install happens at build time
or at review time.

## markdown-it.min.js

- Version: 14.1.0
- License: MIT (`markdown-it.LICENSE`)
- Upstream: <https://github.com/markdown-it/markdown-it>
- Downloaded from: <https://registry.npmjs.org/markdown-it/-/markdown-it-14.1.0.tgz>, file `package/dist/markdown-it.min.js`
- Package tarball integrity (npm registry): `sha512-a54IwgWPaeBCAAsv13YgmALOF1elABB08FxO9i+r4VFk5Vl4pKokRPeX8u5TCgSsPi6ec1otfLjdOpVcgbpshg==`
- File SHA-256: `38c70a1e7ca91ab40e2d9e6e60129851a717ed1c7d4acbbdd41bf9503791cf68`

## mermaid.min.js

- Version: 11.17.2
- License: MIT (`mermaid.LICENSE`)
- Upstream: <https://github.com/mermaid-js/mermaid>
- Downloaded from: <https://registry.npmjs.org/mermaid/-/mermaid-11.17.2.tgz>, file `package/dist/mermaid.min.js`
- Package tarball integrity (npm registry): `sha512-V6K3C8EBdEsPFZXSKMJe6ppQOENxuHARr9GvHX4hh47lAbhMRD9qf4oEK7LoaRQxULMa80/qt5gHO73aCleBBg==`
- File SHA-256: `581ed7d74bd9048d0e3a91363927d72ef22942d7722546b27f7cc29e35390eb8`

3.4 MB, so it is inlined only into pages whose source has a fenced `mermaid` block, and
never when `--no-diagrams` is passed. This is the one prebuilt file in the package that is
self-contained: the ESM entry points load 300-odd chunks over the network, which a page
opened from `file://` cannot do. Verified to render under the page's own CSP with zero
network requests.

The page renders at `securityLevel: "strict"` and never enables `htmlLabels`; a `click`
directive in diagram source must not reach a page that holds the review's submit token.
Rendered SVG is marked `data-rb-ui`, so a reader's annotation anchors to the diagram
source, never to generated layout that another Mermaid version would place elsewhere.

`scripts/test_readback.py` re-checks both file SHA-256s, so a silent swap fails the suite.

To upgrade, download the pinned tarball, verify the registry integrity value, copy
`package/dist/markdown-it.min.js` and `package/LICENSE` here, then update the version,
URL, and both checksums above and in `scripts/test_readback.py`.

The page configures the parser itself (raw HTML off, typographer off, images not fetched,
`http(s)`/`mailto` links only); do not rely on upstream defaults for those.
