def rename_item(item: QTreeWidgetItem, tree) -> None:
    if item.parent() is not None:
        return  # only top-level dataset rows

    old_name = item.text(0).strip()
    if not old_name:
        return

    new_name, ok = QInputDialog.getText(
        tree,
        "Rename dataset",
        "New name:",
        text=old_name,
    )
    if not ok:
        return  # user cancelled

    new_name = new_name.strip()
    if not new_name:
        QMessageBox.warning(tree, "Rename dataset", "Name cannot be empty.")
        return

    if new_name == old_name:
        return

    # Names already used by other datasets
    existing_names = {
        ds.name for ds in tree.project.datasets if ds.name != old_name
    }
    if new_name in existing_names:
        QMessageBox.warning(
            tree,
            "Rename dataset",
            f"A dataset named '{new_name}' already exists.",
        )
        return

    # Update project model
    try:
        dataset = tree.project.get_dataset_by_name(old_name)
    except KeyError:
        QMessageBox.warning(tree, "Rename dataset", f"Dataset '{old_name}' not found.")
        return

    dataset.name = new_name

    # Update analyses that reference this dataset by name
    for analysis in tree.project.analyses:
        analysis.source_datasets = [
            new_name if name == old_name else name
            for name in analysis.source_datasets
        ]

    # Update tree label
    item.setText(0, new_name)

    tree.project.mark_modified()