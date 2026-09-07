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

`scripts/test_readback.py` re-checks the file SHA-256, so a silent swap fails the suite.

To upgrade, download the pinned tarball, verify the registry integrity value, copy
`package/dist/markdown-it.min.js` and `package/LICENSE` here, then update the version,
URL, and both checksums above and in `scripts/test_readback.py`.

The page configures the parser itself (raw HTML off, typographer off, images not fetched,
`http(s)`/`mailto` links only); do not rely on upstream defaults for those.
