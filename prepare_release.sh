#!/bin/bash
# Prepare release package for distribution
# Creates a clean tarball ready for deployment

set -e

VERSION="${1:-2.0}"
RELEASE_NAME="skydio-network-tester-v${VERSION}"
RELEASE_DIR="releases"
PACKAGE_DIR="${RELEASE_DIR}/${RELEASE_NAME}"

echo "=========================================="
echo "Preparing Release Package"
echo "=========================================="
echo ""
echo "Version: $VERSION"
echo "Package: ${RELEASE_NAME}.tar.gz"
echo ""

# Create release directory
mkdir -p "$RELEASE_DIR"
rm -rf "$PACKAGE_DIR"
mkdir -p "$PACKAGE_DIR"

# Copy files
echo "Copying files..."
rsync -av \
    --exclude='.git' \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.DS_Store' \
    --exclude='exports/*' \
    --exclude='test_history/*' \
    --exclude='*.log' \
    --exclude='releases' \
    --exclude='.gitignore' \
    ./ "$PACKAGE_DIR/"

# Create version file
echo "$VERSION" > "$PACKAGE_DIR/VERSION"

# Create checksums
echo "Generating checksums..."
cd "$RELEASE_DIR"
tar czf "${RELEASE_NAME}.tar.gz" "$RELEASE_NAME"
sha256sum "${RELEASE_NAME}.tar.gz" > "${RELEASE_NAME}.tar.gz.sha256"

# Cleanup
rm -rf "$RELEASE_NAME"

echo ""
echo "=========================================="
echo "Release Package Created!"
echo "=========================================="
echo ""
echo "Package: ${RELEASE_DIR}/${RELEASE_NAME}.tar.gz"
echo "SHA256:  ${RELEASE_DIR}/${RELEASE_NAME}.tar.gz.sha256"
echo ""
echo "To deploy:"
echo "  1. Upload to GitHub releases or file server"
echo "  2. Update REPO_URL in quick_install.sh"
echo "  3. Share installation command with users"
echo ""
echo "Installation command:"
echo "  curl -sSL https://YOUR_SERVER/quick_install.sh | bash"
echo ""
echo "Or manual download:"
echo "  wget https://YOUR_SERVER/${RELEASE_NAME}.tar.gz"
echo "  tar xzf ${RELEASE_NAME}.tar.gz"
echo "  cd ${RELEASE_NAME}"
echo "  ./install_raspberry_pi.sh"
echo ""
