# 1. Claude Code CLI インストール（Node.jsが必要）
npm install -g @anthropic-ai/claude-code

# 2. GitHub CLI インストール（Ubuntu/Debian）
type -p gh >/dev/null || (
  curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
  sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
  sudo apt update
  sudo apt install gh -y
)

# 3. GitHubログイン
gh auth login
gh auth setup-git

# 4. Gitユーザー設定
GITHUB_USER=$(gh api user --jq '.login')
if [ -n "$GITHUB_USER" ]; then
  git config --global user.name "$GITHUB_USER"
  git config --global user.email "${GITHUB_USER}@users.noreply.github.com"
  git config --global init.defaultBranch main
  echo "Gitのユーザー設定を [$GITHUB_USER] として完了しました。"
else
  echo "GitHubユーザー名の取得に失敗しました。ログイン状態を確認してください。"
fi