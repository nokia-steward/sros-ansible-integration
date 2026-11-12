"""Generate the MkDocs reference pages from the plugin and module docstrings.

Reads DOCUMENTATION, EXAMPLES and RETURN of every module and plugin below
plugins/, renders docs/reference/*.md and the reference index, and updates
the Reference section of the mkdocs.yml navigation.

Plugins of different types share names (md, classic, light), so pages are
named <namespace>.<collection>.<name>_<type>.md like on docs.ansible.com.
Modules use <namespace>.<collection>.<name>.md.
"""

import ast
import re
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PLUGINS_DIR = PROJECT_ROOT / "plugins"
REFERENCE_DIR = PROJECT_ROOT / "docs" / "reference"
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
MKDOCS_FILE = PROJECT_ROOT / "mkdocs.yml"

# Order of the plugin types in the navigation and the index
PLUGIN_TYPES = ["cliconf", "netconf", "terminal"]

ANSIBLE_DOCS = "https://docs.ansible.com/projects/ansible/latest/collections"

with open(PROJECT_ROOT / "galaxy.yml", encoding="utf-8") as f:
    _galaxy = yaml.safe_load(f)
COLLECTION = "%s.%s" % (_galaxy["namespace"], _galaxy["name"])


def page_name(name, plugin_type):
    if plugin_type == "module":
        return "%s.%s.md" % (COLLECTION, name)
    return "%s.%s_%s.md" % (COLLECTION, name, plugin_type)


def plugin_url(fqcn, plugin_type):
    """Link target for M() and P() references."""
    if fqcn.startswith(COLLECTION + "."):
        return page_name(fqcn.rsplit(".", 1)[1], plugin_type)
    parts = fqcn.split(".")
    if len(parts) != 3:
        return "#"
    suffix = "module" if plugin_type == "module" else plugin_type
    return "%s/%s/%s/%s_%s.html" % (ANSIBLE_DOCS, parts[0], parts[1], parts[2], suffix)


def _closing_paren(text, start):
    depth = 1
    for i in range(start, len(text)):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return i
    return -1


_MACRO = re.compile(r"\b(RV|[CVIBMOPUL])\(")


def ansible_format(text):
    """Convert Ansible documentation markup to Markdown."""
    if not isinstance(text, str):
        return "" if text is None else str(text)
    out = []
    pos = 0
    for match in _MACRO.finditer(text):
        if match.start() < pos:
            continue
        end = _closing_paren(text, match.end())
        if end < 0:
            continue
        macro, inner = match.group(1), text[match.end():end]
        out.append(text[pos:match.start()])
        if macro in ("C", "V"):
            out.append("`%s`" % inner)
        elif macro == "I":
            out.append("*%s*" % inner)
        elif macro == "B":
            out.append("**%s**" % inner)
        elif macro == "M":
            out.append("[`%s`](%s)" % (inner, plugin_url(inner, "module")))
        elif macro == "P" and "#" in inner:
            fqcn, plugin_type = inner.split("#", 1)
            out.append("[`%s`](%s)" % (fqcn, plugin_url(fqcn, plugin_type)))
        elif macro in ("O", "P"):
            name = inner.split("=", 1)[0]
            out.append("[`%s`](#param-%s)" % (inner, name.replace("_", "-")))
        elif macro == "RV":
            name = inner.split("=", 1)[0]
            out.append("[`%s`](#return-%s)" % (inner, name.replace("_", "-")))
        elif macro == "U":
            out.append("<%s>" % inner)
        elif macro == "L":
            label, url = inner.split(",", 1) if "," in inner else (inner, "")
            out.append("[%s](%s)" % (label.strip(), url.strip()))
        pos = end + 1
    out.append(text[pos:])
    return "".join(out)


def as_list(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def read_docs(path):
    """Return DOCUMENTATION, EXAMPLES and RETURN of a plugin file."""
    sections = {}
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in ("DOCUMENTATION", "EXAMPLES", "RETURN"):
                    sections[target.id] = node.value.value
    doc = yaml.safe_load(sections.get("DOCUMENTATION") or "") or {}
    returns = yaml.safe_load(sections.get("RETURN") or "") or {}
    examples = (sections.get("EXAMPLES") or "").strip()
    return doc, examples, returns


def option_rows(options):
    rows = []
    for name, spec in sorted((options or {}).items()):
        comments = [ansible_format(line) for line in as_list(spec.get("description"))]
        if spec.get("choices"):
            comments.append("**Choices:** " + ", ".join("`%s`" % c for c in spec["choices"]))
        if "default" in spec:
            comments.append("**Default:** `%s`" % spec["default"])
        if spec.get("required"):
            comments.append("**Required:** always")
        for var in as_list(spec.get("vars")):
            comments.append("**Variable:** `%s`" % var.get("name"))
        for env in as_list(spec.get("env")):
            comments.append("**Environment:** `%s`" % env.get("name"))
        rows.append({
            "name": name,
            "anchor": "param-" + name.replace("_", "-"),
            "type": spec.get("type", "str"),
            "comments": "<br/>".join(comments) or "-",
        })
    return rows


def return_rows(returns):
    rows = []
    for name, spec in returns.items():
        comments = [ansible_format(line) for line in as_list(spec.get("description"))]
        if spec.get("returned"):
            comments.append("**Returned:** " + ansible_format(spec["returned"]))
        rows.append({
            "name": name,
            "anchor": "return-" + name.replace("_", "-"),
            "type": spec.get("type", "-"),
            "comments": "<br/>".join(comments) or "-",
            "sample": yaml.safe_dump(spec["sample"], default_flow_style=False, sort_keys=False).strip()
            if "sample" in spec else None,
        })
    return rows


def collect():
    items = []
    for path in sorted((PLUGINS_DIR / "modules").glob("*.py")):
        if not path.name.startswith("_"):
            items.append(("module", path))
    for plugin_type in PLUGIN_TYPES:
        for path in sorted((PLUGINS_DIR / plugin_type).glob("*.py")):
            if not path.name.startswith("_"):
                items.append((plugin_type, path))
    return items


def main():
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        keep_trailing_newline=True,
        autoescape=select_autoescape(enabled_extensions=('html', 'xml')),
    )
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    pages = []

    for plugin_type, path in collect():
        doc, examples, returns = read_docs(path)
        name = path.stem
        page = {
            "fqcn": "%s.%s" % (COLLECTION, name),
            "type": plugin_type,
            "file": page_name(name, plugin_type),
            "short_description": ansible_format(doc.get("short_description", name)),
            "description": [ansible_format(line) for line in as_list(doc.get("description"))],
            "requirements": [ansible_format(line) for line in as_list(doc.get("requirements"))],
            "notes": [ansible_format(line) for line in as_list(doc.get("notes"))],
            "author": as_list(doc.get("author")),
            "version_added": doc.get("version_added"),
            "options": option_rows(doc.get("options")),
            "examples": examples,
            "returns": return_rows(returns),
        }
        (REFERENCE_DIR / page["file"]).write_text(env.get_template("page.md.j2").render(page=page), encoding="utf-8")
        print("Generated %s" % (REFERENCE_DIR / page["file"]).relative_to(PROJECT_ROOT))
        pages.append(page)

    (REFERENCE_DIR / "index.md").write_text(
        env.get_template("index.md.j2").render(pages=pages, plugin_types=PLUGIN_TYPES), encoding="utf-8")
    print("Generated %s" % (REFERENCE_DIR / "index.md").relative_to(PROJECT_ROOT))

    with open(MKDOCS_FILE, encoding="utf-8") as mkdocs_stream:
        mkdocs = yaml.safe_load(mkdocs_stream)
    reference = [{"Overview": "reference/index.md"}]
    modules = [{p["fqcn"].rsplit(".", 1)[1]: "reference/" + p["file"]} for p in pages if p["type"] == "module"]
    if modules:
        reference.append({"Modules": modules})
    for plugin_type in PLUGIN_TYPES:
        entries = [{p["fqcn"].rsplit(".", 1)[1]: "reference/" + p["file"]} for p in pages if p["type"] == plugin_type]
        if entries:
            reference.append({"%s Plugins" % plugin_type.capitalize(): entries})
    mkdocs["nav"] = [{"Reference": reference} if isinstance(item, dict) and "Reference" in item else item
                     for item in mkdocs["nav"]]
    with open(MKDOCS_FILE, "w", encoding="utf-8") as mkdocs_stream:
        yaml.dump(mkdocs, mkdocs_stream, default_flow_style=False, sort_keys=False, allow_unicode=True)
    print("Updated %s" % MKDOCS_FILE.relative_to(PROJECT_ROOT))


if __name__ == "__main__":
    main()
