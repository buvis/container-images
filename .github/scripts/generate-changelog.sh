#!/usr/bin/env bash
set -euo pipefail

CATEGORY="$1"
IMAGE="$2"
IMAGE_DIR="${CATEGORY}/${IMAGE}"

echo "# Changelog — ${IMAGE}"
echo ""

git log --format='%as|%s' --no-merges -- "${IMAGE_DIR}/" | awk -F'|' -v image="$IMAGE" '
BEGIN {
  current_date = ""
  # category order for sorting
  order["Added"] = 1
  order["Changed"] = 2
  order["Fixed"] = 3
  order["Removed"] = 4
  order["Security"] = 5
  order["Documentation"] = 6
}

{
  date = $1
  subject = $2

  # skip chore(deps): Renovate noise
  if (subject ~ /^chore\(deps\):/) next

  # skip test-only commits
  if (subject ~ /^test(\(.*\))?:/) next

  # detect third-party version update: "chore: update <image> to version X"
  if (match(subject, /^chore: update .* to version (.+)$/, m)) {
    cat = "Changed"
    desc = "Updated to v" m[1]
  }
  # parse conventional commit
  else if (match(subject, /^(feat|fix|refactor|perf|style|build|docs|chore|ops)(\(.*\))?(!)?:[[:space:]]*(.+)$/, m)) {
    type = m[1]
    desc = m[4]

    if (type == "feat") cat = "Added"
    else if (type == "fix") cat = "Fixed"
    else if (type == "refactor" || type == "perf" || type == "style" || type == "build" || type == "ops") cat = "Changed"
    else if (type == "docs") cat = "Documentation"
    else if (type == "chore") next
    else cat = "Changed"
  }
  # non-conventional commit
  else {
    cat = "Changed"
    desc = subject
  }

  # store entries grouped by date then category
  if (date != current_date) {
    dates[++date_count] = date
    current_date = date
  }
  key = date SUBSEP cat
  if (!(key in entry_count)) {
    cats[date, ++cat_count[date]] = cat
  }
  entry_count[key]++
  entries[key, entry_count[key]] = desc
}

END {
  for (d = 1; d <= date_count; d++) {
    dt = dates[d]
    printf "\n## %s\n", dt

    # collect unique categories for this date
    n = 0
    delete seen
    for (c = 1; c <= cat_count[dt]; c++) {
      ct = cats[dt, c]
      if (!(ct in seen)) {
        seen[ct] = 1
        sorted[++n] = ct
      }
    }

    # sort categories by predefined order
    for (i = 1; i <= n; i++) {
      for (j = i + 1; j <= n; j++) {
        oi = (sorted[i] in order) ? order[sorted[i]] : 99
        oj = (sorted[j] in order) ? order[sorted[j]] : 99
        if (oi > oj) {
          tmp = sorted[i]; sorted[i] = sorted[j]; sorted[j] = tmp
        }
      }
    }

    for (i = 1; i <= n; i++) {
      ct = sorted[i]
      printf "\n### %s\n\n", ct
      key = dt SUBSEP ct
      for (e = 1; e <= entry_count[key]; e++) {
        printf "- %s\n", entries[key, e]
      }
    }
  }
}
'
