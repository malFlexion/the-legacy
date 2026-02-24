# TheLegacy

A Magic: The Gathering game engine built in .NET.

## Overview

TheLegacy is a comprehensive MTG game engine designed with a clean, layered architecture. The core engine is UI-agnostic — it processes game commands without knowing whether they come from a console, a web app, or an AI player.

## Project Structure

```
TheLegacy.sln
├── src/
│   ├── TheLegacy.Core/        # Domain models, game state, command interfaces
│   ├── TheLegacy.Scryfall/    # Scryfall API client, bulk data, card mapping
│   └── TheLegacy.Console/     # Console app frontend
└── tests/
    ├── TheLegacy.Core.Tests/
    └── TheLegacy.Scryfall.Tests/
```

## Architecture

- **Core** has no external dependencies. It defines the card model, game state, zones, and the command/engine interfaces.
- **Scryfall** depends on Core. It fetches card data from the Scryfall API, caches it locally, and maps it into Core's domain model.
- **Console** depends on Core and Scryfall. It translates user input into commands for the engine.
- A future **web app** would replace Console, producing the same commands via HTTP requests.

## Prerequisites

- [.NET 8 SDK](https://dotnet.microsoft.com/download/dotnet/8.0)

## Getting Started

```bash
# Build
dotnet build

# Run the console app
dotnet run --project src/TheLegacy.Console

# Run tests
dotnet test
```

On first run, the console app downloads the Scryfall oracle card database (~60MB). This is cached locally in a `data/` directory.

## Feature Roadmap

### Foundation

| # | Feature | Status | Date |
|---|---------|--------|------|
| 1 | Project structure & solution setup | ✅ Done | 2026-02-23 |
| 2 | Scryfall bulk data integration | ✅ Done | 2026-02-23 |
| 3 | Card domain model | ✅ Done | 2026-02-23 |
| 4 | Command architecture (UI-agnostic) | ✅ Done | 2026-02-23 |
| 5 | Zone & game state model | ✅ Done | 2026-02-23 |

### Rules Engine

| # | Feature | Status | Date |
|---|---------|--------|------|
| 6 | Turn structure (phase/step state machine) | 🔲 Planned | — |
| 7 | Basic actions (draw, play land, cast) | 🔲 Planned | — |
| 8 | Mana system | 🔲 Planned | — |
| 9 | Combat system | 🔲 Planned | — |
| 10 | Rules engine integration | 🔲 Planned | — |
| 11 | Keyword abilities | 🔲 Planned | — |
| 12 | Triggered & activated abilities | 🔲 Planned | — |
| 13 | Targeting & legality | 🔲 Planned | — |
| 14 | State-based actions | 🔲 Planned | — |
| 15 | Continuous effects & layers | 🔲 Planned | — |
| 16 | Rules questions | 🔲 Planned | — |

### Card Searcher

| # | Feature | Status | Date |
|---|---------|--------|------|
| 17 | Card searcher | 🔲 Planned | — |

### Deck Building

| # | Feature | Status | Date |
|---|---------|--------|------|
| 18 | Deck building & validation | 🔲 Planned | — |

### AI Opponent

| # | Feature | Status | Date |
|---|---------|--------|------|
| 19 | AI opponent | 🔲 Planned | — |

### Web App

| # | Feature | Status | Date |
|---|---------|--------|------|
| 20 | Web app frontend | 🔲 Planned | — |

## Legal

TheLegacy is unofficial Fan Content permitted under the [Fan Content Policy](https://company.wizards.com/en/legal/fancontentpolicy). Not approved/endorsed by Wizards. Portions of the materials used are property of Wizards of the Coast. &copy; Wizards of the Coast LLC.

The literal and graphical information presented in this project about Magic: The Gathering, including card images and mana symbols, is copyright Wizards of the Coast, LLC. TheLegacy is not produced by or endorsed by Wizards of the Coast.

Card data provided by [Scryfall](https://scryfall.com). Scryfall is not produced by or endorsed by Wizards of the Coast.
