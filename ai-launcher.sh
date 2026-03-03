#!/bin/bash
#
# ai-launcher.sh — Kiểm tra, cài đặt và khởi chạy AI CLI tools trên macOS
# Hỗ trợ: Gemini CLI (Google) và Claude Code (Anthropic)
# Idempotent: chạy lại bao nhiêu lần cũng an toàn
#

set -euo pipefail

# ──────────────────────────────────────────────
# Hằng số
# ──────────────────────────────────────────────
readonly NODE_MIN_VERSION=18
readonly NODE_DEFAULT_VERSION=24
readonly NVM_INSTALL_URL="https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh"
readonly GEMINI_PKG="@google/gemini-cli"
readonly CLAUDE_PKG="@anthropic-ai/claude-code"
readonly HOMEBREW_INSTALL_URL="https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh"

# ──────────────────────────────────────────────
# Tiện ích
# ──────────────────────────────────────────────
info()    { echo "ℹ️  $*"; }
success() { echo "✅ $*"; }
installing() { echo "📥 $*"; }
fail()    { echo "❌ $*"; }
warn()    { echo "⚠️  $*"; }

# Đảm bảo PATH chứa các thư mục cần thiết (Apple Silicon + Intel)
ensure_path() {
    local dirs=(
        "/opt/homebrew/bin"        # Apple Silicon Homebrew
        "/usr/local/bin"           # Intel Homebrew
    )
    # Thêm nvm bin path nếu có
    if [[ -s "$HOME/.nvm/nvm.sh" ]]; then
        source "$HOME/.nvm/nvm.sh" 2>/dev/null
    fi
    for d in "${dirs[@]}"; do
        if [[ -d "$d" ]] && [[ ":$PATH:" != *":$d:"* ]]; then
            export PATH="$d:$PATH"
        fi
    done
}

# Kiểm tra kết nối internet cơ bản
check_internet() {
    if ! curl -s --connect-timeout 5 --max-time 10 "https://registry.npmjs.org" >/dev/null 2>&1; then
        fail "Không có kết nối internet hoặc không truy cập được npm registry."
        echo "   Vui lòng kiểm tra mạng rồi thử lại."
        exit 1
    fi
}

# So sánh version: trả về 0 nếu $1 >= $2
version_gte() {
    local have="$1"
    local need="$2"
    # Lấy major version number
    local have_major
    have_major=$(echo "$have" | sed 's/^v//' | cut -d. -f1)
    [[ "$have_major" -ge "$need" ]]
}

# ──────────────────────────────────────────────
# Kiểm tra & cài đặt dependencies
# ──────────────────────────────────────────────

check_xcode_clt() {
    echo ""
    info "Kiểm tra Xcode Command Line Tools..."
    if xcode-select -p >/dev/null 2>&1; then
        success "Xcode CLT đã có tại $(xcode-select -p)"
    else
        installing "Đang cài đặt Xcode Command Line Tools..."
        echo "   (Một cửa sổ hệ thống sẽ hiện lên — bấm Install và chờ hoàn tất)"
        xcode-select --install 2>/dev/null || true
        # Chờ user cài xong
        echo ""
        echo "   Sau khi cài xong Xcode CLT, hãy chạy lại script này."
        exit 0
    fi
}

check_homebrew() {
    echo ""
    info "Kiểm tra Homebrew..."
    ensure_path
    if command -v brew >/dev/null 2>&1; then
        success "Homebrew đã có: $(brew --version | head -1)"
    else
        installing "Đang cài đặt Homebrew..."
        check_internet
        /bin/bash -c "$(curl -fsSL "$HOMEBREW_INSTALL_URL")"

        # Thiết lập PATH cho Apple Silicon
        if [[ -f "/opt/homebrew/bin/brew" ]]; then
            eval "$(/opt/homebrew/bin/brew shellenv)"
        elif [[ -f "/usr/local/bin/brew" ]]; then
            eval "$(/usr/local/bin/brew shellenv)"
        fi

        ensure_path

        if command -v brew >/dev/null 2>&1; then
            success "Homebrew cài đặt thành công."
            warn "Nếu dùng Apple Silicon, thêm dòng sau vào ~/.zshrc để Homebrew hoạt động ở terminal mới:"
            echo '   eval "$(/opt/homebrew/bin/brew shellenv)"'
        else
            fail "Không thể cài Homebrew. Vui lòng cài thủ công:"
            echo "   /bin/bash -c \"\$(curl -fsSL $HOMEBREW_INSTALL_URL)\""
            exit 1
        fi
    fi
}

check_nvm() {
    echo ""
    info "Kiểm tra nvm..."
    ensure_path

    if command -v nvm >/dev/null 2>&1 || [[ -s "$HOME/.nvm/nvm.sh" ]]; then
        # Load nvm nếu chưa load
        if ! command -v nvm >/dev/null 2>&1; then
            source "$HOME/.nvm/nvm.sh"
        fi
        success "nvm đã có: $(nvm --version)"
    else
        installing "Đang cài đặt nvm..."
        check_internet
        curl -o- "$NVM_INSTALL_URL" | bash

        # Load nvm ngay sau khi cài
        export NVM_DIR="$HOME/.nvm"
        if [[ -s "$NVM_DIR/nvm.sh" ]]; then
            source "$NVM_DIR/nvm.sh"
        fi

        if command -v nvm >/dev/null 2>&1; then
            success "nvm cài đặt thành công: $(nvm --version)"
            warn "Thêm các dòng sau vào ~/.zshrc (nếu chưa có) để nvm hoạt động ở terminal mới:"
            echo '   export NVM_DIR="$HOME/.nvm"'
            echo '   [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"'
        else
            fail "Không thể cài nvm."
            echo "   Thử cài thủ công: curl -o- $NVM_INSTALL_URL | bash"
            exit 1
        fi
    fi
}

check_nodejs() {
    echo ""
    info "Kiểm tra Node.js $NODE_DEFAULT_VERSION (qua nvm)..."

    # Đảm bảo nvm đã được load
    if [[ -s "$HOME/.nvm/nvm.sh" ]]; then
        source "$HOME/.nvm/nvm.sh"
    fi

    local current_ver
    current_ver=$(node --version 2>/dev/null || echo "v0")

    if version_gte "$current_ver" "$NODE_DEFAULT_VERSION"; then
        success "Node.js đã có: $current_ver"
    else
        if [[ "$current_ver" != "v0" ]]; then
            warn "Node.js hiện tại: $current_ver (cần >= $NODE_DEFAULT_VERSION)"
        fi
        installing "Đang cài đặt Node.js $NODE_DEFAULT_VERSION qua nvm..."
        nvm install "$NODE_DEFAULT_VERSION"
        nvm alias default "$NODE_DEFAULT_VERSION"
        nvm use default

        local new_ver
        new_ver=$(node --version 2>/dev/null || echo "unknown")
        if version_gte "$new_ver" "$NODE_DEFAULT_VERSION"; then
            success "Node.js cài đặt thành công: $new_ver"
            success "nvm default đã set thành $NODE_DEFAULT_VERSION"
        else
            fail "Không thể cài Node.js $NODE_DEFAULT_VERSION."
            echo "   Thử cài thủ công:"
            echo "   nvm install $NODE_DEFAULT_VERSION"
            echo "   nvm alias default $NODE_DEFAULT_VERSION"
            exit 1
        fi
    fi
}

# ──────────────────────────────────────────────
# Kiểm tra & cài đặt AI tools
# ──────────────────────────────────────────────

install_npm_tool() {
    local pkg="$1"
    local cmd="$2"
    local display_name="$3"

    echo ""
    info "Kiểm tra $display_name..."

    if command -v "$cmd" >/dev/null 2>&1; then
        local ver
        ver=$("$cmd" --version 2>/dev/null | head -1 || echo "installed")
        success "$display_name đã có: $ver"
        return 0
    fi

    installing "Đang cài đặt $display_name ($pkg)..."
    check_internet

    if npm install -g "$pkg" 2>/dev/null; then
        ensure_path
        if command -v "$cmd" >/dev/null 2>&1; then
            local ver
            ver=$("$cmd" --version 2>/dev/null | head -1 || echo "installed")
            success "$display_name cài đặt thành công: $ver"
            return 0
        fi
    fi

    # npm install thất bại — thử gợi ý giải pháp
    echo ""
    fail "Không thể cài $display_name bằng npm install -g."
    echo ""
    echo "   Thử một trong các cách sau:"
    echo "   1. Dùng sudo:  sudo npm install -g $pkg"
    echo "   2. Fix npm permissions:"
    echo "      mkdir -p ~/.npm-global"
    echo "      npm config set prefix ~/.npm-global"
    echo "      export PATH=~/.npm-global/bin:\$PATH"
    echo "      (thêm dòng export vào ~/.zshrc)"
    echo "   3. Dùng nvm: https://github.com/nvm-sh/nvm"
    echo ""
    return 1
}

install_gemini() {
    npm install -g @google/gemini-cli
}

install_claude() {
    curl -fsSL https://claude.ai/install.sh | bash
}

# ──────────────────────────────────────────────
# Chạy tool
# ──────────────────────────────────────────────

run_gemini() {
    echo ""
    echo "🚀 Khởi chạy Gemini CLI..."
    echo "─────────────────────────────"
    exec gemini
}

run_claude() {
    echo ""
    echo "🚀 Khởi chạy Claude Code..."
    echo "─────────────────────────────"
    exec claude
}

# ──────────────────────────────────────────────
# Luồng chính cho từng lựa chọn
# ──────────────────────────────────────────────

setup_dependencies() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Kiểm tra dependencies hệ thống"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    check_xcode_clt
    check_homebrew
    check_nvm
    check_nodejs
    echo ""
    success "Tất cả dependencies đã sẵn sàng."
}

do_gemini() {
    setup_dependencies
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Cài đặt Gemini CLI"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    if install_gemini; then
        run_gemini
    fi
}

do_claude() {
    setup_dependencies
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Cài đặt Claude Code"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    if install_claude; then
        run_claude
    fi
}

do_both() {
    setup_dependencies
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Cài đặt AI CLI Tools"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    local gemini_ok=false
    local claude_ok=false

    install_gemini && gemini_ok=true
    install_claude && claude_ok=true

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Kết quả"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if $gemini_ok; then
        success "Gemini CLI  — sẵn sàng (chạy: gemini)"
    else
        fail "Gemini CLI  — cài đặt thất bại"
    fi

    if $claude_ok; then
        success "Claude Code — sẵn sàng (chạy: claude)"
    else
        fail "Claude Code — cài đặt thất bại"
    fi

    echo ""
    if $gemini_ok || $claude_ok; then
        info "Bạn muốn chạy tool nào?"
        echo "   1. Gemini CLI"
        echo "   2. Claude Code"
        echo "   0. Thoát"
        echo ""
        read -rp "   Chọn (0-2): " run_choice
        case "$run_choice" in
            1) $gemini_ok && run_gemini || fail "Gemini CLI chưa được cài đặt." ;;
            2) $claude_ok && run_claude || fail "Claude Code chưa được cài đặt." ;;
            0) echo "👋 Tạm biệt!" ;;
            *) warn "Lựa chọn không hợp lệ. Thoát." ;;
        esac
    fi
}

# ──────────────────────────────────────────────
# Menu chính
# ──────────────────────────────────────────────

main() {
    echo ""
    echo "╔══════════════════════════════════════╗"
    echo "║       🤖 AI CLI Launcher             ║"
    echo "╠══════════════════════════════════════╣"
    echo "║                                      ║"
    echo "║  1. Gemini CLI  (Google)             ║"
    echo "║  2. Claude Code (Anthropic)          ║"
    echo "║  3. Cả hai     (kiểm tra + cài đặt) ║"
    echo "║  0. Thoát                            ║"
    echo "║                                      ║"
    echo "╚══════════════════════════════════════╝"
    echo ""
    read -rp "Chọn (0-3): " choice

    case "$choice" in
        1) do_gemini ;;
        2) do_claude ;;
        3) do_both ;;
        0)
            echo "👋 Tạm biệt!"
            exit 0
            ;;
        *)
            fail "Lựa chọn không hợp lệ. Vui lòng chọn 0-3."
            exit 1
            ;;
    esac
}

# Chạy
main "$@"
