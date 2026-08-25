"""Matching an English quote to its Vietnamese scripture text.

exact.py     -- normalised string containment
retrieval.py -- embedding search, for quotes with no literal match
router.py    -- exact -> fuzzy -> retrieval -> abstain

Abstention is a feature: when no verse matches confidently, the pipeline must
translate the quote normally rather than inject a verse that is probably wrong.
"""
