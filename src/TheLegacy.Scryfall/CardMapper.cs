using TheLegacy.Core.Enums;
using TheLegacy.Core.Models;

namespace TheLegacy.Scryfall;

public static class CardMapper
{
    public static Card ToCard(ScryfallCard scryfall)
    {
        return new Card
        {
            OracleId = scryfall.OracleId,
            Name = scryfall.Name,
            ManaCost = ManaAmount.Parse(scryfall.ManaCost ?? string.Empty),
            Cmc = scryfall.Cmc,
            Colors = ParseColors(scryfall.Colors),
            ColorIdentity = ParseColors(scryfall.ColorIdentity),
            Types = ParseTypes(scryfall.TypeLine),
            Supertypes = ParseSupertypes(scryfall.TypeLine),
            Subtypes = ParseSubtypes(scryfall.TypeLine),
            TypeLine = scryfall.TypeLine,
            OracleText = scryfall.OracleText ?? string.Empty,
            Keywords = scryfall.Keywords,
            Power = scryfall.Power,
            Toughness = scryfall.Toughness,
            Loyalty = scryfall.Loyalty,
            Rarity = ParseRarity(scryfall.Rarity),
            SetCode = scryfall.SetCode,
            Layout = scryfall.Layout,
        };
    }

    public static IReadOnlyList<Card> ToCards(IEnumerable<ScryfallCard> scryfallCards)
    {
        return scryfallCards.Select(ToCard).ToList();
    }

    private static Color ParseColors(IEnumerable<string>? colors)
    {
        if (colors is null) return Color.Colorless;

        var result = Color.Colorless;
        foreach (var c in colors)
        {
            result |= c switch
            {
                "W" => Color.White,
                "U" => Color.Blue,
                "B" => Color.Black,
                "R" => Color.Red,
                "G" => Color.Green,
                _ => Color.Colorless,
            };
        }
        return result;
    }

    private static CardType ParseTypes(string typeLine)
    {
        var mainTypes = typeLine.Split('—')[0].Trim();
        var result = CardType.None;

        if (mainTypes.Contains("Artifact", StringComparison.OrdinalIgnoreCase)) result |= CardType.Artifact;
        if (mainTypes.Contains("Battle", StringComparison.OrdinalIgnoreCase)) result |= CardType.Battle;
        if (mainTypes.Contains("Creature", StringComparison.OrdinalIgnoreCase)) result |= CardType.Creature;
        if (mainTypes.Contains("Enchantment", StringComparison.OrdinalIgnoreCase)) result |= CardType.Enchantment;
        if (mainTypes.Contains("Instant", StringComparison.OrdinalIgnoreCase)) result |= CardType.Instant;
        if (mainTypes.Contains("Land", StringComparison.OrdinalIgnoreCase)) result |= CardType.Land;
        if (mainTypes.Contains("Planeswalker", StringComparison.OrdinalIgnoreCase)) result |= CardType.Planeswalker;
        if (mainTypes.Contains("Sorcery", StringComparison.OrdinalIgnoreCase)) result |= CardType.Sorcery;
        if (mainTypes.Contains("Kindred", StringComparison.OrdinalIgnoreCase)) result |= CardType.Kindred;

        return result;
    }

    private static Supertype ParseSupertypes(string typeLine)
    {
        var mainTypes = typeLine.Split('—')[0].Trim();
        var result = Supertype.None;

        if (mainTypes.Contains("Basic", StringComparison.OrdinalIgnoreCase)) result |= Supertype.Basic;
        if (mainTypes.Contains("Legendary", StringComparison.OrdinalIgnoreCase)) result |= Supertype.Legendary;
        if (mainTypes.Contains("Snow", StringComparison.OrdinalIgnoreCase)) result |= Supertype.Snow;
        if (mainTypes.Contains("World", StringComparison.OrdinalIgnoreCase)) result |= Supertype.World;

        return result;
    }

    private static IReadOnlyList<string> ParseSubtypes(string typeLine)
    {
        var parts = typeLine.Split('—');
        if (parts.Length < 2) return [];

        return parts[1]
            .Split(' ', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries)
            .ToList();
    }

    private static Rarity ParseRarity(string rarity)
    {
        return rarity.ToLowerInvariant() switch
        {
            "common" => Rarity.Common,
            "uncommon" => Rarity.Uncommon,
            "rare" => Rarity.Rare,
            "mythic" => Rarity.Mythic,
            "special" => Rarity.Special,
            "bonus" => Rarity.Bonus,
            _ => Rarity.Common,
        };
    }
}
