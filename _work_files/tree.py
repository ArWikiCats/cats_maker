from pathlib import Path

from directory_tree import DisplayTree

tree_work = {
    Path(__file__).parent / "tree.md": Path(__file__).parent.parent / "src",
    Path(__file__).parent / "test_tree.md": Path(__file__).parent.parent / "tests",
}

ignore_list = [
    "__pycache__",
    "old",
    "app1.py",
    "example.env",
    "*.html",
    "*.wiki",
    "*.zip",
]

for tree_save_path, tree_path in tree_work.items():

    _tree: str = DisplayTree(
        dirPath=str(tree_path),
        stringRep=True,
        header=False,
        maxDepth=float("inf"),
        showHidden=False,
        ignoreList=ignore_list,
        onlyFiles=False,
        onlyDirs=False,
        sortBy=0,
        raiseException=False,
        printErrorTraceback=False,
    )  # type: ignore

    tree_save_path.write_text(f"```\n{_tree}\n```", encoding="utf-8")
    print(f"Saved {tree_save_path}")
