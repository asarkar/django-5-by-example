# import sys
# from pathlib import Path
# from typing import Any
#
# import tomlkit
# from tomlkit import TOMLDocument
# from tomlkit.items import Table, Array
#
# BASE_CONFIG_NAME = "pyproject.toml"
# PROJECT_CONFIG_PATTERN = "pyproject_ch*.toml"
# OUTPUT_CONFIG_NAME = "pyproject.toml"
# PROJECT_VERSION = "0.0.1" # Hardcoded version
#
# def get_modified_time(filepath: Path) -> float:
#     """Returns the last modification time of a file as a timestamp."""
#     try:
#         return filepath.stat().st_mtime
#     except FileNotFoundError:
#         return -1.0
#
#
# def merge_toml_documents(base_doc: dict[str, Any], override_doc: dict[str, Any]) -> dict[str, Any]:
#     """
#     Recursively merges the override document into the base document.
#     - If a key exists in both and is a simple value/table, the override wins.
#     - If a key exists in both and is a list, the override's list is appended to the base's list.
#     """
#     if not isinstance(base_doc, dict):
#         base_doc = tomlkit.document()  # Start with an empty doc if base is not dict-like
#
#     for key, value in override_doc.items():
#         if key in base_doc:
#             if isinstance(base_doc[key], (dict, Table)) and isinstance(value, (dict, Table)):
#                 # Recursive merge for nested tables
#                 base_doc[key] = merge_toml_documents(base_doc[key], value)
#             elif isinstance(base_doc[key], (list, Array)) and isinstance(value, (list, Array)):
#                 # Merge lists by extending the base list with the override list
#                 base_doc[key].extend(value)
#             else:
#                 # Overwrite simple value
#                 base_doc[key] = value
#         else:
#             # Add key/value if it only exists in the override
#             base_doc[key] = value
#
#     return base_doc
#
# def merge_project_config(base_config: Path, project_dir: Path) -> None:
#     """Handles the merging and overwriting for a single project directory."""
#
#     project_config_files = list(project_dir.rglob(PROJECT_CONFIG_PATTERN))
#
#     if not project_config_files:
#         print(
#             f"  > Skipping {project_dir.name}: No file matching '{PROJECT_CONFIG_PATTERN}' found.")
#         return
#
#     # Assuming only one project config file matches the pattern per directory
#     project_config = project_config_files[0]
#     output_config = project_config.parent / OUTPUT_CONFIG_NAME
#     project_name = project_dir.name
#
#     # Get Timestamps
#     base_mtime = get_modified_time(base_config)
#     project_mtime = get_modified_time(project_config)
#     output_mtime = get_modified_time(output_config)
#
#     # Check Condition for Overwrite: Output file is absent or older than inputs
#     if output_mtime < base_mtime or output_mtime < project_mtime:
#         # Merge Configurations
#         try:
#             # 4. Read Base and Project Configuration (full documents)
#             with open(base_config, "r") as f:
#                 base_doc = tomlkit.load(f)
#             with open(project_config, "r") as f:
#                 project_doc = tomlkit.load(f)
#
#             # Perform the Full Document Merge (base is starting point, project overrides)
#             merged_doc = merge_toml_documents(base_doc, project_doc)
#             assert isinstance(merged_doc, TOMLDocument)
#
#             # Overwrite project name
#             if "project" not in merged_doc:
#                 merged_doc.add("project", tomlkit.table())
#
#             merged_doc["project"]["name"] = project_name  # type: ignore[index]
#
#             # 7. Write the Final Structured Document
#             with open(output_config, "w") as f:
#                 f.write(tomlkit.dumps(merged_doc))
#
#         except Exception as e:
#             print(f"Failed to merge {output_config}: {e}.")
#     else:
#         print(f"  > Skipping {project_dir.name}: {output_config.name} is up to date.")
#
#
# def main() -> None:
#     # Determine the REPO_ROOT based on the script's location
#     # This assumes sync.py is executed from the repository root.
#     repo_root = Path(__file__).resolve().parent
#     base_config = repo_root / BASE_CONFIG_NAME
#
#     if not base_config.exists():
#         print(f"Error: Base config file: {base_config} not found.")
#         sys.exit(1)
#
#     print(f"Starting config merge from base: {repo_root}.")
#
#     # Iterate over each chapter
#     for chapter in repo_root.iterdir():
#         if chapter.is_dir() and chapter.name.startswith("ch"):
#             merge_project_config(base_config, chapter)
#
#     print("Merge complete.")
#
#
# if __name__ == "__main__":
#     main()