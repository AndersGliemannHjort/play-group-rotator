"""Child data loading and validation from JSON input files."""

import json


class Child:
    """A child with name, gender, and optimization tracking data."""

    def __init__(self, name, gender):
        self.name = name.strip()
        self.is_girl = gender == "girl"
        self.is_boy = not self.is_girl

        self.hosting_count = 0
        self.hosting_iterations = []
        self.meetings = {}
        self.meeting_iterations = {}

    def __str__(self):
        return f"{self.name} ({'girl' if self.is_girl else 'boy'})"

    def __repr__(self):
        return self.__str__()


class ChildManager:
    """Loads and validates child data from JSON files."""

    def load_children_from_file(self, filepath):
        """Load children from names_gender.json."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            raise ValueError(f"File not found: {filepath}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {filepath}: {e}")

        if "children" not in data:
            raise ValueError(
                f"{filepath}: missing 'children' array"
            )

        children = []
        for i, entry in enumerate(data["children"]):
            name = entry.get("name", "").strip()
            gender = entry.get("gender", "")
            if not name:
                raise ValueError(
                    f"{filepath}: child {i} has no name"
                )
            if gender not in ("boy", "girl"):
                raise ValueError(
                    f"{filepath}: child '{name}' has invalid gender "
                    f"'{gender}' (expected 'boy' or 'girl')"
                )
            children.append(Child(name, gender))

        return children

    def validate_children(self, children):
        """Validate exactly 24 children with 12 boys and 12 girls."""
        if len(children) != 24:
            raise ValueError(
                f"Expected 24 children, found {len(children)}"
            )

        names = [c.name for c in children]
        if len(set(names)) != len(names):
            dupes = [n for n in names if names.count(n) > 1]
            raise ValueError(f"Duplicate names: {set(dupes)}")

        boys = sum(1 for c in children if c.is_boy)
        girls = sum(1 for c in children if c.is_girl)
        if boys != 12 or girls != 12:
            raise ValueError(
                f"Expected 12 boys and 12 girls, "
                f"found {boys} boys and {girls} girls"
            )

        print(f"Validated: {len(children)} children ({boys} boys, {girls} girls)")
        return True

    def load_past_iterations(self, filepath, children):
        """Load past iterations from past_iterations.json."""
        from group_optimizer import Group

        child_by_name = {c.name: c for c in children}

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            raise ValueError(f"File not found: {filepath}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {filepath}: {e}")

        if "iterations" not in data:
            raise ValueError(
                f"{filepath}: missing 'iterations' array"
            )

        past_iterations = []

        for iter_idx, iteration in enumerate(data["iterations"], 1):
            if len(iteration) != 6:
                raise ValueError(
                    f"Iteration {iter_idx}: expected 6 groups, "
                    f"got {len(iteration)}"
                )

            groups = []
            seen = set()

            for grp_idx, group_names in enumerate(iteration, 1):
                if len(group_names) != 4:
                    raise ValueError(
                        f"Iteration {iter_idx}, group {grp_idx}: "
                        f"expected 4 children, got {len(group_names)}"
                    )

                group_children = []
                for name in group_names:
                    if name not in child_by_name:
                        raise ValueError(
                            f"Iteration {iter_idx}: "
                            f"unknown child '{name}'"
                        )
                    if name in seen:
                        raise ValueError(
                            f"Iteration {iter_idx}: "
                            f"child '{name}' in multiple groups"
                        )
                    seen.add(name)
                    group_children.append(child_by_name[name])

                groups.append(Group(group_children))

            if len(seen) != 24:
                missing = set(child_by_name) - seen
                raise ValueError(
                    f"Iteration {iter_idx}: missing children: {missing}"
                )

            past_iterations.append(groups)

        return past_iterations
