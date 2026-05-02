# Kabigon Context

Kabigon turns URLs into text by selecting a source-specific retrieval path, then running loaders in a deliberate order.
This document fixes the project language so routing, planning, and loader work use the same terms.

## Language

**Pipeline**:
A source-specific retrieval path chosen from a URL.
_Avoid_: route, source handler, provider

**Pipeline catalog**:
The module that owns the known Pipelines and exposes lookup from URL.
_Avoid_: registry, routing table

**Loader**:
An adapter that attempts to extract text from a URL or file.
_Avoid_: scraper, parser, backend

**Targeted loaders**:
The Loaders preferred by a matched Pipeline before fallback is considered.
_Avoid_: primary route, first pass

**Fallback loader**:
A Loader attempted after the Targeted loaders when policy allows it.
_Avoid_: backup scraper, rescue path

**Execution plan**:
The ordered list of Loaders attempted for one retrieval.
_Avoid_: chain, stack

## Relationships

- A **Pipeline catalog** owns many **Pipelines**
- A **Pipeline** selects one or more **Targeted loaders**
- An **Execution plan** starts with the **Targeted loaders**
- An **Execution plan** may append **Fallback loaders**
- A **Loader** is attempted within an **Execution plan**

## Architecture Notes

- `docs/EARLY_LOAD_CHAIN.md` records the pre-routing fixed `Compose` load chain used around `v0.14.1` and earlier.

## Example dialogue

> **Dev:** "If the URL matches the YouTube **Pipeline**, where do the fallback rules live?"
> **Domain expert:** "The **Pipeline catalog** owns the **Targeted loaders** and policy, and the **Execution plan** expands that into the ordered Loader list."

## Flagged ambiguities

- "pipeline" and "execution plan" were easy to blur together. Resolution: a **Pipeline** is the chosen retrieval path; an **Execution plan** is the concrete ordered Loader list.
- "registry" was being used for both loader factories and routing data. Resolution: keep **Pipeline catalog** for Pipeline knowledge and reserve "registry" for loader factory wiring if it survives.
