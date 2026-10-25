#!/usr/bin/env bash
# Đồng bộ dữ liệu crawl (latest.json, daily.json, history/) giữa web/data/ và nhánh `data`.
# Nhánh `data` chỉ có đúng một commit, mỗi lần push thì ghi đè (amend + force push),
# nên crawl 30 phút một lần không làm lịch sử của `main` dài thêm.
# catalog.json sửa tay, nằm trong `main`, không đưa sang nhánh `data`.
#
#   tools/sync-data.sh pull   # nhánh data → web/data/
#   tools/sync-data.sh push   # web/data/ → nhánh data (chạy pull trước)
set -euo pipefail
cd "$(dirname "$0")/.."
DIR=.data-branch

case "${1:-}" in
  pull)
    git fetch -q origin data
    rm -rf "$DIR"
    git worktree prune
    git worktree add -q --detach "$DIR" FETCH_HEAD
    rsync -a --checksum --exclude .git "$DIR"/ web/data/
    ;;
  push)
    [ -e "$DIR/.git" ] || { echo "Chưa có $DIR, chạy pull trước" >&2; exit 1; }
    rsync -a --checksum --exclude .git --exclude catalog.json web/data/ "$DIR"/
    cd "$DIR"
    git add -A
    if git diff --cached --quiet; then
      echo "Không có thay đổi"
      exit 0
    fi
    git commit -q --amend -m "data: cập nhật giá $(TZ=Asia/Tokyo date '+%m/%d %H:%M')"
    git push -q --force origin HEAD:data
    echo "Đã đẩy lên nhánh data"
    ;;
  *)
    echo "Dùng: tools/sync-data.sh pull|push" >&2
    exit 2
    ;;
esac
