"""Shared fluid UI actions used from multiple widgets."""
from __future__ import annotations

from PyQt6.QtWidgets import QMessageBox, QWidget

from model.data_models import AnalysisObject
from model.fluid_model import Fluid


def confirm_delete_fluid(
    parent: QWidget,
    analysis: AnalysisObject,
    fluid: Fluid,
    ) -> bool:
    list_of_contacts: list[str] = []
    for other in analysis.fluids:
        bottom_fluid = other.bottom_contact.bottom_fluid
        if bottom_fluid is not None and bottom_fluid is fluid:
            list_of_contacts.append(other.name)

    if not list_of_contacts:
        text_1 = f"Are you sure you want to delete fluid {fluid.name}?"
        text_2 = "\n\nThis action is not reversible"
        text_3 = ""
    else:
        text_1 = f"{fluid.name} is the contact fluid of"
        if len(list_of_contacts) == 1:
            text_2 = f" {list_of_contacts[0]}"
        else:
            text_2 = ":\n\t" + "\n\t".join(list_of_contacts)
        text_3 = (
            "\n\nAre you sure you want to proceed?"
            "\nThis action is not reversible"
            )
    message = text_1 + text_2 + text_3

    reply = QMessageBox.question(parent, "Delete Fluid", message)
    return reply == QMessageBox.StandardButton.Yes
