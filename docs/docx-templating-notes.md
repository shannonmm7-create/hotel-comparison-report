# Working with `.docx` text in Python — the gotchas we hit (and solved)

This is the hard-won knowledge behind `build_template.py` (source `.docx` → Jinja
template) and `render.py` (Jinja template → filled `.docx`). A `.docx` is a ZIP of
XML (`word/document.xml` + relationship files), and **text is not stored as
strings** — it's a tree of runs. Almost every bug below comes from forgetting
that. Read this before changing either module.

Versions we verified against: `python-docx 1.2.0`, `docxtpl 0.20.2`, `lxml 6.1.1`.

---

## 1. A paragraph is a list of *runs*, and a placeholder can span several

Word stores a paragraph (`<w:p>`) as a sequence of runs (`<w:r>`), each with its
own formatting block (`<w:rPr>`: bold, color, font, size…). A single logical
string like `[# days/weeks/months]` is frequently **split across multiple runs**
(spell-check, a stray edit, an autosave). In *this* template one placeholder was
already split across two runs.

Consequences:

- A per-run string search (`if "[x]" in run.text`) **misses** split placeholders.
- Flattening the paragraph to one run to do a replace **destroys** the per-run
  formatting you're trying to preserve.

**What we do** (`replace_tokens` in `build_template.py`): coalesce all run texts
into one string while recording an *owner map* (`owner[i]` = which run owns
character `i`); find matches in the coalesced string; then splice each
replacement back into the run that owned its **first** character, leaving every
other run's text and all `<w:rPr>` untouched. Runs are only ever *rewritten in
place*, never re-parented — so formatting survives.

## 2. `Paragraph.runs` does NOT include runs inside a hyperlink

A `<w:hyperlink>` is a **sibling** of `<w:r>`, not a run, and the link's visible
text lives in `<w:r>` runs *nested inside* it. `Paragraph.runs` only returns the
paragraph's **direct** `<w:r>` children, so it silently skips hyperlink text.

This is true in **every** python-docx version including the current 1.2.0 — it is
not an "old version" quirk. (What changed in 1.0.0: `Paragraph.text` began
*including* hyperlink text, and the `Paragraph.hyperlinks` /
`Paragraph.iter_inner_content()` / `Hyperlink.runs` APIs were added.)

**What we do:** iterate `element.iter(qn("w:r"))` (descends into
`<w:hyperlink>`), not `paragraph.runs`, whenever we need every run.

## 3. Bullets here are literal `•` + tab, not Word list numbering

These bullets are **not** `numPr` list items — each is a run containing a literal
`•` glyph, then a tab run, then the text run. So to templatize a bullet we keep
the `•` and tab runs and only rewrite the **content** run (the one with letters).
Don't assume `numPr`; inspect first.

## 4. `xml:space="preserve"`

If a `<w:t>` value has leading/trailing spaces, Word collapses them unless the
element carries `xml:space="preserve"`. Every time we set run text we set this
attribute (`_set_text`).

---

## docxtpl (Jinja-over-Word) specifics

docxtpl runs Jinja against the raw XML, then cleans it up. Two of its relocation
rules are non-obvious and cost real debugging time.

## 5. `{%tr%}` **replaces the whole table row** — so for/endfor need separate rows

docxtpl's row directive works by a regex that finds the `<w:tr>` containing a
`{%tr … %}` tag and **replaces the entire row** with the bare `{% … %}` tag.

Therefore you must **not** put `{%tr for %}` and `{%tr endfor %}` in the same
(data) row — that row gets deleted and the loop is left unclosed
(`Encountered unknown tag 'endfor'`). Instead use **three rows**:

```
row: {%tr for r in hotel.rooms %}      <- becomes  {% for r in hotel.rooms %}, row removed
row: {{ r.room_type }} | {{ r.offered_rate|usd }} | {{ r.rack_rate|usd }}   <- repeated
row: {%tr endfor %}                    <- becomes  {% endfor %}, row removed
```

`build_template.py` deep-copies the data row twice, clears the copies, and puts
the `for`/`endfor` tags in those dedicated rows.

## 6. `{%p … %}` removes the tag's paragraph cleanly

A block tag alone in its own paragraph (e.g. `{% for hotel in hotels %}`) leaves
an **empty paragraph** behind after rendering → a stray blank line. The `p`
prefix (`{%p for hotel in hotels %}`) makes docxtpl replace the whole `<w:p>`
with the bare tag, so no blank line remains. We use `{%p … %}` for the hotel loop
and every bullet-list loop.

## 7. `autoescape=True` is mandatory (and RichText still works)

Jinja substitutes values into XML. A data value containing `&`, `<`, or `>`
produces **invalid XML** — in practice the character (and sometimes surrounding
text) silently disappears. Fix: build the Jinja `Environment(autoescape=True)`.
docxtpl's `RichText`/`Subdoc` are autoescape-safe, so the dynamic hyperlinks in
§8 still render as real links.

## 8. Dynamic per-item hyperlinks → `RichText`, not the template's `<w:hyperlink>`

You can't easily template the *target URL* of an existing `<w:hyperlink>`. Build
the link at render time instead:

```python
rt = RichText()
rt.add(hotel["name"], url_id=tpl.build_url_id(hotel["website_url"]),
       bold=True, underline=True, color="0000FF", size=24)  # size is half-points
# template: {{ hotel.name_link }}
```

`RichText.add` carries its own run formatting, so we replicate the approved link
look (blue, underlined, correct size/font) captured from the source document.

## 9. Deleting a `<w:hyperlink>` leaves an orphaned relationship (stale URL!)

Removing a `<w:hyperlink>` element does **not** remove its entry in
`word/_rels/document.xml.rels`. The source template's hyperlinks pointed at the
*reference* hotel (Hyatt House Charleston); after deleting the second hotel block
those target URLs lingered as dead relationships and showed up in the output.
Clean them: collect the `r:id`s still referenced by `<w:hyperlink>` elements and
`doc.part.rels.pop(rid)` any hyperlink relationship not in that set.

## 10. Small traps

- **Dict-attribute collision:** Jinja `hotel.items` resolves to the dict's
  `.items()` *method*, not a key named `items`. Avoid schema keys named
  `items`/`keys`/`values`/`get`. (Ours don't.)
- **`Relationships` is a `dict` subclass** in python-docx — iterate with
  `.items()`, delete with `.pop()`.
- **`Paragraph(el, parent)` needs a real parent** for `.style` to work — pass the
  `Document`, not `None`.
- **`build-template` is deterministic** — re-running it on the same source
  produces the same template. Regenerate (don't hand-edit the `.docx`) after
  changing the transform.
