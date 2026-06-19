import pkgutil
import importlib

with open("audit_report.txt","w",encoding="utf8") as f:

    for m in pkgutil.walk_packages(
        ["rasa/actions"],
        "rasa.actions."
    ):

        try:
            importlib.import_module(m.name)

        except Exception as e:

            f.write(
                f"{m.name}\n"
                f"{type(e).__name__}: {e}\n\n"
            )