#!/bin/bash

set -e

no_test=0
no_lint=0

while (( $# > 0 )); do
   case "$1" in
   	--help)
			printf "run.sh [OPTION]... [DIR]\n"
			printf "options:\n"
			printf "\t--help			Show help\n"
			printf "\t--no-test		Skip tests\n"
			printf "\t--no-lint		Skip linting\n"
			exit 0
      	;;
      --no-test)
			no_test=1
			shift
      	;;
      --no-lint)
			no_lint=1
			shift
			;;
		*)
			break
	      ;;
   esac
done

# `root_dir` is the repository root
root_dir="$(git rev-parse --show-toplevel)"
base_dir="${1:-$root_dir}"

while IFS='' read -r -d '' manage; do
  # `project_root_dir` contains the `manage.py` file
  project_root_dir=${manage%/*}
  settings=$(find "$project_root_dir" -type f -name "settings.py" -maxdepth 2 -print -quit)
  # `project_dir` contains the `settings.py` file
  project_dir=${settings%/*}
  project_dir_name="${project_dir##*/}"

	if (( no_test == 0 )); then
    uv run --directory "$project_root_dir" manage.py test
  fi

  if (( no_lint == 0 )); then
	  if [[ -z "$CI" ]]; then
      uv run ruff check --fix "$project_root_dir"
      uv run ruff format "$project_root_dir"
    else
      uv run ruff check "$project_root_dir"
      uv run ruff format --check "$project_root_dir"
    fi

    DJANGO_SETTINGS_MODULE="${project_dir_name}.settings" \
    uv run \
      --directory "$project_root_dir" \
      mypy . \
      --config-file="$root_dir/pyproject.toml" \
      --strict
  fi
done < <(find "$base_dir" -type f -name "manage.py" -maxdepth 3 -print0)
