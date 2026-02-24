using TheLegacy.Core.Enums;

namespace TheLegacy.Core.Models;

public class Card
{
    public required Guid OracleId { get; init; }
    public required string Name { get; init; }
    public ManaAmount ManaCost { get; init; } = new();
    public decimal Cmc { get; init; }

    public Color Colors { get; init; }
    public Color ColorIdentity { get; init; }

    public CardType Types { get; init; }
    public Supertype Supertypes { get; init; }
    public IReadOnlyList<string> Subtypes { get; init; } = [];
    public string TypeLine { get; init; } = string.Empty;

    public string OracleText { get; init; } = string.Empty;
    public IReadOnlyList<string> Keywords { get; init; } = [];

    public string? Power { get; init; }
    public string? Toughness { get; init; }
    public string? Loyalty { get; init; }

    public Rarity Rarity { get; init; }
    public string SetCode { get; init; } = string.Empty;

    public string? Layout { get; init; }

    public override string ToString() => $"{Name} ({ManaCost})";
}
